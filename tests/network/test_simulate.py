"""Tests for hydroflow.network.simulate (integration tests, require WNTR)."""

import pytest

wntr = pytest.importorskip("wntr")

from hydroflow.network.errors import SimulationError  # noqa: E402
from hydroflow.network.model import WaterNetwork  # noqa: E402
from hydroflow.network.results import NetworkResults  # noqa: E402
from hydroflow.network.simulate import simulate  # noqa: E402


def _simple_network() -> WaterNetwork:
    """R1 --P1--> J1 --P2--> J2 (with demand at J2)."""
    net = WaterNetwork("Test")
    net.add_reservoir("R1", head=125.0)
    net.add_junction("J1", elevation=100.0)
    net.add_junction("J2", elevation=95.0, base_demand=0.005)
    net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
    net.add_pipe("P2", "J1", "J2", length=300.0, diameter=0.2, roughness=130.0)
    return net


class TestSimulate:
    def test_basic_simulation(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="24h", timestep="1h")
        assert isinstance(results, NetworkResults)

    def test_returns_pressures(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert not results.pressures.empty
        assert "J1" in results.pressures.columns
        assert "J2" in results.pressures.columns

    def test_returns_flows(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert not results.flows.empty
        assert "P1" in results.flows.columns

    def test_returns_velocities(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert not results.velocities.empty

    def test_timedelta_index(self) -> None:
        import pandas as pd

        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert isinstance(results.pressures.index, pd.TimedeltaIndex)
        assert isinstance(results.flows.index, pd.TimedeltaIndex)

    def test_duration_as_seconds(self) -> None:
        net = _simple_network()
        results = simulate(net, duration=7200, timestep=3600)
        assert isinstance(results, NetworkResults)

    def test_unknown_backend_raises(self) -> None:
        net = _simple_network()
        with pytest.raises(SimulationError, match="Unknown backend"):
            simulate(net, backend="invalid")

    def test_wntr_backend(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h", backend="wntr")
        assert isinstance(results, NetworkResults)

    def test_pressures_are_positive(self) -> None:
        """For this simple gravity-fed network, pressures should be non-negative.

        Reservoir nodes may report a tiny negative pressure (~1e-6) due to
        EPANET floating-point arithmetic, so we allow a small tolerance.
        """
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert (results.pressures >= -1e-4).all().all()

    def test_heads_present(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert not results.heads.empty

    def test_demands_present(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        assert not results.demands.empty

    def test_repr(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="2h", timestep="1h")
        r = repr(results)
        assert "NetworkResults" in r

    def test_short_timestep(self) -> None:
        net = _simple_network()
        results = simulate(net, duration="1h", timestep="15min")
        assert len(results.pressures) >= 4
