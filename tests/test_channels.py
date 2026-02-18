"""Tests for hydroflow.channels.

Reference values from:
    - Chow, V.T. (1959). Open-Channel Hydraulics. McGraw-Hill.
    - Standard hydraulic engineering formulas.
"""

import math

import pytest

import hydroflow as hf
from hydroflow._types import FlowRegime
from hydroflow.core.channels import _classify_flow, _froude, _manning_flow


class TestFlowRegimeRepr:
    def test_repr(self) -> None:
        assert repr(FlowRegime.SUBCRITICAL) == "FlowRegime.SUBCRITICAL"


class TestManningKernel:
    """Test the pure SI kernel function directly."""

    def test_known_value(self) -> None:
        # Simple case: n=0.013, A=1m², R=0.5m, S=0.001
        Q = _manning_flow(n=0.013, area=1.0, R=0.5, S=0.001)
        expected = (1.0 / 0.013) * 1.0 * 0.5 ** (2 / 3) * 0.001**0.5
        assert pytest.approx(expected) == Q

    def test_zero_area_returns_zero(self) -> None:
        assert _manning_flow(n=0.013, area=0.0, R=0.5, S=0.001) == 0.0

    def test_zero_radius_returns_zero(self) -> None:
        assert _manning_flow(n=0.013, area=1.0, R=0.0, S=0.001) == 0.0


class TestTrapezoidalChannel:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_chow_example_6_1(self) -> None:
        """Chow (1959) Example 6-1 — trapezoidal channel.

        b=20ft, z=1.5, S=0.0016, n=0.025, y=4ft
        Hand-verified: A=104ft², P=34.422ft, R=3.0213ft → Q=516.78 cfs
        (Chow's textbook reports ~519 cfs due to intermediate rounding.)
        """
        hf.set_units("imperial")
        ch = hf.TrapezoidalChannel(
            bottom_width=20.0,  # ft
            side_slope=1.5,
            slope=0.0016,
            roughness=0.025,
        )
        Q = ch.normal_flow(depth=4.0)  # returns cfs
        assert pytest.approx(516.78, rel=0.001) == Q

    def test_normal_depth_roundtrip(self) -> None:
        """Compute Q at known depth, then recover that depth from Q."""
        ch = hf.TrapezoidalChannel(
            bottom_width=3.0,
            side_slope=2.0,
            slope=0.001,
            roughness="concrete",
        )
        Q = ch.normal_flow(depth=1.5)
        recovered_depth = ch.normal_depth(flow=Q)
        assert recovered_depth == pytest.approx(1.5, rel=1e-6)

    def test_critical_depth(self) -> None:
        ch = hf.TrapezoidalChannel(
            bottom_width=3.0,
            side_slope=2.0,
            slope=0.001,
            roughness="concrete",
        )
        Q = ch.normal_flow(depth=1.5)
        yc = ch.critical_depth(flow=Q)
        # Critical depth should be less than normal depth for mild slope
        assert yc > 0
        assert yc < 1.5  # subcritical → yc < yn

    def test_froude_subcritical(self) -> None:
        """A mild slope channel should be subcritical."""
        ch = hf.TrapezoidalChannel(
            bottom_width=3.0,
            side_slope=2.0,
            slope=0.001,
            roughness="concrete",
        )
        fr = ch.froude_number(depth=1.5)
        assert fr < 1.0
        assert ch.flow_regime(depth=1.5) == FlowRegime.SUBCRITICAL

    def test_flow_regime_supercritical(self) -> None:
        """A steep slope should produce supercritical flow."""
        ch = hf.TrapezoidalChannel(
            bottom_width=3.0,
            side_slope=1.0,
            slope=0.05,  # very steep
            roughness=0.025,
        )
        fr = ch.froude_number(depth=0.2)
        assert fr > 1.0
        assert ch.flow_regime(depth=0.2) == FlowRegime.SUPERCRITICAL

    def test_si_params(self) -> None:
        ch = hf.TrapezoidalChannel(
            bottom_width=3.0, side_slope=2.0, slope=0.001, roughness="concrete"
        )
        b, z, S, n = ch.si_params
        assert b == pytest.approx(3.0)
        assert z == 2.0
        assert S == 0.001
        assert n == 0.013

    def test_invalid_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="slope"):
            hf.TrapezoidalChannel(bottom_width=3.0, side_slope=2.0, slope=-0.001, roughness=0.013)


