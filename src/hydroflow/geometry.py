"""Channel cross-section geometry engine.

Computes area, wetted perimeter, hydraulic radius, top width, and
hydraulic depth for standard channel shapes.  All functions operate
in SI (meters).

Two APIs per shape:
    - :func:`trapezoidal` etc. → returns a :class:`SectionProperties` dataclass
    - :func:`_trap_apr` etc.   → returns a raw ``(A, P, R)`` tuple for
      tight optimization loops (zero object allocation)
"""

from __future__ import annotations

import math

from hydroflow._types import SectionProperties

__all__ = [
    "trapezoidal",
    "rectangular",
    "triangular",
    "circular",
]

# ── Guards ────────────────────────────────────────────────────────────

_DEPTH_FLOOR = 1e-12  # minimum depth to avoid division by zero


def _check_positive(name: str, value: float) -> None:
    if value <= 0:
        msg = f"{name} must be positive, got {value}"
        raise ValueError(msg)


def _check_non_negative(name: str, value: float) -> None:
    if value < 0:
        msg = f"{name} must be non-negative, got {value}"
        raise ValueError(msg)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRAPEZOIDAL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _trap_apr(y: float, b: float, z: float) -> tuple[float, float, float]:
    """(area, wetted_perimeter, hydraulic_radius) for a trapezoid — no allocation."""
    if y <= _DEPTH_FLOOR:
        return (0.0, 0.0, 0.0)
    area = (b + z * y) * y
    perimeter = b + 2.0 * y * math.sqrt(1.0 + z * z)
    return (area, perimeter, area / perimeter)


