"""Tests for project-level config via hydroflow.toml (Phase 1.4).

Covers TOML loading, auto-discovery, custom materials/fittings,
alias overrides, and standard integration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from hydroflow.materials import (
    clear_project_config,
    get_fitting,
    get_material,
    get_standard,
    list_materials,
    load_project_config,
    resolve_roughness,
    set_standard,
)


@pytest.fixture(autouse=True)
def _reset_state():
    """Ensure every test starts clean."""
    set_standard(None)
    clear_project_config()
    yield
    set_standard(None)
    clear_project_config()


# ── Helpers ───────────────────────────────────────────────────────


def _write_toml(tmp_path: Path, content: str) -> Path:
    """Write a hydroflow.toml and return its path."""
    toml_file = tmp_path / "hydroflow.toml"
    toml_file.write_text(content, encoding="utf-8")
    return toml_file


# ── Loading ───────────────────────────────────────────────────────


class TestLoadProjectConfig:
    def test_explicit_path(self, tmp_path: Path) -> None:
        toml = _write_toml(tmp_path, "[hydroflow]\n")
        load_project_config(toml)
        # Should not raise

    def test_missing_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_project_config(tmp_path / "nonexistent.toml")

    def test_missing_hydroflow_section_raises(self, tmp_path: Path) -> None:
        toml = _write_toml(tmp_path, "[other]\nkey = 1\n")
        with pytest.raises(ValueError, match="\\[hydroflow\\] section"):
            load_project_config(toml)

    def test_auto_discovery(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _write_toml(tmp_path, "[hydroflow]\n")
        subdir = tmp_path / "subproject"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        load_project_config()  # Should find ../hydroflow.toml

    def test_auto_discovery_fails_when_no_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        with pytest.raises(FileNotFoundError):
            load_project_config()


# ── Material overrides ────────────────────────────────────────────


class TestMaterialOverrides:
    def test_override_manning_n(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.015 }
""",
        )
        load_project_config(toml)
        mat = get_material("concrete")
        assert mat.manning_n == pytest.approx(0.015)

    def test_override_description(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
description = "Aged infrastructure concrete"
""",
        )
        load_project_config(toml)
        mat = get_material("concrete")
        assert mat.description == "Aged infrastructure concrete"

    def test_add_custom_material(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.custom_liner]
category = "closed_conduit"
description = "Proprietary CIPP liner"
manning_n = { default = 0.010, range = [0.009, 0.011] }
""",
        )
        load_project_config(toml)
        assert "custom_liner" in list_materials()
        mat = get_material("custom_liner")
        assert mat.manning_n == pytest.approx(0.010)
        assert mat.category == "closed_conduit"

    def test_add_condition_via_project(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete.conditions.site_tested]
manning_n = 0.0145
""",
        )
        load_project_config(toml)
        mat = get_material("concrete", condition="site_tested")
        assert mat.manning_n == pytest.approx(0.0145)

    def test_non_overridden_materials_unchanged(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.099 }
""",
        )
        load_project_config(toml)
        pvc = get_material("pvc")
        assert pvc.manning_n == pytest.approx(0.010)

    def test_resolve_roughness_uses_project_config(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.015 }
""",
        )
        load_project_config(toml)
        assert resolve_roughness("concrete") == pytest.approx(0.015)


# ── Fitting overrides ────────────────────────────────────────────


class TestFittingOverrides:
    def test_add_custom_fitting(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.fittings.custom_bend]
category = "elbow"
description = "Custom fabricated bend"
K = { default = 0.7, range = [0.5, 0.9] }
""",
        )
        load_project_config(toml)
        fit = get_fitting("custom_bend")
        assert pytest.approx(0.7) == fit.K
        assert fit.category == "elbow"


# ── Alias overrides ──────────────────────────────────────────────


class TestAliasOverrides:
    def test_add_project_alias(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete.conditions.site_tested]
manning_n = 0.0145

[hydroflow.aliases]
site_concrete = { material = "concrete", condition = "site_tested" }
""",
        )
        load_project_config(toml)
        mat = get_material("site_concrete")
        assert mat.manning_n == pytest.approx(0.0145)
        assert mat.name == "concrete"
        assert mat.condition == "site_tested"


# ── Standard integration ─────────────────────────────────────────


class TestStandardIntegration:
    def test_toml_sets_standard(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]
standard = "din_en"
""",
        )
        load_project_config(toml)
        assert get_standard() == "din_en"
        # DIN/EN concrete default
        assert get_material("concrete").manning_n == pytest.approx(0.014)

    def test_project_overrides_on_top_of_standard(self, tmp_path: Path) -> None:
        """Merge chain: base < din_en < project."""
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]
standard = "din_en"

[hydroflow.materials.concrete]
manning_n = { default = 0.016 }
""",
        )
        load_project_config(toml)
        mat = get_material("concrete")
        # Project override wins over DIN/EN
        assert mat.manning_n == pytest.approx(0.016)
        # DIN/EN description is preserved
        assert "DIN EN 1916" in mat.description


# ── Clearing ──────────────────────────────────────────────────────


class TestClearProjectConfig:
    def test_clear_restores_base(self, tmp_path: Path) -> None:
        toml = _write_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.099 }
""",
        )
        load_project_config(toml)
        assert get_material("concrete").manning_n == pytest.approx(0.099)

        clear_project_config()
        assert get_material("concrete").manning_n == pytest.approx(0.013)
