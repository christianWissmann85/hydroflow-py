"""Read and write EPANET ``.inp`` files for interoperability.

Leverages WNTR's INP parser internally — we don't reinvent the wheel.

Functions
---------
read_inp
    Read an EPANET ``.inp`` file into a :class:`WaterNetwork`.
write_inp
    Write a :class:`WaterNetwork` to an EPANET ``.inp`` file.
from_wntr
    Convert an existing ``wntr.network.WaterNetworkModel`` to a
    :class:`WaterNetwork`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from hydroflow.network.model import WaterNetwork

__all__ = [
    "from_wntr",
    "read_inp",
    "write_inp",
]


def _import_wntr() -> Any:
    """Lazy-import WNTR, raising a clear error if missing."""
    try:
        import wntr
    except ImportError:
        msg = (
            "WNTR is required for INP file I/O. "
            "Install it with: pip install hydroflow-py[epanet]"
        )
        raise ImportError(msg) from None
    return wntr


def from_wntr(wn: Any) -> WaterNetwork:
    """Convert a WNTR ``WaterNetworkModel`` to a HydroFlow :class:`WaterNetwork`.

    Parameters
    ----------
    wn : wntr.network.WaterNetworkModel
        An existing WNTR model.

    Returns
    -------
    WaterNetwork
        The equivalent HydroFlow model.
    """
    net = WaterNetwork(name=wn.name if wn.name else "Imported")

    # Junctions
    for name, node in wn.junctions():
        net.add_junction(name, elevation=node.elevation, base_demand=node.base_demand)

    # Reservoirs
    for name, node in wn.reservoirs():
        net.add_reservoir(name, head=node.base_head)

    # Tanks
    for name, node in wn.tanks():
        net.add_tank(
            name,
            elevation=node.elevation,
            init_level=node.init_level,
            min_level=node.min_level,
            max_level=node.max_level,
            diameter=node.diameter,
        )

    # Pipes
    for name, link in wn.pipes():
        net.add_pipe(
            name,
            link.start_node_name,
            link.end_node_name,
            length=link.length,
            diameter=link.diameter,
            roughness=link.roughness,
            minor_loss=link.minor_loss,
        )

    # Pumps
    for name, link in wn.pumps():
        if hasattr(link, "power") and link.power is not None and link.power > 0:
            net.add_pump(
                name,
                link.start_node_name,
                link.end_node_name,
                power=link.power,
            )

    # Valves
    for name, link in wn.valves():
        net.add_valve(
            name,
            link.start_node_name,
            link.end_node_name,
            diameter=link.diameter,
            setting=link.setting,
            valve_type=link.valve_type,
            minor_loss=link.minor_loss,
        )

    return net


def read_inp(path: str | Path) -> WaterNetwork:
    """Read an EPANET ``.inp`` file into a :class:`WaterNetwork`.

    Parameters
    ----------
    path : str or Path
        Path to the ``.inp`` file.

    Returns
    -------
    WaterNetwork
        The parsed network.
    """
    wntr = _import_wntr()
    wn = wntr.network.WaterNetworkModel(str(path))
    return from_wntr(wn)


def write_inp(network: WaterNetwork, path: str | Path) -> None:
    """Write a :class:`WaterNetwork` to an EPANET ``.inp`` file.

    Parameters
    ----------
    network : WaterNetwork
        The network to export.
    path : str or Path
        Destination file path.
    """
    wn = network._to_wntr()
    wn.write_inpfile(str(path))
