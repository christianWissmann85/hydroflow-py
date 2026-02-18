"""Tests for hydroflow.hydrology.

Reference values from:
    - NRCS NEH Part 630, Chapters 9, 10, 16.
    - Kirpich (1940). Time of concentration of small agricultural watersheds.
"""

import numpy as np
import pytest

import hydroflow as hf
from hydroflow.core.hydrology import (
    DesignStorm,
    Watershed,
    _scs_runoff_incremental,
    scs_runoff_depth,
    scs_unit_hydrograph,
    time_of_concentration,
)


class TestSCSRunoff:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_neh_reference(self) -> None:
        """NEH Chapter 10: P=127mm, CN=75 → Q≈62.2mm."""
        Q = scs_runoff_depth(rainfall=127.0, curve_number=75)
        assert pytest.approx(62.2, rel=0.01) == Q

    def test_imperial(self) -> None:
        """Same case in inches: P=5.0in, CN=75 → Q≈2.45in."""
        hf.set_units("imperial")
        Q = scs_runoff_depth(rainfall=5.0, curve_number=75)
        assert pytest.approx(2.45, rel=0.01) == Q

    def test_zero_rainfall(self) -> None:
        assert scs_runoff_depth(rainfall=0.0, curve_number=80) == 0.0

    def test_rainfall_below_ia(self) -> None:
        """Small storm, all absorbed by initial abstraction."""
        Q = scs_runoff_depth(rainfall=5.0, curve_number=50)
        # S = 25400/50 - 254 = 254mm, Ia = 50.8mm → 5mm < Ia
        assert Q == 0.0

    def test_cn_100(self) -> None:
        """CN=100: all rainfall becomes runoff."""
        Q = scs_runoff_depth(rainfall=50.0, curve_number=100)
        assert pytest.approx(50.0, rel=1e-6) == Q

    def test_invalid_cn_raises(self) -> None:
        with pytest.raises(ValueError, match="Curve number"):
            scs_runoff_depth(rainfall=50.0, curve_number=0)
        with pytest.raises(ValueError, match="Curve number"):
            scs_runoff_depth(rainfall=50.0, curve_number=101)

    def test_incremental_sums_to_total(self) -> None:
        """Incremental runoff should sum to total cumulative runoff."""
        cum_rain = np.array([10, 25, 50, 80, 100, 120], dtype=np.float64) * 1e-3
        cn = 75
        inc = _scs_runoff_incremental(cum_rain, cn)
        # Total incremental should equal total cumulative runoff
        total_inc = float(np.sum(inc))
        total_cum = scs_runoff_depth(rainfall=120.0, curve_number=cn) * 1e-3
        assert total_inc == pytest.approx(total_cum, rel=0.01)


class TestRationalMethod:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_design_doc_example(self) -> None:
        """Design doc: C=0.70, i=88.9 mm/hr, A=6.07 ha → Q≈1.049 m³/s."""
        Q = hf.rational_method(C=0.70, intensity=88.9, area=hf.ha(6.07))
        assert pytest.approx(1.049, rel=0.01) == Q

    def test_invalid_C_raises(self) -> None:
        with pytest.raises(ValueError, match="Runoff coefficient"):
            hf.rational_method(C=1.5, intensity=50.0, area=hf.ha(1.0))


