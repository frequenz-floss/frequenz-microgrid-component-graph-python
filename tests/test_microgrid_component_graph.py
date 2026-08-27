# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.microgrid_component_graph package."""

from typing import Any, NoReturn

import pytest
from frequenz.client.common.microgrid import MicrogridId
from frequenz.client.common.microgrid.components import ComponentId
from frequenz.client.microgrid.component import (
    AcEvCharger,
    Battery,
    BatteryInverter,
    Chp,
    Component,
    ComponentConnection,
    Converter,
    CryptoMiner,
    DcEvCharger,
    Electrolyzer,
    GridConnectionPoint,
    Hvac,
    HybridEvCharger,
    HybridInverter,
    LiIonBattery,
    Meter,
    NaIonBattery,
    Precharger,
    Relay,
    SolarInverter,
    SteamBoiler,
    UnrecognizedBattery,
    UnrecognizedComponent,
    UnrecognizedEvCharger,
    UnrecognizedInverter,
    UnspecifiedBattery,
    UnspecifiedComponent,
    UnspecifiedEvCharger,
    UnspecifiedInverter,
    VoltageTransformer,
    WindTurbine,
)

from frequenz import microgrid_component_graph


def test_graph_creation() -> None:
    """Test that the microgrid_component_graph module loads correctly."""
    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
            SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
        },
        connections={
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(1), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(4)),
        },
    )
    assert graph.components() == {
        GridConnectionPoint(
            id=ComponentId(1), microgrid_id=MicrogridId(1), rated_fuse_current=100
        ),
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
        Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
        SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
    }
    assert graph.connections() == {
        ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
        ComponentConnection(source=ComponentId(1), destination=ComponentId(3)),
        ComponentConnection(source=ComponentId(2), destination=ComponentId(4)),
    }
    assert graph.components(matching_ids=[ComponentId(2), ComponentId(3)]) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
        Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
    }
    assert graph.components(matching_ids=ComponentId(1)) == {
        GridConnectionPoint(
            id=ComponentId(1), microgrid_id=MicrogridId(1), rated_fuse_current=100
        )
    }
    assert graph.components(matching_types=Meter) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
        Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
    }
    assert graph.components(matching_types=[Meter, GridConnectionPoint]) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
        Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
        GridConnectionPoint(
            id=ComponentId(1), microgrid_id=MicrogridId(1), rated_fuse_current=100
        ),
    }
    assert graph.components(
        matching_types=[Meter, SolarInverter],
        matching_ids=[ComponentId(1), ComponentId(3), ComponentId(4)],
    ) == {
        Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
        SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
    }


def test_wind_turbine_graph() -> None:
    """Test graph creation and formula generation for Wind Turbines."""
    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            WindTurbine(id=ComponentId(3), microgrid_id=MicrogridId(1)),
        },
        connections={
            # Grid -> Meter -> Wind Turbine
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
        },
    )

    # 1. Test Component Retrieval
    assert graph.components(matching_types=WindTurbine) == {
        WindTurbine(id=ComponentId(3), microgrid_id=MicrogridId(1))
    }

    # 2. Test Combined Retrieval (Meter + Wind)
    assert graph.components(matching_types=[Meter, WindTurbine]) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
        WindTurbine(id=ComponentId(3), microgrid_id=MicrogridId(1)),
    }

    # 3. Test Formula Generation
    # Component-first by default: the turbine (ID 3) is the primary source,
    # the meter (ID 2) the fallback.
    assert (
        graph.wind_turbine_formula(wind_turbine_ids={ComponentId(3)})
        == "COALESCE(#3, #2, 0.0)"
    )

    # 4. Test Topology (Successors/Predecessors)
    # The predecessor of the Wind Turbine (3) should be the Meter (2)
    assert graph.predecessors(ComponentId(3)) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1))
    }


def test_steam_boiler_graph() -> None:
    """Test graph creation and formula generation for Steam Boilers."""
    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            SteamBoiler(id=ComponentId(3), microgrid_id=MicrogridId(1)),
        },
        connections={
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
        },
    )

    assert graph.components(matching_types=SteamBoiler) == {
        SteamBoiler(id=ComponentId(3), microgrid_id=MicrogridId(1))
    }
    assert (
        graph.steam_boiler_formula(steam_boiler_ids={ComponentId(3)})
        == "COALESCE(#3, #2, 0.0)"
    )


