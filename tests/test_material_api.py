"""Tests for the new material/fitting API (get_material, get_fitting, etc.)."""

from __future__ import annotations

import pytest

from hydroflow._types import FittingProperties, MaterialProperties
from hydroflow.materials import (
    get_fitting,
    get_material,
    list_fittings,
    list_materials,
    resolve_roughness,
)

# ── get_material() ───────────────────────────────────────────────────


class TestGetMaterial:
    def test_concrete_defaults(self) -> None:
        mat = get_material("concrete")
        assert isinstance(mat, MaterialProperties)
        assert mat.name == "concrete"
        assert mat.category == "closed_conduit"
        assert mat.manning_n == 0.013
        assert mat.hazen_williams_c == 130
        assert mat.condition is None

    def test_concrete_with_condition(self) -> None:
        mat = get_material("concrete", condition="old_rough")
        assert mat.manning_n == 0.016
        assert mat.hazen_williams_c == 100
        assert mat.condition == "old_rough"

    def test_concrete_smooth_alias(self) -> None:
        mat = get_material("concrete_smooth")
        assert mat.name == "concrete"
        assert mat.manning_n == 0.012
        assert mat.condition == "new_smooth"

    def test_concrete_rough_alias(self) -> None:
        mat = get_material("concrete_rough")
        assert mat.name == "concrete"
        assert mat.manning_n == 0.016
        assert mat.condition == "old_rough"

    def test_pvc_no_hazen_williams_none(self) -> None:
        """PVC has hazen_williams_c defined."""
        mat = get_material("pvc")
        assert mat.manning_n == 0.010
        assert mat.hazen_williams_c == 150

    def test_open_channel_no_hazen_williams(self) -> None:
        """Open channel materials don't have Hazen-Williams C."""
        mat = get_material("floodplain")
        assert mat.hazen_williams_c is None

    def test_floodplain_grass_alias(self) -> None:
        mat = get_material("floodplain_grass")
        assert mat.name == "floodplain"
        assert mat.manning_n == 0.035
        assert mat.condition == "grass"

    def test_ductile_iron_new_alias(self) -> None:
        mat = get_material("ductile_iron_new")
        assert mat.name == "ductile_iron"
        assert mat.hazen_williams_c == 140
        assert mat.condition == "cement_lined"

    def test_ductile_iron_old_alias(self) -> None:
        mat = get_material("ductile_iron_old")
        assert mat.name == "ductile_iron"
        assert mat.hazen_williams_c == 100
        assert mat.condition == "unlined"

    def test_cast_iron_new_alias(self) -> None:
        mat = get_material("cast_iron_new")
        assert mat.name == "cast_iron"
        assert mat.hazen_williams_c == 130

    def test_cast_iron_old_alias(self) -> None:
        mat = get_material("cast_iron_old")
        assert mat.name == "cast_iron"
        assert mat.hazen_williams_c == 80

    def test_steel_new_alias(self) -> None:
        mat = get_material("steel_new")
        assert mat.name == "steel"
        assert mat.hazen_williams_c == 140

    def test_steel_riveted_alias(self) -> None:
        mat = get_material("steel_riveted")
        assert mat.name == "steel"
        assert mat.manning_n == 0.017
        assert mat.hazen_williams_c == 110

    def test_case_insensitive(self) -> None:
        mat = get_material("CONCRETE")
        assert mat.manning_n == 0.013

    def test_strips_whitespace(self) -> None:
        mat = get_material("  concrete  ")
        assert mat.manning_n == 0.013

    def test_explicit_condition_overrides_alias(self) -> None:
        """Explicit condition kwarg wins over alias-embedded condition."""
        mat = get_material("concrete_smooth", condition="old_rough")
        assert mat.condition == "old_rough"
        assert mat.manning_n == 0.016

    def test_unknown_material_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown material"):
            get_material("kryptonite")

    def test_unknown_material_fuzzy_match(self) -> None:
        with pytest.raises(ValueError, match="Did you mean"):
            get_material("concrte")

    def test_unknown_condition_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown condition"):
            get_material("concrete", condition="nonexistent")

    def test_manning_n_range_tuple(self) -> None:
        mat = get_material("concrete")
        assert mat.manning_n_range is not None
        assert len(mat.manning_n_range) == 2
        lo, hi = mat.manning_n_range
        assert lo <= mat.manning_n <= hi

    def test_frozen_dataclass(self) -> None:
        mat = get_material("concrete")
        with pytest.raises(AttributeError):
            mat.manning_n = 0.999  # type: ignore[misc]


