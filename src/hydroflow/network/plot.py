"""Network visualization with matplotlib.

Provides ``plot_network()`` for topology plots and ``plot_results()``
for coloring nodes/links by simulation results at a given timestep.

Dependencies (``matplotlib``, ``networkx``) are imported lazily so the
rest of the package works without them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hydroflow.network.model import WaterNetwork
    from hydroflow.network.results import NetworkResults

__all__ = [
    "plot_network",
    "plot_results",
]


# ── Internal helpers ─────────────────────────────────────────────────


def _import_matplotlib() -> Any:
    """Lazy-import matplotlib, raising a clear error if missing."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        msg = (
            "matplotlib is required for plotting. "
            "Install it with: pip install hydroflow-py[plot]"
        )
        raise ImportError(msg) from None
    return plt


def _import_networkx() -> Any:
    """Lazy-import networkx, raising a clear error if missing."""
    try:
        import networkx as nx
    except ImportError:
        msg = (
            "networkx is required for plotting. "
            "Install it with: pip install hydroflow-py[plot]"
        )
        raise ImportError(msg) from None
    return nx


def _build_graph(network: WaterNetwork) -> Any:
    """Build a lightweight networkx graph from the WaterNetwork topology."""
    nx = _import_networkx()
    G = nx.Graph()

    for name in network.junctions:
        G.add_node(name, node_type="junction")
    for name in network.reservoirs:
        G.add_node(name, node_type="reservoir")
    for name in network.tanks:
        G.add_node(name, node_type="tank")

    for name, pipe in network.pipes.items():
        G.add_edge(pipe.start_node, pipe.end_node, link_name=name, link_type="pipe")
    for name, pump in network.pumps.items():
        G.add_edge(pump.start_node, pump.end_node, link_name=name, link_type="pump")
    for name, valve in network.valves.items():
        G.add_edge(valve.start_node, valve.end_node, link_name=name, link_type="valve")

    return G


def _get_positions(network: WaterNetwork) -> dict[str, tuple[float, float]]:
    """Return node positions: user coordinates if available, spring layout otherwise."""
    nx = _import_networkx()

    # Collect any user-specified coordinates
    positions: dict[str, tuple[float, float]] = {}
    all_nodes: dict[str, Any] = {}
    all_nodes.update(network.junctions)
    all_nodes.update(network.reservoirs)
    all_nodes.update(network.tanks)

    for name, node in all_nodes.items():
        if node.coordinates is not None:
            positions[name] = node.coordinates

    if positions:
        # Some nodes have coordinates — fill missing ones with centroid + jitter
        if len(positions) < len(all_nodes):
            import random

            xs = [p[0] for p in positions.values()]
            ys = [p[1] for p in positions.values()]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            spread = max(max(xs) - min(xs), max(ys) - min(ys), 1.0) * 0.1
            for name in all_nodes:
                if name not in positions:
                    positions[name] = (
                        cx + random.uniform(-spread, spread),
                        cy + random.uniform(-spread, spread),
                    )
        return positions

    # No coordinates at all — use spring layout
    G = _build_graph(network)
    pos_layout: dict[str, tuple[float, float]] = nx.spring_layout(G)
    return pos_layout


# ── Public API ───────────────────────────────────────────────────────