def test_consumer_formula_meter_subtraction() -> None:
    """Test the consumer formula's meter-subtraction grouping.

    The non-consumer components behind one internal meter are subtracted
    as one group: the meter reading first, the component readings as the
    fallback.
    """
    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
            SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
        },
        connections={
            # Grid -> Grid Meter -> PV Meter -> PV Inverter
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        },
    )

    # The PV group behind meter #3 is subtracted from the grid meter #2 as
    # one COALESCE term, and consumption is clamped at zero.
    assert graph.consumer_formula() == "MAX(#2 - COALESCE(#3, #4, 0.0), 0.0)"


def test_relay_is_passthrough() -> None:
    """`Relay` maps to cg's `Breaker`, a pass-through category.

    A Relay placed between a Meter and a SolarInverter should be
    transparent: cg walks past it when answering `predecessors`/
    `successors`, and the PV formula references only the Meter and
    the inverter.
    """
    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            Relay(id=ComponentId(3), microgrid_id=MicrogridId(1)),
            SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
        },
        connections={
            # Grid -> Meter -> Relay -> SolarInverter
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        },
    )

    # Neighbor queries walk past the Relay.
    assert graph.predecessors(ComponentId(4)) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
    }
    assert graph.successors(ComponentId(2)) == {
        SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
    }
    # And the formula references the Meter and the inverter only --
    # the Relay (#3) does not appear.
    assert (
        graph.pv_ac_coalesce_formula(pv_inverter_ids={ComponentId(4)})
        == "COALESCE(#2, #4)"
    )


def test_hvac_is_passthrough() -> None:
    """`Hvac` maps to cg's `Hvac`, a pass-through category.

    An Hvac placed between the Grid and a Meter should be
    transparent: `successors(Grid)` walks past it to the Meter,
    and the PV formula references only the Meter and the inverter.
    """
    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Hvac(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
            SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
        },
        connections={
            # Grid -> Hvac -> Meter -> SolarInverter
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        },
    )

    # Neighbor queries walk past the Hvac.
    assert graph.successors(ComponentId(1)) == {
        Meter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
    }
    assert graph.predecessors(ComponentId(3)) == {
        GridConnectionPoint(
            id=ComponentId(1),
            microgrid_id=MicrogridId(1),
            rated_fuse_current=100,
        ),
    }
    # And the formula references the Meter and the inverter only --
    # the Hvac (#2) does not appear.
    assert (
        graph.pv_ac_coalesce_formula(pv_inverter_ids={ComponentId(4)})
        == "COALESCE(#3, #4)"
    )


# Pass-through categories from the microgrid client.
_PASS_THROUGH_CLASSES = (
    Converter,
    CryptoMiner,
    Electrolyzer,
    Hvac,
    Precharger,
    Relay,
    VoltageTransformer,
)


def _build_target(cls: type[Component], cid: int) -> Component:
    """Construct a `cls` instance, supplying ctor args its variants need."""
    extra: dict[str, Any] = {}
    if cls is UnrecognizedComponent:
        extra["category"] = 999
    elif cls in (UnrecognizedBattery, UnrecognizedEvCharger, UnrecognizedInverter):
        extra["type"] = 999
    elif cls is VoltageTransformer:
        extra["primary_voltage"] = 20_000.0
        extra["secondary_voltage"] = 400.0
    return cls(id=ComponentId(cid), microgrid_id=MicrogridId(1), **extra)


