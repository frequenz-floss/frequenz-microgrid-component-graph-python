# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.microgrid_component_graph package."""

from frequenz import microgrid_component_graph


def test_loading() -> None:
    """Test that the microgrid_component_graph module loads correctly."""
    assert microgrid_component_graph is not None
