"""Tests for hydroflow.routing.

Reference behaviour from:
    - Chow et al. (1988). Applied Hydrology, Chapter 8.
"""

import numpy as np
import pytest

import hydroflow as hf
from hydroflow.core.routing import DetentionPond
from hydroflow.core.structures import RectangularWeir


class TestDetentionPond:
    def setup_method(self) -> None:
        hf.set_units("metric")

    def _make_pond(self) -> DetentionPond:
        """Standard test pond from design doc."""
        weir = RectangularWeir(length=2.0, crest=1.0, Cw=1.84)
        return DetentionPond(
            stages=[0, 1, 2, 3],
            storages=[0, 10000, 25000, 45000],
            outlet=weir,
        )

    def _triangular_inflow(self, peak: float, t_peak_hr: float, duration_hr: float, dt_s: float) -> np.ndarray:
        """Generate triangular inflow hydrograph (SI, m³/s)."""
        n = int(duration_hr * 3600 / dt_s) + 1
        times = np.arange(n) * dt_s
        t_peak_s = t_peak_hr * 3600.0
        duration_s = duration_hr * 3600.0
        inflow = np.where(
            times <= t_peak_s,
            peak * times / t_peak_s,
            peak * (duration_s - times) / (duration_s - t_peak_s),
        )
        return np.maximum(inflow, 0.0)

    def test_peak_attenuation(self) -> None:
        """Pond should reduce peak flow."""
        pond = self._make_pond()
        inflow = self._triangular_inflow(peak=15.0, t_peak_hr=3.0, duration_hr=8.0, dt_s=600.0)
        result = pond.route(inflow, dt=600.0)
        assert result.peak_outflow < result.peak_inflow
        assert result.peak_reduction > 0

    def test_peak_delay(self) -> None:
        """Peak outflow should be delayed relative to peak inflow."""
        pond = self._make_pond()
        inflow = self._triangular_inflow(peak=15.0, t_peak_hr=3.0, duration_hr=8.0, dt_s=600.0)
        result = pond.route(inflow, dt=600.0)
        t_peak_inflow = 3.0 * 3600.0
        assert result.time_to_peak_outflow >= t_peak_inflow

    def test_zero_inflow(self) -> None:
        """No inflow → no outflow."""
        pond = self._make_pond()
        inflow = np.zeros(50)
        result = pond.route(inflow, dt=600.0)
        assert result.peak_outflow == pytest.approx(0.0, abs=1e-10)
        assert result.peak_inflow == 0.0

    def test_mass_balance(self) -> None:
        """Outflow volume should not exceed inflow volume."""
        pond = self._make_pond()
        dt = 600.0
        inflow = self._triangular_inflow(peak=10.0, t_peak_hr=2.0, duration_hr=6.0, dt_s=dt)
        result = pond.route(inflow, dt=dt)
        vol_in = float(np.trapezoid(inflow, dx=dt))
        vol_out = float(np.trapezoid(result.outflow_cms, dx=dt))
        # Outflow volume ≤ inflow volume (some water may remain in storage)
        assert vol_out <= vol_in * 1.01

    def test_max_stage_within_table(self) -> None:
        """Moderate inflow should keep stage within table range."""
        pond = self._make_pond()
        inflow = self._triangular_inflow(peak=5.0, t_peak_hr=2.0, duration_hr=6.0, dt_s=600.0)
        result = pond.route(inflow, dt=600.0)
        assert result.max_stage <= 3.0

    def test_requires_dt_for_array(self) -> None:
        """Must provide dt when inflow is a plain array."""
        pond = self._make_pond()
        with pytest.raises(ValueError, match="dt"):
            pond.route(np.ones(10))
