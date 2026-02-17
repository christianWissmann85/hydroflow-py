"""Open-channel flow calculations using Manning's equation.

Provides channel classes for trapezoidal, rectangular, triangular, and
circular cross-sections.  Each class computes normal depth, normal flow,
critical depth, and Froude number.

All internal math uses SI units.  User-facing methods accept and return
values in the active unit system (see :func:`hydroflow.units.set_units`).

References
----------
Chow, V.T. (1959). *Open-Channel Hydraulics*. McGraw-Hill.
"""

from __future__ import annotations

import math

from scipy.optimize import brentq

from hydroflow._types import FlowRegime, SectionProperties
from hydroflow.geometry import (
    _circ_apr,
    _rect_apr,
    _trap_apr,
    _tri_apr,
)
from hydroflow.geometry import (
    circular as _circ_props,
)
from hydroflow.geometry import (
    rectangular as _rect_props,
)
from hydroflow.geometry import (
    trapezoidal as _trap_props,
)
from hydroflow.geometry import (
    triangular as _tri_props,
)
from hydroflow.materials import resolve_roughness
from hydroflow.units import from_si, to_si

__all__ = [
    "TrapezoidalChannel",
    "RectangularChannel",
    "TriangularChannel",
    "CircularChannel",
]

# ── Constants ─────────────────────────────────────────────────────────

_G = 9.80665  # gravitational acceleration (m/s²)
_BRENT_XTOL = 1e-9
_BRENT_MAXITER = 100
_CRITICAL_TOL = 0.01  # |Fr - 1| threshold for "critical" classification


# ── Kernel function (pure SI, zero overhead) ──────────────────────────


def _manning_flow(n: float, area: float, R: float, S: float) -> float:
    """Manning's Q in m³/s.  All inputs SI.  No unit logic."""
    if area <= 0 or R <= 0:
        return 0.0
    return float((1.0 / n) * area * R ** (2.0 / 3.0) * S**0.5)


def _froude(Q: float, area: float, top_width: float) -> float:
    """Froude number.  All inputs SI."""
    if area <= 0 or top_width <= 0:
        return 0.0
    D_h = area / top_width
    return Q / (area * math.sqrt(_G * D_h))


