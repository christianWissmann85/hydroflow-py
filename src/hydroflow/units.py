"""Unit system for hydroflow.

All internal calculations use SI units. Conversion happens at the API boundary:
- On input: user values are converted to SI via ``to_si``
- On output: SI results are converted back via ``from_si``

The imperial Manning's constant (1.49) never appears in this codebase.
"""

from __future__ import annotations

import threading
from typing import Literal

__all__ = [
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
]

# ── Thread-safe global state ──────────────────────────────────────────

_local = threading.local()

UnitSystem = Literal["metric", "imperial"]


def set_units(system: UnitSystem) -> None:
    """Set the global unit system preference.

    Parameters
    ----------
    system : ``"metric"`` or ``"imperial"``
    """
    if system not in ("metric", "imperial"):
        msg = f"Unknown unit system: {system!r}. Use 'metric' or 'imperial'."
        raise ValueError(msg)
    _local.system = system


def get_units() -> UnitSystem:
    """Return the current global unit system (default: ``"metric"``)."""
    system: str = getattr(_local, "system", "metric")
    return system  # type: ignore[return-value]


# ── Conversion factors (all → SI) ────────────────────────────────────

_TO_SI: dict[str, float] = {
    # Length
    "m": 1.0,
    "ft": 0.3048,
    "mm": 1e-3,
    "in": 0.0254,
    # Area
    "m2": 1.0,
    "ft2": 0.09290304,
    # Catchment area
    "km2": 1e6,
    "ha": 1e4,
    "acre": 4046.8564224,
    "mi2": 2_589_988.110336,
    # Volume
    "m3": 1.0,
    "ft3": 0.028316846592,
    # Flow
    "cms": 1.0,  # m³/s
    "cfs": 0.028316846592,
    "lps": 1e-3,  # L/s
    # Velocity
    "m/s": 1.0,
    "ft/s": 0.3048,
    # Rainfall depth (same as length, but listed for clarity)
    "mm_rain": 1e-3,
    "in_rain": 0.0254,
    # Rainfall intensity
    "mm/hr": 1.0 / 3_600_000,  # mm/hr → m/s
    "in/hr": 0.0254 / 3600,  # in/hr → m/s
    # Time
    "s": 1.0,
    "min": 60.0,
    "hr": 3600.0,
}

# Map: (unit_system, physical_quantity) → display unit
_DISPLAY: dict[UnitSystem, dict[str, str]] = {
    "metric": {
        "length": "m",
        "area": "m2",
        "catch_area": "km2",
        "volume": "m3",
        "flow": "cms",
        "velocity": "m/s",
        "rainfall": "mm_rain",
        "rainfall_intensity": "mm/hr",
        "time": "s",
    },
    "imperial": {
        "length": "ft",
        "area": "ft2",
        "catch_area": "mi2",
        "volume": "ft3",
        "flow": "cfs",
        "velocity": "ft/s",
        "rainfall": "in_rain",
        "rainfall_intensity": "in/hr",
        "time": "s",
    },
}


# ── Explicit unit tags ────────────────────────────────────────────────


class _Explicit(float):
    """A float that carries an explicit unit tag.

    Subclasses ``float`` so it works everywhere a float does —
    no wrapper overhead in arithmetic. The ``_unit`` attribute stores
    the unit string for ``to_si`` to detect.
    """

    _unit: str

    def __new__(cls, value: float, unit: str) -> _Explicit:
        if unit not in _TO_SI:
            msg = f"Unknown unit: {unit!r}"
            raise ValueError(msg)
        obj = super().__new__(cls, value)
        obj._unit = unit
        return obj

    def __repr__(self) -> str:
        return f"{float(self):.6g} {self._unit}"


# ── Public shorthands ─────────────────────────────────────────────────


def ft(v: float) -> _Explicit:
    """Tag a value as feet."""
    return _Explicit(v, "ft")


def m(v: float) -> _Explicit:
    """Tag a value as meters."""
    return _Explicit(v, "m")


def cfs(v: float) -> _Explicit:
    """Tag a value as cubic feet per second."""
    return _Explicit(v, "cfs")


def cms(v: float) -> _Explicit:
    """Tag a value as cubic meters per second."""
    return _Explicit(v, "cms")


def inches(v: float) -> _Explicit:
    """Tag a value as inches."""
    return _Explicit(v, "in")


def mm(v: float) -> _Explicit:
    """Tag a value as millimeters."""
    return _Explicit(v, "mm")


def acres(v: float) -> _Explicit:
    """Tag a value as acres."""
    return _Explicit(v, "acre")


def ha(v: float) -> _Explicit:
    """Tag a value as hectares."""
    return _Explicit(v, "ha")


# ── Core conversion ──────────────────────────────────────────────────


def to_si(value: float, quantity: str) -> float:
    """Convert a user-facing value to SI.

    If *value* is an :class:`_Explicit` (e.g. ``hf.ft(10)``), its tag
    is used regardless of the global setting.  Otherwise the current
    global unit system determines the conversion.

    Parameters
    ----------
    value : float or _Explicit
        The value to convert.
    quantity : str
        Physical quantity key (``"length"``, ``"flow"``, etc.).
    """
    if isinstance(value, _Explicit):
        return float(value) * _TO_SI[value._unit]
    unit = _DISPLAY[get_units()][quantity]
    return value * _TO_SI[unit]


def from_si(value_si: float, quantity: str) -> float:
    """Convert an SI value to the user's preferred display unit.

    Parameters
    ----------
    value_si : float
        The value in SI units.
    quantity : str
        Physical quantity key (``"length"``, ``"flow"``, etc.).
    """
    unit = _DISPLAY[get_units()][quantity]
    return value_si / _TO_SI[unit]