@pytest.mark.parametrize(
    "component_type",
    [
        # Pass-through categories: transparent to the graph traversal until
        # explicit handling is added for them.
        Converter,
        CryptoMiner,
        Electrolyzer,
        Hvac,
        Precharger,
        Relay,
        VoltageTransformer,
        # Battery subtypes
        LiIonBattery,
        NaIonBattery,
        UnspecifiedBattery,
        UnrecognizedBattery,
        # EV chargers
        AcEvCharger,
        DcEvCharger,
        HybridEvCharger,
        UnspecifiedEvCharger,
        UnrecognizedEvCharger,
        # Inverters
        BatteryInverter,
        HybridInverter,
        SolarInverter,
        # Other producers and/or consumers.
        Chp,
        SteamBoiler,
    ],
)
def test_component_type_is_accepted(component_type: type[Component]) -> None:
    """Each mapped component class can be added to a graph.

    Builds the smallest topology that's valid for the category and
    asserts the instance ends up in the graph. Covers every concrete
    class the category mapping handles, except the ones already
    exercised by the topology-specific tests above (Grid/Meter/
    SolarInverter/WindTurbine/Relay/Hvac).
    """
    grid = GridConnectionPoint(
        id=ComponentId(1), microgrid_id=MicrogridId(1), rated_fuse_current=100
    )
    meter = Meter(id=ComponentId(2), microgrid_id=MicrogridId(1))

    if issubclass(component_type, Battery):
        # Grid -> Meter -> BatteryInverter -> battery_under_test
        target = _build_target(component_type, cid=4)
        components: set[Component] = {
            grid,
            meter,
            BatteryInverter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
            target,
        }
        connections = {
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        }
    elif component_type in (BatteryInverter, HybridInverter):
        # Grid -> Meter -> inverter_under_test -> LiIonBattery
        target = _build_target(component_type, cid=3)
        components = {
            grid,
            meter,
            target,
            LiIonBattery(id=ComponentId(4), microgrid_id=MicrogridId(1)),
        }
        connections = {
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        }
    elif component_type in _PASS_THROUGH_CLASSES:
        # Grid -> Meter -> pass_through_under_test -> SolarInverter
        target = _build_target(component_type, cid=3)
        components = {
            grid,
            meter,
            target,
            SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1)),
        }
        connections = {
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        }
    else:
        # Grid -> Meter -> leaf (EvChargers, Chp, SteamBoiler, SolarInverter).
        target = _build_target(component_type, cid=3)
        components = {grid, meter, target}
        connections = {
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
        }

    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components=components,
        connections=connections,
    )
    assert target in graph.components()


@pytest.mark.parametrize(
    "component_type",
    [
        # Map to cg::Unspecified, which the graph rejects up-front.
        UnspecifiedComponent,
        UnrecognizedComponent,
        # Map to cg::Inverter(Unspecified), which the graph also rejects
        # under the default config (allow_unspecified_inverters=False).
        UnspecifiedInverter,
        UnrecognizedInverter,
    ],
)
def test_unspecified_component_type_is_rejected(
    component_type: type[Component],
) -> None:
    """Classes whose mapping yields an Unspecified category fail at graph creation.

    The category mapping accepts these classes -- so the user-facing
    error is a topology-level one rather than ``Unsupported component
    category`` -- but the underlying crate refuses to construct a
    graph that contains an Unspecified component or Unspecified
    inverter.
    """
    target = _build_target(component_type, cid=3)
    with pytest.raises(microgrid_component_graph.InvalidGraphError):
        microgrid_component_graph.ComponentGraph(
            components={
                GridConnectionPoint(
                    id=ComponentId(1),
                    microgrid_id=MicrogridId(1),
                    rated_fuse_current=100,
                ),
                Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
                target,
            },
            connections={
                ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
                ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            },
        )


def _pv_graph_with_modes(
    *, provides_telemetry: bool | None, accepts_control: bool | None
) -> microgrid_component_graph.ComponentGraph[
    Component, ComponentConnection, ComponentId
]:
    """Build `Grid -> Meter -> SolarInverter`, with a mode on the inverter."""
    return microgrid_component_graph.ComponentGraph(
        components={
            GridConnectionPoint(
                id=ComponentId(1),
                microgrid_id=MicrogridId(1),
                rated_fuse_current=100,
            ),
            Meter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
            SolarInverter(
                id=ComponentId(3),
                microgrid_id=MicrogridId(1),
                _provides_telemetry=provides_telemetry,
                _accepts_control=accepts_control,
            ),
        },
        connections={
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
        },
    )


def test_operational_mode_default_is_unspecified() -> None:
    """Test that a component with no operational mode still provides telemetry.

    Both flags are `None` on a component built without them, which is the
    unspecified mode. It is treated as providing telemetry, so graphs that
    never set a mode keep their formulas.
    """
    graph = _pv_graph_with_modes(provides_telemetry=None, accepts_control=None)
    assert graph.pv_formula(None) == "COALESCE(#3, #2, 0.0)"


