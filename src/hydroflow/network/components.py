"""Immutable dataclasses for water distribution network elements.

Each component validates at construction and can be converted to WNTR
keyword arguments via ``.to_wntr_kwargs()``.  Material names are resolved
to Hazen-Williams C values through HydroFlow's materials database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hydroflow.network.errors import ComponentError

__all__ = [
    "Junction",
    "Pipe",
    "Pump",
    "Reservoir",
    "Tank",
    "Valve",
]

# ── Helpers ───────────────────────────────────────────────────────────


def _resolve_hw_roughness(roughness: float | str) -> float:
    """Resolve roughness to a Hazen-Williams C coefficient.

    Parameters
    ----------
    roughness : float or str
        Numeric HW C value, or a material name (e.g. ``"ductile_iron"``).

    Returns
    -------
    float
        Hazen-Williams C coefficient.
    """
    if isinstance(roughness, (int, float)):
        return float(roughness)

    from hydroflow.materials import get_material

    mat = get_material(roughness)
    if mat.hazen_williams_c is None:
        raise ComponentError(
            f"Material {roughness!r} has no Hazen-Williams C value.",
            suggestion=(
                "Provide a numeric roughness coefficient instead, "
                "or use a closed-conduit material (e.g. 'ductile_iron', 'pvc')."
            ),
        )
    return mat.hazen_williams_c


def _positive(value: float, name: str) -> float:
    """Validate that *value* is strictly positive."""
    if value <= 0:
        raise ComponentError(
            f"{name} must be positive, got {value}.",
            suggestion=f"Use a positive value for {name}.",
        )
    return value


def _non_negative(value: float, name: str) -> float:
    """Validate that *value* is non-negative."""
    if value < 0:
        raise ComponentError(
            f"{name} must be non-negative, got {value}.",
            suggestion=f"Use a non-negative value for {name}.",
        )
    return value


# ── Nodes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Junction:
    """A demand node in the network.

    Parameters
    ----------
    name : str
        Unique identifier.
    elevation : float
        Elevation in active units (m or ft).
    base_demand : float
        Base demand in active flow units (m3/s or ft3/s).  Default 0.
    """

    name: str
    elevation: float
    base_demand: float = 0.0
    coordinates: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ComponentError("Junction name cannot be empty.")

    def to_wntr_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``wn.add_junction()``."""
        kw: dict[str, Any] = {
            "name": self.name,
            "base_demand": self.base_demand,
            "elevation": self.elevation,
        }
        if self.coordinates is not None:
            kw["coordinates"] = self.coordinates
        return kw


@dataclass(frozen=True, slots=True)
class Reservoir:
    """A fixed-head source node.

    Parameters
    ----------
    name : str
        Unique identifier.
    head : float
        Total head (hydraulic grade line) in active units.
    """

    name: str
    head: float
    coordinates: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ComponentError("Reservoir name cannot be empty.")

    def to_wntr_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``wn.add_reservoir()``."""
        kw: dict[str, Any] = {
            "name": self.name,
            "base_head": self.head,
        }
        if self.coordinates is not None:
            kw["coordinates"] = self.coordinates
        return kw


@dataclass(frozen=True, slots=True)
class Tank:
    """A storage tank with geometry.

    Parameters
    ----------
    name : str
        Unique identifier.
    elevation : float
        Base elevation of the tank bottom.
    init_level : float
        Initial water level above the tank bottom.
    min_level : float
        Minimum water level above the tank bottom.
    max_level : float
        Maximum water level above the tank bottom.
    diameter : float
        Tank diameter in active length units.
    """

    name: str
    elevation: float
    init_level: float
    min_level: float
    max_level: float
    diameter: float
    coordinates: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ComponentError("Tank name cannot be empty.")
        _non_negative(self.init_level, "init_level")
        _non_negative(self.min_level, "min_level")
        _positive(self.max_level, "max_level")
        _positive(self.diameter, "diameter")
        if self.min_level > self.max_level:
            raise ComponentError(
                f"min_level ({self.min_level}) > max_level ({self.max_level}).",
                suggestion="Ensure min_level <= max_level.",
            )
        if self.init_level < self.min_level:
            raise ComponentError(
                f"init_level ({self.init_level}) < min_level ({self.min_level}).",
                suggestion="Set init_level >= min_level.",
            )
        if self.init_level > self.max_level:
            raise ComponentError(
                f"init_level ({self.init_level}) > max_level ({self.max_level}).",
                suggestion="Set init_level <= max_level.",
            )

    def to_wntr_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``wn.add_tank()``."""
        kw: dict[str, Any] = {
            "name": self.name,
            "elevation": self.elevation,
            "init_level": self.init_level,
            "min_level": self.min_level,
            "max_level": self.max_level,
            "diameter": self.diameter,
        }
        if self.coordinates is not None:
            kw["coordinates"] = self.coordinates
        return kw


