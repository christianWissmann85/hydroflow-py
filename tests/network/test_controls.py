"""Tests for hydroflow.network.controls."""

import pytest

from hydroflow.network.controls import ConditionalControl, TimeControl
from hydroflow.network.errors import ComponentError, TopologyError
from hydroflow.network.model import WaterNetwork

# ── TimeControl ───────────────────────────────────────────────────────


class TestTimeControl:
    def test_basic(self) -> None:
        ctrl = TimeControl(link_name="PMP1", status="CLOSED", at="22h")
        assert ctrl.link_name == "PMP1"
        assert ctrl.status == "CLOSED"

    def test_at_seconds(self) -> None:
        ctrl = TimeControl(link_name="PMP1", status="CLOSED", at="22h")
        assert ctrl.at_seconds == 22 * 3600

    def test_at_numeric(self) -> None:
        ctrl = TimeControl(link_name="PMP1", status="OPEN", at=3600)
        assert ctrl.at_seconds == 3600.0

    def test_frozen(self) -> None:
        ctrl = TimeControl(link_name="PMP1", status="CLOSED", at="22h")
        with pytest.raises(AttributeError):
            ctrl.status = "OPEN"  # type: ignore[misc]

    def test_empty_link_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            TimeControl(link_name="", status="CLOSED", at="22h")

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ComponentError, match="Invalid status"):
            TimeControl(link_name="PMP1", status="HALF_OPEN", at="22h")

    def test_to_control_dict(self) -> None:
        ctrl = TimeControl(link_name="PMP1", status="CLOSED", at="22h")
        d = ctrl._to_control_dict(0)
        assert d["type"] == "time"
        assert d["link_name"] == "PMP1"
        assert d["status_code"] == 0
        assert d["at_seconds"] == 22 * 3600

    def test_open_status_code(self) -> None:
        ctrl = TimeControl(link_name="P1", status="OPEN", at="6h")
        d = ctrl._to_control_dict(0)
        assert d["status_code"] == 1


# ── ConditionalControl ────────────────────────────────────────────────


class TestConditionalControl:
    def test_basic(self) -> None:
        ctrl = ConditionalControl(
            link_name="PMP1", status="OPEN",
            node_name="T1", attribute="level",
            operator="<", threshold=3.0,
        )
        assert ctrl.node_name == "T1"
        assert ctrl.threshold == 3.0

    def test_frozen(self) -> None:
        ctrl = ConditionalControl(
            link_name="PMP1", status="OPEN",
            node_name="T1", attribute="level",
            operator="<", threshold=3.0,
        )
        with pytest.raises(AttributeError):
            ctrl.threshold = 5.0  # type: ignore[misc]

    def test_empty_link_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            ConditionalControl(
                link_name="", status="OPEN",
                node_name="T1", attribute="level",
                operator="<", threshold=3.0,
            )

    def test_empty_node_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            ConditionalControl(
                link_name="PMP1", status="OPEN",
                node_name="", attribute="level",
                operator="<", threshold=3.0,
            )

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ComponentError, match="Invalid status"):
            ConditionalControl(
                link_name="PMP1", status="MAYBE",
                node_name="T1", attribute="level",
                operator="<", threshold=3.0,
            )

    def test_invalid_attribute_raises(self) -> None:
        with pytest.raises(ComponentError, match="Invalid attribute"):
            ConditionalControl(
                link_name="PMP1", status="OPEN",
                node_name="T1", attribute="temperature",
                operator="<", threshold=3.0,
            )

    def test_invalid_operator_raises(self) -> None:
        with pytest.raises(ComponentError, match="Invalid operator"):
            ConditionalControl(
                link_name="PMP1", status="OPEN",
                node_name="T1", attribute="level",
                operator="!=", threshold=3.0,
            )

    def test_to_control_dict(self) -> None:
        ctrl = ConditionalControl(
            link_name="PMP1", status="OPEN",
            node_name="T1", attribute="level",
            operator="<", threshold=3.0,
        )
        d = ctrl._to_control_dict(0)
        assert d["type"] == "conditional"
        assert d["link_name"] == "PMP1"
        assert d["node_name"] == "T1"
        assert d["operator"] == "below"
        assert d["threshold"] == 3.0

    def test_pressure_attribute(self) -> None:
        ctrl = ConditionalControl(
            link_name="V1", status="CLOSED",
            node_name="J1", attribute="pressure",
            operator=">", threshold=50.0,
        )
        d = ctrl._to_control_dict(0)
        assert d["attribute"] == "pressure"


# ── Model integration ─────────────────────────────────────────────────


class TestModelControls:
    def _net_with_pump(self) -> WaterNetwork:
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_junction("J2", elevation=110.0)
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        net.add_pump("PMP1", "J1", "J2", power=50000.0)
        return net

    def test_add_time_control(self) -> None:
        net = self._net_with_pump()
        net.add_time_control("PMP1", status="CLOSED", at="22h")
        assert len(net._controls) == 1

    def test_add_conditional_control(self) -> None:
        net = WaterNetwork()
        net.add_reservoir("R1", head=125.0)
        net.add_junction("J1", elevation=100.0)
        net.add_tank(
            "T1", elevation=50.0, init_level=3.0,
            min_level=0.5, max_level=5.0, diameter=10.0,
        )
        net.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.3, roughness=130.0)
        net.add_pump("PMP1", "J1", "T1", power=50000.0)
        net.add_conditional_control(
            "PMP1", status="OPEN",
            condition=("T1", "level", "<", 3.0),
        )
        assert len(net._controls) == 1

    def test_control_for_missing_link_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(TopologyError, match="does not exist"):
            net.add_time_control("MISSING", status="CLOSED", at="22h")

    def test_conditional_missing_link_raises(self) -> None:
        net = WaterNetwork()
        net.add_junction("J1", elevation=100.0)
        with pytest.raises(TopologyError, match="does not exist"):
            net.add_conditional_control(
                "MISSING", status="OPEN",
                condition=("J1", "pressure", "<", 10.0),
            )

    def test_multiple_controls(self) -> None:
        net = self._net_with_pump()
        net.add_time_control("PMP1", status="CLOSED", at="22h")
        net.add_time_control("PMP1", status="OPEN", at="6h")
        assert len(net._controls) == 2


# ── Top-level import ──────────────────────────────────────────────────


class TestTopLevelImport:
    def test_water_network_from_hf(self) -> None:
        import hydroflow as hf

        assert hf.WaterNetwork is WaterNetwork

    def test_construct_via_hf(self) -> None:
        import hydroflow as hf

        net = hf.WaterNetwork("Via hf")
        assert net.name == "Via hf"