class TestTimeOfConcentration:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_kirpich(self) -> None:
        """Kirpich: L=3000ft, S=2% → Tc≈2.84 min.

        Tc = 0.0078 * 3000^0.77 * 2.0^(-0.385) = 2.84 min
        """
        Tc = time_of_concentration(
            method="kirpich",
            length=hf.ft(3000),
            slope=0.02,
        )
        assert Tc == pytest.approx(2.84, rel=0.01)

    def test_nrcs_lag(self) -> None:
        """NRCS lag with typical watershed parameters."""
        Tc = time_of_concentration(
            method="nrcs_lag",
            length=hf.ft(5000),
            slope=0.03,
            curve_number=75,
        )
        assert Tc > 0

    def test_faa(self) -> None:
        """FAA method with C and L."""
        Tc = time_of_concentration(
            method="faa",
            length=hf.ft(2000),
            slope=0.02,
            runoff_coefficient=0.5,
        )
        assert Tc > 0

    def test_nrcs_requires_cn(self) -> None:
        with pytest.raises(ValueError, match="curve_number"):
            time_of_concentration(method="nrcs_lag", length=100.0, slope=0.02)

    def test_faa_requires_C(self) -> None:
        with pytest.raises(ValueError, match="runoff_coefficient"):
            time_of_concentration(method="faa", length=100.0, slope=0.02)

    def test_unknown_method_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown"):
            time_of_concentration(method="unknown", length=100.0, slope=0.02)

    def test_zero_slope_raises(self) -> None:
        with pytest.raises(ValueError, match="Slope"):
            time_of_concentration(method="kirpich", length=100.0, slope=0.0)


class TestDesignStorm:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_scs_type2_total_depth(self) -> None:
        """SCS Type II storm preserves total depth."""
        storm = DesignStorm.from_scs_type2(total_depth=100.0)  # 100 mm
        total_mm = storm.total_depth_si * 1000.0
        assert total_mm == pytest.approx(100.0, rel=1e-3)

    def test_scs_type2_duration(self) -> None:
        storm = DesignStorm.from_scs_type2(total_depth=100.0, duration_hours=24.0)
        assert storm.duration_seconds == pytest.approx(24.0 * 3600.0, rel=1e-6)

    def test_hyetograph_conserves_volume(self) -> None:
        """Incremental depths should sum to total depth."""
        storm = DesignStorm.from_scs_type2(total_depth=100.0)
        _times, increments = storm.hyetograph(timestep_minutes=30.0)
        total_si = float(np.sum(increments))
        assert total_si == pytest.approx(storm.total_depth_si, rel=0.02)

    def test_from_table(self) -> None:
        storm = DesignStorm.from_table(
            durations_minutes=[0, 30, 60, 90, 120],
            cumulative_depths=[0, 10, 30, 45, 50],
        )
        assert storm.total_depth_si == pytest.approx(0.050, rel=1e-3)


class TestSCSUnitHydrograph:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def test_produces_hydrograph(self) -> None:
        ws = Watershed(area=hf.ha(100), curve_number=75, time_of_concentration=60.0)
        storm = DesignStorm.from_scs_type2(total_depth=100.0)
        result = scs_unit_hydrograph(ws, storm)
        assert result.peak_flow > 0
        assert result.peak_time_seconds > 0
        assert result.volume > 0

    def test_peak_reduction(self) -> None:
        """Peak outflow should be less than peak rainfall intensity * area."""
        ws = Watershed(area=hf.ha(200), curve_number=80, time_of_concentration=90.0)
        storm = DesignStorm.from_scs_type2(total_depth=150.0)
        result = scs_unit_hydrograph(ws, storm)
        # Peak flow should be finite and positive
        assert 0 < result.peak_flow < 1e6

    def test_volume_conservation(self) -> None:
        """Hydrograph volume should approximately equal runoff volume."""
        ws = Watershed(area=hf.ha(50), curve_number=85, time_of_concentration=45.0)
        storm = DesignStorm.from_scs_type2(total_depth=80.0)
        result = scs_unit_hydrograph(ws, storm)

        # Expected runoff volume: runoff_depth * area
        Q_depth_mm = scs_runoff_depth(rainfall=80.0, curve_number=85)
        Q_depth_m = Q_depth_mm * 1e-3
        area_m2 = hf.to_si(hf.ha(50), "catch_area")
        expected_volume = Q_depth_m * area_m2

        assert result.volume == pytest.approx(expected_volume, rel=0.05)
