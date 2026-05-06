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