@pytest.mark.parametrize(
    "provides_telemetry, accepts_control",
    [
        pytest.param(True, True, id="control-and-telemetry"),
        pytest.param(True, False, id="telemetry-only"),
    ],
)
def test_operational_mode_with_telemetry_is_a_source(
    provides_telemetry: bool, accepts_control: bool
) -> None:
    """Test that a mode providing telemetry keeps the component as a source."""
    graph = _pv_graph_with_modes(
        provides_telemetry=provides_telemetry, accepts_control=accepts_control
    )
    assert graph.pv_formula(None) == "COALESCE(#3, #2, 0.0)"


@pytest.mark.parametrize(
    "provides_telemetry, accepts_control",
    [
        pytest.param(False, True, id="control-only"),
        pytest.param(False, False, id="inactive"),
    ],
)
def test_operational_mode_without_telemetry_is_not_a_source(
    provides_telemetry: bool, accepts_control: bool
) -> None:
    """Test that a mode providing no telemetry drops the component as a source.

    The inverter's own reading is gone; the meter above it measures it
    instead, and still counts as a PV meter because of it.
    """
    graph = _pv_graph_with_modes(
        provides_telemetry=provides_telemetry, accepts_control=accepts_control
    )
    assert graph.pv_formula(None) == "COALESCE(#2, 0.0)"


@pytest.mark.parametrize(
    "provides_telemetry, accepts_control",
    [
        pytest.param(False, None, id="control-unknown"),
        pytest.param(None, False, id="telemetry-unknown"),
    ],
)
def test_operational_mode_half_known_is_unspecified(
    provides_telemetry: bool | None, accepts_control: bool | None
) -> None:
    """Test that a half-known mode is not guessed at.

    A component can carry one flag without the other. Naming a mode from
    that would mean guessing the missing half, so the mode is unspecified
    and the component stays a measurement source -- even where the known
    flag is `_provides_telemetry=False`.
    """
    graph = _pv_graph_with_modes(
        provides_telemetry=provides_telemetry, accepts_control=accepts_control
    )
    assert graph.pv_formula(None) == "COALESCE(#3, #2, 0.0)"


def test_operational_mode_missing_accessors_is_unspecified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that a component without the mode accessors is still accepted.

    `provides_telemetry()` and `accepts_control()` arrived in
    frequenz-client-microgrid 0.18.4, and the assets client has no
    equivalent, so a supported component can carry neither. Such a
    component has an unspecified mode and stays a measurement source,
    rather than failing the graph. This mirrors the category lookup, which
    keeps working when a class is not present.

    The flags below say "no telemetry", so the two paths give different
    formulas and this test can tell them apart: only removing the methods
    leaves `#3` in the formula. If the removal ever stopped matching, the
    mode would read as `Inactive`, `#3` would drop out, and the test would
    fail rather than pass while checking nothing.
    """
    monkeypatch.delattr(Component, "provides_telemetry")
    monkeypatch.delattr(Component, "accepts_control")

    graph = _pv_graph_with_modes(provides_telemetry=False, accepts_control=False)
    assert graph.pv_formula(None) == "COALESCE(#3, #2, 0.0)"


def test_operational_mode_error_inside_accessor_is_not_hidden() -> None:
    """Test that an `AttributeError` from inside an accessor is passed on.

    A missing accessor means "mode unspecified". An accessor that is
    present but raises `AttributeError` from its own body is the caller's
    bug: reading that as an unspecified mode would hide it and leave the
    component measuring, which is the very thing the mode is meant to
    stop. The lookup and the call are therefore separate steps, so that a
    missing method reads as unspecified while an error out of the method
    body does not.
    """

    class BrokenMeter(Meter):
        """A meter whose accessor raises, standing in for a caller bug."""

        def provides_telemetry(self) -> NoReturn:
            """Raise, as a buggy override would.

            Raises:
                AttributeError: always.
            """
            raise AttributeError("nested attribute missing")

    with pytest.raises(AttributeError):
        microgrid_component_graph.ComponentGraph(
            components={
                GridConnectionPoint(
                    id=ComponentId(1),
                    microgrid_id=MicrogridId(1),
                    rated_fuse_current=100,
                ),
                BrokenMeter(id=ComponentId(2), microgrid_id=MicrogridId(1)),
                SolarInverter(id=ComponentId(3), microgrid_id=MicrogridId(1)),
            },
            connections={
                ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
                ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            },
        )
