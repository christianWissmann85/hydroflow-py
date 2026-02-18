"""Tests for the standards/jurisdiction layer (Phase 1.3).

Covers set_standard / get_standard / list_standards,
override behaviour, thread safety, and cache correctness.
"""

from __future__ import annotations

import threading

import pytest

from hydroflow.materials import (
    get_material,
    get_standard,
    list_materials,
    list_standards,
    set_standard,
)


@pytest.fixture(autouse=True)
def _reset_standard():
    """Ensure every test starts with no standard set."""
    set_standard(None)
    yield
    set_standard(None)


# ── Discovery ─────────────────────────────────────────────────────


class TestListStandards:
    def test_returns_list(self) -> None:
        result = list_standards()
        assert isinstance(result, list)

    def test_din_en_is_available(self) -> None:
        assert "din_en" in list_standards()

    def test_sorted(self) -> None:
        result = list_standards()
        assert result == sorted(result)


# ── set / get ─────────────────────────────────────────────────────


class TestSetGetStandard:
    def test_default_is_none(self) -> None:
        assert get_standard() is None

    def test_set_and_get(self) -> None:
        set_standard("din_en")
        assert get_standard() == "din_en"

    def test_reset_to_none(self) -> None:
        set_standard("din_en")
        set_standard(None)
        assert get_standard() is None

    def test_unknown_standard_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown standard"):
            set_standard("nonexistent_standard")


# ── Override behaviour ────────────────────────────────────────────


class TestStandardOverrides:
    def test_concrete_manning_n_changes_with_din_en(self) -> None:
        base = get_material("concrete").manning_n
        assert base == pytest.approx(0.013)

        set_standard("din_en")
        din = get_material("concrete").manning_n
        assert din == pytest.approx(0.014)

    def test_concrete_description_changes_with_din_en(self) -> None:
        set_standard("din_en")
        mat = get_material("concrete")
        assert "DIN EN 1916" in mat.description

    def test_ductile_iron_hazen_williams_changes(self) -> None:
        base = get_material("ductile_iron").hazen_williams_c
        assert base == pytest.approx(140)

        set_standard("din_en")
        din = get_material("ductile_iron").hazen_williams_c
        assert din == pytest.approx(130)

    def test_standard_adds_new_material(self) -> None:
        """DIN/EN adds 'stoneware' which doesn't exist in the base."""
        base_list = list_materials()
        assert "stoneware" not in base_list

        set_standard("din_en")
        din_list = list_materials()
        assert "stoneware" in din_list

        stoneware = get_material("stoneware")
        assert stoneware.manning_n == pytest.approx(0.013)
        assert stoneware.category == "closed_conduit"

    def test_non_overridden_material_unchanged(self) -> None:
        """Materials not mentioned in the standard keep base values."""
        base_pvc = get_material("pvc")

        set_standard("din_en")
        din_pvc = get_material("pvc")

        assert base_pvc.manning_n == din_pvc.manning_n
        assert base_pvc.hazen_williams_c == din_pvc.hazen_williams_c

    def test_reset_restores_base(self) -> None:
        set_standard("din_en")
        assert get_material("concrete").manning_n == pytest.approx(0.014)

        set_standard(None)
        assert get_material("concrete").manning_n == pytest.approx(0.013)

    def test_conditions_preserved_through_override(self) -> None:
        """Standard overrides base values but conditions still work."""
        set_standard("din_en")
        # Concrete conditions should still be accessible
        mat = get_material("concrete", condition="old_rough")
        assert mat.manning_n == pytest.approx(0.016)


# ── Cache correctness ────────────────────────────────────────────


class TestStandardCache:
    def test_switching_standards_uses_cache(self) -> None:
        """Switching back and forth should hit the cache."""
        set_standard("din_en")
        _ = get_material("concrete")  # Populate cache

        set_standard(None)
        _ = get_material("concrete")  # Populate base cache

        set_standard("din_en")
        mat = get_material("concrete")
        assert mat.manning_n == pytest.approx(0.014)


# ── Thread safety ─────────────────────────────────────────────────


class TestThreadSafety:
    def test_standards_are_thread_local(self) -> None:
        """Each thread has its own standard setting."""
        results: dict[str, float] = {}
        errors: list[str] = []

        def worker_din() -> None:
            try:
                set_standard("din_en")
                mat = get_material("concrete")
                results["din"] = mat.manning_n
            except Exception as e:
                errors.append(str(e))

        def worker_base() -> None:
            try:
                set_standard(None)
                mat = get_material("concrete")
                results["base"] = mat.manning_n
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=worker_din)
        t2 = threading.Thread(target=worker_base)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors, f"Thread errors: {errors}"
        assert results["din"] == pytest.approx(0.014)
        assert results["base"] == pytest.approx(0.013)
