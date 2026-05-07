# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Behavioral tests for `ComponentGraphConfig` formula preferences.

These tests build a small, controllable graph (Grid -> Meter -> Device)
for each per-category formula method and assert the actual formula
output for the four meter/device-preference combinations:

    * default config                -> meter primary
    * global False                  -> device primary
    * per-formula override = True   -> meter primary (override wins)
    * per-formula override = False  -> device primary (override wins)

The drift test in `test_stub_drift.py` only checks signatures; this
file catches actual mis-wiring -- a swapped override, an inverted
boolean, or a missing builder call would change the formula output.
"""

from collections.abc import Callable
from typing import Any

import pytest
from frequenz.client.common.microgrid import MicrogridId
from frequenz.client.common.microgrid.components import ComponentId
from frequenz.client.microgrid.component import (
    AcEvCharger,
    BatteryInverter,
    Chp,
    ComponentConnection,
    GridConnectionPoint,
    LiIonBattery,
    Meter,
    SolarInverter,
    SteamBoiler,
    WindTurbine,
)

from frequenz.microgrid_component_graph import (
    ComponentGraph,
    ComponentGraphConfig,
    FormulaGenerationError,
    FormulaOverrides,
)

_MGRID = MicrogridId(1)

# In every per-category topology built below, component #2 is the meter
# and #3 is the device that appears in the formula.
_METER_PRIMARY = "COALESCE(#2, #3, 0.0)"
_DEVICE_PRIMARY = "COALESCE(#3, #2, 0.0)"

# Each per-category graph builder takes an optional `config` and returns a
# graph rooted at the same Grid -> Meter pair, so the assertion strings
# above are the same across categories.
GraphBuilder = Callable[[ComponentGraphConfig | None], ComponentGraph[Any, Any, Any]]


def _conn(source: int, dest: int) -> ComponentConnection:
    return ComponentConnection(
        source=ComponentId(source), destination=ComponentId(dest)
    )


def _grid() -> GridConnectionPoint:
    return GridConnectionPoint(
        id=ComponentId(1), microgrid_id=_MGRID, rated_fuse_current=100
    )


def _meter() -> Meter:
    return Meter(id=ComponentId(2), microgrid_id=_MGRID)


def _pv_graph(
    config: ComponentGraphConfig | None = None,
) -> ComponentGraph[Any, Any, Any]:
    return ComponentGraph(
        components={
            _grid(),
            _meter(),
            SolarInverter(id=ComponentId(3), microgrid_id=_MGRID),
        },
        connections={_conn(1, 2), _conn(2, 3)},
        config=config or ComponentGraphConfig(),
    )


def _wind_graph(
    config: ComponentGraphConfig | None = None,
) -> ComponentGraph[Any, Any, Any]:
    return ComponentGraph(
        components={
            _grid(),
            _meter(),
            WindTurbine(id=ComponentId(3), microgrid_id=_MGRID),
        },
        connections={_conn(1, 2), _conn(2, 3)},
        config=config or ComponentGraphConfig(),
    )


def _battery_graph(
    config: ComponentGraphConfig | None = None,
) -> ComponentGraph[Any, Any, Any]:
    # Grid -> Meter -> BatteryInverter -> Battery; the formula references
    # the inverter (#3) as the device, the battery (#4) doesn't appear.
    return ComponentGraph(
        components={
            _grid(),
            _meter(),
            BatteryInverter(id=ComponentId(3), microgrid_id=_MGRID),
            LiIonBattery(id=ComponentId(4), microgrid_id=_MGRID),
        },
        connections={_conn(1, 2), _conn(2, 3), _conn(3, 4)},
        config=config or ComponentGraphConfig(),
    )


def _chp_graph(
    config: ComponentGraphConfig | None = None,
) -> ComponentGraph[Any, Any, Any]:
    return ComponentGraph(
        components={
            _grid(),
            _meter(),
            Chp(id=ComponentId(3), microgrid_id=_MGRID),
        },
        connections={_conn(1, 2), _conn(2, 3)},
        config=config or ComponentGraphConfig(),
    )


def _ev_graph(
    config: ComponentGraphConfig | None = None,
) -> ComponentGraph[Any, Any, Any]:
    return ComponentGraph(
        components={
            _grid(),
            _meter(),
            AcEvCharger(id=ComponentId(3), microgrid_id=_MGRID),
        },
        connections={_conn(1, 2), _conn(2, 3)},
        config=config or ComponentGraphConfig(),
    )


def _steam_boiler_graph(
    config: ComponentGraphConfig | None = None,
) -> ComponentGraph[Any, Any, Any]:
    return ComponentGraph(
        components={
            _grid(),
            _meter(),
            SteamBoiler(id=ComponentId(3), microgrid_id=_MGRID),
        },
        connections={_conn(1, 2), _conn(2, 3)},
        config=config or ComponentGraphConfig(),
    )


_CATEGORIES = [
    pytest.param(_pv_graph, "pv_formula", "prefer_meters_in_pv_formula", id="pv"),
    pytest.param(
        _wind_graph,
        "wind_turbine_formula",
        "prefer_meters_in_wind_turbine_formula",
        id="wind_turbine",
    ),
    pytest.param(
        _battery_graph,
        "battery_formula",
        "prefer_meters_in_battery_formula",
        id="battery",
    ),
    pytest.param(_chp_graph, "chp_formula", "prefer_meters_in_chp_formula", id="chp"),
    pytest.param(
        _ev_graph,
        "ev_charger_formula",
        "prefer_meters_in_ev_charger_formula",
        id="ev_charger",
    ),
    pytest.param(
        _steam_boiler_graph,
        "steam_boiler_formula",
        "prefer_meters_in_steam_boiler_formula",
        id="steam_boiler",
    ),
]


@pytest.mark.parametrize("build_graph,method,override_field", _CATEGORIES)
def test_default_config_prefers_meter(
    build_graph: GraphBuilder,
    method: str,
    override_field: str,  # pylint: disable=unused-argument
) -> None:
    """Default config selects the meter as the primary source."""
    formula = getattr(build_graph(None), method)(None)
    assert formula == _METER_PRIMARY


@pytest.mark.parametrize("build_graph,method,override_field", _CATEGORIES)
def test_global_false_prefers_device(
    build_graph: GraphBuilder,
    method: str,
    override_field: str,  # pylint: disable=unused-argument
) -> None:
    """Setting `prefer_meters_in_component_formulas=False` selects the device."""
    config = ComponentGraphConfig(prefer_meters_in_component_formulas=False)
    formula = getattr(build_graph(config), method)(None)
    assert formula == _DEVICE_PRIMARY


@pytest.mark.parametrize("build_graph,method,override_field", _CATEGORIES)
def test_override_true_wins_over_global_false(
    build_graph: GraphBuilder, method: str, override_field: str
) -> None:
    """A `True` per-formula override flips back to meter despite a `False` global."""
    config = ComponentGraphConfig(
        prefer_meters_in_component_formulas=False,
        formula_overrides=FormulaOverrides(**{override_field: True}),
    )
    formula = getattr(build_graph(config), method)(None)
    assert formula == _METER_PRIMARY


@pytest.mark.parametrize("build_graph,method,override_field", _CATEGORIES)
def test_override_false_wins_over_global_true(
    build_graph: GraphBuilder, method: str, override_field: str
) -> None:
    """A `False` per-formula override flips to device despite a `True` global."""
    config = ComponentGraphConfig(
        prefer_meters_in_component_formulas=True,
        formula_overrides=FormulaOverrides(**{override_field: False}),
    )
    formula = getattr(build_graph(config), method)(None)
    assert formula == _DEVICE_PRIMARY


def _empty_graph() -> ComponentGraph[Any, Any, Any]:
    return ComponentGraph(
        components={_grid(), _meter()},
        connections={_conn(1, 2)},
    )


def test_steam_boiler_formula_with_no_ids_returns_zero() -> None:
    """`steam_boiler_formula(None)` on a graph with no steam boilers is `0.0`."""
    assert _empty_graph().steam_boiler_formula(None) == "0.0"


def test_steam_boiler_formula_with_empty_set_returns_zero() -> None:
    """`steam_boiler_formula(set())` short-circuits to `0.0`."""
    assert _empty_graph().steam_boiler_formula(set()) == "0.0"


def test_steam_boiler_formula_unknown_id_raises() -> None:
    """An ID that doesn't exist in the graph raises `FormulaGenerationError`."""
    with pytest.raises(FormulaGenerationError, match="999"):
        _empty_graph().steam_boiler_formula({ComponentId(999)})


def test_steam_boiler_formula_wrong_category_id_raises() -> None:
    """An ID that exists but isn't a steam boiler raises `FormulaGenerationError`."""
    with pytest.raises(FormulaGenerationError, match="not a steam boiler"):
        _empty_graph().steam_boiler_formula({ComponentId(2)})
