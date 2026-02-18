"""Detention pond routing via the Modified Puls (Storage-Indication) method.

The storage-indication formulation eliminates the iterative solve that
plagues spreadsheet implementations: each time step is a direct table lookup.

References
----------
- Chow, V.T. et al. (1988). Applied Hydrology. McGraw-Hill, Chapter 8.
- NRCS NEH Part 630, Chapter 17.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import interp1d

from hydroflow.units import to_si

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from hydroflow.core.hydrology import Hydrograph
    from hydroflow.core.structures import CompositeOutlet, _Structure

__all__ = [
    "DetentionPond",
    "RoutingResult",
]


@dataclass(frozen=True)
class RoutingResult:
    """Result of a detention pond routing analysis."""

    outflow_cms: NDArray[np.floating]
    """Outflow time series (m^3/s)."""

    stages_m: NDArray[np.floating]
    """Stage (water surface elevation) time series (meters)."""

    times_seconds: NDArray[np.floating]
    """Time values in seconds."""

    peak_inflow: float
    """Peak inflow rate (m^3/s)."""

    peak_outflow: float
    """Peak outflow rate (m^3/s)."""

    peak_reduction: float
    """Peak reduction fraction (e.g. 0.55 means 55% reduction)."""

    max_stage: float
    """Maximum water surface stage (meters)."""

    time_to_peak_outflow: float
    """Time of peak outflow (seconds)."""


class DetentionPond:
    """Detention pond with Modified Puls routing.

    Parameters
    ----------
    stages : array-like
        Stage (elevation) values in **active length units**, ascending.
    storages : array-like
        Corresponding storage volumes in **active volume units**.
    outlet : structure or CompositeOutlet
        Outlet structure(s) providing ``discharge_si(stage_si)`` method.

    Examples
    --------
    >>> import hydroflow as hf
    >>> from hydroflow.structures import RectangularWeir, CompositeOutlet
    >>> weir = RectangularWeir(length=2.0, crest=1.0)
    >>> pond = DetentionPond(
    ...     stages=[0, 1, 2, 3],
    ...     storages=[0, 10000, 25000, 45000],
    ...     outlet=weir,
    ... )
    """

    def __init__(
        self,
        stages: list[float] | NDArray[np.floating],
        storages: list[float] | NDArray[np.floating],
        outlet: _Structure | CompositeOutlet,
    ) -> None:
        # Convert to SI
        stages_arr = np.asarray(stages, dtype=np.float64)
        storages_arr = np.asarray(storages, dtype=np.float64)

        self._stages_si = np.array(
            [to_si(float(s), "length") for s in stages_arr]
        )
        self._storages_si = np.array(
            [to_si(float(v), "volume") for v in storages_arr]
        )
        self._outlet = outlet

        # Pre-compute stage-discharge at tabulated stages
        self._outflows_si = np.array(
            [outlet.discharge_si(float(h)) for h in self._stages_si]
        )

    def route(
        self,
        inflow: Hydrograph | NDArray[np.floating],
        dt: float | None = None,
        initial_stage: float = 0.0,
    ) -> RoutingResult:
        """Route an inflow hydrograph through the pond.

        Parameters
        ----------
        inflow : Hydrograph or ndarray
            Inflow time series. If a ``Hydrograph`` object, uses its
            ``flows_cms`` and infers ``dt`` from ``times_seconds``.
            If an ndarray, values are in **m^3/s** (SI).
        dt : float, optional
            Time step in seconds. Required if *inflow* is an ndarray.
        initial_stage : float
            Initial water surface stage (active length units). Default 0.

        Returns
        -------
        RoutingResult

        Examples
        --------
        >>> import numpy as np
        >>> import hydroflow as hf
        >>> hf.set_units("metric")
        >>> from hydroflow.structures import RectangularWeir
        >>> weir = RectangularWeir(length=2.0, crest=1.0)
        >>> pond = hf.DetentionPond(
        ...     stages=[0, 1, 2, 3], storages=[0, 10000, 25000, 45000], outlet=weir,
        ... )
        >>> inflow = np.array([0, 1, 3, 5, 3, 1, 0], dtype=float)
        >>> result = pond.route(inflow, dt=600.0)
        >>> result.peak_outflow < result.peak_inflow
        True
        """
        # Extract inflow array and time step
        from hydroflow.core.hydrology import Hydrograph as _Hydrograph

        if isinstance(inflow, _Hydrograph):
            inflow_si = np.asarray(inflow.flows_cms, dtype=np.float64)
            if dt is None:
                dt_s = float(inflow.times_seconds[1] - inflow.times_seconds[0])
            else:
                dt_s = float(dt)
        else:
            inflow_si = np.asarray(inflow, dtype=np.float64)
            if dt is None:
                msg = "dt (time step in seconds) is required when inflow is an array"
                raise ValueError(msg)
            dt_s = float(dt)

        n_steps = len(inflow_si)
        h0_si = to_si(initial_stage, "length")

        # ── Build the storage-indication curve ───────────────────────────
        # SI(h) = 2*S(h)/dt + O(h)
        SI_values = 2.0 * self._storages_si / dt_s + self._outflows_si

        # Interpolation functions: h → O(h), h → S(h), SI → h (inverse)
        _h_to_outflow = interp1d(
            self._stages_si, self._outflows_si,
            kind="linear", fill_value="extrapolate",
        )
        _h_to_storage = interp1d(
            self._stages_si, self._storages_si,
            kind="linear", fill_value="extrapolate",
        )
        _SI_to_h = interp1d(
            SI_values, self._stages_si,
            kind="linear", fill_value="extrapolate",
        )

        # ── Route ────────────────────────────────────────────────────────
        stages = np.zeros(n_steps)
        outflows = np.zeros(n_steps)

        # Initial conditions
        stages[0] = h0_si
        outflows[0] = float(_h_to_outflow(h0_si))
        S0 = float(_h_to_storage(h0_si))
        SI_prev = 2.0 * S0 / dt_s + outflows[0]

        for i in range(1, n_steps):
            # SI(h₂) = I₁ + I₂ + SI(h₁) - 2*O(h₁)
            SI_next = inflow_si[i - 1] + inflow_si[i] + SI_prev - 2.0 * outflows[i - 1]

            # Clamp: SI cannot go below zero (pond can't have negative storage)
            SI_next = max(SI_next, 0.0)

            # Inverse lookup: SI → h
            h_next = float(_SI_to_h(SI_next))
            h_next = max(h_next, float(self._stages_si[0]))

            stages[i] = h_next
            outflows[i] = max(float(_h_to_outflow(h_next)), 0.0)
            SI_prev = SI_next

        # ── Build result ─────────────────────────────────────────────────
        times = np.arange(n_steps) * dt_s
        peak_in = float(np.max(inflow_si))
        peak_out = float(np.max(outflows))
        reduction = 1.0 - peak_out / peak_in if peak_in > 0 else 0.0
        max_stage = float(np.max(stages))
        t_peak_out = float(times[np.argmax(outflows)])

        return RoutingResult(
            outflow_cms=outflows,
            stages_m=stages,
            times_seconds=times,
            peak_inflow=peak_in,
            peak_outflow=peak_out,
            peak_reduction=reduction,
            max_stage=max_stage,
            time_to_peak_outflow=t_peak_out,
        )
