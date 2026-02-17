"""Tests for hydroflow.materials."""

import pytest

from hydroflow.materials import resolve_roughness


class TestResolveRoughness:
    def test_float_passthrough(self) -> None:
        assert resolve_roughness(0.015) == 0.015

    def test_concrete(self) -> None:
        assert resolve_roughness("concrete") == 0.013

    def test_pvc(self) -> None:
        assert resolve_roughness("pvc") == 0.010

    def test_hdpe(self) -> None:
        assert resolve_roughness("hdpe") == 0.012

    def test_case_insensitive(self) -> None:
        assert resolve_roughness("CONCRETE") == 0.013
        assert resolve_roughness("Concrete") == 0.013

    def test_strips_whitespace(self) -> None:
        assert resolve_roughness("  concrete  ") == 0.013

    def test_unknown_with_close_match(self) -> None:
        with pytest.raises(ValueError, match="Did you mean"):
            resolve_roughness("concrte")  # typo

    def test_unknown_no_close_match(self) -> None:
        with pytest.raises(ValueError, match="Available"):
            resolve_roughness("kryptonite")

    def test_negative_roughness_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            resolve_roughness(-0.01)

    def test_zero_roughness_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            resolve_roughness(0.0)
