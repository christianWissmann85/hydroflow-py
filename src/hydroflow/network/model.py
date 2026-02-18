"""Central water distribution network model.

Users build up a network by adding components one at a time.  The model
validates topology on every mutation and provides a ``validate()`` method
for comprehensive pre-simulation checks.

The ``_to_wntr()`` method creates a fresh WNTR ``WaterNetworkModel``
each time it is called — the HydroFlow model is never mutated by WNTR.
"""

from __future__ import annotations

from typing import Any

from hydroflow.network.components import (
    Junction,
    Pipe,
    Pump,
    Reservoir,
    Tank,
    Valve,
)
from hydroflow.network.errors import (
    TopologyError,
    ValidationError,
)

__all__ = ["WaterNetwork"]


class WaterNetwork:
    """An engineer-friendly water distribution network model.

    Parameters
    ----------
    name : str
        A descriptive name for the network.

    Examples
    --------
    >>> net = WaterNetwork("My Network")
    >>> net.add_junction("J1", elevation=100)
    >>> net.add_reservoir("R1", head=125)
    >>> net.add_pipe("P1", "R1", "J1", length=500, diameter=0.3, roughness=130)
    >>> warnings = net.validate()
    """

    def __init__(self, name: str = "WaterNetwork") -> None:
        self.name = name
        self._junctions: dict[str, Junction] = {}
        self._reservoirs: dict[str, Reservoir] = {}
        self._tanks: dict[str, Tank] = {}
        self._pipes: dict[str, Pipe] = {}
        self._pumps: dict[str, Pump] = {}
        self._valves: dict[str, Valve] = {}
        self._controls: list[dict[str, Any]] = []

    # ── Node accessors ────────────────────────────────────────────────

    @property
    def junctions(self) -> dict[str, Junction]:
        """All junctions (read-only view)."""
        return dict(self._junctions)

    @property
    def reservoirs(self) -> dict[str, Reservoir]:
        """All reservoirs (read-only view)."""
        return dict(self._reservoirs)

    @property
    def tanks(self) -> dict[str, Tank]:
        """All tanks (read-only view)."""
        return dict(self._tanks)

    @property
    def pipes(self) -> dict[str, Pipe]:
        """All pipes (read-only view)."""
        return dict(self._pipes)

    @property
    def pumps(self) -> dict[str, Pump]:
        """All pumps (read-only view)."""
        return dict(self._pumps)

    @property
    def valves(self) -> dict[str, Valve]:
        """All valves (read-only view)."""
        return dict(self._valves)

    @property
    def node_names(self) -> set[str]:
        """Names of all nodes in the network."""
        return set(self._junctions) | set(self._reservoirs) | set(self._tanks)

    @property
    def link_names(self) -> set[str]:
        """Names of all links in the network."""
        return set(self._pipes) | set(self._pumps) | set(self._valves)

    # ── Add methods ───────────────────────────────────────────────────

    def _check_name_unique(self, name: str) -> None:
        """Raise if *name* is already used by any component."""
        all_names = self.node_names | self.link_names
        if name in all_names:
            raise ValidationError(
                f"Name {name!r} is already in use.",
                suggestion="Choose a unique name for each component.",
            )

    def _check_node_exists(self, node_name: str, context: str) -> None:
        """Raise if *node_name* is not a known node."""
        if node_name not in self.node_names:
            raise TopologyError(
                f"Node {node_name!r} does not exist (referenced by {context}).",
                suggestion=f"Add {node_name!r} as a junction, reservoir, or tank first.",
            )

    def add_junction(
        self,
        name: str,
        *,
        elevation: float,
        base_demand: float = 0.0,
    ) -> Junction:
        """Add a demand node.

        Returns the created ``Junction``.
        """
        self._check_name_unique(name)
        j = Junction(name=name, elevation=elevation, base_demand=base_demand)
        self._junctions[name] = j
        return j

    def add_reservoir(self, name: str, *, head: float) -> Reservoir:
        """Add a fixed-head source node.

        Returns the created ``Reservoir``.
        """
        self._check_name_unique(name)
        r = Reservoir(name=name, head=head)
        self._reservoirs[name] = r
        return r

    def add_tank(
        self,
        name: str,
        *,
        elevation: float,
        init_level: float,
        min_level: float,
        max_level: float,
        diameter: float,
    ) -> Tank:
        """Add a storage tank.

        Returns the created ``Tank``.
        """
        self._check_name_unique(name)
        t = Tank(
            name=name,
            elevation=elevation,
            init_level=init_level,
            min_level=min_level,
            max_level=max_level,
            diameter=diameter,
        )
        self._tanks[name] = t
        return t

    def add_pipe(
        self,
        name: str,
        start_node: str,
        end_node: str,
        *,
        length: float,
        diameter: float,
        roughness: float | str,
        minor_loss: float = 0.0,
    ) -> Pipe:
        """Add a pipe connecting two nodes.

        Both *start_node* and *end_node* must already exist in the network.

        Returns the created ``Pipe``.
        """
        self._check_name_unique(name)
        self._check_node_exists(start_node, f"pipe {name!r}")
        self._check_node_exists(end_node, f"pipe {name!r}")
        p = Pipe(
            name=name,
            start_node=start_node,
            end_node=end_node,
            length=length,
            diameter=diameter,
            roughness=roughness,
            minor_loss=minor_loss,
        )
        self._pipes[name] = p
        return p

    def add_pump(
        self,
        name: str,
        start_node: str,
        end_node: str,
        *,
        power: float,
    ) -> Pump:
        """Add a pump.

        Both *start_node* and *end_node* must already exist in the network.

        Returns the created ``Pump``.
        """
        self._check_name_unique(name)
        self._check_node_exists(start_node, f"pump {name!r}")
        self._check_node_exists(end_node, f"pump {name!r}")
        p = Pump(
            name=name,
            start_node=start_node,
            end_node=end_node,
            power=power,
        )
        self._pumps[name] = p
        return p

    def add_valve(
        self,
        name: str,
        start_node: str,
        end_node: str,
        *,
        diameter: float,
        setting: float,
        valve_type: str = "PRV",
        minor_loss: float = 0.0,
    ) -> Valve:
        """Add a valve.

        Both *start_node* and *end_node* must already exist in the network.

        Returns the created ``Valve``.
        """
        self._check_name_unique(name)
        self._check_node_exists(start_node, f"valve {name!r}")
        self._check_node_exists(end_node, f"valve {name!r}")
        v = Valve(
            name=name,
            start_node=start_node,
            end_node=end_node,
            diameter=diameter,
            setting=setting,
            valve_type=valve_type,
            minor_loss=minor_loss,
        )
        self._valves[name] = v
        return v

    # ── Controls ──────────────────────────────────────────────────────

    def add_time_control(
        self,
        link_name: str,
        *,
        status: str,
        at: str | int | float,
    ) -> None:
        """Schedule a link status change at a specific time.

        Parameters
        ----------
        link_name : str
            Name of the link (pipe, pump, or valve) to control.
        status : str
            Target status: ``"OPEN"`` or ``"CLOSED"``.
        at : str | int | float
            Time to apply (e.g. ``"22:00"``, ``"6h"``, or seconds).
        """
        from hydroflow.network.controls import TimeControl

        if link_name not in self.link_names:
            raise TopologyError(
                f"Link {link_name!r} does not exist.",
                suggestion="Add the link before creating a control for it.",
            )
        ctrl = TimeControl(link_name=link_name, status=status, at=at)
        self._controls.append(ctrl._to_control_dict(len(self._controls)))

    def add_conditional_control(
        self,
        link_name: str,
        *,
        status: str,
        condition: tuple[str, str, str, float],
    ) -> None:
        """Change link status when a node condition is met.

        Parameters
        ----------
        link_name : str
            Name of the link to control.
        status : str
            Target status: ``"OPEN"`` or ``"CLOSED"``.
        condition : tuple[str, str, str, float]
            A 4-tuple of ``(node_name, attribute, operator, threshold)``.
            Example: ``("Tank_1", "level", "<", 3.0)``.
        """
        from hydroflow.network.controls import ConditionalControl

        if link_name not in self.link_names:
            raise TopologyError(
                f"Link {link_name!r} does not exist.",
                suggestion="Add the link before creating a control for it.",
            )
        node_name, attribute, operator, threshold = condition
        ctrl = ConditionalControl(
            link_name=link_name,
            status=status,
            node_name=node_name,
            attribute=attribute,
            operator=operator,
            threshold=threshold,
        )
        self._controls.append(ctrl._to_control_dict(len(self._controls)))

    # ── Validation ────────────────────────────────────────────────────

    def validate(self) -> list[str]:
        """Run comprehensive validation checks.

        Returns a list of warning strings.  Raises on critical errors.

        Checks performed:

        - At least one source node (reservoir or tank)
        - No disconnected nodes (every node appears in at least one link)
        - Warns about dead-end nodes (connected to only one link)
        """
        warnings: list[str] = []

        # Must have at least one source
        if not self._reservoirs and not self._tanks:
            raise ValidationError(
                "Network has no source nodes (reservoirs or tanks).",
                suggestion="Add at least one reservoir or tank.",
            )

        # Check for disconnected nodes
        connected_nodes: set[str] = set()
        link_count: dict[str, int] = {n: 0 for n in self.node_names}
        for pipe in self._pipes.values():
            connected_nodes.add(pipe.start_node)
            connected_nodes.add(pipe.end_node)
            link_count[pipe.start_node] = link_count.get(pipe.start_node, 0) + 1
            link_count[pipe.end_node] = link_count.get(pipe.end_node, 0) + 1
        for pump in self._pumps.values():
            connected_nodes.add(pump.start_node)
            connected_nodes.add(pump.end_node)
            link_count[pump.start_node] = link_count.get(pump.start_node, 0) + 1
            link_count[pump.end_node] = link_count.get(pump.end_node, 0) + 1
        for valve in self._valves.values():
            connected_nodes.add(valve.start_node)
            connected_nodes.add(valve.end_node)
            link_count[valve.start_node] = link_count.get(valve.start_node, 0) + 1
            link_count[valve.end_node] = link_count.get(valve.end_node, 0) + 1

        disconnected = self.node_names - connected_nodes
        if disconnected:
            raise ValidationError(
                f"Disconnected nodes: {', '.join(sorted(disconnected))}.",
                suggestion="Connect all nodes with pipes, pumps, or valves.",
            )

        # Warn about dead-ends (only 1 connection, excluding sources)
        for node, count in sorted(link_count.items()):
            if count == 1 and node not in self._reservoirs and node not in self._tanks:
                warnings.append(
                    f"Node {node!r} is a dead-end (connected to only 1 link)."
                )

        return warnings

    # ── WNTR conversion ──────────────────────────────────────────────

    def _to_wntr(self) -> Any:
        """Create a fresh WNTR ``WaterNetworkModel`` from this network.

        This is a private method — users should use :func:`simulate` instead.
        Each call creates a brand-new WNTR model (no state leakage).

        Returns
        -------
        wntr.network.WaterNetworkModel
            A fully configured WNTR model ready for simulation.
        """
        try:
            import wntr
        except ImportError:
            msg = (
                "WNTR is required for network simulation. "
                "Install it with: pip install hydroflow-py[epanet]"
            )
            raise ImportError(msg) from None

        wn = wntr.network.WaterNetworkModel()

        # Add nodes
        for junc in self._junctions.values():
            wn.add_junction(**junc.to_wntr_kwargs())
        for res in self._reservoirs.values():
            wn.add_reservoir(**res.to_wntr_kwargs())
        for tank in self._tanks.values():
            wn.add_tank(**tank.to_wntr_kwargs())

        # Add links
        for pipe in self._pipes.values():
            wn.add_pipe(**pipe.to_wntr_kwargs())
        for pump in self._pumps.values():
            wn.add_pump(**pump.to_wntr_kwargs())
        for valve in self._valves.values():
            wn.add_valve(**valve.to_wntr_kwargs())

        # Apply controls
        for ctrl in self._controls:
            self._apply_control(wn, ctrl)

        return wn

    def _apply_control(self, wn: Any, ctrl: dict[str, Any]) -> None:
        """Apply a single control dict to a WNTR model."""
        try:
            import wntr
        except ImportError:
            return

        if ctrl["type"] == "time":
            link = wn.get_link(ctrl["link_name"])
            action = wntr.network.controls.ControlAction(
                link, "status", ctrl["status_code"]
            )
            control = wntr.network.controls.Control.at_time(
                wn, ctrl["at_seconds"], action
            )
            wn.add_control(ctrl["control_name"], control)
        elif ctrl["type"] == "conditional":
            link = wn.get_link(ctrl["link_name"])
            node = wn.get_node(ctrl["node_name"])
            action = wntr.network.controls.ControlAction(
                link, "status", ctrl["status_code"]
            )
            condition = wntr.network.controls.ValueCondition(
                node, ctrl["attribute"], ctrl["operator"], ctrl["threshold"]
            )
            control = wntr.network.controls.Control(condition, action)
            wn.add_control(ctrl["control_name"], control)

    def __repr__(self) -> str:
        n_nodes = len(self._junctions) + len(self._reservoirs) + len(self._tanks)
        n_links = len(self._pipes) + len(self._pumps) + len(self._valves)
        return f"WaterNetwork({self.name!r}, nodes={n_nodes}, links={n_links})"
