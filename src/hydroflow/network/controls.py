"""Structured control objects for water distribution networks.

Controls automate link status changes during a simulation.  Two types
are supported:

- **TimeControl** — change link status at a specific clock time.
- **ConditionalControl** — change link status when a node attribute
  crosses a threshold.

These are Python objects (not a DSL parser) — a mini-DSL is planned
for Phase 3+.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hydroflow.network._time import parse_duration
from hydroflow.network.errors import ComponentError

__all__ = [
    "ConditionalControl",
    "TimeControl",
]

_VALID_STATUSES = {"OPEN", "CLOSED"}
_STATUS_CODE = {"OPEN": 1, "CLOSED": 0}
_VALID_ATTRIBUTES = {"pressure", "head", "level"}
_VALID_OPERATORS = {"<", ">", "<=", ">=", "=="}
_OPERATOR_NAMES = {
    "<": "below",
    ">": "above",
    "<=": "at_or_below",
    ">=": "at_or_above",
    "==": "equal_to",
}


@dataclass(frozen=True, slots=True)
class TimeControl:
    """Change a link's status at a specific simulation time.

    Parameters
    ----------
    link_name : str
        Name of the link (pipe, pump, or valve) to control.
    status : str
        Target status: ``"OPEN"`` or ``"CLOSED"``.
    at : str | int | float
        Time to apply the control.  String (``"22:00"``, ``"6h"``) or
        seconds from simulation start.
    """

    link_name: str
    status: str
    at: str | int | float

    def __post_init__(self) -> None:
        if not self.link_name:
            raise ComponentError("TimeControl link_name cannot be empty.")
        if self.status not in _VALID_STATUSES:
            raise ComponentError(
                f"Invalid status {self.status!r}.",
                suggestion=f"Use one of: {', '.join(sorted(_VALID_STATUSES))}.",
            )

    @property
    def at_seconds(self) -> float:
        """Resolved time in seconds."""
        return parse_duration(self.at)

    def _to_control_dict(self, index: int) -> dict[str, Any]:
        """Convert to a dict for WaterNetwork._controls."""
        return {
            "type": "time",
            "link_name": self.link_name,
            "status": self.status,
            "status_code": _STATUS_CODE[self.status],
            "at_seconds": self.at_seconds,
            "control_name": f"time_ctrl_{self.link_name}_{index}",
        }


@dataclass(frozen=True, slots=True)
class ConditionalControl:
    """Change a link's status based on a node condition.

    Parameters
    ----------
    link_name : str
        Name of the link to control.
    status : str
        Target status: ``"OPEN"`` or ``"CLOSED"``.
    node_name : str
        Node to monitor.
    attribute : str
        Node attribute to check: ``"pressure"``, ``"head"``, or ``"level"``.
    operator : str
        Comparison operator: ``"<"``, ``">"``, ``"<="``, ``">="``, ``"=="``.
    threshold : float
        Threshold value for the condition.
    """

    link_name: str
    status: str
    node_name: str
    attribute: str
    operator: str
    threshold: float

    def __post_init__(self) -> None:
        if not self.link_name:
            raise ComponentError("ConditionalControl link_name cannot be empty.")
        if not self.node_name:
            raise ComponentError("ConditionalControl node_name cannot be empty.")
        if self.status not in _VALID_STATUSES:
            raise ComponentError(
                f"Invalid status {self.status!r}.",
                suggestion=f"Use one of: {', '.join(sorted(_VALID_STATUSES))}.",
            )
        if self.attribute not in _VALID_ATTRIBUTES:
            raise ComponentError(
                f"Invalid attribute {self.attribute!r}.",
                suggestion=f"Use one of: {', '.join(sorted(_VALID_ATTRIBUTES))}.",
            )
        if self.operator not in _VALID_OPERATORS:
            raise ComponentError(
                f"Invalid operator {self.operator!r}.",
                suggestion=f"Use one of: {', '.join(sorted(_VALID_OPERATORS))}.",
            )

    def _to_control_dict(self, index: int) -> dict[str, Any]:
        """Convert to a dict for WaterNetwork._controls."""
        return {
            "type": "conditional",
            "link_name": self.link_name,
            "status": self.status,
            "status_code": _STATUS_CODE[self.status],
            "node_name": self.node_name,
            "attribute": self.attribute,
            "operator": _OPERATOR_NAMES[self.operator],
            "threshold": self.threshold,
            "control_name": f"cond_ctrl_{self.link_name}_{index}",
        }
