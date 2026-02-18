"""Material and fitting property lookups for hydroflow.

Engineers type ``"concrete"``; we return ``n = 0.013``.

All data is loaded from JSON files in :mod:`hydroflow.data` and cached
on first access.  Materials are split across category files in
``src/hydroflow/data/materials/``, with shared sources in ``_sources.json``
and aliases in ``_aliases.json``.

Data sources:
    - Chow, V.T. (1959). *Open-Channel Hydraulics*. Table 5-6.
    - FHWA HEC-22 (2009). Table 3-1.
    - Brater, E.F. & King, H.W. (1976). *Handbook of Hydraulics*.
"""

from __future__ import annotations

import copy
import difflib
import json
import threading
from importlib import resources
from pathlib import Path
from typing import Any

from hydroflow._types import FittingProperties, MaterialProperties

__all__ = [
    "clear_project_config",
    "get_fitting",
    "get_material",
    "get_standard",
    "list_fittings",
    "list_materials",
    "list_standards",
    "load_project_config",
    "resolve_roughness",
    "set_standard",
]

# ── Thread-local state ────────────────────────────────────────────

_local = threading.local()

# ── Module-level shared caches (loaded once, immutable) ───────────

_base_materials: dict[str, Any] | None = None
_base_fittings: dict[str, Any] | None = None
_std_overlays: dict[str, dict[str, Any]] = {}
_merged_by_std: dict[str | None, dict[str, Any]] = {}

# ── Firm config cache (loaded once per process) ──────────────────

_firm_config: dict[str, Any] | None = None
_firm_config_loaded: bool = False  # distinguish "no file" from "not yet checked"


