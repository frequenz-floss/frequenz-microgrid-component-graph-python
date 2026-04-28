# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.microgrid_component_graph package."""

from typing import Any

import pytest
from frequenz.client.common.microgrid import MicrogridId
from frequenz.client.common.microgrid.components import ComponentId
from frequenz.client.microgrid.component import (
    Component,
    ComponentConnection,
    Converter,
    CryptoMiner,
    Electrolyzer,
    GridConnectionPoint,
    Hvac,
    Meter,
    Precharger,
    Relay,
    SolarInverter,
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
    # References the Meter (ID 2) measuring the Turbine (ID 3).
    assert (
        graph.wind_turbine_formula(wind_turbine_ids={ComponentId(3)})
        == "COALESCE(#2, #3, 0.0)"
    )

    # 4. Test Topology (Successors/Predecessors)
    # The predecessor of the Wind Turbine (3) should be the Meter (2)
    assert graph.predecessors(ComponentId(3)) == {
        Meter(id=ComponentId(2), microgrid_id=MicrogridId(1))
    }


def test_passthrough_voltage_transformer() -> None:
    """A pass-through component (VoltageTransformer) is transparent to
    validators and formula generators.

    Topology: ``Grid → VoltageTransformer → Meter → SolarInverter``.
    The VoltageTransformer maps to ``cg::ComponentCategory::PowerTransformer``,
    which is a pass-through. Building the graph succeeds (the validator
    walks past the transformer when checking the meter's predecessor),
    and topology queries return the *effective* (non-pass-through)
    neighbors.
    """
    grid = GridConnectionPoint(
        id=ComponentId(1), microgrid_id=MicrogridId(1), rated_fuse_current=100
    )
    transformer = VoltageTransformer(
        id=ComponentId(2),
        microgrid_id=MicrogridId(1),
        primary_voltage=20_000.0,
        secondary_voltage=400.0,
    )
    meter = Meter(id=ComponentId(3), microgrid_id=MicrogridId(1))
    inverter = SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1))

    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={grid, transformer, meter, inverter},
        connections={
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        },
    )

    # All four components are in the graph.
    assert graph.components() == {grid, transformer, meter, inverter}

    # The meter's effective predecessor is the grid (the transformer is
    # walked past).
    assert graph.predecessors(ComponentId(3)) == {grid}

    # The grid's effective successor is the meter (skipping the
    # transformer).
    assert graph.successors(ComponentId(1)) == {meter}

    # raw_predecessors / raw_successors expose the transformer.
    assert graph.raw_predecessors(ComponentId(3)) == {transformer}
    assert graph.raw_successors(ComponentId(1)) == {transformer}


@pytest.mark.parametrize(
    "passthrough_class, passthrough_kwargs",
    [
        (Converter, {}),
        (Precharger, {}),
        (Electrolyzer, {}),
        (Hvac, {}),
        (CryptoMiner, {}),
        (Relay, {}),
    ],
)
def test_passthrough_category_recognized(
    passthrough_class: type, passthrough_kwargs: dict[str, Any]
) -> None:
    """Each pass-through component class added in this commit is
    recognized by the bindings, and the meter beneath it sees the grid
    as its effective predecessor.

    Topology: ``Grid → <PT> → Meter → SolarInverter``.
    """
    grid = GridConnectionPoint(
        id=ComponentId(1), microgrid_id=MicrogridId(1), rated_fuse_current=100
    )
    passthrough = passthrough_class(
        id=ComponentId(2), microgrid_id=MicrogridId(1), **passthrough_kwargs
    )
    meter = Meter(id=ComponentId(3), microgrid_id=MicrogridId(1))
    inverter = SolarInverter(id=ComponentId(4), microgrid_id=MicrogridId(1))

    graph: microgrid_component_graph.ComponentGraph[
        Component, ComponentConnection, ComponentId
    ] = microgrid_component_graph.ComponentGraph(
        components={grid, passthrough, meter, inverter},
        connections={
            ComponentConnection(source=ComponentId(1), destination=ComponentId(2)),
            ComponentConnection(source=ComponentId(2), destination=ComponentId(3)),
            ComponentConnection(source=ComponentId(3), destination=ComponentId(4)),
        },
    )

    assert passthrough in graph.components()
    assert graph.predecessors(ComponentId(3)) == {grid}
