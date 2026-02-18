"""Data integrity tests for JSON material and fitting databases.

Validates schema, value ranges, source references, alias consistency,
and condition overrides.  Materials are split across category files in
``data/materials/``, with shared sources and aliases in top-level files.
"""

from __future__ import annotations

import json
from importlib import resources

import pytest


def _load_materials_db() -> dict:
    """Load split materials files into the canonical DB shape."""
    data_pkg = resources.files("hydroflow.data")
    sources = json.loads(data_pkg.joinpath("_sources.json").read_text(encoding="utf-8"))
    aliases = json.loads(data_pkg.joinpath("_aliases.json").read_text(encoding="utf-8"))

    materials: dict = {}
    mat_pkg = resources.files("hydroflow.data.materials")
    for child in mat_pkg.iterdir():
        if hasattr(child, "name") and child.name.endswith(".json"):
            materials.update(json.loads(child.read_text(encoding="utf-8")))

    return {
        "materials": materials,
        "_meta": {"version": "1.0.0", "sources": sources, "aliases": aliases},
    }


@pytest.fixture(scope="module")
def materials_db() -> dict:
    return _load_materials_db()


@pytest.fixture(scope="module")
def fittings_db() -> dict:
    ref = resources.files("hydroflow.data").joinpath("fittings.json")
    return json.loads(ref.read_text(encoding="utf-8"))


# ── Materials JSON schema ────────────────────────────────────────────


class TestMaterialsSchema:
    def test_has_meta_section(self, materials_db: dict) -> None:
        assert "_meta" in materials_db
        assert "version" in materials_db["_meta"]
        assert "sources" in materials_db["_meta"]
        assert "aliases" in materials_db["_meta"]

    def test_has_materials_section(self, materials_db: dict) -> None:
        assert "materials" in materials_db
        assert len(materials_db["materials"]) > 0

    def test_every_material_has_required_fields(self, materials_db: dict) -> None:
        for name, mat in materials_db["materials"].items():
            assert "category" in mat, f"{name}: missing 'category'"
            assert "description" in mat, f"{name}: missing 'description'"
            assert "manning_n" in mat, f"{name}: missing 'manning_n'"
            assert "default" in mat["manning_n"], f"{name}: manning_n missing 'default'"

    def test_manning_n_defaults_are_positive(self, materials_db: dict) -> None:
        for name, mat in materials_db["materials"].items():
            n = mat["manning_n"]["default"]
            assert n > 0, f"{name}: manning_n default {n} must be positive"

    def test_manning_n_ranges_are_valid(self, materials_db: dict) -> None:
        for name, mat in materials_db["materials"].items():
            n_info = mat["manning_n"]
            if "range" in n_info:
                lo, hi = n_info["range"]
                default = n_info["default"]
                assert lo <= default <= hi, (
                    f"{name}: manning_n default {default} outside range [{lo}, {hi}]"
                )
                assert lo > 0, f"{name}: manning_n range min {lo} must be positive"

    def test_hazen_williams_ranges_are_valid(self, materials_db: dict) -> None:
        for name, mat in materials_db["materials"].items():
            if "hazen_williams_c" not in mat:
                continue
            hw = mat["hazen_williams_c"]
            if "range" in hw:
                lo, hi = hw["range"]
                default = hw["default"]
                assert lo <= default <= hi, (
                    f"{name}: hazen_williams_c default {default} outside range [{lo}, {hi}]"
                )
                assert lo > 0, f"{name}: hazen_williams_c range min {lo} must be positive"

    def test_darcy_epsilon_ranges_are_valid(self, materials_db: dict) -> None:
        for name, mat in materials_db["materials"].items():
            if "darcy_epsilon_mm" not in mat:
                continue
            eps = mat["darcy_epsilon_mm"]
            if "range" in eps:
                lo, hi = eps["range"]
                default = eps["default"]
                assert lo <= default <= hi, (
                    f"{name}: darcy_epsilon_mm default {default} outside range [{lo}, {hi}]"
                )
                assert lo >= 0, f"{name}: darcy_epsilon_mm range min {lo} must be non-negative"

    def test_source_keys_reference_valid_sources(self, materials_db: dict) -> None:
        valid_sources = set(materials_db["_meta"]["sources"].keys())
        for name, mat in materials_db["materials"].items():
            for prop in ("manning_n", "hazen_williams_c", "darcy_epsilon_mm"):
                if prop not in mat:
                    continue
                info = mat[prop]
                if "source" in info:
                    assert info["source"] in valid_sources, (
                        f"{name}.{prop}: source '{info['source']}' not in _meta.sources"
                    )


# ── Condition overrides ──────────────────────────────────────────


