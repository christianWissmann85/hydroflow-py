"""HydroFlow Network — water distribution pipe network analysis.

Provides an engineer-friendly Python wrapper around WNTR/EPANET for
building, simulating, and analyzing water distribution networks.
"""

from hydroflow.network.errors import (
    ComponentError,
    NetworkError,
    SimulationError,
    TopologyError,
    ValidationError,
)

__all__ = [
    "ComponentError",
    "NetworkError",
    "SimulationError",
    "TopologyError",
    "ValidationError",
]
