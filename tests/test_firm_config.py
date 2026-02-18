"""Tests for firm-level config via ~/.hydroflow/firm_config.toml (Phase 1.5).

Covers auto-discovery, material/fitting/alias overrides, standard interaction,
and the full merge chain: base < standard < firm_config < project_config.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import hydroflow.materials as mat
from hydroflow.materials import (
    clear_project_config,
    get_fitting,
    get_material,
    list_materials,
    load_project_config,
    set_standard,
)


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Ensure every test starts clean."""
    set_standard(None)
    mat._local.standard_explicit = False  # reset to "never called" state
    clear_project_config()
    mat._firm_config = None
    mat._firm_config_loaded = False
    mat._local.final_db = None
    yield  # type: ignore[misc]
    set_standard(None)
    mat._local.standard_explicit = False
    clear_project_config()
    mat._firm_config = None
    mat._firm_config_loaded = False
    mat._local.final_db = None


@pytest.fixture()
def firm_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up a fake ~/.hydroflow/ directory and return it."""
    hydroflow_dir = tmp_path / ".hydroflow"
    hydroflow_dir.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return hydroflow_dir


def _write_firm_toml(firm_dir: Path, content: str) -> Path:
    """Write a firm_config.toml and return its path."""
    toml_file = firm_dir / "firm_config.toml"
    toml_file.write_text(content, encoding="utf-8")
    return toml_file


def _write_project_toml(tmp_path: Path, content: str) -> Path:
    """Write a hydroflow.toml project config and return its path."""
    toml_file = tmp_path / "hydroflow.toml"
    toml_file.write_text(content, encoding="utf-8")
    return toml_file


# ── Auto-discovery ───────────────────────────────────────────────


class TestAutoDiscovery:
    def test_no_firm_config_is_noop(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No ~/.hydroflow/ dir -> base values unchanged."""
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        concrete = get_material("concrete")
        assert concrete.manning_n == pytest.approx(0.013)

    def test_missing_hydroflow_section_ignored(self, firm_config: Path) -> None:
        """Firm TOML without [hydroflow] -> silently ignored."""
        _write_firm_toml(firm_config, "[other]\nkey = 1\n")
        concrete = get_material("concrete")
        assert concrete.manning_n == pytest.approx(0.013)


# ── Material overrides ───────────────────────────────────────────


class TestFirmMaterialOverrides:
    def test_firm_config_overrides_material(self, firm_config: Path) -> None:
        """Firm sets concrete.manning_n.default = 0.014 -> reflected."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.014 }
""",
        )
        concrete = get_material("concrete")
        assert concrete.manning_n == pytest.approx(0.014)

    def test_firm_config_adds_material(self, firm_config: Path) -> None:
        """Firm adds firm_custom_pipe -> appears in list_materials()."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]

[hydroflow.materials.firm_custom_pipe]
category = "closed_conduit"
description = "Firm standard HDPE pipe"
manning_n = { default = 0.011, range = [0.010, 0.012] }
""",
        )
        assert "firm_custom_pipe" in list_materials()
        pipe = get_material("firm_custom_pipe")
        assert pipe.manning_n == pytest.approx(0.011)
        assert pipe.category == "closed_conduit"


# ── Standard interaction ─────────────────────────────────────────


class TestFirmStandardInteraction:
    def test_firm_config_sets_standard(self, firm_config: Path) -> None:
        """Firm sets standard = 'din_en' -> DIN/EN overrides active."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]
standard = "din_en"
""",
        )
        concrete = get_material("concrete")
        # DIN/EN default for concrete is 0.014
        assert concrete.manning_n == pytest.approx(0.014)

    def test_explicit_standard_overrides_firm(self, firm_config: Path) -> None:
        """Firm sets standard = 'din_en', user calls set_standard(None) -> base values."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]
standard = "din_en"
""",
        )
        # Explicitly set no standard — overrides firm
        set_standard(None)
        concrete = get_material("concrete")
        assert concrete.manning_n == pytest.approx(0.013)


# ── Project overrides firm ────────────────────────────────────────


class TestProjectOverridesFirm:
    def test_project_overrides_firm(
        self, tmp_path: Path, firm_config: Path
    ) -> None:
        """Firm sets n=0.014, project sets n=0.015 -> project wins."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.014 }
""",
        )
        project_toml = _write_project_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.015 }
""",
        )
        load_project_config(project_toml)
        concrete = get_material("concrete")
        assert concrete.manning_n == pytest.approx(0.015)


# ── Full merge chain ──────────────────────────────────────────────


class TestFullChain:
    def test_full_chain(self, tmp_path: Path, firm_config: Path) -> None:
        """Firm + standard + project all active -> correct merge order.

        Chain: base < standard(din_en) < firm < project
        - DIN/EN sets concrete n=0.014
        - Firm adds firm_custom_pipe (n=0.011)
        - Project overrides concrete n=0.016
        - Result: concrete=0.016, firm_custom_pipe=0.011
        """
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]
standard = "din_en"

[hydroflow.materials.firm_custom_pipe]
category = "closed_conduit"
description = "Firm HDPE"
manning_n = { default = 0.011 }
""",
        )
        project_toml = _write_project_toml(
            tmp_path,
            """\
[hydroflow]

[hydroflow.materials.concrete]
manning_n = { default = 0.016 }
""",
        )
        load_project_config(project_toml)

        # Project override wins for concrete
        assert get_material("concrete").manning_n == pytest.approx(0.016)
        # Firm custom material still accessible
        assert "firm_custom_pipe" in list_materials()
        assert get_material("firm_custom_pipe").manning_n == pytest.approx(0.011)


# ── Fitting overrides ────────────────────────────────────────────


class TestFirmFittingOverride:
    def test_firm_config_fitting_override(self, firm_config: Path) -> None:
        """Firm adds custom fitting -> accessible via get_fitting()."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]

[hydroflow.fittings.firm_custom_valve]
category = "valve"
description = "Firm standard butterfly valve"
K = { default = 0.35, range = [0.3, 0.4] }
""",
        )
        valve = get_fitting("firm_custom_valve")
        assert pytest.approx(0.35) == valve.K
        assert valve.category == "valve"


# ── Alias support ────────────────────────────────────────────────


class TestFirmAlias:
    def test_firm_config_alias(self, firm_config: Path) -> None:
        """Firm adds alias -> resolvable via get_material()."""
        _write_firm_toml(
            firm_config,
            """\
[hydroflow]

[hydroflow.aliases]
acme_concrete = { material = "concrete", condition = "old_rough" }
""",
        )
        mat_result = get_material("acme_concrete")
        assert mat_result.name == "concrete"
        assert mat_result.condition == "old_rough"
