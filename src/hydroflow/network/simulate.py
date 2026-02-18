"""Run EPANET simulations via WNTR and return engineer-friendly results.

The :func:`simulate` function is the main entry point.  It takes a
:class:`~hydroflow.network.model.WaterNetwork`, converts it to a WNTR
model, runs EPANET (or the WNTR pressure-driven solver), and wraps the
raw results in a :class:`NetworkResults` object.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hydroflow.network._time import parse_duration
from hydroflow.network.errors import SimulationError

if TYPE_CHECKING:
    from hydroflow.network.model import WaterNetwork
    from hydroflow.network.results import NetworkResults

__all__ = ["simulate"]


def simulate(
    network: WaterNetwork,
    *,
    duration: str | int | float = "24h",
    timestep: str | int | float = "1h",
    backend: str = "epanet",
) -> NetworkResults:
    """Run a hydraulic simulation on the network.

    Parameters
    ----------
    network : WaterNetwork
        The network model to simulate.
    duration : str | int | float
        Simulation duration.  String (``"24h"``, ``"3 days"``) or seconds.
    timestep : str | int | float
        Hydraulic time step.  String (``"1h"``, ``"15min"``) or seconds.
    backend : str
        Solver backend: ``"epanet"`` (default, faster) or ``"wntr"``
        (pressure-driven demand support).

    Returns
    -------
    NetworkResults
        Wrapped simulation results with unit-aware DataFrames.

    Raises
    ------
    SimulationError
        If the solver fails.
    ImportError
        If WNTR is not installed.
    """
    try:
        import wntr
    except ImportError:
        msg = (
            "WNTR is required for network simulation. "
            "Install it with: pip install hydroflow-py[epanet]"
        )
        raise ImportError(msg) from None

    from hydroflow.network.results import NetworkResults

    dur_s = parse_duration(duration)
    ts_s = parse_duration(timestep)

    # Build a fresh WNTR model
    wn: Any = network._to_wntr()
    wn.options.time.duration = int(dur_s)
    wn.options.time.hydraulic_timestep = int(ts_s)
    wn.options.time.report_timestep = int(ts_s)

    # Select backend
    if backend == "epanet":
        sim = wntr.sim.EpanetSimulator(wn)
    elif backend == "wntr":
        sim = wntr.sim.WNTRSimulator(wn)
    else:
        raise SimulationError(
            f"Unknown backend {backend!r}.",
            suggestion="Use 'epanet' or 'wntr'.",
        )

    # Run
    try:
        raw = sim.run_sim()
    except Exception as exc:
        raise SimulationError(
            f"Simulation failed: {exc}",
            suggestion=(
                "Check that the network has at least one source node, "
                "all pipes are connected, and parameters are physically reasonable."
            ),
        ) from exc

    return NetworkResults._from_wntr(raw, network)
