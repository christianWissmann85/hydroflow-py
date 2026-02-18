"""Tests for hydroflow.network.components."""

import pytest

from hydroflow.network.components import (
    Junction,
    Pipe,
    Pump,
    Reservoir,
    Tank,
    Valve,
)
from hydroflow.network.errors import ComponentError

# ── Junction ──────────────────────────────────────────────────────────


class TestJunction:
    def test_basic_construction(self) -> None:
        j = Junction("J1", elevation=100.0)
        assert j.name == "J1"
        assert j.elevation == 100.0
        assert j.base_demand == 0.0

    def test_with_demand(self) -> None:
        j = Junction("J2", elevation=50.0, base_demand=0.005)
        assert j.base_demand == 0.005

    def test_frozen(self) -> None:
        j = Junction("J1", elevation=100.0)
        with pytest.raises(AttributeError):
            j.elevation = 200.0  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            Junction("", elevation=100.0)

    def test_negative_elevation_allowed(self) -> None:
        # Below sea level is valid
        j = Junction("J1", elevation=-5.0)
        assert j.elevation == -5.0

    def test_to_wntr_kwargs(self) -> None:
        j = Junction("J1", elevation=100.0, base_demand=0.01)
        kw = j.to_wntr_kwargs()
        assert kw["name"] == "J1"
        assert kw["elevation"] == 100.0
        assert kw["base_demand"] == 0.01

    def test_coordinates_default_none(self) -> None:
        j = Junction("J1", elevation=100.0)
        assert j.coordinates is None

    def test_coordinates_stored(self) -> None:
        j = Junction("J1", elevation=100.0, coordinates=(10.0, 20.0))
        assert j.coordinates == (10.0, 20.0)

    def test_coordinates_in_wntr_kwargs(self) -> None:
        j = Junction("J1", elevation=100.0, coordinates=(10.0, 20.0))
        kw = j.to_wntr_kwargs()
        assert kw["coordinates"] == (10.0, 20.0)

    def test_coordinates_omitted_when_none(self) -> None:
        j = Junction("J1", elevation=100.0)
        kw = j.to_wntr_kwargs()
        assert "coordinates" not in kw


# ── Reservoir ─────────────────────────────────────────────────────────


class TestReservoir:
    def test_basic(self) -> None:
        r = Reservoir("R1", head=125.0)
        assert r.name == "R1"
        assert r.head == 125.0

    def test_frozen(self) -> None:
        r = Reservoir("R1", head=125.0)
        with pytest.raises(AttributeError):
            r.head = 130.0  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            Reservoir("", head=100.0)

    def test_to_wntr_kwargs(self) -> None:
        r = Reservoir("R1", head=125.0)
        kw = r.to_wntr_kwargs()
        assert kw["name"] == "R1"
        assert kw["base_head"] == 125.0

    def test_coordinates_stored(self) -> None:
        r = Reservoir("R1", head=125.0, coordinates=(5.0, 15.0))
        assert r.coordinates == (5.0, 15.0)

    def test_coordinates_in_wntr_kwargs(self) -> None:
        r = Reservoir("R1", head=125.0, coordinates=(5.0, 15.0))
        kw = r.to_wntr_kwargs()
        assert kw["coordinates"] == (5.0, 15.0)


# ── Tank ──────────────────────────────────────────────────────────────


