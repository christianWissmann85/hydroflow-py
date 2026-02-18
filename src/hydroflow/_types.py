"""Shared types, enums, and dataclasses for hydroflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "FlowRegime",
    "FittingProperties",
    "MaterialProperties",
    "SectionProperties",
]


class FlowRegime(Enum):
    """Classification of open-channel flow regime based on Froude number.

    Examples
    --------
    >>> from hydroflow._types import FlowRegime
    >>> FlowRegime.SUBCRITICAL.value
    'subcritical'
    """

    SUBCRITICAL = "subcritical"
    CRITICAL = "critical"
    SUPERCRITICAL = "supercritical"

    def __repr__(self) -> str:
        return f"FlowRegime.{self.name}"


@dataclass(frozen=True, slots=True)
class SectionProperties:
    """Hydraulic properties of a channel cross-section.

    All values are in SI (meters, m^2) internally.

    Examples
    --------
    >>> from hydroflow.geometry import rectangular
    >>> props = rectangular(y=2.0, b=5.0)
    >>> props.area
    10.0
    """

    area: float
    """Flow area (m²)."""

    wetted_perimeter: float
    """Wetted perimeter (m)."""

    hydraulic_radius: float
    """Hydraulic radius = area / wetted_perimeter (m)."""

    top_width: float
    """Free-surface width (m)."""

    hydraulic_depth: float
    """Hydraulic depth = area / top_width (m)."""


@dataclass(frozen=True, slots=True)
class MaterialProperties:
    """Properties of a pipe or channel material.

    Examples
    --------
    >>> from hydroflow.materials import get_material
    >>> mat = get_material("concrete")
    >>> mat.manning_n
    0.013
    """

    name: str
    """Material key (e.g. ``'concrete'``)."""

    category: str
    """Material category (e.g. ``'closed_conduit'``)."""

    description: str
    """Human-readable description."""

    manning_n: float
    """Manning's *n* roughness coefficient."""

    manning_n_range: tuple[float, float] | None = None
    """(min, max) range for Manning's *n*, if available."""

    hazen_williams_c: float | None = None
    """Hazen-Williams *C* coefficient (closed conduits only)."""

    hazen_williams_c_range: tuple[float, float] | None = None
    """(min, max) range for Hazen-Williams *C*, if available."""

    darcy_epsilon_mm: float | None = None
    """Darcy-Weisbach absolute roughness in mm."""

    darcy_epsilon_mm_range: tuple[float, float] | None = None
    """(min, max) range for Darcy-Weisbach roughness, if available."""

    condition: str | None = None
    """Active condition name (e.g. ``'new_smooth'``), or ``None`` for default."""


@dataclass(frozen=True, slots=True)
class FittingProperties:
    """Properties of a pipe fitting for minor loss calculations.

    Examples
    --------
    >>> from hydroflow.materials import get_fitting
    >>> fit = get_fitting("90_elbow")
    >>> fit.K
    0.9
    """

    name: str
    """Fitting key (e.g. ``'90_elbow'``)."""

    category: str
    """Fitting category (e.g. ``'elbow'``)."""

    description: str
    """Human-readable description."""

    K: float
    """Minor loss coefficient *K* (dimensionless)."""

    K_range: tuple[float, float] | None = None
    """(min, max) range for *K*, if available."""