def _classify_flow(fr: float) -> FlowRegime:
    if abs(fr - 1.0) < _CRITICAL_TOL:
        return FlowRegime.CRITICAL
    return FlowRegime.SUBCRITICAL if fr < 1.0 else FlowRegime.SUPERCRITICAL


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BASE MIXIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class _ChannelBase:
    """Shared logic for all channel types."""

    _n: float
    _S: float

    def _geometry_apr(self, y: float) -> tuple[float, float, float]:
        """(area, perimeter, R) at depth y — override per shape."""
        raise NotImplementedError

    def _geometry_props(self, y: float) -> SectionProperties:
        """Full properties at depth y — override per shape."""
        raise NotImplementedError

    def _find_normal_depth(self, Q_si: float, y_max: float = 100.0) -> float:
        """Brent's method solve for normal depth in SI."""

        def residual(y: float) -> float:
            A, _P, R = self._geometry_apr(y)
            return _manning_flow(self._n, A, R, self._S) - Q_si

        # Find upper bracket
        y_hi = min(1.0, y_max)
        while residual(y_hi) < 0:
            y_hi *= 2.0
            if y_hi > y_max:
                msg = (
                    f"Cannot find normal depth: flow {Q_si:.4f} m³/s exceeds "
                    f"channel capacity at depth {y_max:.1f} m."
                )
                raise ValueError(msg)

        return float(brentq(residual, 1e-9, y_hi, xtol=_BRENT_XTOL, maxiter=_BRENT_MAXITER))

    def _find_critical_depth(
        self,
        Q_si: float,
        y_max: float = 100.0,
    ) -> float:
        """Brent's method solve for critical depth (Fr=1) in SI."""

        def residual(y: float) -> float:
            props = self._geometry_props(y)
            if props.area <= 0 or props.top_width <= 0:
                return 1e12  # large positive at near-zero depth
            return Q_si**2 * props.top_width / (_G * props.area**3) - 1.0

        y_hi = min(1.0, y_max)
        while residual(y_hi) > 0:
            y_hi *= 2.0
            if y_hi > y_max:
                msg = f"Cannot bracket critical depth within {y_max:.1f} m."
                raise ValueError(msg)

        return float(brentq(residual, 1e-9, y_hi, xtol=_BRENT_XTOL, maxiter=_BRENT_MAXITER))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRAPEZOIDAL CHANNEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TrapezoidalChannel(_ChannelBase):
    """Trapezoidal open channel using Manning's equation.

    Parameters
    ----------
    bottom_width : float
        Channel bottom width (length units).
    side_slope : float
        Horizontal:vertical ratio (dimensionless).  ``z=2`` means 2H:1V.
    slope : float
        Longitudinal bed slope (m/m, dimensionless).
    roughness : float or str
        Manning's n coefficient, or a material name (e.g. ``"concrete"``).

    Examples
    --------
    >>> import hydroflow as hf
    >>> ch = hf.TrapezoidalChannel(
    ...     bottom_width=3.0, side_slope=2.0, slope=0.001, roughness="concrete"
    ... )
    >>> ch.normal_flow(depth=1.5)  # m³/s
    5.71...
    """

    def __init__(
        self,
        bottom_width: float,
        side_slope: float,
        slope: float,
        roughness: float | str,
    ) -> None:
        self._b = to_si(bottom_width, "length")
        self._z = float(side_slope)
        self._S = float(slope)
        self._n = resolve_roughness(roughness)

        if self._b <= 0:
            msg = f"bottom_width must be positive, got {bottom_width}"
            raise ValueError(msg)
        if self._z < 0:
            msg = f"side_slope must be non-negative, got {side_slope}"
            raise ValueError(msg)
        if self._S <= 0:
            msg = f"slope must be positive, got {slope}"
            raise ValueError(msg)

    def _geometry_apr(self, y: float) -> tuple[float, float, float]:
        return _trap_apr(y, self._b, self._z)

    def _geometry_props(self, y: float) -> SectionProperties:
        return _trap_props(y, self._b, self._z)

    def normal_flow(self, depth: float) -> float:
        """Compute discharge Q at a given depth via Manning's equation.

        Returns flow in the active unit system.
        """
        y = to_si(depth, "length")
        A, _P, R = _trap_apr(y, self._b, self._z)
        return from_si(_manning_flow(self._n, A, R, self._S), "flow")

    def normal_depth(self, flow: float) -> float:
        """Iteratively solve for normal depth at a given discharge.

        Returns depth in the active unit system.
        """
        Q_si = to_si(flow, "flow")
        y_si = self._find_normal_depth(Q_si)
        return from_si(y_si, "length")

    def critical_depth(self, flow: float) -> float:
        """Solve for critical depth (Fr = 1) at a given discharge.

        Returns depth in the active unit system.
        """
        Q_si = to_si(flow, "flow")
        yc = self._find_critical_depth(Q_si)
        return from_si(yc, "length")

    def froude_number(self, depth: float) -> float:
        """Froude number at given depth (dimensionless)."""
        y = to_si(depth, "length")
        A, _P, R = _trap_apr(y, self._b, self._z)
        Q_si = _manning_flow(self._n, A, R, self._S)
        T = self._b + 2.0 * self._z * y
        return _froude(Q_si, A, T)

    def flow_regime(self, depth: float) -> FlowRegime:
        """Classify flow regime at given depth."""
        return _classify_flow(self.froude_number(depth))

    @property
    def si_params(self) -> tuple[float, float, float, float]:
        """``(b_m, z, S, n)`` in SI — for optimization loops."""
        return self._b, self._z, self._S, self._n


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RECTANGULAR CHANNEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class RectangularChannel(_ChannelBase):
    """Rectangular open channel using Manning's equation.

    Parameters
    ----------
    width : float
        Channel width (length units).
    slope : float
        Longitudinal bed slope (m/m, dimensionless).
    roughness : float or str
        Manning's n coefficient, or a material name.
    """

    def __init__(
        self,
        width: float,
        slope: float,
        roughness: float | str,
    ) -> None:
        self._b = to_si(width, "length")
        self._S = float(slope)
        self._n = resolve_roughness(roughness)

        if self._b <= 0:
            msg = f"width must be positive, got {width}"
            raise ValueError(msg)
        if self._S <= 0:
            msg = f"slope must be positive, got {slope}"
            raise ValueError(msg)

    def _geometry_apr(self, y: float) -> tuple[float, float, float]:
        return _rect_apr(y, self._b)

    def _geometry_props(self, y: float) -> SectionProperties:
        return _rect_props(y, self._b)

    def normal_flow(self, depth: float) -> float:
        """Compute discharge Q at a given depth via Manning's equation."""
        y = to_si(depth, "length")
        A, _P, R = _rect_apr(y, self._b)
        return from_si(_manning_flow(self._n, A, R, self._S), "flow")

    def normal_depth(self, flow: float) -> float:
        """Iteratively solve for normal depth at a given discharge."""
        Q_si = to_si(flow, "flow")
        y_si = self._find_normal_depth(Q_si)
        return from_si(y_si, "length")

    def critical_depth(self, flow: float) -> float:
        """Solve for critical depth (Fr = 1).

        Uses the closed-form solution: ``y_c = (Q² / (g·b²))^(1/3)``.
        """
        Q_si = to_si(flow, "flow")
        yc = (Q_si**2 / (_G * self._b**2)) ** (1.0 / 3.0)
        return from_si(yc, "length")

    def froude_number(self, depth: float) -> float:
        """Froude number at given depth (dimensionless)."""
        y = to_si(depth, "length")
        A, _P, R = _rect_apr(y, self._b)
        Q_si = _manning_flow(self._n, A, R, self._S)
        return _froude(Q_si, A, self._b)

    def flow_regime(self, depth: float) -> FlowRegime:
        """Classify flow regime at given depth."""
        return _classify_flow(self.froude_number(depth))

    @property
    def si_params(self) -> tuple[float, float, float]:
        """``(b_m, S, n)`` in SI — for optimization loops."""
        return self._b, self._S, self._n


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRIANGULAR CHANNEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TriangularChannel(_ChannelBase):
    """Triangular (V-shaped) open channel using Manning's equation.

    Parameters
    ----------
    side_slope : float
        Horizontal:vertical ratio (dimensionless).  Must be > 0.
    slope : float
        Longitudinal bed slope (m/m, dimensionless).
    roughness : float or str
        Manning's n coefficient, or a material name.
    """

    def __init__(
        self,
        side_slope: float,
        slope: float,
        roughness: float | str,
    ) -> None:
        self._z = float(side_slope)
        self._S = float(slope)
        self._n = resolve_roughness(roughness)

        if self._z <= 0:
            msg = f"side_slope must be positive, got {side_slope}"
            raise ValueError(msg)
        if self._S <= 0:
            msg = f"slope must be positive, got {slope}"
            raise ValueError(msg)

    def _geometry_apr(self, y: float) -> tuple[float, float, float]:
        return _tri_apr(y, self._z)

    def _geometry_props(self, y: float) -> SectionProperties:
        return _tri_props(y, self._z)

    def normal_flow(self, depth: float) -> float:
        """Compute discharge Q at a given depth via Manning's equation."""
        y = to_si(depth, "length")
        A, _P, R = _tri_apr(y, self._z)
        return from_si(_manning_flow(self._n, A, R, self._S), "flow")

    def normal_depth(self, flow: float) -> float:
        """Iteratively solve for normal depth at a given discharge."""
        Q_si = to_si(flow, "flow")
        y_si = self._find_normal_depth(Q_si)
        return from_si(y_si, "length")

    def critical_depth(self, flow: float) -> float:
        """Solve for critical depth (Fr = 1).

        Uses the closed-form solution: ``y_c = (2·Q² / (g·z²))^(1/5)``.
        """
        Q_si = to_si(flow, "flow")
        yc = (2.0 * Q_si**2 / (_G * self._z**2)) ** 0.2
        return from_si(yc, "length")

    def froude_number(self, depth: float) -> float:
        """Froude number at given depth (dimensionless)."""
        y = to_si(depth, "length")
        A, _P, R = _tri_apr(y, self._z)
        Q_si = _manning_flow(self._n, A, R, self._S)
        T = 2.0 * self._z * y
        return _froude(Q_si, A, T)

    def flow_regime(self, depth: float) -> FlowRegime:
        """Classify flow regime at given depth."""
        return _classify_flow(self.froude_number(depth))

    @property
    def si_params(self) -> tuple[float, float, float]:
        """``(z, S, n)`` in SI — for optimization loops."""
        return self._z, self._S, self._n


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CIRCULAR CHANNEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class CircularChannel(_ChannelBase):
    """Partially-full circular pipe using Manning's equation.

    Parameters
    ----------
    diameter : float
        Pipe diameter (length units).
    slope : float
        Pipe slope (m/m, dimensionless).
    roughness : float or str
        Manning's n coefficient, or a material name.
    """

    def __init__(
        self,
        diameter: float,
        slope: float,
        roughness: float | str,
    ) -> None:
        self._D = to_si(diameter, "length")
        self._S = float(slope)
        self._n = resolve_roughness(roughness)

        if self._D <= 0:
            msg = f"diameter must be positive, got {diameter}"
            raise ValueError(msg)
        if self._S <= 0:
            msg = f"slope must be positive, got {slope}"
            raise ValueError(msg)

    def _geometry_apr(self, y: float) -> tuple[float, float, float]:
        return _circ_apr(y, self._D)

    def _geometry_props(self, y: float) -> SectionProperties:
        return _circ_props(y, self._D)

    def full_flow_capacity(self) -> float:
        """Maximum discharge at full-pipe flow (y = D).

        Note: actual maximum capacity occurs at y/D ≈ 0.938.
        Use :meth:`max_flow_capacity` for the true maximum.

        Returns flow in the active unit system.
        """
        r = self._D / 2.0
        A = math.pi * r * r
        R = self._D / 4.0  # R = D/4 at full flow
        return from_si(_manning_flow(self._n, A, R, self._S), "flow")

    def max_flow_capacity(self) -> float:
        """True maximum discharge (at y/D ≈ 0.938).

        Returns flow in the active unit system.
        """
        # θ ≈ 2.748 rad gives max Q for circular pipe
        theta_max = 2.748
        r = self._D / 2.0
        A = r * r * (theta_max - math.sin(theta_max) * math.cos(theta_max))
        P = 2.0 * r * theta_max
        R = A / P
        return from_si(_manning_flow(self._n, A, R, self._S), "flow")

    def normal_flow(self, depth: float) -> float:
        """Compute discharge Q at a given depth via Manning's equation."""
        y = to_si(depth, "length")
        if y > self._D:
            msg = (
                f"Depth {depth} exceeds pipe diameter. "
                "This indicates a surcharge condition."
            )
            raise ValueError(msg)
        A, _P, R = _circ_apr(y, self._D)
        return from_si(_manning_flow(self._n, A, R, self._S), "flow")

    def normal_depth(self, flow: float) -> float:
        """Iteratively solve for normal depth at a given discharge.

        Solves in θ-space for numerical stability.
        """
        Q_si = to_si(flow, "flow")
        r = self._D / 2.0

        # Check if Q exceeds max pipe capacity
        Q_max_si = to_si(self.max_flow_capacity(), "flow")
        if Q_si > Q_max_si * 1.001:
            msg = (
                f"Flow {flow} exceeds pipe maximum capacity "
                f"({from_si(Q_max_si, 'flow'):.4f}). "
                "The pipe is surcharged."
            )
            raise ValueError(msg)

        def residual(theta: float) -> float:
            if theta <= 0:
                return -Q_si
            A = r * r * (theta - math.sin(theta) * math.cos(theta))
            P = 2.0 * r * theta
            R = A / P
            return _manning_flow(self._n, A, R, self._S) - Q_si

        theta_sol = float(
            brentq(residual, 1e-9, math.pi - 1e-9, xtol=_BRENT_XTOL, maxiter=_BRENT_MAXITER)
        )
        y_si = r * (1.0 - math.cos(theta_sol))
        return from_si(y_si, "length")

    def critical_depth(self, flow: float) -> float:
        """Solve for critical depth (Fr = 1).

        Uses iterative solve in θ-space.
        """
        Q_si = to_si(flow, "flow")
        r = self._D / 2.0

        def residual(theta: float) -> float:
            A = r * r * (theta - math.sin(theta) * math.cos(theta))
            T = 2.0 * r * math.sin(theta)
            if A <= 0 or T <= 0:
                return 1e12
            return Q_si**2 * T / (_G * A**3) - 1.0

        theta_sol = float(
            brentq(residual, 1e-6, math.pi - 1e-6, xtol=_BRENT_XTOL, maxiter=_BRENT_MAXITER)
        )
        y_si = r * (1.0 - math.cos(theta_sol))
        return from_si(y_si, "length")

    def froude_number(self, depth: float) -> float:
        """Froude number at given depth (dimensionless)."""
        y = to_si(depth, "length")
        props = _circ_props(y, self._D)
        A, _P, R = _circ_apr(y, self._D)
        Q_si = _manning_flow(self._n, A, R, self._S)
        return _froude(Q_si, props.area, props.top_width)

    def flow_regime(self, depth: float) -> FlowRegime:
        """Classify flow regime at given depth."""
        return _classify_flow(self.froude_number(depth))

    @property
    def si_params(self) -> tuple[float, float, float]:
        """``(D_m, S, n)`` in SI — for optimization loops."""
        return self._D, self._S, self._n