# ── Links ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Pipe:
    """A pipe connecting two nodes.

    Parameters
    ----------
    name : str
        Unique identifier.
    start_node : str
        Name of the start node.
    end_node : str
        Name of the end node.
    length : float
        Pipe length in active units.
    diameter : float
        Pipe diameter in active length units.
    roughness : float | str
        Hazen-Williams C coefficient (numeric) or material name
        (e.g. ``"ductile_iron"``, ``"pvc"``).
    minor_loss : float
        Minor loss coefficient.  Default 0.
    """

    name: str
    start_node: str
    end_node: str
    length: float
    diameter: float
    roughness: float | str
    minor_loss: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ComponentError("Pipe name cannot be empty.")
        if not self.start_node or not self.end_node:
            raise ComponentError(
                "Pipe start_node and end_node cannot be empty.",
                suggestion="Provide valid node names.",
            )
        if self.start_node == self.end_node:
            raise ComponentError(
                f"Pipe {self.name!r} has the same start and end node {self.start_node!r}.",
                suggestion="Connect the pipe between two different nodes.",
            )
        _positive(self.length, "length")
        _positive(self.diameter, "diameter")
        _non_negative(self.minor_loss, "minor_loss")
        # Validate roughness can be resolved (eagerly catch bad material names)
        _resolve_hw_roughness(self.roughness)

    @property
    def roughness_value(self) -> float:
        """Resolved Hazen-Williams C coefficient."""
        return _resolve_hw_roughness(self.roughness)

    def to_wntr_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``wn.add_pipe()``."""
        return {
            "name": self.name,
            "start_node_name": self.start_node,
            "end_node_name": self.end_node,
            "length": self.length,
            "diameter": self.diameter,
            "roughness": self.roughness_value,
            "minor_loss": self.minor_loss,
        }


@dataclass(frozen=True, slots=True)
class Pump:
    """A pump linking two nodes.

    Currently supports power-based pumps.  Curve-based pumps will be
    added in a future release.

    Parameters
    ----------
    name : str
        Unique identifier.
    start_node : str
        Suction side node name.
    end_node : str
        Discharge side node name.
    power : float
        Pump power in watts (SI) or horsepower (imperial).
    """

    name: str
    start_node: str
    end_node: str
    power: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ComponentError("Pump name cannot be empty.")
        if not self.start_node or not self.end_node:
            raise ComponentError(
                "Pump start_node and end_node cannot be empty.",
                suggestion="Provide valid node names.",
            )
        _positive(self.power, "power")

    def to_wntr_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``wn.add_pump()``."""
        return {
            "name": self.name,
            "start_node_name": self.start_node,
            "end_node_name": self.end_node,
            "pump_type": "POWER",
            "pump_parameter": self.power,
        }


@dataclass(frozen=True, slots=True)
class Valve:
    """A pressure-reducing valve (PRV).

    Additional valve types (PSV, FCV, TCV, GPV) will be added in a
    future release.

    Parameters
    ----------
    name : str
        Unique identifier.
    start_node : str
        Upstream node name.
    end_node : str
        Downstream node name.
    diameter : float
        Valve diameter in active length units.
    setting : float
        Pressure setting for PRV (maximum downstream pressure).
    valve_type : str
        Valve type.  Currently only ``"PRV"`` is supported.
    minor_loss : float
        Minor loss coefficient.  Default 0.
    """

    name: str
    start_node: str
    end_node: str
    diameter: float
    setting: float
    valve_type: str = "PRV"
    minor_loss: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ComponentError("Valve name cannot be empty.")
        if not self.start_node or not self.end_node:
            raise ComponentError(
                "Valve start_node and end_node cannot be empty.",
                suggestion="Provide valid node names.",
            )
        _positive(self.diameter, "diameter")
        _non_negative(self.setting, "setting")
        _non_negative(self.minor_loss, "minor_loss")
        supported = {"PRV"}
        if self.valve_type not in supported:
            raise ComponentError(
                f"Valve type {self.valve_type!r} is not supported.",
                suggestion=f"Use one of: {', '.join(sorted(supported))}.",
            )

    def to_wntr_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for ``wn.add_valve()``."""
        return {
            "name": self.name,
            "start_node_name": self.start_node,
            "end_node_name": self.end_node,
            "diameter": self.diameter,
            "valve_type": self.valve_type,
            "minor_loss": self.minor_loss,
            "setting": self.setting,
        }