class TestRectangularChannel:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_critical_depth_closed_form(self) -> None:
        """Rectangular critical depth: y_c = (Q²/(g·b²))^(1/3)."""
        ch = hf.RectangularChannel(width=3.0, slope=0.002, roughness=0.013)

        Q = 7.0  # m³/s
        yc = ch.critical_depth(flow=Q)
        expected = (Q**2 / (9.80665 * 3.0**2)) ** (1.0 / 3.0)
        assert yc == pytest.approx(expected, rel=1e-6)

    def test_froude_at_critical_depth_is_one(self) -> None:
        """Fr should be ≈ 1 at the critical depth."""
        ch = hf.RectangularChannel(width=3.0, slope=0.002, roughness=0.013)
        Q = 7.0
        yc = ch.critical_depth(flow=Q)
        # Compute Fr directly from flow and depth
        A = 3.0 * yc
        V = Q / A
        fr = V / math.sqrt(9.80665 * yc)
        assert fr == pytest.approx(1.0, abs=0.01)

    def test_normal_depth_roundtrip(self) -> None:
        ch = hf.RectangularChannel(width=5.0, slope=0.001, roughness="earth_clean")
        Q = ch.normal_flow(depth=2.0)
        y_back = ch.normal_depth(flow=Q)
        assert y_back == pytest.approx(2.0, rel=1e-6)

    def test_imperial_mode(self) -> None:
        """Verify imperial inputs/outputs work correctly."""
        hf.set_units("imperial")
        ch = hf.RectangularChannel(width=10.0, slope=0.001, roughness=0.013)  # ft
        Q = ch.normal_flow(depth=3.0)  # should return cfs
        assert Q > 0
        # Verify roundtrip
        y_back = ch.normal_depth(flow=Q)
        assert y_back == pytest.approx(3.0, rel=1e-5)


class TestTriangularChannel:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_critical_depth_closed_form(self) -> None:
        """Triangular critical depth: y_c = (2Q²/(g·z²))^(1/5)."""
        ch = hf.TriangularChannel(side_slope=2.0, slope=0.005, roughness=0.025)
        Q = 3.0  # m³/s
        yc = ch.critical_depth(flow=Q)
        expected = (2.0 * Q**2 / (9.80665 * 4.0)) ** 0.2
        assert yc == pytest.approx(expected, rel=1e-6)

    def test_normal_depth_roundtrip(self) -> None:
        ch = hf.TriangularChannel(side_slope=1.5, slope=0.01, roughness=0.025)
        Q = ch.normal_flow(depth=1.0)
        y_back = ch.normal_depth(flow=Q)
        assert y_back == pytest.approx(1.0, rel=1e-6)


class TestCircularChannel:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_full_flow_capacity(self) -> None:
        """D=0.6m, S=0.005, n=0.013 → Q_full via Manning's."""
        ch = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="concrete")
        Q_full = ch.full_flow_capacity()
        # Manual: A=π(0.3)²=0.2827, R=0.15, Q=(1/0.013)*0.2827*0.15^(2/3)*0.005^0.5
        r = 0.3
        A = math.pi * r**2
        R = 0.6 / 4.0
        expected = (1.0 / 0.013) * A * R ** (2 / 3) * 0.005**0.5
        assert Q_full == pytest.approx(expected, rel=1e-3)

    def test_max_flow_exceeds_full_flow(self) -> None:
        """Maximum Q occurs at y/D ≈ 0.938, not at y = D."""
        ch = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="concrete")
        Q_full = ch.full_flow_capacity()
        Q_max = ch.max_flow_capacity()
        assert Q_max > Q_full

    def test_normal_depth_roundtrip(self) -> None:
        ch = hf.CircularChannel(diameter=1.0, slope=0.002, roughness="concrete")
        Q = ch.normal_flow(depth=0.5)  # half full
        y_back = ch.normal_depth(flow=Q)
        assert y_back == pytest.approx(0.5, rel=1e-4)

    def test_surcharge_raises(self) -> None:
        ch = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="concrete")
        with pytest.raises(ValueError, match=r"surcharge|exceed"):
            ch.normal_flow(depth=0.7)

    def test_supercritical_on_steep_slope(self) -> None:
        ch = hf.CircularChannel(diameter=1.0, slope=0.05, roughness="concrete")
        fr = ch.froude_number(depth=0.3)
        assert fr > 1.0
        assert ch.flow_regime(depth=0.3) == FlowRegime.SUPERCRITICAL

    def test_subcritical_on_mild_slope(self) -> None:
        ch = hf.CircularChannel(diameter=1.0, slope=0.001, roughness="concrete")
        fr = ch.froude_number(depth=0.7)
        assert fr < 1.0
        assert ch.flow_regime(depth=0.7) == FlowRegime.SUBCRITICAL

    def test_imperial_roundtrip(self) -> None:
        hf.set_units("imperial")
        ch = hf.CircularChannel(diameter=2.0, slope=0.005, roughness="concrete")  # 2 ft
        Q = ch.normal_flow(depth=1.0)  # cfs at 1 ft depth
        y_back = ch.normal_depth(flow=Q)
        assert y_back == pytest.approx(1.0, rel=1e-4)

    def test_critical_depth(self) -> None:
        ch = hf.CircularChannel(diameter=1.0, slope=0.005, roughness="concrete")
        Q = ch.normal_flow(depth=0.5)
        yc = ch.critical_depth(flow=Q)
        assert yc > 0
        assert yc < 1.0

    def test_si_params(self) -> None:
        ch = hf.CircularChannel(diameter=1.0, slope=0.002, roughness="concrete")
        D, S, n = ch.si_params
        assert pytest.approx(1.0) == D
        assert S == 0.002
        assert n == 0.013

    def test_normal_depth_surcharge_raises(self) -> None:
        """Flow exceeding max pipe capacity raises ValueError."""
        ch = hf.CircularChannel(diameter=0.6, slope=0.005, roughness="concrete")
        Q_max = ch.max_flow_capacity()
        with pytest.raises(ValueError, match=r"surcharge|exceed"):
            ch.normal_depth(flow=Q_max * 1.5)

    def test_invalid_diameter_raises(self) -> None:
        with pytest.raises(ValueError, match="diameter"):
            hf.CircularChannel(diameter=-1.0, slope=0.005, roughness=0.013)

    def test_invalid_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="slope"):
            hf.CircularChannel(diameter=1.0, slope=-0.005, roughness=0.013)


