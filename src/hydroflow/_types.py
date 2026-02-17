"""Shared types, enums, and dataclasses for hydroflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "FlowRegime",
    "SectionProperties",
]


class FlowRegime(Enum):
    """Classification of open-channel flow regime based on Froude number."""

    SUBCRITICAL = "subcritical"
    CRITICAL = "critical"
    SUPERCRITICAL = "supercritical"

    def __repr__(self) -> str:
        return f"FlowRegime.{self.name}"


@dataclass(frozen=True, slots=True)
class SectionProperties:
    """Hydraulic properties of a channel cross-section.

    All values are in SI (meters, m²) internally.
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
