"""Engineer-friendly simulation result wrapper.

Wraps WNTR's raw result DataFrames with ``pd.TimedeltaIndex``,
meaningful column names, and a :meth:`health_check` method.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hydroflow.network.model import WaterNetwork

__all__ = ["NetworkResults"]


@dataclass
class NetworkResults:
    """Simulation results with engineer-friendly access.

    Attributes
    ----------
    pressures : pd.DataFrame
        Node pressures over time (index = ``TimedeltaIndex``).
    flows : pd.DataFrame
        Link flow rates over time (index = ``TimedeltaIndex``).
    velocities : pd.DataFrame
        Link velocities over time (index = ``TimedeltaIndex``).
    heads : pd.DataFrame
        Node hydraulic heads over time (index = ``TimedeltaIndex``).
    demands : pd.DataFrame
        Node demands over time (index = ``TimedeltaIndex``).
    """

    pressures: Any  # pd.DataFrame
    flows: Any  # pd.DataFrame
    velocities: Any  # pd.DataFrame
    heads: Any  # pd.DataFrame
    demands: Any  # pd.DataFrame
    _network_name: str = field(default="", repr=False)

    @classmethod
    def _from_wntr(cls, raw: Any, network: WaterNetwork) -> NetworkResults:
        """Construct from WNTR simulation results.

        Converts raw second-based integer index to ``pd.TimedeltaIndex``.
        """
        import pandas as pd

        pressures = raw.node["pressure"]
        heads = raw.node["head"]
        demands = raw.node["demand"]
        flows = raw.link["flowrate"]
        velocities = raw.link["velocity"]

        # Convert index to TimedeltaIndex
        for df in (pressures, heads, demands, flows, velocities):
            df.index = pd.to_timedelta(df.index, unit="s")

        return cls(
            pressures=pressures,
            flows=flows,
            velocities=velocities,
            heads=heads,
            demands=demands,
            _network_name=network.name,
        )

    def health_check(
        self,
        *,
        min_pressure: float = 0.0,
        max_velocity: float = 3.0,
    ) -> list[str]:
        """Run basic health checks on the simulation results.

        Parameters
        ----------
        min_pressure : float
            Minimum acceptable pressure (default 0 = no negative pressures).
        max_velocity : float
            Maximum acceptable velocity in m/s (default 3.0).

        Returns
        -------
        list[str]
            Warning messages for any issues found.
        """
        warnings: list[str] = []

        # Negative pressures
        neg_mask = self.pressures < min_pressure
        if neg_mask.any().any():
            neg_nodes = list(self.pressures.columns[neg_mask.any()])
            min_p = self.pressures.min().min()
            warnings.append(
                f"Negative pressure detected at node(s): "
                f"{', '.join(str(n) for n in neg_nodes)} "
                f"(min = {min_p:.2f})."
            )

        # Excessive velocity
        high_mask = self.velocities.abs() > max_velocity
        if high_mask.any().any():
            high_links = list(self.velocities.columns[high_mask.any()])
            max_v = self.velocities.abs().max().max()
            warnings.append(
                f"Velocity exceeds {max_velocity} m/s in link(s): "
                f"{', '.join(str(n) for n in high_links)} "
                f"(max = {max_v:.2f} m/s)."
            )

        return warnings

    def __repr__(self) -> str:
        n_nodes = len(self.pressures.columns)
        n_links = len(self.flows.columns)
        n_steps = len(self.pressures)
        return (
            f"NetworkResults("
            f"nodes={n_nodes}, links={n_links}, timesteps={n_steps})"
        )