def trapezoidal(y: float, b: float, z: float) -> SectionProperties:
    """Hydraulic properties of a trapezoidal cross-section.

    Parameters
    ----------
    y : float
        Flow depth (m).
    b : float
        Bottom width (m).  Must be > 0.
    z : float
        Side slope as horizontal:vertical (dimensionless).  Must be >= 0.
        ``z = 0`` is a rectangular channel; ``z = 2`` means 2H:1V.

    Examples
    --------
    >>> from hydroflow.geometry import trapezoidal
    >>> props = trapezoidal(y=1.5, b=3.0, z=2.0)
    >>> f"{props.area:.1f}"
    '9.0'
    >>> f"{props.hydraulic_radius:.3f}"
    '0.927'
    """
    _check_positive("bottom_width", b)
    _check_non_negative("side_slope", z)
    _check_non_negative("depth", y)

    if y <= _DEPTH_FLOOR:
        return SectionProperties(0.0, 0.0, 0.0, b, 0.0)

    area = (b + z * y) * y
    perimeter = b + 2.0 * y * math.sqrt(1.0 + z * z)
    top_w = b + 2.0 * z * y
    return SectionProperties(
        area=area,
        wetted_perimeter=perimeter,
        hydraulic_radius=area / perimeter,
        top_width=top_w,
        hydraulic_depth=area / top_w,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RECTANGULAR  (special case of trapezoidal with z = 0)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _rect_apr(y: float, b: float) -> tuple[float, float, float]:
    """(area, wetted_perimeter, hydraulic_radius) for a rectangle — no allocation."""
    if y <= _DEPTH_FLOOR:
        return (0.0, 0.0, 0.0)
    area = b * y
    perimeter = b + 2.0 * y
    return (area, perimeter, area / perimeter)


def rectangular(y: float, b: float) -> SectionProperties:
    """Hydraulic properties of a rectangular cross-section.

    Parameters
    ----------
    y : float
        Flow depth (m).
    b : float
        Channel width (m).  Must be > 0.

    Examples
    --------
    >>> from hydroflow.geometry import rectangular
    >>> props = rectangular(y=2.0, b=5.0)
    >>> props.area
    10.0
    >>> f"{props.hydraulic_radius:.4f}"
    '1.1111'
    """
    _check_positive("width", b)
    _check_non_negative("depth", y)

    if y <= _DEPTH_FLOOR:
        return SectionProperties(0.0, 0.0, 0.0, b, 0.0)

    area = b * y
    perimeter = b + 2.0 * y
    return SectionProperties(
        area=area,
        wetted_perimeter=perimeter,
        hydraulic_radius=area / perimeter,
        top_width=b,
        hydraulic_depth=y,  # A/T = by/b = y for rectangular
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TRIANGULAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _tri_apr(y: float, z: float) -> tuple[float, float, float]:
    """(area, wetted_perimeter, hydraulic_radius) for a triangle — no allocation."""
    if y <= _DEPTH_FLOOR:
        return (0.0, 0.0, 0.0)
    area = z * y * y
    perimeter = 2.0 * y * math.sqrt(1.0 + z * z)
    return (area, perimeter, area / perimeter)


def triangular(y: float, z: float) -> SectionProperties:
    """Hydraulic properties of a triangular (V-shaped) cross-section.

    Parameters
    ----------
    y : float
        Flow depth (m).
    z : float
        Side slope as horizontal:vertical (dimensionless).  Must be > 0.

    Examples
    --------
    >>> from hydroflow.geometry import triangular
    >>> props = triangular(y=1.0, z=2.0)
    >>> props.area
    2.0
    >>> props.hydraulic_depth
    0.5
    """
    _check_positive("side_slope", z)
    _check_non_negative("depth", y)

    if y <= _DEPTH_FLOOR:
        return SectionProperties(0.0, 0.0, 0.0, 0.0, 0.0)

    area = z * y * y
    perimeter = 2.0 * y * math.sqrt(1.0 + z * z)
    top_w = 2.0 * z * y
    return SectionProperties(
        area=area,
        wetted_perimeter=perimeter,
        hydraulic_radius=area / perimeter,
        top_width=top_w,
        hydraulic_depth=area / top_w,  # = y/2
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CIRCULAR  (partially full pipe, using central half-angle θ)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#   θ = arccos(1 - 2y/D)
#   A = r²(θ - sinθ·cosθ)
#   P = 2rθ
#   T = 2r·sinθ
#
# Special: y = D (full pipe) → θ = π, T = 0 → use full-pipe formulas.
# Max Q occurs at y/D ≈ 0.938 (θ ≈ 2.748 rad), NOT at full pipe.


def _circ_theta(y: float, diameter: float) -> float:
    """Central half-angle θ from depth and diameter."""
    r = diameter / 2.0
    cos_theta = 1.0 - y / r
    # Clamp for numerical safety
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.acos(cos_theta)


def _circ_apr(y: float, diameter: float) -> tuple[float, float, float]:
    """(area, wetted_perimeter, hydraulic_radius) for a circle — no allocation."""
    if y <= _DEPTH_FLOOR:
        return (0.0, 0.0, 0.0)

    r = diameter / 2.0

    # Full pipe: θ = π, avoid sin(π) ≈ 0 issues
    if y >= diameter - _DEPTH_FLOOR:
        area = math.pi * r * r
        perimeter = 2.0 * math.pi * r
        return (area, perimeter, area / perimeter)  # R = D/4

    theta = _circ_theta(y, diameter)
    area = r * r * (theta - math.sin(theta) * math.cos(theta))
    perimeter = 2.0 * r * theta
    if perimeter <= _DEPTH_FLOOR:
        return (0.0, 0.0, 0.0)
    return (area, perimeter, area / perimeter)


def circular(y: float, diameter: float) -> SectionProperties:
    """Hydraulic properties of a circular cross-section (partially full pipe).

    Parameters
    ----------
    y : float
        Flow depth (m).  Must be in ``[0, diameter]``.
    diameter : float
        Pipe diameter (m).  Must be > 0.

    Raises
    ------
    ValueError
        If depth exceeds diameter (surcharge condition).

    Examples
    --------
    >>> from hydroflow.geometry import circular
    >>> props = circular(y=0.5, diameter=1.0)  # half-full 1m pipe
    >>> f"{props.area:.4f}"
    '0.3927'
    >>> f"{props.hydraulic_radius:.4f}"
    '0.2500'
    """
    _check_positive("diameter", diameter)
    _check_non_negative("depth", y)

    if y > diameter + _DEPTH_FLOOR:
        msg = (
            f"Depth {y:.4f} m exceeds pipe diameter {diameter:.4f} m. "
            "This indicates a surcharge condition."
        )
        raise ValueError(msg)

    if y <= _DEPTH_FLOOR:
        return SectionProperties(0.0, 0.0, 0.0, 0.0, 0.0)

    r = diameter / 2.0

    # Full pipe
    if y >= diameter - _DEPTH_FLOOR:
        area = math.pi * r * r
        perimeter = 2.0 * math.pi * r
        return SectionProperties(
            area=area,
            wetted_perimeter=perimeter,
            hydraulic_radius=area / perimeter,
            top_width=0.0,
            hydraulic_depth=diameter / 4.0,  # conventional: D_h = D/4 at full
        )

    theta = _circ_theta(y, diameter)
    area = r * r * (theta - math.sin(theta) * math.cos(theta))
    perimeter = 2.0 * r * theta
    top_w = 2.0 * r * math.sin(theta)

    return SectionProperties(
        area=area,
        wetted_perimeter=perimeter,
        hydraulic_radius=area / perimeter,
        top_width=top_w,
        hydraulic_depth=area / top_w if top_w > _DEPTH_FLOOR else 0.0,
    )
