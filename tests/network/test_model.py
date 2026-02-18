"""Tests for hydroflow.network.model."""

import pytest

from hydroflow.network.errors import TopologyError, ValidationError
from hydroflow.network.model import WaterNetwork


class TestWaterNetworkConstruction:
    def test_default_name(self) -> None:
        net = WaterNetwork()
        assert net.name == "WaterNetwork"

    def test_custom_name(self) -> None:
        net = WaterNetwork("My Network")
        assert net.name == "My Network"

    def test_repr(self) -> None:
        net = WaterNetwork("Test")
        assert "Test" in repr(net)
        assert "nodes=0" in repr(net)
        assert "links=0" in repr(net)


class TestAddJunction:
    def test_basic(self) -> None:
        net = WaterNetwork()
        j = net.add_junction("J1", elevation=100.0)
        assert j.name == "J1"
        assert "J1" in net.junctions

    def test_with_demand(self) -> None:
        net = WaterNetwork()
        j = net.add_junction("J1", elevation=100.0, base_demand=0.005)
        assert j.base_demand == 0.005

    def test_duplicate_name_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(ValidationError, match="already in use"):
            net.add_junction("J1", elevation=200.0)


class TestAddJunctionCoordinates:
    def test_with_coordinates(self) -> None:
        net = WaterNetwork()
        j = net.add_junction("J1", elevation=100.0, coordinates=(10.0, 20.0))
        assert j.coordinates == (10.0, 20.0)

    def test_default_no_coordinates(self) -> None:
        net = WaterNetwork()
        j = net.add_junction("J1", elevation=100.0)
        assert j.coordinates is None


class TestAddReservoir:
    def test_basic(self) -> None:
        net = WaterNetwork()
        r = net.add_reservoir("R1", head=125.0)
        assert r.head == 125.0
        assert "R1" in net.reservoirs

    def test_duplicate_name_raises(self) -> None:
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        with pytest.raises(ValidationError, match="already in use"):
            net.add_reservoir("R1", head=130.0)


class TestAddTank:
    def test_basic(self) -> None:
        net = WaterNetwork()
        t = net.add_tank(
            "T1", elevation=50.0, init_level=3.0,
            min_level=0.5, max_level=5.0, diameter=10.0,
        )
        assert t.diameter == 10.0
        assert "T1" in net.tanks

    def test_duplicate_across_types_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("N1", elevation=100.0)
        with pytest.raises(ValidationError, match="already in use"):
            net.add_tank(
                "N1", elevation=50.0, init_level=3.0,
                min_level=0.5, max_level=5.0, diameter=10.0,
            )


class TestAddPipe:
    def _net_with_nodes(self) -> WaterNetwork:
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        return net

    def test_basic(self) -> None:
        net = self._net_with_nodes()
        p = net.add_pipe(
            "P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0,
        )
        assert p.start_node == "R1"
        assert "P1" in net.pipes

    def test_material_roughness(self) -> None:
        net = self._net_with_nodes()
        p = net.add_pipe(
            "P1", "R1", "J1", length=500.0, diameter=0.3, roughness="ductile_iron",
        )
        assert p.roughness_value == 140.0

    def test_missing_start_node_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(TopologyError, match="does not exist"):
            net.add_pipe(
                "P1", "MISSING", "J1", length=500.0, diameter=0.3, roughness=130.0,
            )

    def test_missing_end_node_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(TopologyError, match="does not exist"):
            net.add_pipe(
                "P1", "J1", "MISSING", length=500.0, diameter=0.3, roughness=130.0,
            )

    def test_duplicate_pipe_name_raises(self) -> None:
        net = self._net_with_nodes()
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        with pytest.raises(ValidationError, match="already in use"):
            net.add_pipe(
                "P1", "J1", "J2", length=200.0, diameter=0.2, roughness=130.0,
            )

    def test_pipe_name_conflicts_with_node(self) -> None:
        net = self._net_with_nodes()
        with pytest.raises(ValidationError, match="already in use"):
            net.add_pipe(
                "J1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0,
            )


class TestAddPump:
    def test_basic(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=110.0)
        p = net.add_pump("PMP1", "J1", "J2", power=50000.0)
        assert p.power == 50000.0
        assert "PMP1" in net.pumps

    def test_missing_node_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(TopologyError):
            net.add_pump("PMP1", "J1", "MISSING", power=50000.0)


class TestAddValve:
    def test_basic_prv(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        v = net.add_valve("V1", "J1", "J2", diameter=0.3, setting=40.0)
        assert v.valve_type == "PRV"
        assert "V1" in net.valves

    def test_missing_node_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(TopologyError):
            net.add_valve("V1", "J1", "MISSING", diameter=0.3, setting=40.0)


class TestNodeAndLinkNames:
    def test_node_names(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        net.add_reservoir("R1", head=125.0)
        net.add_tank(
            "T1", elevation=50.0, init_level=3.0,
            min_level=0.5, max_level=5.0, diameter=10.0,
        )
        assert net.node_names == {"J1", "R1", "T1"}

    def test_link_names(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        net.add_reservoir("R1", head=125.0)
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        net.add_pump("PMP1", "J1", "J2", power=50000.0)
        assert net.link_names == {"P1", "PMP1"}


class TestValidate:
    def _simple_network(self) -> WaterNetwork:
        """R1 --P1--> J1 --P2--> J2"""
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        net.add_pipe("P2", "J1", "J2", length=300.0, diameter=0.2, roughness=130.0)
        return net

    def test_valid_network(self) -> None:
        net = self._simple_network()
        warnings = net.validate()
        # J2 is a dead-end
        assert any("J2" in w for w in warnings)

    def test_no_source_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        net.add_pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness=130.0)
        with pytest.raises(ValidationError, match="no source"):
            net.validate()

    def test_disconnected_node_raises(self) -> None:
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)  # disconnected
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        with pytest.raises(ValidationError, match="Disconnected"):
            net.validate()

    def test_dead_end_warning(self) -> None:
        net = self._simple_network()
        warnings = net.validate()
        dead_ends = [w for w in warnings if "dead-end" in w]
        assert len(dead_ends) >= 1

    def test_no_dead_end_for_reservoirs(self) -> None:
        """Reservoirs at dead ends should NOT trigger warnings."""
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        net.add_pipe("P2", "J1", "J2", length=300.0, diameter=0.2, roughness=130.0)
        warnings = net.validate()
        # R1 is a dead-end reservoir — no warning for it
        reservoir_warnings = [w for w in warnings if "R1" in w]
        assert len(reservoir_warnings) == 0

    def test_tank_as_source(self) -> None:
        """A tank counts as a source — no 'no source' error."""
        net = WaterNetwork()
        net.add_tank(
            "T1", elevation=50.0, init_level=3.0,
            min_level=0.5, max_level=5.0, diameter=10.0,
        )
        net.add_junction("J1", elevation=40.0)
        net.add_pipe("P1", "T1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        warnings = net.validate()
        assert isinstance(warnings, list)

    def test_looped_network_no_dead_end(self) -> None:
        """Fully looped network should have no dead-end warnings."""
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=95.0)
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        net.add_pipe("P2", "J1", "J2", length=300.0, diameter=0.2, roughness=130.0)
        net.add_pipe("P3", "J2", "R1", length=400.0, diameter=0.2, roughness=130.0)
        warnings = net.validate()
        dead_ends = [w for w in warnings if "dead-end" in w]
        assert len(dead_ends) == 0


class TestRepr:
    def test_counts(self) -> None:
        net = WaterNetwork("Test")
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        r = repr(net)
        assert "nodes=2" in r
        assert "links=1" in r
