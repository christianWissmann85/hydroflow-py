"""Hydraulic structures: orifices, weirs, and culverts.

Provides discharge calculations for common outlet structures used in
detention ponds, flow measurement, and road crossings.

References
----------
- FHWA HDS-5 (2012). Hydraulic Design of Highway Culverts.
- Brater, E.F. & King, H.W. (1976). Handbook of Hydraulics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

from hydroflow.materials import resolve_roughness
from hydroflow.units import from_si, to_si

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = [
    "Orifice",
    "RectangularWeir",
    "VNotchWeir",
    "BroadCrestedWeir",
    "CompositeOutlet",
    "Culvert",
    "CulvertResult",
]

_G = 9.80665


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ORIFICE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class Orifice:
    """Circular orifice outlet.

    Parameters
    ----------
    diameter : float
        Orifice diameter (length units).
    invert : float
        Invert elevation of orifice center (length units).  Default 0.
    Cd : float
        Discharge coefficient (default 0.61 for sharp-edged).

    Notes
    -----
    Q = Cd * A * sqrt(2 * g * H_eff)
    where H_eff = stage - invert - diameter/2  (head above centroid).

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> orif = hf.Orifice(diameter=0.3, invert=0.0, Cd=0.61)
    >>> f"{orif.discharge(stage=2.15):.3f}"
    '0.270'
    """

    def __init__(
        self, diameter: float, invert: float = 0.0, Cd: float = 0.61
    ) -> None:
        self._diameter_si = to_si(diameter, "length")
        self._invert_si = to_si(invert, "length")
        self._Cd = Cd
        self._area_si = math.pi * (self._diameter_si / 2.0) ** 2

    def discharge_si(self, stage_si: float) -> float:
        """Discharge in m³/s at a given stage (meters, SI)."""
        centroid = self._invert_si + self._diameter_si / 2.0
        H = stage_si - centroid
        if H <= 0:
            return 0.0
        return self._Cd * self._area_si * math.sqrt(2.0 * _G * H)

    def discharge(self, stage: float) -> float:
        """Discharge at a given stage (in active units)."""
        stage_si = to_si(stage, "length")
        return from_si(self.discharge_si(stage_si), "flow")

    def __add__(self, other: Orifice | RectangularWeir | VNotchWeir | BroadCrestedWeir | CompositeOutlet) -> CompositeOutlet:
        if isinstance(other, CompositeOutlet):
            return CompositeOutlet(self, *other._structures)
        return CompositeOutlet(self, other)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEIRS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class RectangularWeir:
    """Sharp-crested rectangular weir.

    Parameters
    ----------
    length : float
        Weir crest length (length units).
    crest : float
        Crest elevation (length units).
    Cw : float
        Weir coefficient (default 1.84 for SI).

    Notes
    -----
    Q = Cw * L * H^(3/2),  Cw = 1.84 SI (= 3.33 imperial).

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> weir = hf.RectangularWeir(length=3.0, crest=0.0, Cw=1.84)
    >>> f"{weir.discharge(stage=0.5):.3f}"
    '1.952'
    """

    def __init__(
        self, length: float, crest: float = 0.0, Cw: float = 1.84
    ) -> None:
        self._length_si = to_si(length, "length")
        self._crest_si = to_si(crest, "length")
        self._Cw = Cw

    def discharge_si(self, stage_si: float) -> float:
        """Discharge in m³/s at a given stage (meters, SI)."""
        H = stage_si - self._crest_si
        if H <= 0:
            return 0.0
        return float(self._Cw * self._length_si * H**1.5)

    def discharge(self, stage: float) -> float:
        """Discharge at a given stage (in active units)."""
        stage_si = to_si(stage, "length")
        return from_si(self.discharge_si(stage_si), "flow")

    def __add__(self, other: Orifice | RectangularWeir | VNotchWeir | BroadCrestedWeir | CompositeOutlet) -> CompositeOutlet:
        if isinstance(other, CompositeOutlet):
            return CompositeOutlet(self, *other._structures)
        return CompositeOutlet(self, other)


class VNotchWeir:
    """Sharp-crested V-notch (triangular) weir.

    Parameters
    ----------
    angle_degrees : float
        Notch angle in degrees (default 90).
    vertex : float
        Vertex elevation (length units).
    Cd : float
        Discharge coefficient (default 0.58).

    Notes
    -----
    Q = (8/15) * Cd * tan(θ/2) * sqrt(2g) * H^(5/2)

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> weir = hf.VNotchWeir(angle_degrees=90.0, vertex=0.0, Cd=0.58)
    >>> f"{weir.discharge(stage=0.3):.4f}"
    '0.0675'
    """

    def __init__(
        self, angle_degrees: float = 90.0, vertex: float = 0.0, Cd: float = 0.58
    ) -> None:
        self._angle_rad = math.radians(angle_degrees)
        self._vertex_si = to_si(vertex, "length")
        self._Cd = Cd
        self._coeff = (8.0 / 15.0) * Cd * math.tan(self._angle_rad / 2.0) * math.sqrt(2.0 * _G)

    def discharge_si(self, stage_si: float) -> float:
        """Discharge in m³/s at a given stage (meters, SI)."""
        H = stage_si - self._vertex_si
        if H <= 0:
            return 0.0
        return float(self._coeff * H**2.5)

    def discharge(self, stage: float) -> float:
        """Discharge at a given stage (in active units)."""
        stage_si = to_si(stage, "length")
        return from_si(self.discharge_si(stage_si), "flow")

    def __add__(self, other: Orifice | RectangularWeir | VNotchWeir | BroadCrestedWeir | CompositeOutlet) -> CompositeOutlet:
        if isinstance(other, CompositeOutlet):
            return CompositeOutlet(self, *other._structures)
        return CompositeOutlet(self, other)


class BroadCrestedWeir:
    """Broad-crested weir.

    Parameters
    ----------
    length : float
        Weir crest length (length units).
    crest : float
        Crest elevation (length units).
    Cw : float
        Weir coefficient (default 1.70 for SI).

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> weir = hf.BroadCrestedWeir(length=5.0, crest=0.0, Cw=1.70)
    >>> f"{weir.discharge(stage=1.0):.2f}"
    '8.50'
    """

    def __init__(
        self, length: float, crest: float = 0.0, Cw: float = 1.70
    ) -> None:
        self._length_si = to_si(length, "length")
        self._crest_si = to_si(crest, "length")
        self._Cw = Cw

    def discharge_si(self, stage_si: float) -> float:
        """Discharge in m³/s at a given stage (meters, SI)."""
        H = stage_si - self._crest_si
        if H <= 0:
            return 0.0
        return float(self._Cw * self._length_si * H**1.5)

    def discharge(self, stage: float) -> float:
        """Discharge at a given stage (in active units)."""
        stage_si = to_si(stage, "length")
        return from_si(self.discharge_si(stage_si), "flow")

    def __add__(self, other: Orifice | RectangularWeir | VNotchWeir | BroadCrestedWeir | CompositeOutlet) -> CompositeOutlet:
        if isinstance(other, CompositeOutlet):
            return CompositeOutlet(self, *other._structures)
        return CompositeOutlet(self, other)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPOSITE OUTLET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_Structure = Orifice | RectangularWeir | VNotchWeir | BroadCrestedWeir


class CompositeOutlet:
    """Sum of multiple outlet structures acting simultaneously.

    Created by adding structures together::

        outlet = Orifice(diameter=0.3) + RectangularWeir(length=3.0, crest=1.5)

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> outlet = hf.Orifice(diameter=0.3) + hf.RectangularWeir(length=3.0, crest=1.5)
    >>> outlet.discharge(stage=2.0) > 0
    True
    """

    def __init__(self, *structures: _Structure) -> None:
        self._structures: tuple[_Structure, ...] = structures

    def discharge_si(self, stage_si: float) -> float:
        """Total discharge in m³/s at a given stage (meters, SI)."""
        return sum(s.discharge_si(stage_si) for s in self._structures)

    def discharge(self, stage: float) -> float:
        """Total discharge at a given stage (in active units)."""
        stage_si = to_si(stage, "length")
        return from_si(self.discharge_si(stage_si), "flow")

    def stage_discharge_curve_si(
        self, stages_si: NDArray[np.floating]
    ) -> NDArray[np.floating]:
        """Compute discharge at an array of stages (all SI)."""
        return np.array([self.discharge_si(float(h)) for h in stages_si])

    def __add__(self, other: _Structure | CompositeOutlet) -> CompositeOutlet:
        if isinstance(other, CompositeOutlet):
            return CompositeOutlet(*self._structures, *other._structures)
        return CompositeOutlet(*self._structures, other)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CULVERT (FHWA HDS-5)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Inlet control coefficients: (K, M, c, Y, ke)
_INLET_COEFFICIENTS: dict[str, tuple[float, float, float, float, float]] = {
    "square_edge": (0.0098, 2.0, 0.0398, 0.67, 0.5),
    "groove_end": (0.0018, 2.0, 0.0292, 0.74, 0.2),
    "beveled": (0.0045, 2.0, 0.0317, 0.69, 0.25),
    "projecting": (0.0098, 2.0, 0.0398, 0.67, 0.9),
}


@dataclass(frozen=True)
class CulvertResult:
    """Result of a culvert analysis."""

    flow: float
    """Discharge (active flow units)."""

    headwater: float
    """Headwater depth above inlet invert (active length units)."""

    control: Literal["INLET_CONTROL", "OUTLET_CONTROL"]
    """Governing hydraulic control."""

    headwater_ratio: float
    """HW/D — headwater to diameter ratio."""

    velocity: float
    """Full-pipe velocity (active velocity units)."""

    hw_inlet: float
    """Inlet control headwater (active length units)."""

    hw_outlet: float
    """Outlet control headwater (active length units)."""


class Culvert:
    """Circular culvert analysis using FHWA HDS-5 methodology.

    Always computes both inlet and outlet control; reports the governing one.

    Parameters
    ----------
    diameter : float
        Culvert diameter (length units).
    length : float
        Culvert length (length units).
    slope : float
        Culvert slope (m/m, dimensionless).
    roughness : float or str
        Manning's n or material name.
    inlet : str
        Inlet type: ``"square_edge"``, ``"groove_end"``, ``"beveled"``,
        or ``"projecting"``.

    References
    ----------
    FHWA HDS-5 (2012), 3rd Edition. Hydraulic Design of Highway Culverts.

    Examples
    --------
    >>> import hydroflow as hf
    >>> hf.set_units("metric")
    >>> c = hf.Culvert(
    ...     diameter=0.9, length=30.0, slope=0.01,
    ...     roughness="concrete", inlet="square_edge",
    ... )
    >>> result = c.analyze(flow=1.0)
    >>> result.headwater > 0
    True
    >>> result.control in ("INLET_CONTROL", "OUTLET_CONTROL")
    True
    """

    def __init__(
        self,
        diameter: float,
        length: float,
        slope: float,
        roughness: float | str,
        inlet: str = "square_edge",
    ) -> None:
        self._D = to_si(diameter, "length")
        self._L = to_si(length, "length")
        self._S = float(slope)
        self._n = resolve_roughness(roughness)

        inlet_key = inlet.lower().strip()
        if inlet_key not in _INLET_COEFFICIENTS:
            valid = ", ".join(f"'{k}'" for k in _INLET_COEFFICIENTS)
            msg = f"Unknown inlet type '{inlet}'. Available: {valid}"
            raise ValueError(msg)
        self._inlet_key = inlet_key
        self._K, self._M, self._c, self._Y, self._ke = _INLET_COEFFICIENTS[inlet_key]

        # Pre-compute full-pipe properties
        self._r = self._D / 2.0
        self._A_full = math.pi * self._r**2
        self._R_full = self._D / 4.0

    def analyze(self, flow: float, tailwater: float = 0.0) -> CulvertResult:
        """Analyze culvert for a given discharge.

        Parameters
        ----------
        flow : float
            Design discharge (active flow units).
        tailwater : float
            Tailwater depth above outlet invert (active length units).
            Default 0 (free outfall).

        Returns
        -------
        CulvertResult
        """
        Q_si = to_si(flow, "flow")
        TW_si = to_si(tailwater, "length")

        V_full = Q_si / self._A_full
        D = self._D

        # ── Inlet control ─────────────────────────────────────────────
        # Discharge factor (dimensionless via consistent units)
        # Use imperial form for the regression constants (HDS-5 convention)
        D_ft = D / 0.3048
        A_ft = self._A_full / 0.3048**2
        Q_cfs = Q_si / 0.028316846592
        Qr = Q_cfs / (A_ft * D_ft**0.5)

        # Form 1 (unsubmerged) and Form 2 (submerged)
        HW_D_form1 = self._K * Qr**self._M - 0.5 * self._S
        HW_D_form2 = self._c * Qr**2 + self._Y - 0.5 * self._S

        # Use Form 1 below transition, Form 2 above, take max to be safe
        HW_D_ic = max(HW_D_form1, HW_D_form2)
        HW_inlet_si = HW_D_ic * D

        # ── Outlet control ────────────────────────────────────────────
        # kf = friction factor for full pipe (SI: 19.63 * n² * L / R^(4/3))
        kf = 19.63 * self._n**2 * self._L / self._R_full ** (4.0 / 3.0)
        hv = V_full**2 / (2.0 * _G)
        HW_outlet_si = max(TW_si + (1.0 + self._ke + kf) * hv - self._S * self._L, 0.0)

        # ── Governing condition ───────────────────────────────────────
        if HW_inlet_si >= HW_outlet_si:
            HW_si = HW_inlet_si
            control: Literal["INLET_CONTROL", "OUTLET_CONTROL"] = "INLET_CONTROL"
        else:
            HW_si = HW_outlet_si
            control = "OUTLET_CONTROL"

        return CulvertResult(
            flow=flow,
            headwater=from_si(HW_si, "length"),
            control=control,
            headwater_ratio=HW_si / D,
            velocity=from_si(V_full, "velocity"),
            hw_inlet=from_si(HW_inlet_si, "length"),
            hw_outlet=from_si(HW_outlet_si, "length"),
        )

    def performance_curve(
        self,
        flow_range: tuple[float, float],
        steps: int = 50,
        tailwater: float = 0.0,
    ) -> list[CulvertResult]:
        """Compute headwater for a range of flows.

        Parameters
        ----------
        flow_range : tuple
            (min_flow, max_flow) in active flow units.
        steps : int
            Number of points.
        tailwater : float
            Tailwater depth.

        Returns
        -------
        list[CulvertResult]
        """
        flows = np.linspace(flow_range[0], flow_range[1], steps)
        return [self.analyze(flow=float(q), tailwater=tailwater) for q in flows]
