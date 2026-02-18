"""HydroFlow — The Python library for water engineering.

From Excel to elegant code.
"""

from __future__ import annotations

from typing import Any

# ── Foundation ────────────────────────────────────────────────────────
from hydroflow._types import (
    FittingProperties,
    FlowRegime,
    MaterialProperties,
    SectionProperties,
)

# ── Layer 0: Channels ────────────────────────────────────────────────
from hydroflow.core.channels import (
    CircularChannel,
    RectangularChannel,
    TrapezoidalChannel,
    TriangularChannel,
)

# ── Hydrology ────────────────────────────────────────────────────────
from hydroflow.core.hydrology import (
    DesignStorm,
    Hydrograph,
    Watershed,
    rational_method,
    scs_runoff_depth,
    scs_unit_hydrograph,
    time_of_concentration,
)

# ── Pressure pipe flow ──────────────────────────────────────────────
from hydroflow.core.pressure import (
    HydraulicJumpResult,
    PipeLossResult,
    darcy_weisbach,
    hazen_williams,
    hydraulic_jump,
    minor_loss,
)

# ── Routing ─────────────────────────────────────────────────────────
from hydroflow.core.routing import DetentionPond, RoutingResult

# ── Structures ──────────────────────────────────────────────────────
from hydroflow.core.structures import (
    BroadCrestedWeir,
    CompositeOutlet,
    Culvert,
    CulvertResult,
    Orifice,
    RectangularWeir,
    VNotchWeir,
)

# ── Geometry (advanced usage) ─────────────────────────────────────────
from hydroflow.geometry import circular, rectangular, trapezoidal, triangular

# ── Materials (functions load lazily from JSON) ──────────────────────
from hydroflow.materials import (
    clear_project_config,
    get_fitting,
    get_material,
    get_standard,
    list_fittings,
    list_materials,
    list_standards,
    load_project_config,
    resolve_roughness,
    set_standard,
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
    "MaterialProperties",
    "FittingProperties",
    # Materials
    "resolve_roughness",
    "get_material",
    "get_fitting",
    "list_materials",
    "list_fittings",
    "set_standard",
    "get_standard",
    "list_standards",
    "load_project_config",
    "clear_project_config",
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
    # Network (lazy)
    "WaterNetwork",
]

__version__ = "0.1.1"


# ── Lazy proxy for deprecated dict constants ─────────────────────────
_DEPRECATED_DICTS = {"MANNING_ROUGHNESS", "HAZEN_WILLIAMS_C", "MINOR_LOSS_K"}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED_DICTS:
        from hydroflow import materials as _mat

        return getattr(_mat, name)
    if name == "WaterNetwork":
        from hydroflow.network.model import WaterNetwork

        return WaterNetwork
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
