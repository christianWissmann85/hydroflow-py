"""Tests for hydroflow.geometry.

Reference values computed from known formulas and verified against
Chow (1959) and standard hydraulic engineering textbooks.
"""

import math

import pytest

from hydroflow.geometry import circular, rectangular, trapezoidal, triangular


class TestTrapezoidal:
    def test_basic_properties(self) -> None:
        # b=3m, z=2, y=1.5m
        props = trapezoidal(y=1.5, b=3.0, z=2.0)
        expected_area = (3.0 + 2.0 * 1.5) * 1.5  # 9.0
        expected_perimeter = 3.0 + 2 * 1.5 * math.sqrt(1 + 4)  # 3 + 3*2.236 = 9.708
        expected_top_width = 3.0 + 2 * 2.0 * 1.5  # 9.0
        assert props.area == pytest.approx(expected_area)
        assert props.wetted_perimeter == pytest.approx(expected_perimeter, rel=1e-3)
        assert props.hydraulic_radius == pytest.approx(expected_area / expected_perimeter)
        assert props.top_width == pytest.approx(expected_top_width)
        assert props.hydraulic_depth == pytest.approx(expected_area / expected_top_width)

    def test_chow_example(self) -> None:
        """Chow (1959) Example 6-1: b=20ft (6.096m), z=1.5, y=4ft (1.2192m)."""
        b = 20 * 0.3048  # ft to m
        y = 4 * 0.3048
        props = trapezoidal(y=y, b=b, z=1.5)
        expected_area = (b + 1.5 * y) * y
        assert props.area == pytest.approx(expected_area, rel=1e-6)

    def test_zero_depth(self) -> None:
        props = trapezoidal(y=0.0, b=3.0, z=2.0)
        assert props.area == 0.0
        assert props.top_width == 3.0  # bottom width at zero depth

    def test_zero_side_slope_is_rectangular(self) -> None:
        trap = trapezoidal(y=2.0, b=5.0, z=0.0)
        rect = rectangular(y=2.0, b=5.0)
        assert trap.area == pytest.approx(rect.area)
        assert trap.wetted_perimeter == pytest.approx(rect.wetted_perimeter)

    def test_negative_depth_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            trapezoidal(y=-1.0, b=3.0, z=2.0)


class TestRectangular:
    def test_basic_properties(self) -> None:
        props = rectangular(y=2.0, b=5.0)
        assert props.area == pytest.approx(10.0)
        assert props.wetted_perimeter == pytest.approx(9.0)
        assert props.hydraulic_radius == pytest.approx(10.0 / 9.0)
        assert props.top_width == pytest.approx(5.0)
        assert props.hydraulic_depth == pytest.approx(2.0)  # = y for rectangular

    def test_hydraulic_depth_equals_actual_depth(self) -> None:
        """For rectangular channels, D_h = A/T = by/b = y."""
        for y in [0.5, 1.0, 2.0, 5.0]:
            props = rectangular(y=y, b=3.0)
            assert props.hydraulic_depth == pytest.approx(y)


class TestTriangular:
    def test_basic_properties(self) -> None:
        props = triangular(y=1.0, z=2.0)
        expected_area = 2.0 * 1.0**2  # 2.0
        expected_perimeter = 2.0 * 1.0 * math.sqrt(5)  # 4.472
        assert props.area == pytest.approx(expected_area)
        assert props.wetted_perimeter == pytest.approx(expected_perimeter, rel=1e-3)
        assert props.top_width == pytest.approx(4.0)  # 2*z*y
        assert props.hydraulic_depth == pytest.approx(0.5)  # y/2

    def test_hydraulic_depth_is_half_depth(self) -> None:
        """For triangular channels, D_h = A/T = zy²/(2zy) = y/2."""
        for y in [0.5, 1.0, 3.0]:
            props = triangular(y=y, z=1.5)
            assert props.hydraulic_depth == pytest.approx(y / 2.0)


class TestCircular:
    def test_half_full(self) -> None:
        """At y = D/2 (half full), θ = π/2."""
        D = 1.0
        props = circular(y=0.5, diameter=D)
        r = D / 2.0
        expected_area = math.pi * r**2 / 2.0  # half the full area
        assert props.area == pytest.approx(expected_area, rel=1e-6)
        # R at half full = R at full = D/4
        assert props.hydraulic_radius == pytest.approx(D / 4.0, rel=1e-3)
        # Top width at half full = D
        assert props.top_width == pytest.approx(D, rel=1e-6)

    def test_full_pipe(self) -> None:
        D = 0.6
        props = circular(y=D, diameter=D)
        r = D / 2.0
        assert props.area == pytest.approx(math.pi * r**2)
        assert props.wetted_perimeter == pytest.approx(2 * math.pi * r)
        assert props.hydraulic_radius == pytest.approx(D / 4.0)
        assert props.top_width == 0.0  # full pipe has no free surface

    def test_quarter_full(self) -> None:
        D = 1.0
        y = 0.25  # quarter depth
        props = circular(y=y, diameter=D)
        assert props.area > 0
        assert props.wetted_perimeter > 0
        assert props.area < math.pi * (D / 2) ** 2  # less than full

    def test_surcharge_raises(self) -> None:
        with pytest.raises(ValueError, match="surcharge"):
            circular(y=1.1, diameter=1.0)

    def test_zero_depth(self) -> None:
        props = circular(y=0.0, diameter=1.0)
        assert props.area == 0.0
        assert props.wetted_perimeter == 0.0

    def test_area_increases_with_depth(self) -> None:
        D = 1.0
        depths = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        areas = [circular(y=y, diameter=D).area for y in depths]
        for i in range(len(areas) - 1):
            assert areas[i + 1] > areas[i]
