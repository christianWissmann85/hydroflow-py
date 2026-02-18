"""Tests for hydroflow.network.plot (require matplotlib)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

plt = pytest.importorskip("matplotlib.pyplot")
pytest.importorskip("networkx")

from hydroflow.network.model import WaterNetwork  # noqa: E402
from hydroflow.network.plot import plot_network, plot_results  # noqa: E402

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _close_plots() -> None:  # type: ignore[misc]
    """Close all matplotlib figures after each test."""
    yield  # type: ignore[misc]
    plt.close("all")


def _simple_network(*, with_coords: bool = False) -> WaterNetwork:
    """R1 --P1--> J1 --P2--> J2."""
    net = WaterNetwork("Plot Test")
    coords_r = (0.0, 50.0) if with_coords else None
    coords_j1 = (50.0, 50.0) if with_coords else None
    coords_j2 = (100.0, 50.0) if with_coords else None
    net.add_reservoir("R1", head=125.0, coordinates=coords_r)
    net.add_junction("J1", elevation=100.0, coordinates=coords_j1)
    net.add_junction("J2", elevation=95.0, base_demand=0.005, coordinates=coords_j2)
    net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
    net.add_pipe("P2", "J1", "J2", length=300.0, diameter=0.2, roughness=130.0)
    return net


def _network_with_tank() -> WaterNetwork:
    """R1 --PMP1--> T1 --P1--> J1."""
    net = WaterNetwork("Tank Network")
    net.add_reservoir("R1", head=50.0, coordinates=(0.0, 0.0))
    net.add_tank(
        "T1", elevation=50.0, init_level=3.0, min_level=0.5,
        max_level=5.0, diameter=10.0, coordinates=(50.0, 0.0),
    )
    net.add_junction("J1", elevation=40.0, coordinates=(100.0, 0.0))
    net.add_pump("PMP1", "R1", "T1", power=50000.0)
    net.add_pipe("P1", "T1", "J1", length=500.0, diameter=0.3, roughness=130.0)
    return net


# ── Tests ────────────────────────────────────────────────────────────


class TestPlotEmpty:
    def test_raises_on_empty_network(self) -> None:
        net = WaterNetwork("Empty")
        with pytest.raises(ValueError, match="empty network"):
            plot_network(net)


class TestPlotTopology:
    def test_returns_axes(self) -> None:
        net = _simple_network()
        ax = plot_network(net)
        assert ax is not None
        assert hasattr(ax, "plot")  # quack like matplotlib Axes

    def test_with_coordinates(self) -> None:
        net = _simple_network(with_coords=True)
        ax = plot_network(net)
        assert ax is not None

    def test_spring_layout_fallback(self) -> None:
        net = _simple_network(with_coords=False)
        ax = plot_network(net)
        assert ax is not None

    def test_with_existing_axes(self) -> None:
        net = _simple_network()
        _fig, existing_ax = plt.subplots()
        ax = plot_network(net, ax=existing_ax)
        assert ax is existing_ax

    def test_node_labels_shown(self) -> None:
        net = _simple_network(with_coords=True)
        ax = plot_network(net, node_labels=True)
        texts = [t.get_text() for t in ax.texts]
        assert "J1" in texts

    def test_node_labels_hidden(self) -> None:
        net = _simple_network(with_coords=True)
        ax = plot_network(net, node_labels=False)
        texts = [t.get_text() for t in ax.texts]
        assert "J1" not in texts

    def test_custom_title(self) -> None:
        net = _simple_network()
        ax = plot_network(net, title="My Network")
        assert ax.get_title() == "My Network"

    def test_link_labels(self) -> None:
        net = _simple_network(with_coords=True)
        ax = plot_network(net, link_labels=True)
        texts = [t.get_text() for t in ax.texts]
        assert "P1" in texts


class TestPlotNodeAttribute:
    def test_colors_nodes_by_attribute(self) -> None:
        net = _simple_network(with_coords=True)
        attrs = {"R1": 125.0, "J1": 30.0, "J2": 25.0}
        ax = plot_network(net, node_attribute=attrs)
        assert ax is not None

    def test_link_attribute(self) -> None:
        net = _simple_network(with_coords=True)
        attrs = {"P1": 0.05, "P2": 0.03}
        ax = plot_network(net, link_attribute=attrs)
        assert ax is not None


class TestPlotReservoirMarker:
    def test_reservoir_rendered_as_square(self) -> None:
        net = _simple_network(with_coords=True)
        ax = plot_network(net)
        # Check that the legend has a "Reservoir" entry
        legend = ax.get_legend()
        assert legend is not None
        labels = [t.get_text() for t in legend.get_texts()]
        assert "Reservoir" in labels


class TestPlotWithTank:
    def test_tank_in_plot(self) -> None:
        net = _network_with_tank()
        ax = plot_network(net)
        legend = ax.get_legend()
        labels = [t.get_text() for t in legend.get_texts()]
        assert "Tank" in labels


class TestPlotResults:
    def _mock_results(self) -> MagicMock:
        """Create a mock NetworkResults with DataFrame-like objects."""
        import pandas as pd

        times = pd.to_timedelta([0, 3600, 7200], unit="s")
        pressures = pd.DataFrame(
            {"R1": [125.0, 125.0, 125.0], "J1": [30.0, 29.5, 29.0], "J2": [25.0, 24.5, 24.0]},
            index=times,
        )
        heads = pd.DataFrame(
            {"R1": [125.0, 125.0, 125.0], "J1": [130.0, 129.5, 129.0], "J2": [120.0, 119.5, 119.0]},
            index=times,
        )
        demands = pd.DataFrame(
            {"R1": [0.0, 0.0, 0.0], "J1": [0.0, 0.0, 0.0], "J2": [0.005, 0.005, 0.005]},
            index=times,
        )
        flows = pd.DataFrame(
            {"P1": [0.005, 0.005, 0.005], "P2": [0.005, 0.005, 0.005]},
            index=times,
        )
        velocities = pd.DataFrame(
            {"P1": [0.07, 0.07, 0.07], "P2": [0.16, 0.16, 0.16]},
            index=times,
        )

        results = MagicMock()
        results.pressures = pressures
        results.heads = heads
        results.demands = demands
        results.flows = flows
        results.velocities = velocities
        return results

    def test_plot_results_pressure(self) -> None:
        net = _simple_network(with_coords=True)
        results = self._mock_results()
        ax = plot_results(net, results, timestep=0, node_attribute="pressure")
        assert ax is not None

    def test_plot_results_velocity(self) -> None:
        net = _simple_network(with_coords=True)
        results = self._mock_results()
        ax = plot_results(
            net, results, timestep=1,
            node_attribute="pressure", link_attribute="velocity",
        )
        assert ax is not None

    def test_plot_results_returns_axes_type(self) -> None:
        net = _simple_network(with_coords=True)
        results = self._mock_results()
        ax = plot_results(net, results)
        assert type(ax).__name__ == "Axes" or hasattr(ax, "plot")
