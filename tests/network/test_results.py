"""Tests for hydroflow.network.results (unit tests with mock DataFrames)."""

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")

from hydroflow.network.results import NetworkResults  # noqa: E402


def _make_results(
    *,
    pressures: pd.DataFrame | None = None,
    flows: pd.DataFrame | None = None,
    velocities: pd.DataFrame | None = None,
    heads: pd.DataFrame | None = None,
    demands: pd.DataFrame | None = None,
) -> NetworkResults:
    """Build a NetworkResults from mock DataFrames."""
    idx = pd.to_timedelta([0, 3600, 7200], unit="s")

    if pressures is None:
        pressures = pd.DataFrame(
            {"J1": [25.0, 25.0, 25.0], "J2": [20.0, 20.0, 20.0]},
            index=idx,
        )
    if flows is None:
        flows = pd.DataFrame(
            {"P1": [0.01, 0.01, 0.01], "P2": [0.005, 0.005, 0.005]},
            index=idx,
        )
    if velocities is None:
        velocities = pd.DataFrame(
            {"P1": [0.5, 0.5, 0.5], "P2": [0.3, 0.3, 0.3]},
            index=idx,
        )
    if heads is None:
        heads = pd.DataFrame(
            {"J1": [125.0, 125.0, 125.0], "J2": [115.0, 115.0, 115.0]},
            index=idx,
        )
    if demands is None:
        demands = pd.DataFrame(
            {"J1": [0.0, 0.0, 0.0], "J2": [0.005, 0.005, 0.005]},
            index=idx,
        )

    return NetworkResults(
        pressures=pressures,
        flows=flows,
        velocities=velocities,
        heads=heads,
        demands=demands,
    )


class TestHealthCheck:
    def test_healthy_network(self) -> None:
        results = _make_results()
        warnings = results.health_check()
        assert warnings == []

    def test_negative_pressure(self) -> None:
        idx = pd.to_timedelta([0, 3600], unit="s")
        pressures = pd.DataFrame(
            {"J1": [25.0, 25.0], "J2": [-5.0, -3.0]},
            index=idx,
        )
        results = _make_results(pressures=pressures)
        warnings = results.health_check()
        assert len(warnings) == 1
        assert "Negative pressure" in warnings[0]
        assert "J2" in warnings[0]

    def test_high_velocity(self) -> None:
        idx = pd.to_timedelta([0, 3600], unit="s")
        velocities = pd.DataFrame(
            {"P1": [0.5, 0.5], "P2": [4.0, 4.5]},
            index=idx,
        )
        results = _make_results(velocities=velocities)
        warnings = results.health_check()
        assert len(warnings) == 1
        assert "Velocity" in warnings[0]
        assert "P2" in warnings[0]

    def test_custom_thresholds(self) -> None:
        results = _make_results()
        # Set a very high min_pressure threshold
        warnings = results.health_check(min_pressure=30.0)
        assert len(warnings) == 1
        assert "Negative pressure" in warnings[0] or "pressure" in warnings[0].lower()

    def test_both_warnings(self) -> None:
        idx = pd.to_timedelta([0, 3600], unit="s")
        pressures = pd.DataFrame(
            {"J1": [25.0, 25.0], "J2": [-5.0, -3.0]},
            index=idx,
        )
        velocities = pd.DataFrame(
            {"P1": [5.0, 5.0], "P2": [4.0, 4.5]},
            index=idx,
        )
        results = _make_results(pressures=pressures, velocities=velocities)
        warnings = results.health_check()
        assert len(warnings) == 2

    def test_velocity_threshold_custom(self) -> None:
        idx = pd.to_timedelta([0, 3600], unit="s")
        velocities = pd.DataFrame(
            {"P1": [2.0, 2.0], "P2": [1.5, 1.5]},
            index=idx,
        )
        results = _make_results(velocities=velocities)
        # Default threshold 3.0 — no warnings
        assert results.health_check() == []
        # Lower threshold — triggers warning
        warnings = results.health_check(max_velocity=1.0)
        assert len(warnings) == 1


class TestRepr:
    def test_repr_format(self) -> None:
        results = _make_results()
        r = repr(results)
        assert "NetworkResults" in r
        assert "nodes=2" in r
        assert "links=2" in r
        assert "timesteps=3" in r


class TestDataFrameContents:
    def test_pressures_columns(self) -> None:
        results = _make_results()
        assert list(results.pressures.columns) == ["J1", "J2"]

    def test_flows_columns(self) -> None:
        results = _make_results()
        assert list(results.flows.columns) == ["P1", "P2"]

    def test_timedelta_index(self) -> None:
        results = _make_results()
        assert isinstance(results.pressures.index, pd.TimedeltaIndex)

    def test_values_numeric(self) -> None:
        results = _make_results()
        assert np.issubdtype(results.pressures.dtypes["J1"], np.floating)
        assert np.issubdtype(results.flows.dtypes["P1"], np.floating)