class TestTank:
    def test_basic(self) -> None:
        t = Tank("T1", elevation=50.0, init_level=3.0, min_level=0.5,
                 max_level=5.0, diameter=10.0)
        assert t.name == "T1"
        assert t.diameter == 10.0

    def test_frozen(self) -> None:
        t = Tank("T1", elevation=50.0, init_level=3.0, min_level=0.5,
                 max_level=5.0, diameter=10.0)
        with pytest.raises(AttributeError):
            t.diameter = 20.0  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            Tank("", elevation=50.0, init_level=3.0, min_level=0.5,
                 max_level=5.0, diameter=10.0)

    def test_negative_init_level_raises(self) -> None:
        with pytest.raises(ComponentError, match="non-negative"):
            Tank("T1", elevation=50.0, init_level=-1.0, min_level=0.0,
                 max_level=5.0, diameter=10.0)

    def test_negative_diameter_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Tank("T1", elevation=50.0, init_level=3.0, min_level=0.0,
                 max_level=5.0, diameter=-1.0)

    def test_zero_max_level_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Tank("T1", elevation=50.0, init_level=0.0, min_level=0.0,
                 max_level=0.0, diameter=10.0)

    def test_min_gt_max_raises(self) -> None:
        with pytest.raises(ComponentError, match=r"min_level.*max_level"):
            Tank("T1", elevation=50.0, init_level=3.0, min_level=6.0,
                 max_level=5.0, diameter=10.0)

    def test_init_lt_min_raises(self) -> None:
        with pytest.raises(ComponentError, match=r"init_level.*min_level"):
            Tank("T1", elevation=50.0, init_level=0.0, min_level=1.0,
                 max_level=5.0, diameter=10.0)

    def test_init_gt_max_raises(self) -> None:
        with pytest.raises(ComponentError, match=r"init_level.*max_level"):
            Tank("T1", elevation=50.0, init_level=6.0, min_level=0.0,
                 max_level=5.0, diameter=10.0)

    def test_to_wntr_kwargs(self) -> None:
        t = Tank("T1", elevation=50.0, init_level=3.0, min_level=0.5,
                 max_level=5.0, diameter=10.0)
        kw = t.to_wntr_kwargs()
        assert kw["name"] == "T1"
        assert kw["elevation"] == 50.0
        assert kw["init_level"] == 3.0
        assert kw["min_level"] == 0.5
        assert kw["max_level"] == 5.0
        assert kw["diameter"] == 10.0

    def test_coordinates_stored(self) -> None:
        t = Tank("T1", elevation=50.0, init_level=3.0, min_level=0.5,
                 max_level=5.0, diameter=10.0, coordinates=(30.0, 40.0))
        assert t.coordinates == (30.0, 40.0)


# ── Pipe ──────────────────────────────────────────────────────────────


class TestPipe:
    def test_basic_numeric_roughness(self) -> None:
        p = Pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness=130.0)
        assert p.roughness_value == 130.0

    def test_material_string_roughness(self) -> None:
        p = Pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness="ductile_iron")
        assert p.roughness == "ductile_iron"
        assert p.roughness_value == 140.0

    def test_pvc_roughness(self) -> None:
        p = Pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness="pvc")
        assert p.roughness_value == 150.0

    def test_frozen(self) -> None:
        p = Pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness=130.0)
        with pytest.raises(AttributeError):
            p.length = 600.0  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            Pipe("", "J1", "J2", length=500.0, diameter=0.3, roughness=130.0)

    def test_empty_start_node_raises(self) -> None:
        with pytest.raises(ComponentError, match="cannot be empty"):
            Pipe("P1", "", "J2", length=500.0, diameter=0.3, roughness=130.0)

    def test_same_start_end_raises(self) -> None:
        with pytest.raises(ComponentError, match="same start and end"):
            Pipe("P1", "J1", "J1", length=500.0, diameter=0.3, roughness=130.0)

    def test_negative_length_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Pipe("P1", "J1", "J2", length=-100.0, diameter=0.3, roughness=130.0)

    def test_zero_diameter_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Pipe("P1", "J1", "J2", length=500.0, diameter=0.0, roughness=130.0)

    def test_negative_minor_loss_raises(self) -> None:
        with pytest.raises(ComponentError, match="non-negative"):
            Pipe("P1", "J1", "J2", length=500.0, diameter=0.3,
                 roughness=130.0, minor_loss=-0.5)

    def test_bad_material_name_raises(self) -> None:
        with pytest.raises((ComponentError, ValueError)):
            Pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness="unobtainium")

    def test_minor_loss_default(self) -> None:
        p = Pipe("P1", "J1", "J2", length=500.0, diameter=0.3, roughness=130.0)
        assert p.minor_loss == 0.0

    def test_to_wntr_kwargs(self) -> None:
        p = Pipe("P1", "R1", "J1", length=500.0, diameter=0.3,
                 roughness=130.0, minor_loss=0.5)
        kw = p.to_wntr_kwargs()
        assert kw["name"] == "P1"
        assert kw["start_node_name"] == "R1"
        assert kw["end_node_name"] == "J1"
        assert kw["length"] == 500.0
        assert kw["diameter"] == 0.3
        assert kw["roughness"] == 130.0
        assert kw["minor_loss"] == 0.5

    def test_to_wntr_kwargs_material(self) -> None:
        p = Pipe("P1", "R1", "J1", length=500.0, diameter=0.3,
                 roughness="ductile_iron")
        kw = p.to_wntr_kwargs()
        assert kw["roughness"] == 140.0


