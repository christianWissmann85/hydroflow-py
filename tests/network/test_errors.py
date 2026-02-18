"""Tests for hydroflow.network.errors."""

import pytest

from hydroflow.network.errors import (
    ComponentError,
    NetworkError,
    SimulationError,
    TopologyError,
    ValidationError,
)


class TestNetworkError:
    def test_message_only(self) -> None:
        err = NetworkError("something broke")
        assert str(err) == "something broke"
        assert err.suggestion == ""

    def test_message_with_suggestion(self) -> None:
        err = NetworkError("bad input", suggestion="try again")
        assert "bad input" in str(err)
        assert "try again" in str(err)
        assert err.suggestion == "try again"

    def test_is_exception(self) -> None:
        assert issubclass(NetworkError, Exception)

    def test_raise_and_catch(self) -> None:
        with pytest.raises(NetworkError, match="oops"):
            raise NetworkError("oops")


class TestTopologyError:
    def test_is_network_error(self) -> None:
        assert issubclass(TopologyError, NetworkError)

    def test_with_suggestion(self) -> None:
        err = TopologyError(
            "Node J1 not found",
            suggestion="Add the junction before referencing it in a pipe.",
        )
        assert err.suggestion.startswith("Add")
        assert "J1" in str(err)


class TestValidationError:
    def test_is_network_error(self) -> None:
        assert issubclass(ValidationError, NetworkError)

    def test_raise(self) -> None:
        with pytest.raises(ValidationError):
            raise ValidationError("duplicate name 'P1'")


class TestComponentError:
    def test_is_network_error(self) -> None:
        assert issubclass(ComponentError, NetworkError)

    def test_with_suggestion(self) -> None:
        err = ComponentError(
            "Pipe diameter must be positive, got -0.3",
            suggestion="Use a positive value in active units (e.g. 0.3 m).",
        )
        assert "positive" in err.suggestion


class TestSimulationError:
    def test_is_network_error(self) -> None:
        assert issubclass(SimulationError, NetworkError)

    def test_catch_as_network_error(self) -> None:
        with pytest.raises(NetworkError):
            raise SimulationError(
                "EPANET solver failed",
                suggestion="Check that the network has at least one source node.",
            )
