"""Tests for hydroflow.structures.

Reference values from:
    - FHWA HDS-5 (2012). Hydraulic Design of Highway Culverts.
    - Brater & King (1976). Handbook of Hydraulics.
"""

import math

import pytest

import hydroflow as hf
from hydroflow.structures import (
    BroadCrestedWeir,
    CompositeOutlet,
    Culvert,
    Orifice,
    RectangularWeir,
    VNotchWeir,
)


class TestOrifice:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_design_doc_reference(self) -> None:
        """Design doc: D=0.3m, Cd=0.61, head=2.0m → Q≈0.270 m³/s."""
        orif = Orifice(diameter=0.3, Cd=0.61)
        # Head of 2.0m above centroid means stage = invert + D/2 + 2.0
        # With invert=0, centroid=0.15, so stage = 2.15m
        Q = orif.discharge(stage=2.15)
        expected = 0.61 * (math.pi * 0.15**2) * math.sqrt(2 * 9.80665 * 2.0)
        assert pytest.approx(expected, rel=0.001) == Q

    def test_below_centroid(self) -> None:
        """Stage below orifice centroid → no flow."""
        orif = Orifice(diameter=0.3, invert=1.0)
        assert orif.discharge(stage=1.1) == 0.0

    def test_at_centroid(self) -> None:
        """Stage exactly at centroid → no flow."""
        orif = Orifice(diameter=0.3, invert=0.0)
        assert orif.discharge(stage=0.15) == 0.0

    def test_imperial(self) -> None:
        """Imperial units roundtrip."""
        hf.set_units("imperial")
        orif = Orifice(diameter=1.0, invert=0.0)
        Q = orif.discharge(stage=5.0)
        assert Q > 0


class TestRectangularWeir:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_design_doc_reference(self) -> None:
        """Design doc: L=3.0m, H=0.5m, Cw=1.84 → Q≈1.952 m³/s."""
        weir = RectangularWeir(length=3.0, crest=0.0, Cw=1.84)
        Q = weir.discharge(stage=0.5)
        expected = 1.84 * 3.0 * 0.5**1.5
        assert pytest.approx(expected, rel=0.001) == Q

    def test_below_crest(self) -> None:
        weir = RectangularWeir(length=3.0, crest=1.0)
        assert weir.discharge(stage=0.5) == 0.0

    def test_at_crest(self) -> None:
        weir = RectangularWeir(length=3.0, crest=1.0)
        assert weir.discharge(stage=1.0) == 0.0


class TestVNotchWeir:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_90_degree(self) -> None:
        """90° V-notch at H=0.3m → known value."""
        weir = VNotchWeir(angle_degrees=90.0, vertex=0.0, Cd=0.58)
        Q = weir.discharge(stage=0.3)
        expected = (8.0 / 15.0) * 0.58 * math.tan(math.pi / 4) * math.sqrt(2 * 9.80665) * 0.3**2.5
        assert pytest.approx(expected, rel=0.001) == Q

    def test_below_vertex(self) -> None:
        weir = VNotchWeir(vertex=1.0)
        assert weir.discharge(stage=0.5) == 0.0


class TestBroadCrestedWeir:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_basic(self) -> None:
        weir = BroadCrestedWeir(length=5.0, crest=0.0, Cw=1.70)
        Q = weir.discharge(stage=1.0)
        expected = 1.70 * 5.0 * 1.0**1.5
        assert pytest.approx(expected, rel=0.001) == Q


