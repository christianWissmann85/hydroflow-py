"""Tests for hydroflow.network.io (require WNTR)."""

from __future__ import annotations

from pathlib import Path

import pytest

wntr = pytest.importorskip("wntr")

from hydroflow.network.io import from_wntr, read_inp, write_inp  # noqa: E402
from hydroflow.network.model import WaterNetwork  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
SIMPLE_INP = DATA_DIR / "simple_network.inp"


def _simple_network() -> WaterNetwork:
    """R1 --P1--> J1 --P2--> J2."""
    net = WaterNetwork("Test IO")
    net.add_reservoir("R1", head=125.0)
    net.add_junction("J1", elevation=100.0)
    net.add_junction("J2", elevation=95.0, base_demand=0.005)
    net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
    net.add_pipe("P2", "J1", "J2", length=300.0, diameter=0.2, roughness=130.0)
    return net


class TestReadInp:
    def test_reads_file(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert isinstance(net, WaterNetwork)

    def test_junctions_loaded(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert "J1" in net.junctions
        assert "J2" in net.junctions

    def test_reservoir_loaded(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert "R1" in net.reservoirs

    def test_pipes_loaded(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert "P1" in net.pipes
        assert "P2" in net.pipes

    def test_node_count(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert len(net.node_names) == 3

    def test_link_count(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert len(net.link_names) == 2

    def test_junction_elevation(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert net.junctions["J1"].elevation == 100.0

    def test_reservoir_head(self) -> None:
        net = read_inp(SIMPLE_INP)
        assert net.reservoirs["R1"].head == 125.0


class TestWriteInp:
    def test_write_and_read_back(self, tmp_path: Path) -> None:
        net = _simple_network()
        out = tmp_path / "out.inp"
        write_inp(net, out)
        assert out.exists()
        net2 = read_inp(out)
        assert set(net2.node_names) == set(net.node_names)
        assert set(net2.link_names) == set(net.link_names)

    def test_pipe_properties_preserved(self, tmp_path: Path) -> None:
        net = _simple_network()
        out = tmp_path / "out.inp"
        write_inp(net, out)
        net2 = read_inp(out)
        p1 = net2.pipes["P1"]
        assert p1.length == pytest.approx(500.0)
        assert p1.roughness_value == pytest.approx(130.0)

    def test_junction_elevation_preserved(self, tmp_path: Path) -> None:
        net = _simple_network()
        out = tmp_path / "out.inp"
        write_inp(net, out)
        net2 = read_inp(out)
        assert net2.junctions["J1"].elevation == pytest.approx(100.0)

    def test_round_trip_fidelity(self, tmp_path: Path) -> None:
        """write_inp(read_inp(f), out) should be functionally equivalent."""
        net1 = read_inp(SIMPLE_INP)
        out1 = tmp_path / "rt1.inp"
        write_inp(net1, out1)
        net2 = read_inp(out1)
        assert set(net2.node_names) == set(net1.node_names)
        assert set(net2.link_names) == set(net1.link_names)


class TestCoordinatesRoundTrip:
    def test_coordinates_preserved_on_round_trip(self, tmp_path: Path) -> None:
        """Coordinates survive write_inp -> read_inp round-trip."""
        net = WaterNetwork("Coords Test")
        net.add_reservoir("R1", head=125.0, coordinates=(0.0, 0.0))
        net.add_junction("J1", elevation=100.0, coordinates=(100.0, 50.0))
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        out = tmp_path / "coords.inp"
        write_inp(net, out)
        net2 = read_inp(out)
        assert net2.junctions["J1"].coordinates is not None
        assert net2.junctions["J1"].coordinates[0] == pytest.approx(100.0)
        assert net2.junctions["J1"].coordinates[1] == pytest.approx(50.0)


class TestFromWntr:
    def test_converts_model(self) -> None:
        wn = wntr.network.WaterNetworkModel(str(SIMPLE_INP))
        net = from_wntr(wn)
        assert isinstance(net, WaterNetwork)
        assert "J1" in net.junctions
        assert "R1" in net.reservoirs
        assert "P1" in net.pipes

    def test_default_name(self) -> None:
        wn = wntr.network.WaterNetworkModel()
        wn.add_junction("J1", base_demand=0, elevation=100)
        wn.add_reservoir("R1", base_head=125)
        wn.add_pipe("P1", "R1", "J1", length=500, diameter=0.3, roughness=130)
        net = from_wntr(wn)
        assert isinstance(net.name, str)

    def test_preserves_elevation(self) -> None:
        wn = wntr.network.WaterNetworkModel(str(SIMPLE_INP))
        net = from_wntr(wn)
        assert net.junctions["J1"].elevation == pytest.approx(100.0)

    def test_preserves_pipe_roughness(self) -> None:
        wn = wntr.network.WaterNetworkModel(str(SIMPLE_INP))
        net = from_wntr(wn)
        assert net.pipes["P1"].roughness_value == pytest.approx(130.0)