class TestKernelHelpers:
    """Test internal kernel functions for edge cases."""

    def test_froude_zero_area(self) -> None:
        assert _froude(1.0, 0.0, 1.0) == 0.0

    def test_froude_zero_top_width(self) -> None:
        assert _froude(1.0, 1.0, 0.0) == 0.0

    def test_classify_critical(self) -> None:
        assert _classify_flow(1.0) == FlowRegime.CRITICAL
        assert _classify_flow(1.005) == FlowRegime.CRITICAL
        assert _classify_flow(0.995) == FlowRegime.CRITICAL


class TestRectangularChannelExtended:
    """Additional coverage for RectangularChannel."""

    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_froude_and_regime(self) -> None:
        ch = hf.RectangularChannel(width=3.0, slope=0.002, roughness=0.013)
        fr = ch.froude_number(depth=1.0)
        assert fr > 0
        regime = ch.flow_regime(depth=1.0)
        assert isinstance(regime, FlowRegime)

    def test_si_params(self) -> None:
        ch = hf.RectangularChannel(width=5.0, slope=0.001, roughness="concrete")
        b, S, n = ch.si_params
        assert b == pytest.approx(5.0)
        assert S == 0.001
        assert n == 0.013

    def test_invalid_width_raises(self) -> None:
        with pytest.raises(ValueError, match="width"):
            hf.RectangularChannel(width=-1.0, slope=0.001, roughness=0.013)

    def test_invalid_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="slope"):
            hf.RectangularChannel(width=3.0, slope=-0.001, roughness=0.013)


class TestTriangularChannelExtended:
    """Additional coverage for TriangularChannel."""

    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_froude_and_regime(self) -> None:
        ch = hf.TriangularChannel(side_slope=2.0, slope=0.005, roughness=0.025)
        fr = ch.froude_number(depth=0.5)
        assert fr > 0
        regime = ch.flow_regime(depth=0.5)
        assert isinstance(regime, FlowRegime)

    def test_si_params(self) -> None:
        ch = hf.TriangularChannel(side_slope=1.5, slope=0.01, roughness=0.025)
        z, S, n = ch.si_params
        assert z == 1.5
        assert S == 0.01
        assert n == 0.025

    def test_invalid_side_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="side_slope"):
            hf.TriangularChannel(side_slope=-1.0, slope=0.01, roughness=0.025)

    def test_invalid_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="slope"):
            hf.TriangularChannel(side_slope=2.0, slope=-0.01, roughness=0.025)


class TestTrapezoidalChannelExtended:
    """Additional coverage for TrapezoidalChannel validation."""

    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_invalid_bottom_width_raises(self) -> None:
        with pytest.raises(ValueError, match="bottom_width"):
            hf.TrapezoidalChannel(bottom_width=-1.0, side_slope=2.0, slope=0.001, roughness=0.013)

    def test_invalid_side_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="side_slope"):
            hf.TrapezoidalChannel(bottom_width=3.0, side_slope=-1.0, slope=0.001, roughness=0.013)
