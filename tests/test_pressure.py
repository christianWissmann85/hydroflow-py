"""Tests for hydroflow.pressure.

Reference values from:
    - Colebrook (1939), Swamee-Jain (1976).
    - Design doc hand calculations.
"""

import math

import pytest

import hydroflow as hf
from hydroflow.pressure import (
    darcy_weisbach,
    friction_factor,
    hazen_williams,
    hydraulic_jump,
    minor_loss,
)


class TestFrictionFactor:
    def test_laminar(self) -> None:
        """Laminar flow: f = 64/Re."""
        f = friction_factor(reynolds=1000, roughness=0.045e-3, diameter=0.3)
        assert f == pytest.approx(64.0 / 1000, rel=1e-6)

    def test_turbulent_smooth(self) -> None:
        """Turbulent smooth pipe: f should be reasonable."""
        f = friction_factor(reynolds=100000, roughness=0.001e-3, diameter=0.3)
        assert 0.01 < f < 0.03

    def test_turbulent_rough(self) -> None:
        """Turbulent rough pipe: f should be higher."""
        f_smooth = friction_factor(reynolds=100000, roughness=0.001e-3, diameter=0.3)
        f_rough = friction_factor(reynolds=100000, roughness=1.0e-3, diameter=0.3)
        assert f_rough > f_smooth

    def test_invalid_reynolds(self) -> None:
        with pytest.raises(ValueError, match="Reynolds"):
            friction_factor(reynolds=0, roughness=0.045e-3, diameter=0.3)


class TestDarcyWeisbach:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_design_doc_reference(self) -> None:
        """L=100m, D=0.3m, Q=0.05m³/s, ε=0.045mm.

        V=0.7074 m/s, Re=211361, f=0.01663, hf=0.1414 m.
        """
        result = darcy_weisbach(
            flow=0.05,
            diameter=0.3,
            length=100.0,
            roughness_mm=0.045,
        )
        assert result.head_loss == pytest.approx(0.1414, rel=0.01)
        assert result.reynolds == pytest.approx(211361, rel=0.01)
        assert result.velocity == pytest.approx(0.7074, rel=0.01)

    def test_longer_pipe_more_loss(self) -> None:
        r1 = darcy_weisbach(flow=0.05, diameter=0.3, length=100.0)
        r2 = darcy_weisbach(flow=0.05, diameter=0.3, length=200.0)
        assert r2.head_loss > r1.head_loss

    def test_imperial(self) -> None:
        hf.set_units("imperial")
        result = darcy_weisbach(flow=1.0, diameter=1.0, length=100.0)
        assert result.head_loss > 0


class TestHazenWilliams:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_design_doc_reference(self) -> None:
        """L=100m, D=0.3m, Q=0.05m³/s, C=130 → hf=0.1778m."""
        hf_val = hazen_williams(flow=0.05, diameter=0.3, length=100.0, C=130)
        assert hf_val == pytest.approx(0.1778, rel=0.01)

    def test_string_material(self) -> None:
        """Lookup C from material name."""
        hf_val = hazen_williams(flow=0.05, diameter=0.3, length=100.0, C="pvc")
        # PVC has C=150, so should have less loss than C=130
        hf_130 = hazen_williams(flow=0.05, diameter=0.3, length=100.0, C=130)
        assert hf_val < hf_130

    def test_unknown_material_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown material"):
            hazen_williams(flow=0.05, diameter=0.3, length=100.0, C="unobtanium")

    def test_higher_C_less_loss(self) -> None:
        """Higher C → smoother pipe → less head loss."""
        hf_low = hazen_williams(flow=0.05, diameter=0.3, length=100.0, C=80)
        hf_high = hazen_williams(flow=0.05, diameter=0.3, length=100.0, C=150)
        assert hf_high < hf_low


class TestMinorLoss:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_known_value(self) -> None:
        """h_m = K * V²/(2g)."""
        V = 2.0  # m/s
        K = 0.9  # 90° elbow
        hm = minor_loss(velocity=V, K=K)
        expected = 0.9 * 2.0**2 / (2.0 * 9.80665)
        assert hm == pytest.approx(expected, rel=1e-4)

    def test_string_lookup(self) -> None:
        hm = minor_loss(velocity=2.0, K="90_elbow")
        expected = 0.9 * 2.0**2 / (2.0 * 9.80665)
        assert hm == pytest.approx(expected, rel=1e-4)

    def test_unknown_fitting_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown fitting"):
            minor_loss(velocity=2.0, K="magic_valve")


class TestHydraulicJump:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_design_doc_reference(self) -> None:
        """Design doc: y1=0.3m, Fr1=3.0 → y2≈1.132m, ΔE≈0.423m."""
        # Fr1 = V1 / sqrt(g*y1) = 3.0
        # V1 = 3.0 * sqrt(9.81 * 0.3) = 5.147 m/s
        # Q = V1 * b * y1; pick b=1.0m → Q = 5.147 * 1.0 * 0.3 = 1.544 m³/s
        V1 = 3.0 * math.sqrt(9.80665 * 0.3)
        Q = V1 * 1.0 * 0.3

        result = hydraulic_jump(flow=Q, upstream_depth=0.3, width=1.0)
        assert result.sequent_depth == pytest.approx(1.132, rel=0.01)
        assert result.energy_loss == pytest.approx(0.423, rel=0.02)
        assert result.froude_upstream == pytest.approx(3.0, rel=0.001)
        assert result.froude_downstream < 1.0

    def test_subcritical_raises(self) -> None:
        """Subcritical upstream flow should raise."""
        with pytest.raises(ValueError, match="supercritical"):
            hydraulic_jump(flow=0.1, upstream_depth=1.0, width=1.0)

    def test_sequent_depth_increases_with_froude(self) -> None:
        """Higher Froude → larger sequent depth ratio."""
        b = 1.0
        y1 = 0.2

        V_lo = 2.0 * math.sqrt(9.80665 * y1)  # Fr=2
        V_hi = 5.0 * math.sqrt(9.80665 * y1)  # Fr=5

        r_lo = hydraulic_jump(flow=V_lo * b * y1, upstream_depth=y1, width=b)
        r_hi = hydraulic_jump(flow=V_hi * b * y1, upstream_depth=y1, width=b)
        assert r_hi.sequent_depth > r_lo.sequent_depth
