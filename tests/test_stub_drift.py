# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Catches drift between `__init__.pyi` stubs and the compiled bindings.

The stub file is hand-written, so a `#[pymethod]` rename or a new
`#[pyo3(signature = ...)]` parameter on the Rust side has to be mirrored
manually. These tests fail loudly when that mirror lapses.
"""

import ast
import inspect
from pathlib import Path

import frequenz.microgrid_component_graph as mcg

_PUBLIC_RUNTIME_CLASSES = (
    mcg.ComponentGraph,
    mcg.ComponentGraphConfig,
    mcg.FormulaOverrides,
)

_STUB_PATH = Path(mcg.__file__).parent / "__init__.pyi"


def _parse_stub_classes() -> dict[str, dict[str, list[str]]]:
    """Parse the stub into ``{ClassName: {method_name: [param_name, ...]}}``."""
    tree = ast.parse(_STUB_PATH.read_text())
    out: dict[str, dict[str, list[str]]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods: dict[str, list[str]] = {}
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            args = item.args
            methods[item.name] = [a.arg for a in args.args] + [
                a.arg for a in args.kwonlyargs
            ]
        out[node.name] = methods
    return out


def test_stub_and_runtime_methods_agree() -> None:
    """Public method names in the stub must match those on the runtime class."""
    stub = _parse_stub_classes()
    for cls in _PUBLIC_RUNTIME_CLASSES:
        stub_methods = {
            name for name in stub.get(cls.__name__, {}) if not name.startswith("_")
        }
        runtime_methods = {
            name
            for name in dir(cls)
            if not name.startswith("_") and callable(getattr(cls, name))
        }
        assert stub_methods == runtime_methods, (
            f"{cls.__name__} method drift:\n"
            f"  in stub but not runtime: {sorted(stub_methods - runtime_methods)}\n"
            f"  in runtime but not stub: {sorted(runtime_methods - stub_methods)}"
        )


def test_stub_and_runtime_init_params_agree() -> None:
    """`__init__` parameter names in the stub must match the runtime signature.

    Skips classes where the runtime signature is not introspectable
    (pyo3 fails to expose one when ``text_signature`` contains an
    expression it can't parse).
    """
    stub = _parse_stub_classes()
    for cls in _PUBLIC_RUNTIME_CLASSES:
        stub_params = [
            p for p in stub.get(cls.__name__, {}).get("__init__", []) if p != "self"
        ]
        try:
            runtime_sig = inspect.signature(cls)
        except ValueError:
            continue
        runtime_params = list(runtime_sig.parameters.keys())
        assert stub_params == runtime_params, (
            f"{cls.__name__}.__init__ param drift:\n"
            f"  stub:    {stub_params}\n"
            f"  runtime: {runtime_params}"
        )


_NON_LITERAL = "<non-literal stub default>"

# pyo3 exposes no introspectable signature for these classes (their
# `text_signature` holds an expression `inspect` can not parse), so the
# defaults test can not cover them.  The test pins this set: a class that
# starts (or stops) being skipped fails the run instead of being skipped
# silently.
_KNOWN_NOT_INTROSPECTABLE = frozenset({"ComponentGraph"})


def _literal_or_marker(node: ast.expr) -> object:
    """Evaluate a stub default, or return the ``_NON_LITERAL`` marker."""
    try:
        return ast.literal_eval(node)
    except (TypeError, ValueError):
        return _NON_LITERAL


def _parse_stub_init_defaults() -> dict[str, dict[str, object]]:
    """Parse the stub into ``{ClassName: {param_name: default_value}}``.

    Only ``__init__`` parameters with a default are included. A default
    that is not a plain literal (like ``False`` or ``None``) is stored as
    the ``_NON_LITERAL`` marker; it never equals a runtime value, so a
    comparison against it fails loudly.
    """
    tree = ast.parse(_STUB_PATH.read_text())
    out: dict[str, dict[str, object]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef) or item.name != "__init__":
                continue
            args = item.args
            defaults: dict[str, object] = {}
            positional = args.posonlyargs + args.args
            for arg, default in zip(positional[-len(args.defaults) :], args.defaults):
                defaults[arg.arg] = _literal_or_marker(default)
            for kwarg, kw_default in zip(args.kwonlyargs, args.kw_defaults):
                if kw_default is not None:
                    defaults[kwarg.arg] = _literal_or_marker(kw_default)
            out[node.name] = defaults
    return out


def test_stub_and_runtime_init_defaults_agree() -> None:
    """`__init__` default values in the stub must match the runtime signature.

    The parameter-name test above can not catch a default changed on only
    one side -- for example a flag like `prefer_meters_in_component_formulas`
    flipped in the Rust `#[pyo3(signature = ...)]` but not in the stub.
    Type checkers and IDEs would then report the wrong default for a flag
    that inverts behavior.

    Classes without an introspectable runtime signature can not be checked.
    The known set of such classes is pinned in `_KNOWN_NOT_INTROSPECTABLE`,
    so a new silent skip fails the test.
    """
    stub_defaults = _parse_stub_init_defaults()
    skipped: set[str] = set()
    for cls in _PUBLIC_RUNTIME_CLASSES:
        try:
            runtime_sig = inspect.signature(cls)
        except ValueError:
            skipped.add(cls.__name__)
            continue
        runtime_defaults = {
            name: param.default
            for name, param in runtime_sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }
        cls_stub_defaults = stub_defaults.get(cls.__name__, {})
        assert cls_stub_defaults == runtime_defaults, (
            f"{cls.__name__}.__init__ default drift:\n"
            f"  stub:    {cls_stub_defaults}\n"
            f"  runtime: {runtime_defaults}"
        )
    assert skipped == _KNOWN_NOT_INTROSPECTABLE, (
        "classes skipped by the defaults check changed: "
        f"{sorted(skipped)} (expected {sorted(_KNOWN_NOT_INTROSPECTABLE)}); "
        "update `_KNOWN_NOT_INTROSPECTABLE` and check those stub defaults by hand"
    )