class TestConditionOverrides:
    def test_condition_manning_n_within_parent_range(self, materials_db: dict) -> None:
        for name, mat in materials_db["materials"].items():
            n_info = mat["manning_n"]
            if "range" not in n_info or "conditions" not in mat:
                continue
            lo, hi = n_info["range"]
            for cond_name, overrides in mat["conditions"].items():
                if "manning_n" in overrides:
                    n = overrides["manning_n"]
                    assert lo <= n <= hi, (
                        f"{name}/{cond_name}: manning_n {n} outside parent range [{lo}, {hi}]"
                    )

    def test_condition_hazen_williams_within_parent_range(
        self, materials_db: dict
    ) -> None:
        for name, mat in materials_db["materials"].items():
            if "hazen_williams_c" not in mat or "conditions" not in mat:
                continue
            hw = mat["hazen_williams_c"]
            if "range" not in hw:
                continue
            lo, hi = hw["range"]
            for cond_name, overrides in mat["conditions"].items():
                if "hazen_williams_c" in overrides:
                    c = overrides["hazen_williams_c"]
                    assert lo <= c <= hi, (
                        f"{name}/{cond_name}: hazen_williams_c {c} outside "
                        f"parent range [{lo}, {hi}]"
                    )


# ── Alias integrity ──────────────────────────────────────────────


class TestAliasIntegrity:
    def test_aliases_point_to_valid_materials(self, materials_db: dict) -> None:
        materials = materials_db["materials"]
        for alias, ref in materials_db["_meta"]["aliases"].items():
            mat_name = ref["material"]
            assert mat_name in materials, (
                f"alias '{alias}' points to unknown material '{mat_name}'"
            )

    def test_aliases_point_to_valid_conditions(self, materials_db: dict) -> None:
        materials = materials_db["materials"]
        for alias, ref in materials_db["_meta"]["aliases"].items():
            mat_name = ref["material"]
            cond = ref.get("condition")
            if cond is None:
                continue
            mat = materials[mat_name]
            conditions = mat.get("conditions", {})
            assert cond in conditions, (
                f"alias '{alias}' points to unknown condition '{cond}' "
                f"of material '{mat_name}'"
            )

    def test_aliases_do_not_shadow_material_names(self, materials_db: dict) -> None:
        materials = materials_db["materials"]
        for alias in materials_db["_meta"]["aliases"]:
            assert alias not in materials, (
                f"alias '{alias}' shadows material name"
            )


# ── Fittings JSON schema ────────────────────────────────────────


class TestFittingsSchema:
    def test_has_meta_section(self, fittings_db: dict) -> None:
        assert "_meta" in fittings_db
        assert "version" in fittings_db["_meta"]
        assert "sources" in fittings_db["_meta"]

    def test_has_fittings_section(self, fittings_db: dict) -> None:
        assert "fittings" in fittings_db
        assert len(fittings_db["fittings"]) > 0

    def test_every_fitting_has_required_fields(self, fittings_db: dict) -> None:
        for name, fit in fittings_db["fittings"].items():
            assert "category" in fit, f"{name}: missing 'category'"
            assert "description" in fit, f"{name}: missing 'description'"
            assert "K" in fit, f"{name}: missing 'K'"
            assert "default" in fit["K"], f"{name}: K missing 'default'"

    def test_K_defaults_are_positive(self, fittings_db: dict) -> None:
        for name, fit in fittings_db["fittings"].items():
            k = fit["K"]["default"]
            assert k > 0, f"{name}: K default {k} must be positive"

    def test_K_ranges_are_valid(self, fittings_db: dict) -> None:
        for name, fit in fittings_db["fittings"].items():
            k_info = fit["K"]
            if "range" in k_info:
                lo, hi = k_info["range"]
                default = k_info["default"]
                assert lo <= default <= hi, (
                    f"{name}: K default {default} outside range [{lo}, {hi}]"
                )

    def test_fitting_source_keys_reference_valid_sources(
        self, fittings_db: dict
    ) -> None:
        valid_sources = set(fittings_db["_meta"]["sources"].keys())
        for name, fit in fittings_db["fittings"].items():
            k_info = fit["K"]
            if "source" in k_info:
                assert k_info["source"] in valid_sources, (
                    f"{name}: source '{k_info['source']}' not in _meta.sources"
                )


# ── Cross-DB consistency ─────────────────────────────────────────


class TestCrossConsistency:
    def test_material_count_at_least_30(self, materials_db: dict) -> None:
        total = len(materials_db["materials"])
        assert total >= 30, f"Expected >=30 materials, got {total}"

    def test_fitting_count_at_least_30(self, fittings_db: dict) -> None:
        total = len(fittings_db["fittings"])
        assert total >= 30, f"Expected >=30 fittings, got {total}"

    def test_alias_count_at_least_15(self, materials_db: dict) -> None:
        total = len(materials_db["_meta"]["aliases"])
        assert total >= 15, f"Expected >=15 aliases, got {total}"
