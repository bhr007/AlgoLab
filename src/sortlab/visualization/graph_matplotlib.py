"""Dedicated Matplotlib renderer for AlgoLab graph algorithm event streams."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from sortlab.graphs.events import (
    GraphEvent,
    GraphEventType,
    extract_graph_from_events,
)
from sortlab.graphs.model import Graph, GraphEdge, Node

from ._playback import (
    PlaybackControllerMixin,
    compute_default_interval,
    select_rendered_indices,
)

NODE_STATE_COLORS: dict[str, str] = {
    "unvisited": "#17243A",
    "frontier": "#EECA3B",
    "current": "#FF9B45",
    "visited": "#2E8B57",
    "cycle": "#E45756",
}

EDGE_STATE_COLORS: dict[str, str] = {
    "default": "#9AA5B1",
    "active": "#FF9B45",
    "selected": "#2E8B57",
    "rejected": "#E45756",
    "cycle": "#E45756",
}


@dataclass(frozen=True)
class GraphEventCounters:
    """Cumulative operation counters up to a given graph event."""

    explorations: int = 0
    relaxations: int = 0
    distance_updates: int = 0
    selections: int = 0
    rejections: int = 0


def _compute_default_interval(frame_count: int) -> int:
    """Choose a responsive playback interval in milliseconds for ``frame_count``."""
    return compute_default_interval(
        frame_count, min_ms=80, max_ms=650, target_total_ms=12_000
    )


def _select_rendered_indices(total: int, max_frames: int | None) -> list[int]:
    """Select evenly spaced event indices, always keeping the first and last."""
    return select_rendered_indices(total, max_frames)


def _format_weight(weight: float) -> str:
    if isinstance(weight, int) and not isinstance(weight, bool):
        return str(weight)
    if float(weight).is_integer():
        return str(int(weight))
    return f"{weight:g}"


def _format_distance(dist: float | None) -> str:
    if dist is None or math.isinf(dist):
        return "∞"
    return _format_weight(dist)


def compute_graph_layout(graph: Graph) -> dict[Node, tuple[float, float]]:
    """Compute a deterministic, lightweight 2D layout without NetworkX.

    Starts from deterministic circular positions and applies a deterministic
    Fruchterman-Reingold force-directed refinement pass so trees, cycles,
    weighted graphs, and disconnected components are cleanly separated.
    """
    nodes = graph.nodes
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: (0.0, 0.0)}
    if n == 2:
        return {nodes[0]: (-0.6, 0.0), nodes[1]: (0.6, 0.0)}

    # Deterministic circular seed keeps initial positions non-collinear.
    positions: list[list[float]] = []
    for idx in range(n):
        angle = (2.0 * math.pi * idx) / n - math.pi / 2.0
        positions.append([math.cos(angle), math.sin(angle)])

    node_to_idx = {node: idx for idx, node in enumerate(nodes)}
    unique_pairs: set[tuple[int, int]] = set()
    for edge in graph.edges:
        u_idx = node_to_idx[edge.source]
        v_idx = node_to_idx[edge.target]
        if u_idx != v_idx:
            pair = (min(u_idx, v_idx), max(u_idx, v_idx))
            unique_pairs.add(pair)

    area = 4.0
    k = math.sqrt(area / n)
    iterations = 60
    temp = 0.35

    for step in range(iterations):
        disp = [[0.0, 0.0] for _ in range(n)]

        # Pairwise repulsive forces keep disconnected and non-adjacent nodes apart.
        for i in range(n):
            xi, yi = positions[i]
            for j in range(i + 1, n):
                dx = xi - positions[j][0]
                dy = yi - positions[j][1]
                dist_sq = dx * dx + dy * dy
                dist = math.sqrt(dist_sq) if dist_sq > 1e-9 else 1e-4
                force = (k * k) / dist
                ux = (dx / dist) * force
                uy = (dy / dist) * force
                disp[i][0] += ux
                disp[i][1] += uy
                disp[j][0] -= ux
                disp[j][1] -= uy

        # Attractive forces along edges pull connected neighbors together.
        for u_idx, v_idx in unique_pairs:
            dx = positions[u_idx][0] - positions[v_idx][0]
            dy = positions[u_idx][1] - positions[v_idx][1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 1e-9:
                continue
            force = (dist * dist) / k
            ux = (dx / dist) * force
            uy = (dy / dist) * force
            disp[u_idx][0] -= ux
            disp[u_idx][1] -= uy
            disp[v_idx][0] += ux
            disp[v_idx][1] += uy

        # Mild gravity keeps disconnected components centered in the viewport.
        for i in range(n):
            disp[i][0] -= 0.08 * positions[i][0]
            disp[i][1] -= 0.08 * positions[i][1]

        cooling = temp * (1.0 - step / iterations)
        for i in range(n):
            dx, dy = disp[i]
            mag = math.sqrt(dx * dx + dy * dy)
            if mag > 1e-9:
                scale = min(mag, cooling) / mag
                positions[i][0] += dx * scale
                positions[i][1] += dy * scale

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1e-6)
    target_radius = 0.92
    scale_factor = (2.0 * target_radius) / span

    return {
        node: (
            (positions[idx][0] - cx) * scale_factor,
            (positions[idx][1] - cy) * scale_factor,
        )
        for idx, node in enumerate(nodes)
    }


def _build_counter_timeline(events: list[GraphEvent]) -> list[GraphEventCounters]:
    counters: list[GraphEventCounters] = []
    exp = rel = upd = sel = rej = 0
    for event in events:
        etype = event.type
        if etype == GraphEventType.EXPLORE_EDGE:
            exp += 1
        elif etype == GraphEventType.RELAX_EDGE:
            rel += 1
        elif etype == GraphEventType.UPDATE_DISTANCE:
            upd += 1
        elif etype == GraphEventType.SELECT_EDGE:
            sel += 1
        elif etype == GraphEventType.REJECT_EDGE:
            rej += 1
        counters.append(
            GraphEventCounters(
                explorations=exp,
                relaxations=rel,
                distance_updates=upd,
                selections=sel,
                rejections=rej,
            )
        )
    return counters


def _canonical_edge_key(
    edge: tuple[Node, Node], *, directed: bool
) -> tuple[Node, Node]:
    u, v = edge
    if directed:
        return (u, v)
    key_u = (type(u).__name__, str(u))
    key_v = (type(v).__name__, str(v))
    return (u, v) if key_u <= key_v else (v, u)


def _node_label_color(hex_color: str) -> str:
    if hex_color in (NODE_STATE_COLORS["frontier"], NODE_STATE_COLORS["current"]):
        return "#17243A"
    return "#FFFFFF"


class GraphAnimationController(PlaybackControllerMixin):
    """Interactive controller managing Matplotlib graph nodes, edges, HUD, and controls."""

    def __init__(
        self,
        fig,
        ax,
        graph: Graph,
        events: list[GraphEvent],
        algorithm_name: str,
        interval: int,
        max_frames: int | None = None,
        external_ui: dict[str, object] | None = None,
    ) -> None:
        from matplotlib.animation import FuncAnimation
        from matplotlib.lines import Line2D
        from matplotlib.patches import Circle, FancyArrowPatch, Patch
        from matplotlib.widgets import Button, Slider

        self.fig = fig
        self.ax = ax
        self.graph = graph
        self.events = events
        self.algorithm_name = algorithm_name
        self.interval = interval
        self.counters = _build_counter_timeline(events)
        self.rendered_map = _select_rendered_indices(len(events), max_frames)
        self.total_rendered = len(self.rendered_map)

        self.layout = compute_graph_layout(graph)
        n = graph.node_count
        self.node_radius = max(0.065, min(0.125, 0.42 / math.sqrt(max(1, n))))
        self._has_distances = any(e.distances is not None for e in events)
        self._distance_timeline: list[dict[Node, float | None] | None] = []
        last_dist: dict[Node, float | None] | None = None
        for event in events:
            if event.distances is not None:
                last_dist = event.distances
            self._distance_timeline.append(last_dist)

        if external_ui is None:
            self.fig.subplots_adjust(top=0.77, bottom=0.22, left=0.04, right=0.96)
        self.ax.set_aspect("equal", adjustable="datalim")
        self.ax.set_xlim(-1.32, 1.32)
        self.ax.set_ylim(-1.26, 1.26)
        self.ax.axis("off")

        if n == 0:
            self.ax.text(
                0.0,
                0.0,
                "Empty graph — nothing to traverse",
                ha="center",
                va="center",
                fontsize=12,
                color="#555555",
            )

        # Draw edges underneath nodes.
        directed_pair_set = (
            {(e.source, e.target) for e in graph.edges} if graph.directed else set()
        )
        self._edge_artists: list[tuple[GraphEdge, FancyArrowPatch]] = []
        self._edge_weight_texts: list = []

        # Track parallel edges so multigraph edges fan out legibly.
        seen_parallel_counts: dict[tuple[Node, Node], int] = {}

        for edge in graph.edges:
            u, v = edge.source, edge.target
            x1, y1 = self.layout[u]
            x2, y2 = self.layout[v]
            pair_key = _canonical_edge_key((u, v), directed=graph.directed)
            dup_idx = seen_parallel_counts.get(pair_key, 0)
            seen_parallel_counts[pair_key] = dup_idx + 1

            rad = 0.0
            if u == v:
                rad = 0.35 + 0.12 * dup_idx
            elif graph.directed and (v, u) in directed_pair_set:
                rad = 0.16 + 0.08 * dup_idx
            elif dup_idx > 0:
                rad = (0.14 if dup_idx % 2 == 1 else -0.14) * ((dup_idx + 1) // 2)

            if u == v:
                sx, sy = x1 - self.node_radius * 0.7, y1 + self.node_radius * 0.7
                ex, ey = x1 + self.node_radius * 0.7, y1 + self.node_radius * 0.7
            else:
                dx = x2 - x1
                dy = y2 - y1
                dist = math.hypot(dx, dy) or 1.0
                ux, uy = dx / dist, dy / dist
                sx = x1 + ux * self.node_radius
                sy = y1 + uy * self.node_radius
                ex = x2 - ux * self.node_radius
                ey = y2 - uy * self.node_radius

            arrow_style = "-|>" if graph.directed else "-"
            patch = FancyArrowPatch(
                (sx, sy),
                (ex, ey),
                arrowstyle=arrow_style,
                mutation_scale=14 if graph.directed else 1,
                connectionstyle=f"arc3,rad={rad}",
                linewidth=1.8,
                color=EDGE_STATE_COLORS["default"],
                zorder=1,
            )
            self.ax.add_patch(patch)
            self._edge_artists.append((edge, patch))

            if graph.weighted:
                mx = (sx + ex) / 2.0
                my = (sy + ey) / 2.0
                if u == v:
                    mx = x1
                    my = y1 + self.node_radius * 2.2
                elif rad != 0.0:
                    dx = ex - sx
                    dy = ey - sy
                    dist = math.hypot(dx, dy) or 1.0
                    # Arc3 bows to the right-hand normal of (sx, sy) -> (ex, ey) for positive rad.
                    nx, ny = dy / dist, -dx / dist
                    offset = 0.5 * rad * dist
                    mx += nx * offset
                    my += ny * offset
                w_text = self.ax.text(
                    mx,
                    my,
                    _format_weight(edge.weight),
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    fontweight="bold",
                    color="#1F2933",
                    bbox={
                        "boxstyle": "round,pad=0.15",
                        "facecolor": "white",
                        "edgecolor": "#D1D5DB",
                        "alpha": 0.9,
                    },
                    zorder=3,
                )
                self._edge_weight_texts.append(w_text)

        # Draw nodes and node labels.
        self._node_patches: dict[Node, Circle] = {}
        self._node_labels: dict[Node, object] = {}
        self._distance_labels: dict[Node, object] = {}

        for node in graph.nodes:
            x, y = self.layout[node]
            circle = Circle(
                (x, y),
                radius=self.node_radius,
                facecolor=NODE_STATE_COLORS["unvisited"],
                edgecolor="#1F2933",
                linewidth=1.5,
                zorder=4,
            )
            self.ax.add_patch(circle)
            self._node_patches[node] = circle

            label = self.ax.text(
                x,
                y,
                str(node),
                ha="center",
                va="center",
                fontsize=9.5 if n <= 14 else 8,
                fontweight="bold",
                color="#FFFFFF",
                zorder=5,
            )
            self._node_labels[node] = label

            if self._has_distances:
                d_label = self.ax.text(
                    x,
                    y - self.node_radius - 0.045,
                    "d=∞",
                    ha="center",
                    va="top",
                    fontsize=8,
                    color="#1F2933",
                    bbox={
                        "boxstyle": "round,pad=0.12",
                        "facecolor": "#F9FAFB",
                        "edgecolor": "#D1D5DB",
                        "alpha": 0.9,
                    },
                    zorder=5,
                )
                self._distance_labels[node] = d_label

        # Header HUD.
        kind_parts = [
            "Directed" if graph.directed else "Undirected",
            "Weighted" if graph.weighted else "Unweighted",
        ]
        if external_ui is not None:
            self.title_text = external_ui["title_text"]
            self.operation_text = external_ui["operation_text"]
            self.counter_text = external_ui["counter_text"]
            self.summary_text = external_ui["summary_text"]
            self.title_text.set_text(
                f"AlgoLab — {self.algorithm_name} ({', '.join(kind_parts)})"
            )
        else:
            self.title_text = self.fig.text(
                0.5,
                0.955,
                f"AlgoLab — {self.algorithm_name} ({', '.join(kind_parts)})",
                ha="center",
                va="top",
                fontsize=13.5,
                fontweight="bold",
                color="#17243A",
            )
            self.operation_text = self.fig.text(
                0.5,
                0.905,
                "",
                ha="center",
                va="top",
                fontsize=10.5,
                color="#17243A",
            )
            self.counter_text = self.fig.text(
                0.5,
                0.86,
                "",
                ha="center",
                va="top",
                fontsize=9.2,
                color="#17243A",
                bbox={
                    "boxstyle": "round,pad=0.28",
                    "facecolor": "#F3F5F8",
                    "edgecolor": "#D1D5DB",
                },
            )
            self.summary_text = self.fig.text(
                0.5,
                0.145,
                "",
                ha="center",
                va="center",
                fontsize=9.0,
                color="#17243A",
                bbox={
                    "boxstyle": "round,pad=0.3",
                    "facecolor": "#F3F5F8",
                    "edgecolor": "#CBD5E1",
                },
            )

        # Compact legend.
        legend_items = [
            Patch(facecolor=NODE_STATE_COLORS["unvisited"], label="Unvisited"),
            Patch(facecolor=NODE_STATE_COLORS["frontier"], label="Frontier"),
            Patch(facecolor=NODE_STATE_COLORS["current"], label="Current"),
            Patch(facecolor=NODE_STATE_COLORS["visited"], label="Visited / Done"),
            Line2D([0], [0], color=EDGE_STATE_COLORS["active"], lw=2.5, label="Active Edge"),
            Line2D([0], [0], color=EDGE_STATE_COLORS["selected"], lw=2.5, label="Selected Path/Tree"),
        ]
        self.ax.legend(
            handles=legend_items,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.11),
            ncol=6,
            frameon=False,
            fontsize=8.2,
        )

        # Interactive playback controls.
        if external_ui is not None:
            self.btn_play = external_ui["btn_play"]
            self.btn_step = external_ui["btn_step"]
            self.btn_reset = external_ui["btn_reset"]
            self.slider_speed = external_ui["slider_speed"]
            self.btn_play.label.set_text("Pause")
        else:
            ax_play = self.fig.add_axes([0.10, 0.035, 0.13, 0.052])
            ax_step = self.fig.add_axes([0.25, 0.035, 0.10, 0.052])
            ax_reset = self.fig.add_axes([0.37, 0.035, 0.10, 0.052])
            ax_speed = self.fig.add_axes([0.57, 0.042, 0.31, 0.038])

            self.btn_play = Button(ax_play, "Pause")
            self.btn_step = Button(ax_step, "Step")
            self.btn_reset = Button(ax_reset, "Reset")
            self.slider_speed = Slider(
                ax_speed,
                "Delay (ms)",
                10,
                1500,
                valinit=max(10, min(1500, interval)),
                valstep=10,
            )

            self.btn_play.on_clicked(self.toggle_play)
            self.btn_step.on_clicked(self.step_once)
            self.btn_reset.on_clicked(self.reset)
            self.slider_speed.on_changed(self._on_speed_change)

        self.is_paused = False
        self.current_render_idx = -1
        self.render_frame(0)

        if external_ui is not None and external_ui.get("manage_animation") is False:
            self.animation = None
        else:
            self.animation = FuncAnimation(
                self.fig,
                self._tick,
                init_func=self._init_frame,
                frames=self._frame_iterator,
                interval=self.interval,
                blit=False,
                cache_frame_data=False,
                repeat=False,
            )
        self.fig._algolab_graph_controller = self
        self.fig._algolab_controller = self
        self.fig._sortlab_graph_controller = self
        self.fig._sortlab_controller = self

    def _init_frame(self):
        return self._all_artists()

    def _tick(self, _frame: int):
        if self.is_paused:
            return self._all_artists()
        next_idx = self.current_render_idx + 1
        if next_idx >= self.total_rendered:
            self.is_paused = True
            self.btn_play.label.set_text("Play")
            anim = getattr(self, "animation", None)
            if anim is not None and anim.event_source is not None:
                anim.event_source.stop()
            return self._all_artists()
        return self.render_frame(next_idx)

    def _all_artists(self):
        return tuple(self._node_patches.values()) + tuple(
            patch for _, patch in self._edge_artists
        )

    def _apply_event_state(self, event_idx: int) -> None:
        event = self.events[event_idx]
        visited_set = set(event.visited)
        frontier_set = set(event.frontier)

        latest_distances = self._distance_timeline[event_idx]

        cycle_nodes: set[Node] = set()
        if event.type == GraphEventType.CYCLE_DETECTED:
            if event.node is not None:
                cycle_nodes.add(event.node)
            if event.edge is not None:
                cycle_nodes.update(event.edge)
            if event.metadata and isinstance(event.metadata.get("cycle_nodes"), (list, tuple)):
                cycle_nodes.update(event.metadata["cycle_nodes"])

        for node, circle in self._node_patches.items():
            if node in cycle_nodes:
                color = NODE_STATE_COLORS["cycle"]
                lw = 2.6
            elif event.node == node and event.type in (
                GraphEventType.VISIT_NODE,
                GraphEventType.DISCOVER_NODE,
                GraphEventType.UPDATE_DISTANCE,
            ):
                color = NODE_STATE_COLORS["current"]
                lw = 2.6
            elif node in visited_set:
                color = NODE_STATE_COLORS["visited"]
                lw = 1.6
            elif node in frontier_set:
                color = NODE_STATE_COLORS["frontier"]
                lw = 1.8
            elif (
                event.type == GraphEventType.COMPLETE
                and node in set(event.traversal_order)
            ):
                color = NODE_STATE_COLORS["visited"]
                lw = 1.6
            else:
                color = NODE_STATE_COLORS["unvisited"]
                lw = 1.4

            circle.set_facecolor(color)
            circle.set_linewidth(lw)
            self._node_labels[node].set_color(_node_label_color(color))

            if node in self._distance_labels and latest_distances is not None:
                dist_val = latest_distances.get(node)
                self._distance_labels[node].set_text(f"d={_format_distance(dist_val)}")

        selected_keys = {
            _canonical_edge_key(pair, directed=self.graph.directed)
            for pair in event.selected_edges
        }
        active_key = (
            _canonical_edge_key(event.edge, directed=self.graph.directed)
            if event.edge is not None
            else None
        )

        for edge, patch in self._edge_artists:
            key = _canonical_edge_key(
                (edge.source, edge.target), directed=self.graph.directed
            )
            if active_key == key and event.type == GraphEventType.CYCLE_DETECTED:
                patch.set_color(EDGE_STATE_COLORS["cycle"])
                patch.set_linewidth(3.4)
                patch.set_linestyle("-")
                patch.set_zorder(3)
            elif active_key == key and event.type == GraphEventType.REJECT_EDGE:
                patch.set_color(EDGE_STATE_COLORS["rejected"])
                patch.set_linewidth(2.3)
                patch.set_linestyle("--")
                patch.set_zorder(2)
            elif active_key == key and event.type in (
                GraphEventType.EXPLORE_EDGE,
                GraphEventType.RELAX_EDGE,
            ):
                patch.set_color(EDGE_STATE_COLORS["active"])
                patch.set_linewidth(3.1)
                patch.set_linestyle("-")
                patch.set_zorder(3)
            elif key in selected_keys:
                patch.set_color(EDGE_STATE_COLORS["selected"])
                patch.set_linewidth(3.0)
                patch.set_linestyle("-")
                patch.set_zorder(2)
            else:
                patch.set_color(EDGE_STATE_COLORS["default"])
                patch.set_linewidth(1.7)
                patch.set_linestyle("-")
                patch.set_zorder(1)

        op_name = event.type.value.replace("_", " ").title()
        op_desc = event.message or op_name
        self.operation_text.set_text(f"Operation: {op_name} — {op_desc}")

        cnt = self.counters[event_idx]
        counter_parts = [
            f"Step: {event_idx + 1}/{len(self.events)}",
            f"Visited: {len(visited_set)}/{self.graph.node_count}",
            f"Selected Edges: {len(event.selected_edges)}",
            f"Explored: {cnt.explorations}",
        ]
        if cnt.relaxations:
            counter_parts.append(f"Relaxations: {cnt.relaxations}")
        if cnt.distance_updates:
            counter_parts.append(f"Updates: {cnt.distance_updates}")
        if cnt.rejections:
            counter_parts.append(f"Rejected: {cnt.rejections}")
        self.counter_text.set_text("   |   ".join(counter_parts))

        summary_lines: list[str] = []
        if event.traversal_order:
            order_str = " → ".join(str(n) for n in event.traversal_order)
            summary_lines.append(f"Order: {order_str}")
        if event.frontier:
            frontier_str = ", ".join(str(n) for n in event.frontier)
            summary_lines.append(f"Frontier: [{frontier_str}]")
        if latest_distances is not None:
            dist_items = [
                f"{n}:{_format_distance(latest_distances.get(n))}"
                for n in self.graph.nodes
            ]
            summary_lines.append("Distances: " + ", ".join(dist_items))
        elif event.selected_edges:
            edges_str = ", ".join(f"({u},{v})" for u, v in event.selected_edges)
            summary_lines.append(f"Selected Path/Edges: {edges_str}")
        if not summary_lines:
            summary_lines.append(
                f"Nodes: {self.graph.node_count}   |   Edges: {self.graph.edge_count}"
            )
        self.summary_text.set_text("\n".join(summary_lines[:2]))

    def render_frame(self, render_idx: int):
        """Render a specific keyframe index in ``[0, total_rendered)``."""
        render_idx = max(0, min(render_idx, self.total_rendered - 1))
        event_idx = self.rendered_map[render_idx]
        self._apply_event_state(event_idx)
        self.current_render_idx = render_idx

        event = self.events[event_idx]
        if (
            event.type == GraphEventType.COMPLETE
            and render_idx == self.total_rendered - 1
        ):
            self.is_paused = True
            self.btn_play.label.set_text("Play")
        return self._all_artists()


def animate_graph_events(
    events: Iterable[GraphEvent],
    graph: Graph | None = None,
    interval: int | None = None,
    *,
    algorithm_name: str | None = None,
    show: bool = True,
    max_frames: int | None = None,
):
    """Animate AlgoLab graph events. Requires the optional Matplotlib dependency."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is optional. Install it with: pip install algolab[visualization]"
        ) from exc

    event_list = list(events)
    if not event_list:
        raise ValueError("events must contain at least one event")

    resolved_graph = graph if graph is not None else extract_graph_from_events(event_list)
    if resolved_graph is None:
        raise ValueError(
            "No graph structure found; pass graph=... or include a START event with graph metadata"
        )

    resolved_name = algorithm_name
    if resolved_name is None:
        first_meta = event_list[0].metadata or {}
        resolved_name = str(first_meta.get("algorithm", "Graph Algorithm"))

    resolved_interval = (
        interval
        if interval is not None
        else _compute_default_interval(
            min(len(event_list), max_frames) if max_frames else len(event_list)
        )
    )

    fig, ax = plt.subplots(figsize=(10.5, 6.8))
    controller = GraphAnimationController(
        fig=fig,
        ax=ax,
        graph=resolved_graph,
        events=event_list,
        algorithm_name=resolved_name,
        interval=resolved_interval,
        max_frames=max_frames,
    )

    if show:
        try:
            plt.show()
        finally:
            plt.close(fig)
    else:
        fig.canvas.draw()

    return controller.animation