# ── Deep merge utility ────────────────────────────────────────────


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursive dict merge. overlay values win for non-dict types.

    dict+dict recurses. Returns new dict (base not mutated).
    """
    result = copy.deepcopy(base)
    for key, val in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = copy.deepcopy(val)
    return result


# ── Base data loaders ─────────────────────────────────────────────


def _load_base_materials() -> dict[str, Any]:
    """Walk data/materials/*.json + load _sources.json + _aliases.json.

    Returns ``{"materials": {...}, "_meta": {"sources": {...}, "aliases": {...}}}``.
    """
    global _base_materials
    if _base_materials is not None:
        return _base_materials

    data_pkg = resources.files("hydroflow.data")
    sources: dict[str, Any] = json.loads(
        data_pkg.joinpath("_sources.json").read_text(encoding="utf-8")
    )
    aliases: dict[str, Any] = json.loads(
        data_pkg.joinpath("_aliases.json").read_text(encoding="utf-8")
    )

    materials: dict[str, Any] = {}
    mat_pkg = resources.files("hydroflow.data.materials")
    for child in mat_pkg.iterdir():
        if hasattr(child, "name") and child.name.endswith(".json"):
            materials.update(json.loads(child.read_text(encoding="utf-8")))

    _base_materials = {
        "materials": materials,
        "_meta": {"version": "1.0.0", "sources": sources, "aliases": aliases},
    }
    return _base_materials


def _load_fittings() -> dict[str, Any]:
    """Load and cache the fittings JSON database."""
    global _base_fittings
    if _base_fittings is None:
        ref = resources.files("hydroflow.data").joinpath("fittings.json")
        _base_fittings = json.loads(ref.read_text(encoding="utf-8"))
    return _base_fittings


# ── Standards layer ───────────────────────────────────────────────


def set_standard(name: str | None) -> None:
    """Set the active engineering standard. ``None`` resets to base.

    Parameters
    ----------
    name : str or None
        Standard name (e.g. ``"din_en"``), or ``None`` to clear.

    Raises
    ------
    ValueError
        If the named standard does not exist.
    """
    if name is not None:
        available = list_standards()
        if name not in available:
            msg = f"Unknown standard '{name}'. Available: {', '.join(available)}"
            raise ValueError(msg)
    _local.standard = name
    _local.standard_explicit = True  # user explicitly chose a standard (even None)
    _local.final_db = None  # invalidate cached effective DB


def get_standard() -> str | None:
    """Return the active standard name, or ``None``."""
    return getattr(_local, "standard", None)


def list_standards() -> list[str]:
    """Return sorted list of available bundled standards."""
    std_pkg = resources.files("hydroflow.data.standards")
    result: list[str] = []
    for child in std_pkg.iterdir():
        if hasattr(child, "name") and child.name != "__pycache__":
            # Check if it's a package with a materials.json
            meta = child.joinpath("_meta.json")
            if hasattr(meta, "read_text"):
                try:
                    meta.read_text(encoding="utf-8")
                    result.append(child.name)
                except (FileNotFoundError, OSError):
                    pass
    return sorted(result)


def _load_standard_overlay(name: str) -> dict[str, Any]:
    """Load and cache a standard's material overrides."""
    if name in _std_overlays:
        return _std_overlays[name]

    std_pkg = resources.files("hydroflow.data.standards").joinpath(name)
    mat_file = std_pkg.joinpath("materials.json")
    overlay: dict[str, Any] = json.loads(mat_file.read_text(encoding="utf-8"))
    _std_overlays[name] = overlay
    return overlay


def _get_base_with_standard(standard: str | None) -> dict[str, Any]:
    """Return base materials merged with the named standard (cached)."""
    if standard in _merged_by_std:
        return _merged_by_std[standard]

    base = _load_base_materials()
    if standard is None:
        _merged_by_std[None] = base
        return base

    overlay = _load_standard_overlay(standard)
    merged_materials = _deep_merge(base["materials"], overlay)
    result = {
        "materials": merged_materials,
        "_meta": base["_meta"],
    }
    _merged_by_std[standard] = result
    return result


# ── Firm config layer ─────────────────────────────────────────────


def _find_firm_config() -> Path | None:
    """Return path to ~/.hydroflow/firm_config.toml if it exists, else None."""
    try:
        candidate = Path.home() / ".hydroflow" / "firm_config.toml"
        if candidate.is_file():
            return candidate
    except OSError:
        pass
    return None


def _load_firm_config() -> dict[str, Any] | None:
    """Load and cache firm config. Returns None if no file exists."""
    global _firm_config, _firm_config_loaded
    if _firm_config_loaded:
        return _firm_config

    import tomllib

    path = _find_firm_config()
    if path is not None:
        raw = path.read_text(encoding="utf-8")
        config = tomllib.loads(raw)
        if "hydroflow" in config:
            _firm_config = config["hydroflow"]
    _firm_config_loaded = True
    return _firm_config


# ── Config overlay helper ────────────────────────────────────────


def _apply_config_overlay(db: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Apply a config overlay (firm or project) to a materials DB."""
    mat_overrides = config.get("materials", {})
    if mat_overrides:
        db = {
            "materials": _deep_merge(db["materials"], mat_overrides),
            "_meta": db["_meta"],
        }

    alias_overrides = config.get("aliases", {})
    if alias_overrides:
        merged_aliases = _deep_merge(db["_meta"].get("aliases", {}), alias_overrides)
        db = {
            "materials": db["materials"],
            "_meta": {**db["_meta"], "aliases": merged_aliases},
        }
    return db


def _apply_fittings_overlay(
    db: dict[str, Any], config: dict[str, Any]
) -> dict[str, Any]:
    """Apply a config overlay (firm or project) to a fittings DB."""
    fitting_overrides = config.get("fittings", {})
    if fitting_overrides:
        merged_fittings = _deep_merge(db["fittings"], fitting_overrides)
        db = {
            "_meta": db["_meta"],
            "fittings": merged_fittings,
        }
    return db


# ── Project config layer ──────────────────────────────────────────


def _find_project_config() -> Path:
    """Walk CWD upward looking for ``hydroflow.toml``.

    Returns
    -------
    Path
        Absolute path to the discovered file.

    Raises
    ------
    FileNotFoundError
        If no ``hydroflow.toml`` is found in any ancestor directory.
    """
    cwd = Path.cwd().resolve()
    for directory in (cwd, *cwd.parents):
        candidate = directory / "hydroflow.toml"
        if candidate.is_file():
            return candidate
    msg = f"No hydroflow.toml found in {cwd} or any parent directory"
    raise FileNotFoundError(msg)


def _validate_project_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate and return the ``[hydroflow]`` section of a parsed TOML file.

    Raises
    ------
    ValueError
        If the config is missing the ``[hydroflow]`` section.
    """
    if "hydroflow" not in config:
        msg = "hydroflow.toml must contain a [hydroflow] section"
        raise ValueError(msg)
    section: dict[str, Any] = config["hydroflow"]
    return section


def load_project_config(path: str | Path | None = None) -> None:
    """Load project overrides from TOML.

    Parameters
    ----------
    path : str, Path, or None
        Explicit path to ``hydroflow.toml``. If ``None``, auto-discovers
        by walking CWD upward.

    Raises
    ------
    FileNotFoundError
        If auto-discovery fails or the explicit path doesn't exist.
    ValueError
        If the TOML file is missing the ``[hydroflow]`` section.
    """
    import tomllib

    if path is None:
        path = _find_project_config()
    else:
        path = Path(path)
        if not path.is_file():
            msg = f"Config file not found: {path}"
            raise FileNotFoundError(msg)

    raw = path.read_text(encoding="utf-8")
    config = tomllib.loads(raw)
    hf_config = _validate_project_config(config)

    # Apply standard if specified
    if "standard" in hf_config:
        set_standard(hf_config["standard"])

    _local.project_config = hf_config
    _local.final_db = None  # invalidate cached effective DB


def clear_project_config() -> None:
    """Remove loaded project config for current thread."""
    _local.project_config = None
    _local.final_db = None


# ── Effective database (single choke point) ───────────────────────


def _get_effective_db() -> dict[str, Any]:
    """Return fully-merged materials DB: base < standard < firm < project."""
    cached: dict[str, Any] | None = getattr(_local, "final_db", None)
    if cached is not None:
        return cached

    standard = get_standard()
    db = _get_base_with_standard(standard)

    # Apply firm config (between standard and project)
    firm = _load_firm_config()
    if firm is not None:
        # Apply firm standard only if user never called set_standard()
        standard_explicit = getattr(_local, "standard_explicit", False)
        if standard is None and not standard_explicit and "standard" in firm:
            db = _get_base_with_standard(firm["standard"])
        db = _apply_config_overlay(db, firm)

    # Apply project config (highest priority)
    project_config: dict[str, Any] | None = getattr(_local, "project_config", None)
    if project_config is not None:
        db = _apply_config_overlay(db, project_config)

    _local.final_db = db
    return db


def _get_effective_fittings() -> dict[str, Any]:
    """Return fittings DB with firm and project config overrides applied."""
    db = _load_fittings()

    # Apply firm config
    firm = _load_firm_config()
    if firm is not None:
        db = _apply_fittings_overlay(db, firm)

    # Apply project config (highest priority)
    project_config: dict[str, Any] | None = getattr(_local, "project_config", None)
    if project_config is not None:
        db = _apply_fittings_overlay(db, project_config)

    return db


# ── Fuzzy matching helper ────────────────────────────────────────


def _fuzzy_lookup(key: str, valid_keys: list[str], label: str = "material") -> str:
    """Raise :class:`ValueError` with fuzzy-match suggestions.

    Parameters
    ----------
    key : str
        The unknown key the user typed.
    valid_keys : list[str]
        All valid keys to match against.
    label : str
        Human label for error messages (``"material"`` or ``"fitting"``).

    Raises
    ------
    ValueError
        Always --- this is an error helper.
    """
    close = difflib.get_close_matches(key, valid_keys, n=3, cutoff=0.5)
    if close:
        suggestions = ", ".join(f"'{c}'" for c in close)
        msg = f"Unknown {label} '{key}'. Did you mean: {suggestions}?"
    else:
        msg = (
            f"Unknown {label} '{key}'. "
            f"Available: {', '.join(sorted(valid_keys))}"
        )
    raise ValueError(msg)


# ── Core public API ──────────────────────────────────────────────


def get_material(name: str, *, condition: str | None = None) -> MaterialProperties:
    """Look up a material by name, with optional condition override.

    Parameters
    ----------
    name : str
        Material name (e.g. ``"concrete"``) or legacy alias
        (e.g. ``"concrete_smooth"``).
    condition : str, optional
        Condition name to apply (e.g. ``"new_smooth"``).  Overrides any
        condition embedded in an alias.

    Returns
    -------
    MaterialProperties

    Raises
    ------
    ValueError
        If the material or condition is not found (suggests closest match).

    Examples
    --------
    >>> get_material("concrete").manning_n
    0.013
    >>> get_material("concrete", condition="old_rough").manning_n
    0.016
    """
    db = _get_effective_db()
    materials = db["materials"]
    aliases = db["_meta"].get("aliases", {})
    key = name.lower().strip()

    # Resolve alias
    resolved_material = key
    alias_condition: str | None = None
    if key not in materials and key in aliases:
        alias = aliases[key]
        resolved_material = alias["material"]
        alias_condition = alias.get("condition")

    if resolved_material not in materials:
        all_keys = sorted(set(list(materials.keys()) + list(aliases.keys())))
        _fuzzy_lookup(key, all_keys, "material")

    mat = materials[resolved_material]
    active_condition = condition if condition is not None else alias_condition

    # Base values
    manning_n_info = mat["manning_n"]
    n_val = manning_n_info["default"]
    n_range = tuple(manning_n_info["range"]) if "range" in manning_n_info else None

    hw_c: float | None = None
    hw_c_range: tuple[float, float] | None = None
    if "hazen_williams_c" in mat:
        hw_info = mat["hazen_williams_c"]
        hw_c = hw_info["default"]
        hw_c_range = tuple(hw_info["range"]) if "range" in hw_info else None

    eps: float | None = None
    eps_range: tuple[float, float] | None = None
    if "darcy_epsilon_mm" in mat:
        eps_info = mat["darcy_epsilon_mm"]
        eps = eps_info["default"]
        eps_range = tuple(eps_info["range"]) if "range" in eps_info else None

    # Apply condition overrides
    if active_condition is not None:
        conditions = mat.get("conditions", {})
        if active_condition not in conditions:
            valid_conds = sorted(conditions.keys())
            msg = (
                f"Unknown condition '{active_condition}' for material "
                f"'{resolved_material}'. Available: {', '.join(valid_conds)}"
            )
            raise ValueError(msg)
        overrides = conditions[active_condition]
        if "manning_n" in overrides:
            n_val = overrides["manning_n"]
        if "hazen_williams_c" in overrides:
            hw_c = overrides["hazen_williams_c"]
        if "darcy_epsilon_mm" in overrides:
            eps = overrides["darcy_epsilon_mm"]

    return MaterialProperties(
        name=resolved_material,
        category=mat["category"],
        description=mat["description"],
        manning_n=n_val,
        manning_n_range=n_range,
        hazen_williams_c=hw_c,
        hazen_williams_c_range=hw_c_range,
        darcy_epsilon_mm=eps,
        darcy_epsilon_mm_range=eps_range,
        condition=active_condition,
    )


def get_fitting(name: str) -> FittingProperties:
    """Look up a fitting by name.

    Parameters
    ----------
    name : str
        Fitting key (e.g. ``"90_elbow"``).

    Returns
    -------
    FittingProperties

    Raises
    ------
    ValueError
        If the fitting is not found (suggests closest match).

    Examples
    --------
    >>> get_fitting("90_elbow").K
    0.9
    """
    db = _get_effective_fittings()
    fittings = db["fittings"]
    key = name.lower().strip()

    if key not in fittings:
        _fuzzy_lookup(key, sorted(fittings.keys()), "fitting")

    fit = fittings[key]
    k_info = fit["K"]

    return FittingProperties(
        name=key,
        category=fit["category"],
        description=fit["description"],
        K=k_info["default"],
        K_range=tuple(k_info["range"]) if "range" in k_info else None,
    )


def list_materials() -> list[str]:
    """Return a sorted list of all material names (excluding aliases).

    Returns
    -------
    list[str]
    """
    db = _get_effective_db()
    return sorted(db["materials"].keys())


def list_fittings() -> list[str]:
    """Return a sorted list of all fitting names.

    Returns
    -------
    list[str]
    """
    db = _get_effective_fittings()
    return sorted(db["fittings"].keys())


# ── Backwards-compatible resolve functions ───────────────────────


def resolve_roughness(roughness: float | str, *, condition: str | None = None) -> float:
    """Resolve a roughness value --- numeric pass-through or string lookup.

    Parameters
    ----------
    roughness : float or str
        If ``float``, returned as-is.  If ``str``, looked up in the
        material database (supports aliases like ``"concrete_smooth"``).
    condition : str, optional
        Condition override (e.g. ``"new_smooth"``).

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
        mat = get_material(roughness, condition=condition)
        return mat.manning_n

    n = float(roughness)
    if n <= 0:
        msg = f"Manning's n must be positive, got {n}"
        raise ValueError(msg)
    return n


def _resolve_hazen_williams(C: float | str) -> float:
    """Resolve Hazen-Williams C --- numeric pass-through or string lookup.

    This is a package-internal helper used by :func:`hydroflow.pressure.hazen_williams`.
    """
    if isinstance(C, str):
        key = C.lower().strip()
        mat = _lookup_hazen_williams_key(key)
        if mat is None:
            # Build list of valid HW keys for error message
            valid = sorted(_build_hazen_williams_dict().keys())
            valid_str = ", ".join(f"'{k}'" for k in valid)
            msg = f"Unknown material '{C}'. Available: {valid_str}"
            raise ValueError(msg)
        return mat

    return float(C)


def _resolve_minor_loss(K: float | str) -> float:
    """Resolve minor loss K --- numeric pass-through or string lookup.

    This is a package-internal helper used by :func:`hydroflow.pressure.minor_loss`.
    """
    if isinstance(K, str):
        fit = get_fitting(K)
        return fit.K

    return float(K)


def _lookup_hazen_williams_key(key: str) -> float | None:
    """Look up a single Hazen-Williams key, returning the C value or None."""
    db = _get_effective_db()
    materials: dict[str, Any] = db["materials"]
    aliases: dict[str, Any] = db["_meta"].get("aliases", {})

    # Direct material lookup
    if key in materials:
        mat: dict[str, Any] = materials[key]
        if "hazen_williams_c" in mat:
            return float(mat["hazen_williams_c"]["default"])
        return None

    # Alias lookup
    if key in aliases:
        alias: dict[str, Any] = aliases[key]
        mat_name: str = alias["material"]
        cond: str | None = alias.get("condition")
        if mat_name not in materials:
            return None
        mat = materials[mat_name]
        if cond and "conditions" in mat and cond in mat["conditions"]:
            overrides: dict[str, Any] = mat["conditions"][cond]
            if "hazen_williams_c" in overrides:
                return float(overrides["hazen_williams_c"])
        if "hazen_williams_c" in mat:
            return float(mat["hazen_williams_c"]["default"])
        return None

    return None


# ── Legacy dict builders ─────────────────────────────────────────


def _build_manning_dict() -> dict[str, float]:
    """Build the legacy ``MANNING_ROUGHNESS`` dict from JSON data."""
    db = _get_effective_db()
    materials = db["materials"]
    aliases = db["_meta"].get("aliases", {})
    result: dict[str, float] = {}

    # All base materials with manning_n
    for name, mat in materials.items():
        result[name] = mat["manning_n"]["default"]

    # All aliases that resolve to manning_n
    for alias_key, alias in aliases.items():
        mat_name = alias["material"]
        cond = alias.get("condition")
        if mat_name not in materials:
            continue
        mat = materials[mat_name]
        if cond and "conditions" in mat and cond in mat["conditions"]:
            overrides = mat["conditions"][cond]
            if "manning_n" in overrides:
                result[alias_key] = overrides["manning_n"]
                continue
        result[alias_key] = mat["manning_n"]["default"]

    return result


def _build_hazen_williams_dict() -> dict[str, float]:
    """Build the legacy ``HAZEN_WILLIAMS_C`` dict from JSON data."""
    db = _get_effective_db()
    materials = db["materials"]
    aliases = db["_meta"].get("aliases", {})
    result: dict[str, float] = {}

    # Base materials with hazen_williams_c
    for name, mat in materials.items():
        if "hazen_williams_c" in mat:
            result[name] = mat["hazen_williams_c"]["default"]

    # Aliases that resolve to hazen_williams_c
    for alias_key, alias in aliases.items():
        mat_name = alias["material"]
        cond = alias.get("condition")
        if mat_name not in materials:
            continue
        mat = materials[mat_name]
        if cond and "conditions" in mat and cond in mat["conditions"]:
            overrides = mat["conditions"][cond]
            if "hazen_williams_c" in overrides:
                result[alias_key] = overrides["hazen_williams_c"]
                continue
        if "hazen_williams_c" in mat:
            result[alias_key] = mat["hazen_williams_c"]["default"]

    return result


def _build_minor_loss_dict() -> dict[str, float]:
    """Build the legacy ``MINOR_LOSS_K`` dict from JSON data."""
    db = _get_effective_fittings()
    return {name: fit["K"]["default"] for name, fit in db["fittings"].items()}


# ── Lazy module-level attributes for backwards compatibility ─────

_MANNING_ROUGHNESS: dict[str, float] | None = None
_HAZEN_WILLIAMS_C: dict[str, float] | None = None
_MINOR_LOSS_K: dict[str, float] | None = None

_LAZY_DICTS = {
    "MANNING_ROUGHNESS": "_MANNING_ROUGHNESS",
    "HAZEN_WILLIAMS_C": "_HAZEN_WILLIAMS_C",
    "MINOR_LOSS_K": "_MINOR_LOSS_K",
}

_LAZY_BUILDERS = {
    "MANNING_ROUGHNESS": _build_manning_dict,
    "HAZEN_WILLIAMS_C": _build_hazen_williams_dict,
    "MINOR_LOSS_K": _build_minor_loss_dict,
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_DICTS:
        cache_attr = _LAZY_DICTS[name]
        cached = globals()[cache_attr]
        if cached is None:
            cached = _LAZY_BUILDERS[name]()
            globals()[cache_attr] = cached
        return cached
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