class TestCompositeOutlet:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_add_orifice_weir(self) -> None:
        """Combining structures with + operator."""
        orif = Orifice(diameter=0.3)
        weir = RectangularWeir(length=3.0, crest=1.5)
        combo = orif + weir
        assert isinstance(combo, CompositeOutlet)

    def test_composite_discharge(self) -> None:
        """Combined Q = sum of individual Qs."""
        orif = Orifice(diameter=0.3, invert=0.0)
        weir = RectangularWeir(length=3.0, crest=1.0)
        combo = orif + weir

        stage = 2.0
        Q_total = combo.discharge(stage=stage)
        Q_orif = orif.discharge(stage=stage)
        Q_weir = weir.discharge(stage=stage)
        assert Q_total == pytest.approx(Q_orif + Q_weir, rel=1e-6)

    def test_triple_add(self) -> None:
        """Three structures added together."""
        a = Orifice(diameter=0.2)
        b = RectangularWeir(length=2.0, crest=1.0)
        c = VNotchWeir(vertex=0.5)
        combo = a + b + c
        assert isinstance(combo, CompositeOutlet)
        Q = combo.discharge(stage=2.0)
        Q_expected = a.discharge(stage=2.0) + b.discharge(stage=2.0) + c.discharge(stage=2.0)
        assert pytest.approx(Q_expected, rel=1e-6) == Q

    def test_weir_add_composite(self) -> None:
        """Weir + CompositeOutlet should merge."""
        orif = Orifice(diameter=0.3)
        weir1 = RectangularWeir(length=2.0, crest=1.0)
        weir2 = BroadCrestedWeir(length=4.0, crest=1.5)
        combo = orif + weir1
        merged = weir2 + combo
        assert isinstance(merged, CompositeOutlet)
        Q = merged.discharge(stage=2.5)
        expected = orif.discharge(stage=2.5) + weir1.discharge(stage=2.5) + weir2.discharge(stage=2.5)
        assert pytest.approx(expected, rel=1e-6) == Q

    def test_vnotch_add_composite(self) -> None:
        """VNotchWeir + CompositeOutlet."""
        v = VNotchWeir(vertex=0.0)
        combo = Orifice(diameter=0.2) + RectangularWeir(length=1.0, crest=0.5)
        merged = v + combo
        assert isinstance(merged, CompositeOutlet)

    def test_broad_crested_discharge_si(self) -> None:
        """Test discharge_si directly."""
        weir = BroadCrestedWeir(length=3.0, crest=0.0, Cw=1.70)
        Q_si = weir.discharge_si(0.5)
        assert Q_si > 0

    def test_composite_stage_discharge_curve(self) -> None:
        """Test stage-discharge curve method."""
        import numpy as np

        outlet = Orifice(diameter=0.3) + RectangularWeir(length=2.0, crest=1.0)
        stages = np.array([0.5, 1.0, 1.5, 2.0])
        discharges = outlet.stage_discharge_curve_si(stages)
        assert len(discharges) == 4
        assert all(q >= 0 for q in discharges)


class TestCulvert:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_basic_analysis(self) -> None:
        """Basic culvert analysis returns valid result."""
        c = Culvert(
            diameter=0.9,
            length=30.0,
            slope=0.01,
            roughness="concrete",
            inlet="square_edge",
        )
        result = c.analyze(flow=1.0, tailwater=0.0)
        assert result.flow == 1.0
        assert result.headwater > 0
        assert result.headwater_ratio > 0
        assert result.velocity > 0
        assert result.control in ("INLET_CONTROL", "OUTLET_CONTROL")

    def test_invalid_inlet_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown inlet"):
            Culvert(diameter=0.9, length=30.0, slope=0.01, roughness=0.013, inlet="bad")

    def test_groove_end_lower_hw(self) -> None:
        """Groove-end inlet should produce lower headwater than square-edge."""
        kwargs: dict[str, object] = {"diameter": 0.9, "length": 30.0, "slope": 0.01, "roughness": "concrete"}
        sq = Culvert(**kwargs, inlet="square_edge")  # type: ignore[arg-type]
        gr = Culvert(**kwargs, inlet="groove_end")  # type: ignore[arg-type]
        r_sq = sq.analyze(flow=1.5)
        r_gr = gr.analyze(flow=1.5)
        # Groove end should have lower or equal headwater
        assert r_gr.headwater <= r_sq.headwater * 1.01

    def test_performance_curve(self) -> None:
        """Performance curve returns multiple results."""
        c = Culvert(diameter=0.9, length=30.0, slope=0.01, roughness="concrete")
        results = c.performance_curve(flow_range=(0.1, 3.0), steps=10)
        assert len(results) == 10
        # Headwater should generally increase with flow
        hws = [r.headwater for r in results]
        assert hws[-1] > hws[0]

    def test_imperial(self) -> None:
        """Imperial units analysis."""
        hf.set_units("imperial")
        c = Culvert(
            diameter=3.0,
            length=100.0,
            slope=0.01,
            roughness="concrete",
            inlet="square_edge",
        )
        result = c.analyze(flow=50.0, tailwater=1.0)
        assert result.headwater > 0
