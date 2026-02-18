"""Error hierarchy for the network package.

Every error carries a ``suggestion`` attribute with a human-readable hint
on how to fix the problem.  This makes EPANET's cryptic failures actionable.
"""

from __future__ import annotations

__all__ = [
    "ComponentError",
    "NetworkError",
    "SimulationError",
    "TopologyError",
    "ValidationError",
]


class NetworkError(Exception):
    """Base class for all network-related errors.

    Parameters
    ----------
    message : str
        What went wrong.
    suggestion : str
        How to fix it.
    """

    def __init__(self, message: str, *, suggestion: str = "") -> None:
        self.suggestion = suggestion
        full = f"{message}  Suggestion: {suggestion}" if suggestion else message
        super().__init__(full)


class TopologyError(NetworkError):
    """Raised when the network graph is invalid.

    Examples: referencing a node that doesn't exist, creating a pipe loop
    with no source, or leaving a node disconnected.
    """


class ValidationError(NetworkError):
    """Raised when a component or network fails validation.

    Examples: negative diameter, missing required field, duplicate name.
    """


class ComponentError(NetworkError):
    """Raised when a component cannot be constructed.

    Examples: negative elevation, zero-length pipe, invalid material name.
    """


class SimulationError(NetworkError):
    """Raised when an EPANET/WNTR simulation fails.

    Wraps the underlying solver error with a clear explanation and fix hint.
    """
