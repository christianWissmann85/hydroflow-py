"""Rainfall-runoff hydrology: SCS Curve Number, Rational Method, design storms.

Provides the core calculations that every civil engineer does daily —
currently locked inside Excel spreadsheets.

References
----------
- NRCS NEH Part 630, Chapters 9, 10, 16 (SCS methods).
- Kirpich, Z.P. (1940). Time of concentration of small agricultural watersheds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from hydroflow.units import from_si, to_si

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = [
    "scs_runoff_depth",
    "rational_method",
    "time_of_concentration",
    "Watershed",
    "DesignStorm",
    "scs_unit_hydrograph",
]

# ── Constants ─────────────────────────────────────────────────────────

_G = 9.80665

# SCS dimensionless unit hydrograph ordinates (NEH Part 630, Ch. 16, Table 16-4)
_SCS_UH_T_RATIO = np.array([
    0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
    1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9,
    2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6, 3.8,
    4.0, 4.5, 5.0,
])
_SCS_UH_Q_RATIO = np.array([
    0.000, 0.030, 0.100, 0.190, 0.310, 0.470, 0.660, 0.820, 0.930, 0.990,
    1.000, 0.990, 0.930, 0.860, 0.780, 0.680, 0.560, 0.460, 0.390, 0.330,
    0.280, 0.207, 0.147, 0.107, 0.077, 0.055, 0.040, 0.029, 0.021, 0.015,
    0.011, 0.005, 0.000,
])

# SCS Type II 24-hour cumulative distribution (fraction of 24h, fraction of total depth)
_SCS_TYPE_II_TIME = np.array([
    0.000, 0.042, 0.083, 0.125, 0.167, 0.208,
    0.250, 0.292, 0.333, 0.375, 0.396, 0.417,
    0.438, 0.458, 0.479, 0.487, 0.492, 0.500,
    0.521, 0.542, 0.563, 0.583, 0.625, 0.667,
    0.708, 0.750, 0.792, 0.833, 0.875, 0.917,
    0.958, 1.000,
])
_SCS_TYPE_II_FRAC = np.array([
    0.000, 0.011, 0.022, 0.035, 0.048, 0.063,
    0.080, 0.098, 0.120, 0.147, 0.163, 0.181,
    0.204, 0.235, 0.283, 0.357, 0.663, 0.735,
    0.772, 0.799, 0.820, 0.838, 0.866, 0.891,
    0.914, 0.935, 0.953, 0.968, 0.980, 0.989,
    0.995, 1.000,
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCS CURVE NUMBER RUNOFF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def scs_runoff_depth(
    rainfall: float,
    curve_number: float,
    *,
    initial_abstraction_ratio: float = 0.2,
) -> float:
    """Compute direct runoff depth using the SCS Curve Number method.

    Parameters
    ----------
    rainfall : float
        Total rainfall depth (in active rainfall units: mm or inches).
    curve_number : float
        SCS Curve Number (1-99).
    initial_abstraction_ratio : float
        Ratio of initial abstraction to maximum retention (default 0.2).

    Returns
    -------
    float
        Direct runoff depth (same units as rainfall).

    References
    ----------
    NRCS NEH Part 630, Chapter 10, Eq. 10-1 through 10-4.

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> f"{scs_runoff_depth(rainfall=127.0, curve_number=75):.1f}"  # mm
    '62.2'
    """
    if curve_number <= 0 or curve_number > 100:
        msg = f"Curve number must be in (0, 100], got {curve_number}"
        raise ValueError(msg)
    if rainfall <= 0:
        return 0.0

    # Convert rainfall to SI (meters) for internal calculation
    P_si = to_si(rainfall, "rainfall")

    if curve_number == 100:
        return from_si(P_si, "rainfall")

    # S in meters: S = (25400/CN - 254) mm → convert to m
    S_mm = 25400.0 / curve_number - 254.0
    S_si = S_mm * 1e-3  # mm to meters

    Ia = initial_abstraction_ratio * S_si

    if P_si <= Ia:
        return 0.0

    Q_si = (P_si - Ia) ** 2 / (P_si - Ia + S_si)
    return from_si(Q_si, "rainfall")


def _scs_runoff_incremental(
    cumulative_rainfall_si: NDArray[np.floating],
    cn: float,
    ia_ratio: float = 0.2,
) -> NDArray[np.floating]:
    """Incremental runoff from a cumulative rainfall array (SI, meters).

    Must be applied cumulatively — NOT per-increment.
    """
    if cn == 100:
        increments = np.diff(cumulative_rainfall_si, prepend=0.0)
        return np.maximum(increments, 0.0)

    S_si = (25400.0 / cn - 254.0) * 1e-3
    Ia = ia_ratio * S_si

    Q_cum = np.where(
        cumulative_rainfall_si <= Ia,
        0.0,
        (cumulative_rainfall_si - Ia) ** 2 / (cumulative_rainfall_si - Ia + S_si),
    )
    return np.maximum(np.diff(Q_cum, prepend=0.0), 0.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RATIONAL METHOD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def rational_method(
    C: float,
    intensity: float,
    area: float,
) -> float:
    """Peak discharge using the Rational Method (Q = CiA).

    Parameters
    ----------
    C : float
        Runoff coefficient (dimensionless, 0-1).
    intensity : float
        Rainfall intensity at time of concentration
        (in active units: mm/hr or in/hr).
    area : float
        Catchment area (in active catch_area units: km² or mi²).

    Returns
    -------
    float
        Peak discharge (in active flow units: m³/s or cfs).

    References
    ----------
    Mulvaney, T.J. (1851). On the use of self-registering rain and flood gauges.

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> f"{rational_method(C=0.70, intensity=88.9, area=hf.ha(6.07)):.3f}"
    '1.049'
    """
    if C < 0 or C > 1:
        msg = f"Runoff coefficient C must be in [0, 1], got {C}"
        raise ValueError(msg)

    # Convert to SI: intensity → m/s, area → m²
    i_si = to_si(intensity, "rainfall_intensity")  # m/s
    A_si = to_si(area, "catch_area")  # m²

    Q_si = C * i_si * A_si  # m³/s
    return from_si(Q_si, "flow")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIME OF CONCENTRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def time_of_concentration(
    method: str,
    length: float,
    slope: float,
    *,
    curve_number: float | None = None,
    runoff_coefficient: float | None = None,
) -> float:
    """Compute time of concentration using a named method.

    Parameters
    ----------
    method : str
        One of ``"kirpich"``, ``"nrcs_lag"``, ``"faa"``.
    length : float
        Flow path length (in active length units).
    slope : float
        Average slope (as a fraction, e.g. 0.02 for 2%).
    curve_number : float, optional
        Required for ``"nrcs_lag"`` method.
    runoff_coefficient : float, optional
        Required for ``"faa"`` method.

    Returns
    -------
    float
        Time of concentration in **minutes**.

    References
    ----------
    - Kirpich (1940): Tc = 0.0078 * L^0.77 * S_pct^(-0.385) [L in ft, Tc in min]
    - NRCS Lag: Lag = L^0.8 * (S_ret+1)^0.7 / (1140 * Y^0.5) [hours]
    - FAA: Tc = 1.8 * (1.1 - C) * L^0.5 / S_pct^(1/3) [L in ft, Tc in min]

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> Tc = hf.time_of_concentration(
    ...     method="kirpich", length=hf.ft(3000), slope=0.02
    ... )
    >>> f"{Tc:.1f}"
    '2.8'
    """
    # Convert length to feet for all formulas (they were derived in imperial)
    L_si = to_si(length, "length")
    L_ft = L_si / 0.3048
    S_pct = slope * 100.0  # convert fraction to percent

    if S_pct <= 0:
        msg = f"Slope must be positive, got {slope}"
        raise ValueError(msg)

    method_lower = method.lower().strip()

    if method_lower == "kirpich":
        Tc_min = 0.0078 * L_ft**0.77 * S_pct ** (-0.385)
        return float(Tc_min)

    if method_lower == "nrcs_lag":
        if curve_number is None:
            msg = "curve_number is required for 'nrcs_lag' method"
            raise ValueError(msg)
        S_ret = 1000.0 / curve_number - 10.0  # retention in inches
        lag_hr = (L_ft**0.8 * (S_ret + 1.0) ** 0.7) / (1140.0 * S_pct**0.5)
        Tc_min = lag_hr / 0.6 * 60.0  # lag = 0.6 * Tc → Tc = lag/0.6; hours→min
        return float(Tc_min)

    if method_lower == "faa":
        if runoff_coefficient is None:
            msg = "runoff_coefficient is required for 'faa' method"
            raise ValueError(msg)
        C = runoff_coefficient
        Tc_min = 1.8 * (1.1 - C) * L_ft**0.5 / S_pct ** (1.0 / 3.0)
        return float(Tc_min)

    msg = f"Unknown Tc method: {method!r}. Available: 'kirpich', 'nrcs_lag', 'faa'"
    raise ValueError(msg)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WATERSHED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class Watershed:
    """Container for watershed properties.

    Parameters
    ----------
    area : float
        Watershed area (in active catch_area units: km² or mi²).
    curve_number : float
        SCS Curve Number (1-99).
    time_of_concentration : float
        Time of concentration in **minutes**.
    slope : float
        Average watershed slope (fraction), optional.

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> ws = hf.Watershed(area=hf.ha(50), curve_number=80, time_of_concentration=30.0)
    >>> f"{ws.area_km2:.1f}"
    '0.5'
    """

    area: float
    curve_number: float
    time_of_concentration: float  # minutes
    slope: float = 0.0

    @property
    def area_si(self) -> float:
        """Watershed area in m²."""
        return to_si(self.area, "catch_area")

    @property
    def area_km2(self) -> float:
        """Watershed area in km²."""
        return self.area_si / 1e6

    @property
    def tc_seconds(self) -> float:
        """Time of concentration in seconds."""
        return self.time_of_concentration * 60.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DESIGN STORM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class DesignStorm:
    """A rainfall hyetograph (intensity/depth vs. time).

    Create via :meth:`from_table` or :meth:`from_scs_type2`.

    All depths stored internally in meters.

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> storm = hf.DesignStorm.from_scs_type2(total_depth=100.0)
    >>> f"{storm.total_depth_si * 1000:.0f}"
    '100'
    """

    def __init__(
        self,
        times_seconds: NDArray[np.floating],
        cumulative_depths_si: NDArray[np.floating],
    ) -> None:
        self._times = times_seconds.copy()
        self._cum_depths = cumulative_depths_si.copy()

    @classmethod
    def from_table(
        cls,
        durations_minutes: list[float] | NDArray[np.floating],
        cumulative_depths: list[float] | NDArray[np.floating],
    ) -> DesignStorm:
        """Create a design storm from a table of cumulative depths.

        Parameters
        ----------
        durations_minutes : array-like
            Time values in minutes.
        cumulative_depths : array-like
            Cumulative rainfall depth at each time (in active rainfall units).
        """
        times_s = np.asarray(durations_minutes, dtype=np.float64) * 60.0
        depths = np.asarray(cumulative_depths, dtype=np.float64)
        # Convert depths to SI (meters)
        depths_si = np.array([to_si(float(d), "rainfall") for d in depths])
        return cls(times_s, depths_si)

    @classmethod
    def from_scs_type2(cls, total_depth: float, duration_hours: float = 24.0) -> DesignStorm:
        """Create an SCS Type II design storm.

        Parameters
        ----------
        total_depth : float
            Total 24-hour rainfall depth (in active rainfall units).
        duration_hours : float
            Storm duration (default 24 hours).
        """
        total_si = to_si(total_depth, "rainfall")
        times_s = _SCS_TYPE_II_TIME * duration_hours * 3600.0
        cum_depths_si = _SCS_TYPE_II_FRAC * total_si
        return cls(times_s, cum_depths_si)

    @property
    def duration_seconds(self) -> float:
        """Total storm duration in seconds."""
        return float(self._times[-1] - self._times[0])

    @property
    def total_depth_si(self) -> float:
        """Total rainfall depth in meters."""
        return float(self._cum_depths[-1])

    def hyetograph(
        self, timestep_minutes: float
    ) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        """Generate incremental rainfall hyetograph at a uniform time step.

        Parameters
        ----------
        timestep_minutes : float
            Desired output time step in minutes.

        Returns
        -------
        times_s : ndarray
            Time values in seconds (start of each interval).
        incremental_depths_si : ndarray
            Incremental rainfall depth (meters) per time step.
        """
        dt = timestep_minutes * 60.0
        t_out = np.arange(self._times[0], self._times[-1] + dt / 2, dt)
        cum_out = np.interp(t_out, self._times, self._cum_depths)
        increments = np.diff(cum_out)
        return t_out[:-1], np.maximum(increments, 0.0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCS UNIT HYDROGRAPH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True)
class Hydrograph:
    """A flow-vs-time result."""

    times_seconds: NDArray[np.floating]
    flows_cms: NDArray[np.floating]

    @property
    def peak_flow(self) -> float:
        """Peak discharge in m³/s."""
        return float(np.max(self.flows_cms))

    @property
    def peak_time_seconds(self) -> float:
        """Time of peak discharge in seconds."""
        return float(self.times_seconds[np.argmax(self.flows_cms)])

    @property
    def volume(self) -> float:
        """Total runoff volume in m³ (trapezoidal integration)."""
        return float(np.trapezoid(self.flows_cms, self.times_seconds))


def scs_unit_hydrograph(
    watershed: Watershed,
    storm: DesignStorm,
    timestep_minutes: float | None = None,
) -> Hydrograph:
    """Compute a composite runoff hydrograph using the SCS Unit Hydrograph method.

    Parameters
    ----------
    watershed : Watershed
        Watershed properties (area, CN, Tc).
    storm : DesignStorm
        Design storm hyetograph.
    timestep_minutes : float, optional
        Computation time step in minutes.  Default: Tc/5.

    Returns
    -------
    Hydrograph
        Flow vs. time result with peak_flow, peak_time, and volume.

    References
    ----------
    NRCS NEH Part 630, Chapter 16.

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> ws = hf.Watershed(area=hf.ha(50), curve_number=80, time_of_concentration=30.0)
    >>> storm = hf.DesignStorm.from_scs_type2(total_depth=100.0)
    >>> hydrograph = hf.scs_unit_hydrograph(ws, storm)
    >>> hydrograph.peak_flow > 0
    True
    """
    Tc_min = watershed.time_of_concentration

    # Default time step: Tc/5
    if timestep_minutes is None:
        timestep_minutes = max(Tc_min / 5.0, 1.0)  # at least 1 minute

    dt_min = timestep_minutes
    dt_s = dt_min * 60.0

    # ── Step 1: Get incremental rainfall ──────────────────────────────
    _times, rain_inc_si = storm.hyetograph(dt_min)

    # ── Step 2: Compute incremental runoff (SCS CN, cumulative method) ─
    cum_rain = np.cumsum(rain_inc_si)
    runoff_inc = _scs_runoff_incremental(cum_rain, watershed.curve_number)

    # ── Step 3: Build the unit hydrograph ─────────────────────────────
    # Tp = dt/2 + 0.6*Tc  (time to peak, in minutes)
    Tp_min = dt_min / 2.0 + 0.6 * Tc_min
    Tp_s = Tp_min * 60.0

    # Peak flow of UH for 1 mm of runoff over the watershed
    # qp = 0.208 * A_km2 / Tp_hr  [m³/s per mm of runoff]
    A_km2 = watershed.area_km2
    Tp_hr = Tp_min / 60.0
    qp = 0.208 * A_km2 / Tp_hr  # m³/s per mm of runoff depth

    # Interpolate dimensionless UH to computation time step
    t_uh = np.arange(0, 5.01 * Tp_s, dt_s)
    t_ratio = t_uh / Tp_s
    q_ratio = np.interp(t_ratio, _SCS_UH_T_RATIO, _SCS_UH_Q_RATIO, right=0.0)
    uh_ordinates = qp * q_ratio  # m³/s per mm of runoff depth

    # ── Step 4: Convolve runoff increments with UH ────────────────────
    # Convert runoff_inc from meters to mm to match UH units
    runoff_inc_mm = runoff_inc * 1000.0
    composite_flows = np.convolve(runoff_inc_mm, uh_ordinates)
    n_total = len(composite_flows)
    times_s = np.arange(n_total) * dt_s

    return Hydrograph(times_seconds=times_s, flows_cms=composite_flows)
