"""Tests for hydroflow.units."""

import math

import pytest

import hydroflow as hf
from hydroflow.units import _Explicit


class TestSetGetUnits:
    def setup_method(self) -> None:
        hf.set_units("metric")  # reset before each test

    def test_default_is_metric(self) -> None:
        assert hf.get_units() == "metric"

    def test_set_imperial(self) -> None:
        hf.set_units("imperial")
        assert hf.get_units() == "imperial"

    def test_set_metric(self) -> None:
        hf.set_units("imperial")
        hf.set_units("metric")
        assert hf.get_units() == "metric"

    def test_invalid_system_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown unit system"):
            hf.set_units("martian")  # type: ignore[arg-type]


class TestToSi:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_metric_length_passthrough(self) -> None:
        assert hf.to_si(1.0, "length") == 1.0

    def test_imperial_length(self) -> None:
        hf.set_units("imperial")
        assert hf.to_si(1.0, "length") == pytest.approx(0.3048)

    def test_imperial_flow(self) -> None:
        hf.set_units("imperial")
        assert hf.to_si(1.0, "flow") == pytest.approx(0.028316846592)

    def test_explicit_overrides_global(self) -> None:
        # Global is metric, but value is tagged as feet
        result = hf.to_si(hf.ft(1.0), "length")
        assert result == pytest.approx(0.3048)

    def test_explicit_in_imperial_mode(self) -> None:
        hf.set_units("imperial")
        # Explicit meters should still work in imperial mode
        result = hf.to_si(hf.m(1.0), "length")
        assert result == pytest.approx(1.0)


class TestFromSi:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_metric_flow_passthrough(self) -> None:
        assert hf.from_si(1.0, "flow") == 1.0

    def test_imperial_length(self) -> None:
        hf.set_units("imperial")
        # 1 meter = 3.28084 feet
        assert hf.from_si(1.0, "length") == pytest.approx(1.0 / 0.3048, rel=1e-6)

    def test_roundtrip(self) -> None:
        hf.set_units("imperial")
        original = 42.0
        si = hf.to_si(original, "length")
        back = hf.from_si(si, "length")
        assert back == pytest.approx(original)


class TestExplicitTags:
    def test_ft_is_float_subclass(self) -> None:
        v = hf.ft(10.0)
        assert isinstance(v, float)
        assert isinstance(v, _Explicit)
        assert float(v) == 10.0

    def test_ft_arithmetic(self) -> None:
        # Should work like a regular float in arithmetic
        assert hf.ft(10.0) + 5.0 == 15.0
        assert hf.ft(3.0) * 2.0 == 6.0

    def test_unknown_unit_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown unit"):
            _Explicit(1.0, "parsecs")

    def test_all_shorthands_work(self) -> None:
        assert hf.to_si(hf.ft(1.0), "length") == pytest.approx(0.3048)
        assert hf.to_si(hf.m(1.0), "length") == pytest.approx(1.0)
        assert hf.to_si(hf.cfs(1.0), "flow") == pytest.approx(0.028316846592)
        assert hf.to_si(hf.cms(1.0), "flow") == pytest.approx(1.0)
        assert hf.to_si(hf.inches(1.0), "rainfall") == pytest.approx(0.0254)
        assert hf.to_si(hf.mm(1.0), "rainfall") == pytest.approx(0.001)
        assert hf.to_si(hf.acres(1.0), "catch_area") == pytest.approx(4046.8564224)
        assert hf.to_si(hf.ha(1.0), "catch_area") == pytest.approx(10000.0)

    def test_repr(self) -> None:
        assert "ft" in repr(hf.ft(10.0))
        assert "10" in repr(hf.ft(10.0))


class TestConversionAccuracy:
    """Verify specific conversion factors against known values."""

    def test_feet_to_meters(self) -> None:
        assert hf.to_si(hf.ft(100.0), "length") == pytest.approx(30.48)

    def test_cfs_to_cms(self) -> None:
        # 1000 cfs is a common engineering flow
        assert hf.to_si(hf.cfs(1000.0), "flow") == pytest.approx(28.3168, rel=1e-4)

    def test_acre_to_m2(self) -> None:
        assert hf.to_si(hf.acres(1.0), "catch_area") == pytest.approx(4046.86, rel=1e-4)

    def test_inches_to_mm(self) -> None:
        one_inch_si = hf.to_si(hf.inches(1.0), "rainfall")
        one_mm_si = hf.to_si(hf.mm(1.0), "rainfall")
        assert one_inch_si / one_mm_si == pytest.approx(25.4)

    def test_one_foot_cubed_equals_one_cfs_second(self) -> None:
        # cfs and ft³/s are the same unit
        ft3_si = 0.3048**3
        cfs_si = hf.to_si(hf.cfs(1.0), "flow")
        assert ft3_si == pytest.approx(cfs_si, rel=1e-6)

    def test_pi_relationship(self) -> None:
        # Sanity: circle area = pi*r^2, not unit-dependent
        r_ft = 10.0
        area_ft2 = math.pi * r_ft**2
        area_m2 = math.pi * (r_ft * 0.3048) ** 2
        assert hf.to_si(hf.ft(r_ft), "length") ** 2 * math.pi == pytest.approx(
            area_m2, rel=1e-6
        )
        assert area_ft2 * 0.3048**2 == pytest.approx(area_m2, rel=1e-6)
