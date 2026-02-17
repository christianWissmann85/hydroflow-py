"""HydroFlow — The Python library for water engineering.

From Excel to elegant code.
"""

from __future__ import annotations

# ── Foundation ────────────────────────────────────────────────────────
from hydroflow._types import FlowRegime, SectionProperties

# ── Layer 0: Channels ────────────────────────────────────────────────
from hydroflow.channels import (
    CircularChannel,
    RectangularChannel,
    TrapezoidalChannel,
    TriangularChannel,
)

# ── Geometry (advanced usage) ─────────────────────────────────────────
from hydroflow.geometry import circular, rectangular, trapezoidal, triangular

# ── Hydrology ────────────────────────────────────────────────────────
from hydroflow.hydrology import (
    DesignStorm,
    Hydrograph,
    Watershed,
    rational_method,
    scs_runoff_depth,
    scs_unit_hydrograph,
    time_of_concentration,
)
from hydroflow.materials import MANNING_ROUGHNESS, resolve_roughness

# ── Pressure pipe flow ──────────────────────────────────────────────
from hydroflow.pressure import (
    HAZEN_WILLIAMS_C,
    MINOR_LOSS_K,
    HydraulicJumpResult,
    PipeLossResult,
    darcy_weisbach,
    hazen_williams,
    hydraulic_jump,
    minor_loss,
)

# ── Routing ─────────────────────────────────────────────────────────
from hydroflow.routing import DetentionPond, RoutingResult

# ── Structures ──────────────────────────────────────────────────────
from hydroflow.structures import (
    BroadCrestedWeir,
    CompositeOutlet,
    Culvert,
    CulvertResult,
    Orifice,
    RectangularWeir,
    VNotchWeir,
)
from hydroflow.units import (
    acres,
    cfs,
    cms,
    from_si,
    ft,
    get_units,
    ha,
    inches,
    m,
    mm,
    set_units,
    to_si,
)

__all__ = [
    # Units
    "set_units",
    "get_units",
    "to_si",
    "from_si",
    "ft",
    "m",
    "cfs",
    "cms",
    "inches",
    "mm",
    "acres",
    "ha",
    # Types
    "FlowRegime",
    "SectionProperties",
    # Materials
    "resolve_roughness",
    "MANNING_ROUGHNESS",
    # Channels
    "TrapezoidalChannel",
    "RectangularChannel",
    "TriangularChannel",
    "CircularChannel",
    # Geometry
    "trapezoidal",
    "rectangular",
    "triangular",
    "circular",
    # Hydrology
    "scs_runoff_depth",
    "rational_method",
    "time_of_concentration",
    "Watershed",
    "DesignStorm",
    "Hydrograph",
    "scs_unit_hydrograph",
    # Structures
    "Orifice",
    "RectangularWeir",
    "VNotchWeir",
    "BroadCrestedWeir",
    "CompositeOutlet",
    "Culvert",
    "CulvertResult",
    # Routing
    "DetentionPond",
    "RoutingResult",
    # Pressure
    "darcy_weisbach",
    "hazen_williams",
    "minor_loss",
    "hydraulic_jump",
    "PipeLossResult",
    "HydraulicJumpResult",
    "MINOR_LOSS_K",
    "HAZEN_WILLIAMS_C",
]

__version__ = "0.1.0"
