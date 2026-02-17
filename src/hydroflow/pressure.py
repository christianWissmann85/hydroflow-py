"""Pressurized pipe flow: Darcy-Weisbach, Hazen-Williams, minor losses.

Provides head loss calculations for closed-conduit water systems —
water distribution, pump station design, force mains.

References
----------
- Colebrook, C.F. (1939). Turbulent flow in pipes.
- Swamee, P.K. & Jain, A.K. (1976). Explicit equations for pipe-flow problems.
- Brater, E.F. & King, H.W. (1976). Handbook of Hydraulics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from hydroflow.units import from_si, to_si

__all__ = [
    "darcy_weisbach",
    "friction_factor",
    "hazen_williams",
    "minor_loss",
    "hydraulic_jump",
    "MINOR_LOSS_K",
]

_G = 9.80665

# ── Minor loss coefficients (standard values) ───────────────────────
MINOR_LOSS_K: dict[str, float] = {
    "entrance_sharp": 0.5,
    "entrance_rounded": 0.2,
    "entrance_projecting": 0.8,
    "exit": 1.0,
    "90_elbow": 0.9,
    "90_elbow_long": 0.6,
    "45_elbow": 0.4,
    "tee_through": 0.6,
    "tee_branch": 1.8,
    "gate_valve_open": 0.2,
    "gate_valve_half": 5.6,
    "check_valve": 2.5,
    "butterfly_valve": 0.3,
    "sudden_expansion": 1.0,
    "sudden_contraction": 0.5,
}

# ── Hazen-Williams C values for common materials ────────────────────
HAZEN_WILLIAMS_C: dict[str, float] = {
    "pvc": 150.0,
    "hdpe": 150.0,
    "copper": 140.0,
    "ductile_iron_new": 140.0,
    "ductile_iron_old": 100.0,
    "cast_iron_new": 130.0,
    "cast_iron_old": 80.0,
    "steel_new": 140.0,
    "steel_riveted": 110.0,
    "concrete": 130.0,
    "asbestos_cement": 140.0,
    "galvanized_iron": 120.0,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FRICTION FACTOR (COLEBROOK-WHITE / SWAMEE-JAIN)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def friction_factor(
    reynolds: float,
    roughness: float,
    diameter: float,
) -> float:
    """Darcy friction factor via Colebrook-White iteration.

    Parameters
    ----------
    reynolds : float
        Reynolds number (dimensionless).
    roughness : float
        Absolute pipe roughness (same length units as diameter).
    diameter : float
        Pipe diameter (same length units as roughness).

    Returns
    -------
    float
        Darcy friction factor *f*.

    Notes
    -----
    Uses Swamee-Jain (1976) as initial guess, then 3 iterations of
    Colebrook-White for precision (error < 0.01%).
    """
    Re = reynolds
    if Re <= 0:
        msg = f"Reynolds number must be positive, got {Re}"
        raise ValueError(msg)

    # Laminar flow
    if Re < 2300:
        return 64.0 / Re

    eps_D = roughness / diameter

    # Swamee-Jain explicit approximation (initial guess)
    term = eps_D / 3.7 + 5.74 / Re**0.9
    f = 0.25 / (math.log10(term)) ** 2

    # Colebrook-White iterations
    for _ in range(3):
        rhs = -2.0 * math.log10(eps_D / 3.7 + 2.51 / (Re * math.sqrt(f)))
        f = 1.0 / rhs**2

    return f


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DARCY-WEISBACH HEAD LOSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True)
class PipeLossResult:
    """Result of a pipe head loss calculation."""

    head_loss: float
    """Friction head loss (active length units)."""

    velocity: float
    """Flow velocity (active velocity units)."""

    friction_factor_value: float
    """Darcy friction factor (dimensionless)."""

    reynolds: float
    """Reynolds number (dimensionless)."""


def darcy_weisbach(
    flow: float,
    diameter: float,
    length: float,
    roughness_mm: float = 0.045,
    *,
    kinematic_viscosity: float = 1.004e-6,
) -> PipeLossResult:
    """Compute friction head loss using Darcy-Weisbach equation.

    Parameters
    ----------
    flow : float
        Discharge (active flow units).
    diameter : float
        Pipe diameter (active length units).
    length : float
        Pipe length (active length units).
    roughness_mm : float
        Absolute pipe roughness in **millimeters** (default 0.045 mm
        for commercial steel). This is always in mm regardless of unit system.
    kinematic_viscosity : float
        Kinematic viscosity in m^2/s (default 1.004e-6 for water at 20 C).

    Returns
    -------
    PipeLossResult
    """
    Q_si = to_si(flow, "flow")
    D_si = to_si(diameter, "length")
    L_si = to_si(length, "length")
    eps_si = roughness_mm * 1e-3  # mm to m

    A = math.pi * (D_si / 2.0) ** 2
    V = Q_si / A
    Re = V * D_si / kinematic_viscosity

    f = friction_factor(Re, eps_si, D_si)
    hf = f * (L_si / D_si) * (V**2 / (2.0 * _G))

    return PipeLossResult(
        head_loss=from_si(hf, "length"),
        velocity=from_si(V, "velocity"),
        friction_factor_value=f,
        reynolds=Re,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HAZEN-WILLIAMS HEAD LOSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def hazen_williams(
    flow: float,
    diameter: float,
    length: float,
    C: float | str = 130.0,
) -> float:
    """Compute friction head loss using Hazen-Williams equation.

    Parameters
    ----------
    flow : float
        Discharge (active flow units).
    diameter : float
        Pipe diameter (active length units).
    length : float
        Pipe length (active length units).
    C : float or str
        Hazen-Williams coefficient. If a string, looked up from
        ``HAZEN_WILLIAMS_C`` (e.g. ``"pvc"`` -> 150).

    Returns
    -------
    float
        Head loss (active length units).

    Notes
    -----
    SI form: h_f = 10.67 * Q^1.852 * L / (C^1.852 * D^4.87)
    """
    Q_si = to_si(flow, "flow")
    D_si = to_si(diameter, "length")
    L_si = to_si(length, "length")

    if isinstance(C, str):
        key = C.lower().strip()
        if key not in HAZEN_WILLIAMS_C:
            valid = ", ".join(f"'{k}'" for k in HAZEN_WILLIAMS_C)
            msg = f"Unknown material '{C}'. Available: {valid}"
            raise ValueError(msg)
        C_val = HAZEN_WILLIAMS_C[key]
    else:
        C_val = C

    hf = float(
        10.67 * Q_si**1.852 * L_si / (C_val**1.852 * D_si**4.87)
    )
    return from_si(hf, "length")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MINOR LOSSES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def minor_loss(
    velocity: float,
    K: float | str,
) -> float:
    """Compute minor (local) head loss: h_m = K * V^2 / (2g).

    Parameters
    ----------
    velocity : float
        Flow velocity (active velocity units).
    K : float or str
        Loss coefficient. If a string, looked up from ``MINOR_LOSS_K``
        (e.g. ``"90_elbow"`` -> 0.9).

    Returns
    -------
    float
        Head loss (active length units).
    """
    V_si = to_si(velocity, "velocity")

    if isinstance(K, str):
        key = K.lower().strip()
        if key not in MINOR_LOSS_K:
            valid = ", ".join(f"'{k}'" for k in MINOR_LOSS_K)
            msg = f"Unknown fitting '{K}'. Available: {valid}"
            raise ValueError(msg)
        K_val = MINOR_LOSS_K[key]
    else:
        K_val = K

    hm = K_val * V_si**2 / (2.0 * _G)
    return from_si(hm, "length")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HYDRAULIC JUMP (RECTANGULAR CHANNELS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass(frozen=True)
class HydraulicJumpResult:
    """Result of a hydraulic jump calculation."""

    sequent_depth: float
    """Downstream (subcritical) depth (active length units)."""

    energy_loss: float
    """Energy dissipated in the jump (active length units)."""

    froude_upstream: float
    """Upstream Froude number (dimensionless)."""

    froude_downstream: float
    """Downstream Froude number (dimensionless)."""


def hydraulic_jump(
    flow: float,
    upstream_depth: float,
    width: float,
) -> HydraulicJumpResult:
    """Compute sequent depth and energy loss for a hydraulic jump.

    Uses the Belanger equation for rectangular channels.

    Parameters
    ----------
    flow : float
        Discharge (active flow units).
    upstream_depth : float
        Supercritical upstream depth (active length units).
    width : float
        Channel width (active length units).

    Returns
    -------
    HydraulicJumpResult

    References
    ----------
    Belanger, J.B. (1828). Essai sur la solution numerique.
    """
    Q_si = to_si(flow, "flow")
    y1 = to_si(upstream_depth, "length")
    b = to_si(width, "length")

    V1 = Q_si / (b * y1)
    Fr1 = V1 / math.sqrt(_G * y1)

    if Fr1 < 1.0:
        msg = f"Upstream flow must be supercritical (Fr > 1), got Fr = {Fr1:.3f}"
        raise ValueError(msg)

    # Belanger equation: y2/y1 = 0.5 * (sqrt(1 + 8*Fr1^2) - 1)
    y2 = y1 * 0.5 * (math.sqrt(1.0 + 8.0 * Fr1**2) - 1.0)

    # Energy loss: dE = (y2 - y1)^3 / (4*y1*y2)
    dE = (y2 - y1) ** 3 / (4.0 * y1 * y2)

    # Downstream Froude
    V2 = Q_si / (b * y2)
    Fr2 = V2 / math.sqrt(_G * y2)

    return HydraulicJumpResult(
        sequent_depth=from_si(y2, "length"),
        energy_loss=from_si(dE, "length"),
        froude_upstream=Fr1,
        froude_downstream=Fr2,
    )
