"""Material property lookups for hydroflow.

Engineers type ``"concrete"``; we return ``n = 0.013``.

Data sources:
    - Chow, V.T. (1959). *Open-Channel Hydraulics*. Table 5-6.
    - FHWA HEC-22 (2009). Table 3-1.
"""

from __future__ import annotations

import difflib

__all__ = [
    "resolve_roughness",
    "MANNING_ROUGHNESS",
]

# ── Manning's n lookup table ──────────────────────────────────────────

MANNING_ROUGHNESS: dict[str, float] = {
    # ── Closed conduits ───────────────────────────────────────────────
    "concrete": 0.013,
    "concrete_smooth": 0.012,
    "concrete_rough": 0.016,
    "corrugated_metal": 0.024,
    "corrugated_metal_paved_invert": 0.020,
    "hdpe": 0.012,
    "hdpe_smooth": 0.011,
    "pvc": 0.010,
    "cast_iron": 0.013,
    "ductile_iron": 0.013,
    "steel": 0.012,
    "steel_riveted": 0.017,
    "clay_tile": 0.014,
    "brick": 0.016,
    # ── Open channels — lined ─────────────────────────────────────────
    "concrete_trowel": 0.013,
    "concrete_float": 0.015,
    "asphalt_smooth": 0.013,
    "riprap": 0.035,
    "gabion": 0.028,
    # ── Open channels — unlined ───────────────────────────────────────
    "earth_clean": 0.022,
    "earth_weedy": 0.030,
    "earth_gravelly": 0.025,
    "rock_cut": 0.035,
    "natural_clean": 0.030,
    "natural_weedy": 0.050,
    "natural_heavy_brush": 0.075,
    "floodplain_grass": 0.035,
    "floodplain_light_brush": 0.050,
    "floodplain_heavy_trees": 0.100,
}


def resolve_roughness(roughness: float | str) -> float:
    """Resolve a roughness value — numeric pass-through or string lookup.

    Parameters
    ----------
    roughness : float or str
        If ``float``, returned as-is.  If ``str``, looked up in
        :data:`MANNING_ROUGHNESS`.

    Returns
    -------
    float
        Manning's *n* coefficient.

    Raises
    ------
    ValueError
        If the string key is not found (suggests closest match).

    Examples
    --------
    >>> resolve_roughness(0.015)
    0.015
    >>> resolve_roughness("concrete")
    0.013
    """
    if isinstance(roughness, str):
        key = roughness.lower().strip()
        if key in MANNING_ROUGHNESS:
            return MANNING_ROUGHNESS[key]

        # Fuzzy suggestion
        close = difflib.get_close_matches(key, MANNING_ROUGHNESS.keys(), n=3, cutoff=0.5)
        if close:
            suggestions = ", ".join(f"'{c}'" for c in close)
            msg = f"Unknown material '{roughness}'. Did you mean: {suggestions}?"
        else:
            msg = (
                f"Unknown material '{roughness}'. "
                f"Available: {', '.join(sorted(MANNING_ROUGHNESS.keys()))}"
            )
        raise ValueError(msg)

    n = float(roughness)
    if n <= 0:
        msg = f"Manning's n must be positive, got {n}"
        raise ValueError(msg)
    return n