def plot_network(
    network: WaterNetwork,
    *,
    node_attribute: dict[str, float] | None = None,
    link_attribute: dict[str, float] | None = None,
    node_cmap: str = "RdYlGn",
    link_cmap: str = "viridis",
    node_size: float = 300,
    link_width: float = 2.0,
    node_labels: bool = True,
    link_labels: bool = False,
    title: str | None = None,
    ax: Any | None = None,
) -> Any:
    """Plot the network topology, optionally colored by attributes.

    Parameters
    ----------
    network : WaterNetwork
        The network to plot.
    node_attribute : dict[str, float] | None
        Optional mapping of node names to values for color-coding.
    link_attribute : dict[str, float] | None
        Optional mapping of link names to values for color-coding.
    node_cmap : str
        Matplotlib colormap name for node attribute coloring.
    link_cmap : str
        Matplotlib colormap name for link attribute coloring.
    node_size : float
        Base size for node markers.
    link_width : float
        Base width for link lines.
    node_labels : bool
        Whether to show node name labels.
    link_labels : bool
        Whether to show link name labels.
    title : str | None
        Plot title.
    ax : matplotlib Axes | None
        Existing axes to draw on.  If ``None``, creates a new figure.

    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot.
    """
    plt = _import_matplotlib()
    import matplotlib.colors as mcolors

    if not network.node_names:
        raise ValueError("Cannot plot an empty network (no nodes).")

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(10, 8))

    G = _build_graph(network)
    pos = _get_positions(network)

    # ── Draw edges ───────────────────────────────────────────────
    edge_list = list(G.edges(data=True))
    if edge_list:
        if link_attribute is not None:
            # Color edges by attribute values
            edge_colors = []
            for _u, _v, data in edge_list:
                link_name = data.get("link_name", "")
                edge_colors.append(link_attribute.get(link_name, 0.0))
            cmap_obj = plt.get_cmap(link_cmap)
            norm = mcolors.Normalize(
                vmin=min(edge_colors), vmax=max(edge_colors)
            )
            rgba_colors = [cmap_obj(norm(val)) for val in edge_colors]
            for (u, v, _), color in zip(edge_list, rgba_colors, strict=True):
                ax.plot(
                    [pos[u][0], pos[v][0]],
                    [pos[u][1], pos[v][1]],
                    color=color,
                    linewidth=link_width,
                    zorder=1,
                )
            sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label="Link attribute", shrink=0.8)
        else:
            for u, v, data in edge_list:
                link_type = data.get("link_type", "pipe")
                style = "--" if link_type == "pump" else "-"
                ax.plot(
                    [pos[u][0], pos[v][0]],
                    [pos[u][1], pos[v][1]],
                    color="gray",
                    linewidth=link_width,
                    linestyle=style,
                    zorder=1,
                )

    # ── Draw nodes by type ───────────────────────────────────────
    type_config = {
        "junction": {"marker": "o", "color": "#888888", "label": "Junction"},
        "reservoir": {"marker": "s", "color": "#1f77b4", "label": "Reservoir"},
        "tank": {"marker": "D", "color": "#2ca02c", "label": "Tank"},
    }

    if node_attribute is not None:
        # Color all nodes by attribute value
        all_node_names = list(pos.keys())
        vals = [node_attribute.get(n, 0.0) for n in all_node_names]
        cmap_obj = plt.get_cmap(node_cmap)
        norm = mcolors.Normalize(vmin=min(vals), vmax=max(vals))
        for node_type, cfg in type_config.items():
            names = [n for n in all_node_names if G.nodes[n].get("node_type") == node_type]
            if not names:
                continue
            xs = [pos[n][0] for n in names]
            ys = [pos[n][1] for n in names]
            colors = [cmap_obj(norm(node_attribute.get(n, 0.0))) for n in names]
            ax.scatter(
                xs, ys,
                c=colors,
                s=node_size,
                marker=cfg["marker"],
                edgecolors="black",
                linewidths=0.5,
                zorder=2,
            )
        sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label="Node attribute", shrink=0.8)
    else:
        for node_type, cfg in type_config.items():
            names = [n for n in pos if G.nodes[n].get("node_type") == node_type]
            if not names:
                continue
            xs = [pos[n][0] for n in names]
            ys = [pos[n][1] for n in names]
            ax.scatter(
                xs, ys,
                c=cfg["color"],
                s=node_size,
                marker=cfg["marker"],
                edgecolors="black",
                linewidths=0.5,
                label=cfg["label"],
                zorder=2,
            )
        ax.legend(loc="best")

    # ── Labels ───────────────────────────────────────────────────
    if node_labels:
        for name, (x, y) in pos.items():
            ax.annotate(
                name,
                (x, y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
            )

    if link_labels:
        for u, v, data in edge_list:
            link_name = data.get("link_name", "")
            mx = (pos[u][0] + pos[v][0]) / 2
            my = (pos[u][1] + pos[v][1]) / 2
            ax.annotate(link_name, (mx, my), fontsize=7, ha="center", color="darkblue")

    if title:
        ax.set_title(title)
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, alpha=0.3)

    return ax


def plot_results(
    network: WaterNetwork,
    results: NetworkResults,
    *,
    timestep: int = 0,
    node_attribute: str = "pressure",
    link_attribute: str | None = None,
    ax: Any | None = None,
    title: str | None = None,
) -> Any:
    """Plot simulation results at a given timestep.

    Extracts the relevant row from the results DataFrames and passes
    them to :func:`plot_network` as attribute dicts.

    Parameters
    ----------
    network : WaterNetwork
        The network that was simulated.
    results : NetworkResults
        Simulation results.
    timestep : int
        Row index into the results DataFrames (0 = first timestep).
    node_attribute : str
        Which node result to color by: ``"pressure"``, ``"head"``, or ``"demand"``.
    link_attribute : str | None
        Which link result to color by: ``"flow"``, ``"velocity"``, or ``None``.
    ax : matplotlib Axes | None
        Existing axes to draw on.
    title : str | None
        Plot title.  Defaults to auto-generated from attribute names.

    Returns
    -------
    matplotlib.axes.Axes
        The axes with the plot.
    """
    node_attr_map = {
        "pressure": results.pressures,
        "head": results.heads,
        "demand": results.demands,
    }
    link_attr_map = {
        "flow": results.flows,
        "velocity": results.velocities,
    }

    node_df = node_attr_map.get(node_attribute)
    if node_df is None:
        raise ValueError(
            f"Unknown node_attribute {node_attribute!r}. "
            f"Choose from: {', '.join(node_attr_map)}."
        )
    node_dict = dict(node_df.iloc[timestep])

    link_dict = None
    if link_attribute is not None:
        link_df = link_attr_map.get(link_attribute)
        if link_df is None:
            raise ValueError(
                f"Unknown link_attribute {link_attribute!r}. "
                f"Choose from: {', '.join(link_attr_map)}."
            )
        link_dict = dict(link_df.iloc[timestep])

    if title is None:
        time_val = node_df.index[timestep]
        parts = [f"{node_attribute.title()}"]
        if link_attribute:
            parts.append(f"& {link_attribute.title()}")
        parts.append(f"at t={time_val}")
        title = " ".join(parts)

    return plot_network(
        network,
        node_attribute=node_dict,
        link_attribute=link_dict,
        title=title,
        ax=ax,
    )