# ── Pump ──────────────────────────────────────────────────────────────


class TestPump:
    def test_basic(self) -> None:
        p = Pump("PMP1", "J1", "J2", power=50000.0)
        assert p.name == "PMP1"
        assert p.power == 50000.0

    def test_frozen(self) -> None:
        p = Pump("PMP1", "J1", "J2", power=50000.0)
        with pytest.raises(AttributeError):
            p.power = 60000.0  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            Pump("", "J1", "J2", power=50000.0)

    def test_empty_nodes_raises(self) -> None:
        with pytest.raises(ComponentError, match="cannot be empty"):
            Pump("PMP1", "", "J2", power=50000.0)

    def test_zero_power_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Pump("PMP1", "J1", "J2", power=0.0)

    def test_negative_power_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Pump("PMP1", "J1", "J2", power=-100.0)

    def test_to_wntr_kwargs(self) -> None:
        p = Pump("PMP1", "J1", "J2", power=50000.0)
        kw = p.to_wntr_kwargs()
        assert kw["name"] == "PMP1"
        assert kw["start_node_name"] == "J1"
        assert kw["end_node_name"] == "J2"
        assert kw["pump_type"] == "POWER"
        assert kw["pump_parameter"] == 50000.0


# ── Valve ─────────────────────────────────────────────────────────────


class TestValve:
    def test_basic_prv(self) -> None:
        v = Valve("V1", "J1", "J2", diameter=0.3, setting=40.0)
        assert v.valve_type == "PRV"
        assert v.setting == 40.0

    def test_frozen(self) -> None:
        v = Valve("V1", "J1", "J2", diameter=0.3, setting=40.0)
        with pytest.raises(AttributeError):
            v.setting = 50.0  # type: ignore[misc]

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ComponentError):
            Valve("", "J1", "J2", diameter=0.3, setting=40.0)

    def test_empty_nodes_raises(self) -> None:
        with pytest.raises(ComponentError, match="cannot be empty"):
            Valve("V1", "", "J2", diameter=0.3, setting=40.0)

    def test_negative_diameter_raises(self) -> None:
        with pytest.raises(ComponentError, match="positive"):
            Valve("V1", "J1", "J2", diameter=-0.3, setting=40.0)

    def test_negative_setting_raises(self) -> None:
        with pytest.raises(ComponentError, match="non-negative"):
            Valve("V1", "J1", "J2", diameter=0.3, setting=-10.0)

    def test_unsupported_valve_type_raises(self) -> None:
        with pytest.raises(ComponentError, match="not supported"):
            Valve("V1", "J1", "J2", diameter=0.3, setting=40.0, valve_type="FCV")

    def test_zero_setting_allowed(self) -> None:
        v = Valve("V1", "J1", "J2", diameter=0.3, setting=0.0)
        assert v.setting == 0.0

    def test_minor_loss_default(self) -> None:
        v = Valve("V1", "J1", "J2", diameter=0.3, setting=40.0)
        assert v.minor_loss == 0.0

    def test_to_wntr_kwargs(self) -> None:
        v = Valve("V1", "J1", "J2", diameter=0.3, setting=40.0, minor_loss=0.2)
        kw = v.to_wntr_kwargs()
        assert kw["name"] == "V1"
        assert kw["start_node_name"] == "J1"
        assert kw["end_node_name"] == "J2"
        assert kw["diameter"] == 0.3
        assert kw["valve_type"] == "PRV"
        assert kw["setting"] == 40.0
        assert kw["minor_loss"] == 0.2
