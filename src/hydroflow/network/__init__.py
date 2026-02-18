"""HydroFlow Network — water distribution pipe network analysis.

Provides an engineer-friendly Python wrapper around WNTR/EPANET for
building, simulating, and analyzing water distribution networks.
"""

from hydroflow.network._time import format_time, parse_duration
from hydroflow.network.components import (
    Junction,
    Pipe,
    Pump,
    Reservoir,
    Tank,
    Valve,
)
from hydroflow.network.controls import ConditionalControl, TimeControl
from hydroflow.network.errors import (
    ComponentError,
    NetworkError,
    SimulationError,
    TopologyError,
    ValidationError,
)
from hydroflow.network.model import WaterNetwork

__all__ = [
    # Model
    "WaterNetwork",
    # Components
    "Junction",
    "Reservoir",
    "Tank",
    "Pipe",
    "Pump",
    "Valve",
    # Controls
    "TimeControl",
    "ConditionalControl",
    # Errors
    "ComponentError",
    "NetworkError",
    "SimulationError",
    "TopologyError",
    "ValidationError",
    # Time utilities
    "parse_duration",
    "format_time",
]