# ── get_fitting() ────────────────────────────────────────────────────


class TestGetFitting:
    def test_90_elbow(self) -> None:
        fit = get_fitting("90_elbow")
        assert isinstance(fit, FittingProperties)
        assert fit.name == "90_elbow"
        assert fit.K == 0.9
        assert fit.category == "elbow"

    def test_entrance_sharp(self) -> None:
        fit = get_fitting("entrance_sharp")
        assert fit.K == 0.5

    def test_exit(self) -> None:
        fit = get_fitting("exit")
        assert fit.K == 1.0

    def test_gate_valve_open(self) -> None:
        fit = get_fitting("gate_valve_open")
        assert fit.K == 0.2

    def test_case_insensitive(self) -> None:
        fit = get_fitting("CHECK_VALVE")
        assert fit.K == 2.5

    def test_unknown_fitting_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown fitting"):
            get_fitting("magic_valve")

    def test_K_range_tuple(self) -> None:
        fit = get_fitting("90_elbow")
        assert fit.K_range is not None
        lo, hi = fit.K_range
        assert lo <= fit.K <= hi

    def test_frozen_dataclass(self) -> None:
        fit = get_fitting("90_elbow")
        with pytest.raises(AttributeError):
            fit.K = 999.0  # type: ignore[misc]


# ── list functions ───────────────────────────────────────────────────


class TestListFunctions:
    def test_list_materials_returns_sorted(self) -> None:
        names = list_materials()
        assert isinstance(names, list)
        assert names == sorted(names)
        assert len(names) >= 30

    def test_list_materials_contains_known(self) -> None:
        names = list_materials()
        assert "concrete" in names
        assert "pvc" in names
        assert "earth" in names

    def test_list_fittings_returns_sorted(self) -> None:
        names = list_fittings()
        assert isinstance(names, list)
        assert names == sorted(names)
        assert len(names) >= 30

    def test_list_fittings_contains_known(self) -> None:
        names = list_fittings()
        assert "90_elbow" in names
        assert "exit" in names
        assert "check_valve" in names


# ── resolve_roughness with condition ──────────────────────────────────


class TestResolveRoughnessCondition:
    def test_condition_kwarg(self) -> None:
        n = resolve_roughness("concrete", condition="old_rough")
        assert n == 0.016

    def test_condition_kwarg_with_alias(self) -> None:
        """Explicit condition overrides alias."""
        n = resolve_roughness("concrete_smooth", condition="old_rough")
        assert n == 0.016


# ── Legacy dict backwards compatibility ───────────────────────────────


class TestLegacyDicts:
    def test_manning_roughness_dict(self) -> None:
        from hydroflow.materials import MANNING_ROUGHNESS

        assert isinstance(MANNING_ROUGHNESS, dict)
        assert MANNING_ROUGHNESS["concrete"] == 0.013
        assert MANNING_ROUGHNESS["pvc"] == 0.010
        assert MANNING_ROUGHNESS["concrete_smooth"] == 0.012

    def test_hazen_williams_dict(self) -> None:
        from hydroflow.materials import HAZEN_WILLIAMS_C

        assert isinstance(HAZEN_WILLIAMS_C, dict)
        assert HAZEN_WILLIAMS_C["pvc"] == 150
        assert HAZEN_WILLIAMS_C["concrete"] == 130
        assert HAZEN_WILLIAMS_C["ductile_iron_new"] == 140

    def test_minor_loss_dict(self) -> None:
        from hydroflow.materials import MINOR_LOSS_K

        assert isinstance(MINOR_LOSS_K, dict)
        assert MINOR_LOSS_K["90_elbow"] == 0.9
        assert MINOR_LOSS_K["exit"] == 1.0

    def test_package_level_manning(self) -> None:
        import hydroflow as hf

        assert hf.MANNING_ROUGHNESS["concrete"] == 0.013

    def test_package_level_hazen_williams(self) -> None:
        import hydroflow as hf

        assert hf.HAZEN_WILLIAMS_C["pvc"] == 150

    def test_package_level_minor_loss(self) -> None:
        import hydroflow as hf

        assert hf.MINOR_LOSS_K["90_elbow"] == 0.9

    def test_pressure_module_hazen_williams(self) -> None:
        from hydroflow.pressure import HAZEN_WILLIAMS_C

        assert HAZEN_WILLIAMS_C["pvc"] == 150

    def test_pressure_module_minor_loss(self) -> None:
        from hydroflow.pressure import MINOR_LOSS_K

        assert MINOR_LOSS_K["90_elbow"] == 0.9
