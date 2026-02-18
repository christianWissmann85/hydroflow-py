"""Time parsing and formatting utilities for the network package.

Converts human-friendly duration strings (``"24h"``, ``"15min"``, ``"3 days"``)
to seconds, and formats elapsed seconds as ``"HH:MM"`` or ``"Dd HH:MM"`` strings.
"""

from __future__ import annotations

import re

__all__ = [
    "format_time",
    "parse_duration",
]

# Matches patterns like "24h", "15 min", "3.5 days", "30s", "1.5 hours"
_DURATION_RE = re.compile(
    r"^\s*(?P<value>[0-9]*\.?[0-9]+)\s*(?P<unit>[a-zA-Z]+)\s*$"
)

_UNIT_TO_SECONDS: dict[str, float] = {
    # Seconds
    "s": 1.0,
    "sec": 1.0,
    "secs": 1.0,
    "second": 1.0,
    "seconds": 1.0,
    # Minutes
    "m": 60.0,
    "min": 60.0,
    "mins": 60.0,
    "minute": 60.0,
    "minutes": 60.0,
    # Hours
    "h": 3600.0,
    "hr": 3600.0,
    "hrs": 3600.0,
    "hour": 3600.0,
    "hours": 3600.0,
    # Days
    "d": 86400.0,
    "day": 86400.0,
    "days": 86400.0,
}


def parse_duration(value: str | int | float) -> float:
    """Convert a duration value to seconds.

    Parameters
    ----------
    value : str | int | float
        A human-friendly duration string (e.g. ``"24h"``, ``"15min"``,
        ``"30s"``, ``"3 days"``) or a numeric value already in seconds.

    Returns
    -------
    float
        Duration in seconds.

    Raises
    ------
    ValueError
        If the string cannot be parsed.

    Examples
    --------
    >>> parse_duration("24h")
    86400.0
    >>> parse_duration("15min")
    900.0
    >>> parse_duration("30s")
    30.0
    >>> parse_duration("3 days")
    259200.0
    >>> parse_duration(3600)
    3600.0
    """
    if isinstance(value, (int, float)):
        if value < 0:
            msg = f"Duration must be non-negative, got {value}"
            raise ValueError(msg)
        return float(value)

    match = _DURATION_RE.match(value)
    if not match:
        msg = (
            f"Cannot parse duration {value!r}. "
            f"Expected format like '24h', '15min', '30s', or '3 days'."
        )
        raise ValueError(msg)

    num = float(match.group("value"))
    unit = match.group("unit").lower()

    if unit not in _UNIT_TO_SECONDS:
        msg = (
            f"Unknown time unit {unit!r} in {value!r}. "
            f"Supported: s, min, h, d (and their long forms)."
        )
        raise ValueError(msg)

    result = num * _UNIT_TO_SECONDS[unit]
    if result < 0:
        msg = f"Duration must be non-negative, got {value!r}"
        raise ValueError(msg)
    return result


def format_time(seconds: float) -> str:
    """Format elapsed seconds as a human-readable time string.

    Parameters
    ----------
    seconds : float
        Elapsed time in seconds (must be non-negative).

    Returns
    -------
    str
        Formatted string: ``"HH:MM"`` for durations under 24 hours,
        ``"Dd HH:MM"`` for longer durations.

    Raises
    ------
    ValueError
        If *seconds* is negative.

    Examples
    --------
    >>> format_time(0)
    '00:00'
    >>> format_time(3600)
    '01:00'
    >>> format_time(90000)
    '1d 01:00'
    >>> format_time(5400)
    '01:30'
    """
    if seconds < 0:
        msg = f"Cannot format negative time: {seconds}"
        raise ValueError(msg)

    total_minutes = int(seconds // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours < 24:
        return f"{hours:02d}:{minutes:02d}"

    days = hours // 24
    remaining_hours = hours % 24
    return f"{days}d {remaining_hours:02d}:{minutes:02d}"
