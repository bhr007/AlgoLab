"""Single-window native Matplotlib desktop studio and input validation for SortLab.

Provides:
- Input validation helpers (:func:`build_sorting_request`, :func:`build_graph_request`)
  shared across CLI and GUI workflows.
- :class:`SortLabStudio`, a responsive single-window Matplotlib desktop interface
  combining guided Sorting & Graph controls, complexity/constraint cards, quick
  educational presets, and live animation playback without requiring a browser.
"""

from __future__ import annotations

import math
import random
import textwrap
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Union

from sortlab.cli import (
    build_graph_from_input,
    parse_values,
    resolve_cli_start_node,
)
from sortlab.core.registry import (
    ALGORITHM_SPECS,
    AlgorithmSpec,
    get_algorithm_spec,
    validate_inputs_for_spec,
)
from sortlab.graphs.model import (
    Graph,
    GraphCycleError,
    MSTResult,
    NegativeCycleError,
    Node,
    ShortestPathResult,
)
from sortlab.graphs.registry import (
    GRAPH_ALGORITHM_SPECS,
    GraphAlgorithmSpec,
    get_graph_algorithm_spec,
    validate_graph_for_spec,
)


@dataclass(frozen=True)
class SortingInputRequest:
    """Validated user request for a sorting run."""

    spec: AlgorithmSpec
    values: list[float]
    interval: int | None = None


@dataclass(frozen=True)
class GraphInputRequest:
    """Validated user request for a graph algorithm run."""

    spec: GraphAlgorithmSpec
    graph: Graph
    start: Node | None = None
    interval: int | None = None


InputRequest = Union[SortingInputRequest, GraphInputRequest]


@dataclass(frozen=True)
class GraphExamplePreset:
    """Sample graph preset tailored to a specific graph algorithm."""

    directed: bool
    weighted: bool
    nodes: str
    edges: str
    start: str


GRAPH_EXAMPLES: dict[str, GraphExamplePreset] = {
    "bfs": GraphExamplePreset(
        directed=False,
        weighted=False,
        nodes="A B C D E F G",
        edges="A B, A C, B D, C D, E F",
        start="A",
    ),
    "dfs": GraphExamplePreset(
        directed=False,
        weighted=False,
        nodes="A B C D E F",
        edges="A B, A C, B D, B E, C F",
        start="A",
    ),
    "dijkstra": GraphExamplePreset(
        directed=True,
        weighted=True,
        nodes="",
        edges="A B 4, A C 1, C B 2, B D 1, C D 5, B E 6, D E 2",
        start="A",
    ),
    "bellman_ford": GraphExamplePreset(
        directed=True,
        weighted=True,
        nodes="",
        edges="S A 4, S B 5, B A -3, A C 6, C B -1",
        start="S",
    ),
    "prim": GraphExamplePreset(
        directed=False,
        weighted=True,
        nodes="",
        edges="A B 4, A C 2, B C 1, B D 5, C D 8, C E 10, D E 2",
        start="A",
    ),
    "kruskal": GraphExamplePreset(
        directed=False,
        weighted=True,
        nodes="",
        edges="A B 4, A C 2, B C 1, B D 5, C D 8, C E 10, D E 2",
        start="",
    ),
    "topological_sort": GraphExamplePreset(
        directed=True,
        weighted=False,
        nodes="prep cook plate serve clean dry",
        edges="prep cook, prep plate, cook serve, plate serve, clean dry",
        start="",
    ),
}

_SORT_GUIDES: dict[str, str] = {
    "bubble_sort": "Swaps adjacent out-of-order pairs. Time: O(n^2) | Stable | Any finite numbers",
    "selection_sort": "Selects minimum each pass. Time: O(n^2) | Unstable | Any finite numbers",
    "insertion_sort": "Inserts each item into sorted prefix. Time: O(n^2) | Stable",
    "merge_sort": "Divide & conquer merge. Time: O(n log n) | Stable | Any finite numbers",
    "quick_sort": "3-way pivot partitioning. Avg: O(n log n) | Space: O(log n)",
    "heap_sort": "Binary max-heap extraction. Time: O(n log n) | In-place",
    "shell_sort": "Gapped insertion passes. In-place | Any finite numbers",
    "counting_sort": "Counts value frequencies. Time: O(n + k) | INTEGERS ONLY",
    "radix_sort": "Digit-by-digit buckets. Time: O(d(n + b)) | INTEGERS ONLY",
    "bucket_sort": "Distributes into buckets & sorts. Expected O(n + k)",
}

_GRAPH_GUIDES: dict[str, str] = {
    "bfs": "Level-order traversal. Time: O(V + E) | Space: O(V) | Start required",
    "dfs": "Depth-first branch exploration. Time: O(V + E) | Start required",
    "dijkstra": "Shortest path. O((V + E) log V) | Weights >= 0 | Start required",
    "bellman_ford": "Shortest path w/ negative weights & cycle check. O(V * E)",
    "prim": "Grows MST from start node. O((V + E) log V) | Undirected & weighted",
    "kruskal": "Sorts edges w/ Union-Find MST. O(E log E) | Undirected & weighted",
    "topological_sort": "Orders DAG dependencies (Kahn's). O(V + E) | Directed acyclic",
}


def parse_optional_interval(raw: str) -> int | None:
    """Parse an optional positive integer delay in milliseconds."""
    cleaned = raw.strip()
    if not cleaned:
        return None
    try:
        interval = int(cleaned)
    except ValueError as exc:
        raise ValueError(
            "Animation delay must be a whole number of milliseconds."
        ) from exc
    if interval < 1:
        raise ValueError("Animation delay must be at least 1 ms.")
    return interval


def describe_sort_constraints(spec: AlgorithmSpec) -> str:
    """Return a concise constraint summary for a sorting algorithm."""
    if spec.integer_only:
        return f"{spec.name}: Integers only (negatives OK)."
    return f"{spec.name}: Finite ints or decimals."


def describe_graph_constraints(spec: GraphAlgorithmSpec) -> str:
    """Return a concise constraint summary for a graph algorithm."""
    parts: list[str] = []
    if spec.requires_directed is True:
        parts.append("Directed")
    elif spec.requires_directed is False:
        parts.append("Undirected")
    else:
        parts.append("Dir/Undir")

    if spec.requires_non_negative_weights:
        parts.append("Weights >= 0")
    elif spec.requires_weighted:
        parts.append("Weighted")
    else:
        parts.append("Opt. weights")

    if spec.requires_start:
        parts.append("Start req.")
    elif spec.optional_start:
        parts.append("Start opt.")
    else:
        parts.append("No start")
    return f"{spec.name}: " + " | ".join(parts)


def build_sorting_request(
    algorithm_name: str,
    values_raw: str,
    interval_raw: str = "",
) -> SortingInputRequest:
    """Validate raw sorting fields and return a :class:`SortingInputRequest`."""
    spec = get_algorithm_spec(algorithm_name)
    values = parse_values(values_raw)
    validate_inputs_for_spec(spec, values)
    interval = parse_optional_interval(interval_raw)
    return SortingInputRequest(spec=spec, values=values, interval=interval)


def build_graph_request(
    algorithm_name: str,
    *,
    directed: bool,
    weighted: bool,
    nodes_raw: str,
    edges_raw: str,
    start_raw: str = "",
    interval_raw: str = "",
) -> GraphInputRequest:
    """Validate raw graph fields and return a :class:`GraphInputRequest`."""
    spec = get_graph_algorithm_spec(algorithm_name)
    resolved_directed = (
        spec.requires_directed if spec.requires_directed is not None else directed
    )
    resolved_weighted = (
        spec.requires_weighted if spec.requires_weighted is not None else weighted
    )

    graph = build_graph_from_input(
        nodes_raw,
        edges_raw,
        directed=resolved_directed,
        weighted=resolved_weighted,
    )

    start_node: Node | None = None
    if spec.requires_start:
        start_node = resolve_cli_start_node(start_raw, graph, optional=False)
    elif spec.optional_start:
        start_node = resolve_cli_start_node(start_raw, graph, optional=True)

    validate_graph_for_spec(spec, graph, start_node)
    interval = parse_optional_interval(interval_raw)
    return GraphInputRequest(
        spec=spec,
        graph=graph,
        start=start_node,
        interval=interval,
    )


def _format_studio_graph_summary(
    spec: GraphAlgorithmSpec,
    graph: Graph,
    result: Any,
    elapsed: float,
) -> str:
    """Format a compact multi-line summary for the studio sidebar."""
    if isinstance(result, ShortestPathResult):
        items = [
            f"{n}:{'∞' if math.isinf(result.distances[n]) else f'{result.distances[n]:g}'}"
            for n in graph.nodes[:6]
        ]
        suffix = "..." if len(graph.nodes) > 6 else ""
        return (
            f"Completed {spec.name} ({elapsed:.6f}s)\n"
            f"Distances: {', '.join(items)}{suffix}"
        )
    if isinstance(result, MSTResult):
        kind = "MST" if result.is_spanning else f"Forest ({result.components} comp.)"
        return (
            f"Completed {spec.name} ({elapsed:.6f}s)\n"
            f"{kind}: {len(result.edges)} edges, total weight = {result.total_weight:g}"
        )
    order_str = " -> ".join(str(n) for n in result[:7])
    suffix = " -> ..." if len(result) > 7 else ""
    return f"Completed {spec.name} ({elapsed:.6f}s)\nOrder: {order_str}{suffix}"


def _stop_macosx_event_loop() -> None:
    """Break out of Matplotlib's macosx Cocoa run loop when closing the window."""
    try:
        from matplotlib.backends import _macosx
    except ImportError:
        return
    if _macosx.event_loop_is_running():
        _macosx.stop()


class SortLabStudio:
    """Single-window native Matplotlib GUI combining guided inputs and live playback."""

    def __init__(
        self,
        fig,
        *,
        initial_mode: str = "sorting",
        default_interval: int | None = None,
    ) -> None:
        from matplotlib.patches import FancyBboxPatch
        from matplotlib.widgets import Button, RadioButtons, Slider, TextBox

        self.fig = fig
        self.fig.set_facecolor("#EEF2F6")
        self.mode = "graph" if initial_mode == "graph" else "sorting"
        self.default_interval = (
            default_interval if default_interval is not None else 160
        )
        self.selected_sort_key = ALGORITHM_SPECS[0].key
        self.selected_graph_key = GRAPH_ALGORITHM_SPECS[0].key
        self.graph_directed = False
        self.graph_weighted = False
        self.active_controller: Any = None
        self._closed = False
        self._close_pending = False
        self._close_timer: Any = None
        self._syncing_radio = False
        self._waiting_for_draw = False
        self._all_textboxes: list[Any] = []

        # Connect before TextBox creation so clicking outside a TextBox blurs
        # cleanly without TextBox.stop_typing() blocking button_press_event.
        self.fig.canvas.mpl_connect("button_press_event", self._on_canvas_press)
        self.fig.canvas.mpl_connect("draw_event", self._on_draw_event)

        # Single-shot chained timer never starves Cocoa's run loop at fast speeds.
        self._timer = self.fig.canvas.new_timer(interval=self.default_interval)
        self._timer.single_shot = True
        self._timer.add_callback(self._on_timer_tick)

        # Elevated Left Control Card & Right Visualization Card.
        self.fig.patches.extend(
            [
                FancyBboxPatch(
                    (0.015, 0.025),
                    0.345,
                    0.95,
                    boxstyle="round,pad=0.008,rounding_size=0.015",
                    facecolor="#FFFFFF",
                    edgecolor="#CBD5E1",
                    linewidth=1.2,
                    transform=self.fig.transFigure,
                    zorder=-2,
                ),
                FancyBboxPatch(
                    (0.375, 0.025),
                    0.610,
                    0.95,
                    boxstyle="round,pad=0.008,rounding_size=0.015",
                    facecolor="#FFFFFF",
                    edgecolor="#CBD5E1",
                    linewidth=1.2,
                    transform=self.fig.transFigure,
                    zorder=-2,
                ),
            ]
        )

        # Sidebar Header.
        self.fig.text(
            0.03,
            0.956,
            "SortLab Studio",
            ha="left",
            va="top",
            fontsize=14,
            fontweight="bold",
            color="#0F172A",
        )
        self.fig.text(
            0.03,
            0.920,
            "1. Choose Mode",
            ha="left",
            va="top",
            fontsize=9.2,
            fontweight="bold",
            color="#475569",
        )

        # Mode switch buttons (switch tabs and show paused Step-0 preview).
        self.btn_mode_sort = Button(
            self.fig.add_axes([0.03, 0.865, 0.15, 0.042]), "Sorting"
        )
        self.btn_mode_graph = Button(
            self.fig.add_axes([0.19, 0.865, 0.15, 0.042]), "Graph"
        )
        self.btn_mode_sort.on_clicked(
            lambda _e: self.switch_mode("sorting", run_preview=True)
        )
        self.btn_mode_graph.on_clicked(
            lambda _e: self.switch_mode("graph", run_preview=True)
        )

        self.fig.text(
            0.03,
            0.848,
            "2. Select Algorithm",
            ha="left",
            va="top",
            fontsize=9.2,
            fontweight="bold",
            color="#475569",
        )

        # ---------------- Sorting Controls ----------------
        self._sort_widgets: list[tuple[Any, Any]] = []
        ax_sort_radio = self.fig.add_axes(
            [0.03, 0.592, 0.31, 0.235], facecolor="#F8FAFC"
        )
        self._sort_name_to_key = {spec.name: spec.key for spec in ALGORITHM_SPECS}
        self.radio_sort = RadioButtons(
            ax_sort_radio,
            [spec.name for spec in ALGORITHM_SPECS],
            active=0,
            activecolor="#2563EB",
        )
        for lbl in self.radio_sort.labels:
            lbl.set_fontsize(8.7)
        self.radio_sort.on_clicked(self._on_sort_radio_clicked)
        self._sort_widgets.append((self.radio_sort, ax_sort_radio))

        self.sort_constraint_text = self.fig.text(
            0.03,
            0.578,
            "",
            ha="left",
            va="top",
            fontsize=8.2,
            color="#1E3A8A",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "#EFF6FF",
                "edgecolor": "#BFDBFE",
            },
        )
        self.sort_step3_text = self.fig.text(
            0.03,
            0.515,
            "3. Enter Values (comma or space separated)",
            ha="left",
            va="top",
            fontsize=9.2,
            fontweight="bold",
            color="#475569",
        )

        ax_sort_vals = self.fig.add_axes([0.095, 0.448, 0.245, 0.044])
        self.tb_sort_values = TextBox(
            ax_sort_vals,
            "Data: ",
            initial="8, 3, 5, 1, 9, 2",
            color="#F8FAFC",
            hovercolor="#FFFFFF",
        )
        self._sort_widgets.append((self.tb_sort_values, ax_sort_vals))

        sort_presets = [
            ("Sample", lambda _e: self._apply_sort_preset("8, 3, 5, 1, 9, 2")),
            (
                "Random",
                lambda _e: self._apply_sort_preset(
                    ", ".join(str(random.randint(-20, 45)) for _ in range(10))
                ),
            ),
            (
                "Reverse",
                lambda _e: self._apply_sort_preset(
                    ", ".join(str(v) for v in range(10, 0, -1))
                ),
            ),
            (
                "Negs",
                lambda _e: self._apply_sort_preset("-5, 12, 0, -3, 8, 4, -5, 1"),
            ),
        ]
        for idx, (label, handler) in enumerate(sort_presets):
            ax_p = self.fig.add_axes([0.03 + idx * 0.079, 0.394, 0.073, 0.034])
            btn_p = Button(ax_p, label, color="#F1F5F9", hovercolor="#E2E8F0")
            btn_p.label.set_fontsize(8.3)
            btn_p.on_clicked(handler)
            self._sort_widgets.append((btn_p, ax_p))

        # ---------------- Graph Controls ----------------
        self._graph_widgets: list[tuple[Any, Any]] = []
        ax_graph_radio = self.fig.add_axes(
            [0.03, 0.635, 0.31, 0.192], facecolor="#F8FAFC"
        )
        self._graph_name_to_key = {
            spec.name: spec.key for spec in GRAPH_ALGORITHM_SPECS
        }
        self.radio_graph = RadioButtons(
            ax_graph_radio,
            [spec.name for spec in GRAPH_ALGORITHM_SPECS],
            active=0,
            activecolor="#2563EB",
        )
        for lbl in self.radio_graph.labels:
            lbl.set_fontsize(8.5)
        self.radio_graph.on_clicked(self._on_graph_radio_clicked)
        self._graph_widgets.append((self.radio_graph, ax_graph_radio))

        self.graph_constraint_text = self.fig.text(
            0.03,
            0.622,
            "",
            ha="left",
            va="top",
            fontsize=8.1,
            color="#1E3A8A",
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "#EFF6FF",
                "edgecolor": "#BFDBFE",
            },
        )
        self.graph_step3_text = self.fig.text(
            0.03,
            0.556,
            "3. Graph Input (edges: 'A B' or 'A B 4')",
            ha="left",
            va="top",
            fontsize=9.0,
            fontweight="bold",
            color="#475569",
        )

        ax_dir = self.fig.add_axes([0.03, 0.502, 0.15, 0.034])
        ax_wgt = self.fig.add_axes([0.19, 0.502, 0.15, 0.034])
        self.btn_directed = Button(ax_dir, "Directed: No")
        self.btn_weighted = Button(ax_wgt, "Weighted: No")
        self.btn_directed.label.set_fontsize(8.4)
        self.btn_weighted.label.set_fontsize(8.4)
        self.btn_directed.on_clicked(self._toggle_directed)
        self.btn_weighted.on_clicked(self._toggle_weighted)
        self._graph_widgets.extend(
            [(self.btn_directed, ax_dir), (self.btn_weighted, ax_wgt)]
        )

        ax_nodes = self.fig.add_axes([0.105, 0.452, 0.235, 0.036])
        self.tb_graph_nodes = TextBox(
            ax_nodes, "Nodes: ", initial="", color="#F8FAFC", hovercolor="#FFFFFF"
        )
        ax_edges = self.fig.add_axes([0.105, 0.404, 0.235, 0.038])
        self.tb_graph_edges = TextBox(
            ax_edges, "Edges: ", initial="", color="#F8FAFC", hovercolor="#FFFFFF"
        )
        ax_start = self.fig.add_axes([0.105, 0.356, 0.235, 0.036])
        self.tb_graph_start = TextBox(
            ax_start, "Start: ", initial="A", color="#F8FAFC", hovercolor="#FFFFFF"
        )
        self._graph_widgets.extend(
            [
                (self.tb_graph_nodes, ax_nodes),
                (self.tb_graph_edges, ax_edges),
                (self.tb_graph_start, ax_start),
            ]
        )

        graph_presets = [
            ("Example", lambda _e: self._apply_graph_preset("example")),
            ("Cycle Demo", lambda _e: self._apply_graph_preset("cycle")),
            ("Disconn.", lambda _e: self._apply_graph_preset("disconnected")),
            ("Clear", lambda _e: self._clear_graph_fields()),
        ]
        for idx, (label, handler) in enumerate(graph_presets):
            ax_g = self.fig.add_axes([0.03 + idx * 0.079, 0.308, 0.073, 0.034])
            btn_g = Button(ax_g, label, color="#F1F5F9", hovercolor="#E2E8F0")
            btn_g.label.set_fontsize(8.0)
            btn_g.on_clicked(handler)
            self._graph_widgets.append((btn_g, ax_g))

        self._all_textboxes = [
            self.tb_sort_values,
            self.tb_graph_nodes,
            self.tb_graph_edges,
            self.tb_graph_start,
        ]

        # ---------------- Shared Sidebar Actions ----------------
        self.btn_run = Button(
            self.fig.add_axes([0.03, 0.234, 0.21, 0.048]),
            "Run & Visualize",
            color="#16A34A",
            hovercolor="#15803D",
        )
        self.btn_run.label.set_color("#FFFFFF")
        self.btn_run.label.set_fontweight("bold")
        self.btn_run.label.set_fontsize(10.0)
        self.btn_run.on_clicked(self.run_current)

        self.btn_exit = Button(
            self.fig.add_axes([0.25, 0.234, 0.09, 0.048]),
            "Exit",
            color="#FEE2E2",
            hovercolor="#FCA5A5",
        )
        self.btn_exit.label.set_color("#991B1B")
        self.btn_exit.label.set_fontweight("bold")
        self.btn_exit.on_clicked(self.close)

        self.status_text = self.fig.text(
            0.03,
            0.210,
            "Ready. Pick an algorithm and click Run & Visualize.",
            ha="left",
            va="top",
            fontsize=8.4,
            color="#1E293B",
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#F8FAFC",
                "edgecolor": "#CBD5E1",
            },
        )

        # ---------------- Right Visualization Panel ----------------
        self.title_text = self.fig.text(
            0.68,
            0.955,
            "SortLab",
            ha="center",
            va="top",
            fontsize=13.5,
            fontweight="bold",
            color="#0F172A",
        )
        self.operation_text = self.fig.text(
            0.68,
            0.912,
            "",
            ha="center",
            va="top",
            fontsize=10.0,
            color="#334155",
        )
        self.counter_text = self.fig.text(
            0.68,
            0.870,
            "",
            ha="center",
            va="top",
            fontsize=8.9,
            color="#1F2933",
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "#F3F4F6",
                "edgecolor": "#D1D5DB",
            },
        )
        self.summary_text = self.fig.text(
            0.68,
            0.142,
            "",
            ha="center",
            va="center",
            fontsize=8.7,
            color="#1F2933",
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "#F8FAFC",
                "edgecolor": "#CBD5E1",
            },
        )

        self.ax_vis = self.fig.add_axes([0.405, 0.215, 0.555, 0.565])

        self.btn_play = Button(
            self.fig.add_axes([0.405, 0.048, 0.10, 0.046]),
            "Pause",
            color="#E2E8F0",
            hovercolor="#CBD5E1",
        )
        self.btn_step = Button(
            self.fig.add_axes([0.52, 0.048, 0.085, 0.046]),
            "Step",
            color="#E2E8F0",
            hovercolor="#CBD5E1",
        )
        self.btn_reset = Button(
            self.fig.add_axes([0.62, 0.048, 0.085, 0.046]),
            "Reset",
            color="#E2E8F0",
            hovercolor="#CBD5E1",
        )
        self.slider_speed = Slider(
            self.fig.add_axes([0.785, 0.056, 0.17, 0.032]),
            "Delay (ms)",
            20,
            1000,
            valinit=max(20, min(1000, self.default_interval)),
            valstep=10,
        )
        self.btn_play.on_clicked(self._on_play)
        self.btn_step.on_clicked(self._on_step)
        self.btn_reset.on_clicked(self._on_reset)
        self.slider_speed.on_changed(self._on_speed)

        self._external_ui = {
            "manage_animation": False,
            "title_text": self.title_text,
            "operation_text": self.operation_text,
            "counter_text": self.counter_text,
            "summary_text": self.summary_text,
            "btn_play": self.btn_play,
            "btn_step": self.btn_step,
            "btn_reset": self.btn_reset,
            "slider_speed": self.slider_speed,
        }

        self.fig.canvas.mpl_connect("close_event", self._on_close_event)

        self._select_sort_algo(self.selected_sort_key, redraw=False)
        self._select_graph_algo(self.selected_graph_key, redraw=False)
        self.switch_mode(self.mode, run_preview=True, auto_play=False)
        self.fig._sortlab_studio = self

    def _blur_textbox(self, tb: Any) -> None:
        """Quietly exit typing mode without triggering a synchronous draw or submit."""
        if getattr(tb, "capturekeystrokes", False):
            on_stop = getattr(tb, "_on_stop_typing", None)
            if on_stop is not None:
                on_stop()
                tb._on_stop_typing = None
            tb.capturekeystrokes = False
            tb.cursor.set_visible(False)

    def _on_canvas_press(self, event: Any) -> None:
        for tb in self._all_textboxes:
            if event.inaxes != tb.ax and getattr(tb, "capturekeystrokes", False):
                self._blur_textbox(tb)
                if self.fig.canvas.mouse_grabber == tb.ax:
                    self.fig.canvas.release_mouse(tb.ax)

    def _commit_text_boxes(self) -> None:
        """Stop active text editing and release widget lock so close/run never hangs."""
        for tb in self._all_textboxes:
            self._blur_textbox(tb)
            if self.fig.canvas.mouse_grabber == tb.ax:
                self.fig.canvas.release_mouse(tb.ax)
        widgetlock = getattr(self.fig.canvas, "widgetlock", None)
        if widgetlock is not None:
            for tb in self._all_textboxes:
                if widgetlock.isowner(tb):
                    widgetlock.release(tb)

    def _stop_timer(self) -> None:
        self._waiting_for_draw = False
        if getattr(self, "_timer", None) is not None:
            self._timer.stop()

    def _schedule_next_tick(self, interval: int) -> None:
        if self._closed or self.active_controller is None:
            return
        if self.active_controller.is_paused:
            return
        self._timer.interval = max(20, int(interval))
        self._timer.start()

    def _on_draw_event(self, _event=None) -> None:
        if not self._waiting_for_draw:
            return
        self._waiting_for_draw = False
        if (
            not self._closed
            and self.active_controller is not None
            and not self.active_controller.is_paused
        ):
            self._schedule_next_tick(self.active_controller.interval)

    def _on_timer_tick(self) -> None:
        if self._closed or self.active_controller is None:
            self._stop_timer()
            return
        if self.active_controller.is_paused:
            self._stop_timer()
            return
        self.active_controller._tick(0)
        if self.active_controller.is_paused:
            self._stop_timer()
            self.btn_play.label.set_text("Play")
            if not self._closed:
                self.fig.canvas.draw_idle()
            return
        if not self._closed:
            self._waiting_for_draw = True
            self.fig.canvas.draw_idle()

    def _set_status(self, message: str, *, is_error: bool = False) -> None:
        wrapped_lines = [
            textwrap.fill(line, width=42) if line else ""
            for line in message.splitlines()
        ]
        self.status_text.set_text("\n".join(wrapped_lines))
        self.status_text.set_color("#B91C1C" if is_error else "#1E293B")
        self.status_text.set_bbox(
            {
                "boxstyle": "round,pad=0.35",
                "facecolor": "#FEF2F2" if is_error else "#F8FAFC",
                "edgecolor": "#FECACA" if is_error else "#CBD5E1",
            }
        )

    def _style_button(self, btn, *, selected: bool, disabled: bool = False) -> None:
        if disabled:
            color = "#E2E8F0"
            hover = "#E2E8F0"
            fg = "#94A3B8"
        elif selected:
            color = "#2563EB"
            hover = "#1D4ED8"
            fg = "#FFFFFF"
        else:
            color = "#F1F5F9"
            hover = "#CBD5E1"
            fg = "#0F172A"
        btn.color = color
        btn.hovercolor = hover
        btn.ax.set_facecolor(color)
        btn.label.set_color(fg)

    def switch_mode(
        self, mode: str, *, run_preview: bool = False, auto_play: bool = False
    ) -> None:
        from matplotlib.widgets import RadioButtons

        self._commit_text_boxes()
        self.mode = "graph" if mode == "graph" else "sorting"
        is_sort = self.mode == "sorting"

        self._style_button(self.btn_mode_sort, selected=is_sort)
        self._style_button(self.btn_mode_graph, selected=not is_sort)

        for widget, ax in self._sort_widgets:
            ax.set_visible(is_sort)
            if isinstance(widget, RadioButtons):
                widget.active = is_sort
                widget.eventson = is_sort
            else:
                widget.set_active(is_sort)
        self.sort_constraint_text.set_visible(is_sort)
        self.sort_step3_text.set_visible(is_sort)

        for widget, ax in self._graph_widgets:
            ax.set_visible(not is_sort)
            if isinstance(widget, RadioButtons):
                widget.active = not is_sort
                widget.eventson = not is_sort
            else:
                widget.set_active(not is_sort)
        self.graph_constraint_text.set_visible(not is_sort)
        self.graph_step3_text.set_visible(not is_sort)
        self.summary_text.set_visible(not is_sort)

        if not is_sort:
            self._sync_graph_constraint_ui()

        if run_preview:
            self.run_current(auto_play=auto_play)
        elif not self._closed:
            self.fig.canvas.draw_idle()

    def _on_sort_radio_clicked(self, label: str | None) -> None:
        if self._syncing_radio or label is None:
            return
        key = self._sort_name_to_key.get(label)
        if key:
            self._select_sort_algo(key, update_preview=True)

    def _on_graph_radio_clicked(self, label: str | None) -> None:
        if self._syncing_radio or label is None:
            return
        key = self._graph_name_to_key.get(label)
        if key:
            self._select_graph_algo(key, update_preview=True)

    def _select_sort_algo(
        self, key: str, *, redraw: bool = True, update_preview: bool = False
    ) -> None:
        self.selected_sort_key = key
        guide = _SORT_GUIDES.get(key, describe_sort_constraints(get_algorithm_spec(key)))
        self.sort_constraint_text.set_text(textwrap.fill(guide, width=42))

        target_idx = next(
            i for i, spec in enumerate(ALGORITHM_SPECS) if spec.key == key
        )
        if self.radio_sort.value_selected != ALGORITHM_SPECS[target_idx].name:
            self._syncing_radio = True
            try:
                self.radio_sort.set_active(target_idx)
            finally:
                self._syncing_radio = False

        if update_preview:
            self.run_current(auto_play=False)
        elif redraw and not self._closed:
            self.fig.canvas.draw_idle()

    def _set_sort_values(self, text: str) -> None:
        self._commit_text_boxes()
        self.tb_sort_values.set_val(text)
        if not self._closed:
            self.fig.canvas.draw_idle()

    def _apply_sort_preset(self, text: str) -> None:
        self._set_sort_values(text)
        self.run_current(auto_play=False)

    def _select_graph_algo(
        self, key: str, *, redraw: bool = True, update_preview: bool = False
    ) -> None:
        self._commit_text_boxes()
        self.selected_graph_key = key

        target_idx = next(
            i for i, spec in enumerate(GRAPH_ALGORITHM_SPECS) if spec.key == key
        )
        if self.radio_graph.value_selected != GRAPH_ALGORITHM_SPECS[target_idx].name:
            self._syncing_radio = True
            try:
                self.radio_graph.set_active(target_idx)
            finally:
                self._syncing_radio = False

        self._load_graph_example(redraw=False)
        self._sync_graph_constraint_ui()
        if update_preview:
            self.run_current(auto_play=False)
        elif redraw and not self._closed:
            self.fig.canvas.draw_idle()

    def _sync_graph_constraint_ui(self) -> None:
        spec = get_graph_algorithm_spec(self.selected_graph_key)
        guide = _GRAPH_GUIDES.get(spec.key, describe_graph_constraints(spec))
        self.graph_constraint_text.set_text(textwrap.fill(guide, width=42))

        if spec.requires_directed is not None:
            self.graph_directed = spec.requires_directed
        if spec.requires_weighted is not None:
            self.graph_weighted = spec.requires_weighted

        dir_suffix = " (Lock)" if spec.requires_directed is not None else ""
        wgt_suffix = " (Lock)" if spec.requires_weighted is not None else ""
        self.btn_directed.label.set_text(
            f"Directed: {'Yes' if self.graph_directed else 'No'}{dir_suffix}"
        )
        self.btn_weighted.label.set_text(
            f"Weighted: {'Yes' if self.graph_weighted else 'No'}{wgt_suffix}"
        )
        self._style_button(
            self.btn_directed,
            selected=self.graph_directed,
            disabled=(spec.requires_directed is not None),
        )
        self._style_button(
            self.btn_weighted,
            selected=self.graph_weighted,
            disabled=(spec.requires_weighted is not None),
        )
        self.btn_directed.set_active(
            self.mode == "graph" and spec.requires_directed is None
        )
        self.btn_weighted.set_active(
            self.mode == "graph" and spec.requires_weighted is None
        )

        start_enabled = spec.requires_start or spec.optional_start
        self.tb_graph_start.set_active(self.mode == "graph" and start_enabled)
        if not start_enabled:
            self.tb_graph_start.set_val("")

    def _toggle_directed(self, _event=None) -> None:
        spec = get_graph_algorithm_spec(self.selected_graph_key)
        if spec.requires_directed is not None:
            return
        self.graph_directed = not self.graph_directed
        self._sync_graph_constraint_ui()
        if not self._closed:
            self.fig.canvas.draw_idle()

    def _toggle_weighted(self, _event=None) -> None:
        spec = get_graph_algorithm_spec(self.selected_graph_key)
        if spec.requires_weighted is not None:
            return
        self.graph_weighted = not self.graph_weighted
        self._sync_graph_constraint_ui()
        if not self._closed:
            self.fig.canvas.draw_idle()

    def _apply_graph_preset(self, kind: str) -> None:
        if kind == "example":
            self._load_graph_example(redraw=False)
        elif kind == "cycle":
            self._load_cycle_demo()
        elif kind == "disconnected":
            self._load_disconnected_demo()
        self.run_current(auto_play=False)

    def _load_graph_example(self, *, redraw: bool = True) -> None:
        self._commit_text_boxes()
        spec = get_graph_algorithm_spec(self.selected_graph_key)
        preset = GRAPH_EXAMPLES[spec.key]
        self.graph_directed = (
            spec.requires_directed
            if spec.requires_directed is not None
            else preset.directed
        )
        self.graph_weighted = (
            spec.requires_weighted
            if spec.requires_weighted is not None
            else preset.weighted
        )
        self.tb_graph_nodes.set_val(preset.nodes)
        self.tb_graph_edges.set_val(preset.edges)
        self.tb_graph_start.set_val(preset.start)
        self._sync_graph_constraint_ui()
        if redraw and not self._closed:
            self.fig.canvas.draw_idle()

    def _load_cycle_demo(self) -> None:
        """Load a cycle / negative-cycle preset suited to the selected algorithm."""
        self._commit_text_boxes()
        key = self.selected_graph_key
        if key == "bellman_ford":
            self.graph_directed = True
            self.graph_weighted = True
            self.tb_graph_nodes.set_val("")
            self.tb_graph_edges.set_val("A B 1, B C -3, C A 1")
            self.tb_graph_start.set_val("A")
        elif key == "topological_sort":
            self.graph_directed = True
            self.graph_weighted = False
            self.tb_graph_nodes.set_val("")
            self.tb_graph_edges.set_val("A B, B C, C A")
            self.tb_graph_start.set_val("")
        elif key in ("prim", "kruskal"):
            self.graph_directed = False
            self.graph_weighted = True
            self.tb_graph_nodes.set_val("")
            self.tb_graph_edges.set_val("A B 3, B C 1, A C 4, C D 2, B D 5")
            self.tb_graph_start.set_val("A" if key == "prim" else "")
        else:
            self.graph_directed = True
            self.graph_weighted = key == "dijkstra"
            self.tb_graph_nodes.set_val("")
            self.tb_graph_edges.set_val(
                "A B 2, B C 3, C A 1, C D 4"
                if self.graph_weighted
                else "A B, B C, C A, C D"
            )
            self.tb_graph_start.set_val("A")
        self._sync_graph_constraint_ui()
        if not self._closed:
            self.fig.canvas.draw_idle()

    def _load_disconnected_demo(self) -> None:
        """Load a disconnected multi-component graph with an isolated node."""
        self._commit_text_boxes()
        spec = get_graph_algorithm_spec(self.selected_graph_key)
        self.graph_directed = (
            spec.requires_directed if spec.requires_directed is not None else False
        )
        self.graph_weighted = (
            spec.requires_weighted if spec.requires_weighted is not None else False
        )
        self.tb_graph_nodes.set_val("A B C D E F")
        if self.graph_weighted:
            self.tb_graph_edges.set_val("A B 2, B C 3, D E 4")
        else:
            self.tb_graph_edges.set_val("A B, B C, D E")
        self.tb_graph_start.set_val(
            "A" if (spec.requires_start or spec.optional_start) else ""
        )
        self._sync_graph_constraint_ui()
        if not self._closed:
            self.fig.canvas.draw_idle()

    def _clear_graph_fields(self) -> None:
        self._commit_text_boxes()
        self.tb_graph_nodes.set_val("")
        self.tb_graph_edges.set_val("")
        self.tb_graph_start.set_val("")
        if not self._closed:
            self.fig.canvas.draw_idle()

    def run_current(self, _event=None, *, auto_play: bool = True) -> bool:
        """Validate current inputs, run the pure algorithm, and start animation."""
        self._commit_text_boxes()
        interval = int(self.slider_speed.val)
        try:
            if self.mode == "sorting":
                req = build_sorting_request(
                    self.selected_sort_key,
                    self.tb_sort_values.text,
                    str(interval),
                )
                return self._launch_sorting(req, auto_play=auto_play)

            g_req = build_graph_request(
                self.selected_graph_key,
                directed=self.graph_directed,
                weighted=self.graph_weighted,
                nodes_raw=self.tb_graph_nodes.text,
                edges_raw=self.tb_graph_edges.text,
                start_raw=self.tb_graph_start.text,
                interval_raw=str(interval),
            )
            return self._launch_graph(g_req, auto_play=auto_play)
        except (ValueError, TypeError) as exc:
            self._set_status(f"Input error: {exc}", is_error=True)
            if not self._closed:
                self.fig.canvas.draw_idle()
            return False

    def _launch_sorting(
        self, req: SortingInputRequest, *, auto_play: bool = True
    ) -> bool:
        from sortlab.visualization.matplotlib import SortAnimationController

        t0 = perf_counter()
        sorted_vals = req.spec.algorithm(req.values)
        elapsed = perf_counter() - t0
        preview = ", ".join(str(v) for v in sorted_vals[:8])
        if len(sorted_vals) > 8:
            preview += ", ..."

        events = list(req.spec.event_generator(req.values))
        self._stop_timer()
        self.ax_vis.clear()
        self.summary_text.set_visible(False)

        ctrl = SortAnimationController(
            fig=self.fig,
            ax=self.ax_vis,
            events=events,
            algorithm_name=req.spec.name,
            interval=req.interval or int(self.slider_speed.val),
            max_frames=800,
            external_ui=self._external_ui,
        )
        self.active_controller = ctrl
        self._apply_playback_mode(ctrl, auto_play=auto_play)
        if auto_play:
            self._set_status(
                f"Running {req.spec.name} ({elapsed:.6f}s)\n"
                f"Sorted ({len(sorted_vals)}): [{preview}]"
            )
        else:
            self._set_status(
                f"Preview ready: {req.spec.name}\n"
                "Adjust inputs or click Run & Visualize to start."
            )
        if not self._closed:
            self.fig.canvas.draw_idle()
        return True

    def _launch_graph(
        self, req: GraphInputRequest, *, auto_play: bool = True
    ) -> bool:
        from sortlab.visualization.graph_matplotlib import GraphAnimationController

        status_msg = ""
        try:
            t0 = perf_counter()
            if req.spec.requires_start or req.spec.optional_start:
                result = req.spec.algorithm(req.graph, req.start)
            else:
                result = req.spec.algorithm(req.graph)
            elapsed = perf_counter() - t0
            status_msg = _format_studio_graph_summary(
                req.spec, req.graph, result, elapsed
            )
        except (NegativeCycleError, GraphCycleError) as exc:
            status_msg = f"Cycle detected: {exc}"

        if req.spec.requires_start or req.spec.optional_start:
            events = list(req.spec.event_generator(req.graph, req.start))
        else:
            events = list(req.spec.event_generator(req.graph))

        self._stop_timer()
        self.ax_vis.clear()
        self.summary_text.set_visible(True)

        ctrl = GraphAnimationController(
            fig=self.fig,
            ax=self.ax_vis,
            graph=req.graph,
            events=events,
            algorithm_name=req.spec.name,
            interval=req.interval or int(self.slider_speed.val),
            max_frames=800,
            external_ui=self._external_ui,
        )
        self.active_controller = ctrl
        self._apply_playback_mode(ctrl, auto_play=auto_play)
        if auto_play or status_msg.startswith("Cycle detected"):
            self._set_status(status_msg)
        else:
            self._set_status(
                f"Preview ready: {req.spec.name}\n"
                "Adjust graph or click Run & Visualize to start."
            )
        if not self._closed:
            self.fig.canvas.draw_idle()
        return True

    def _apply_playback_mode(self, ctrl: Any, *, auto_play: bool) -> None:
        self._stop_timer()
        self._timer.interval = ctrl.interval
        if not auto_play or ctrl.total_rendered <= 1:
            ctrl.is_paused = True
            self.btn_play.label.set_text("Play")
        else:
            ctrl.is_paused = False
            self.btn_play.label.set_text("Pause")
            self._schedule_next_tick(ctrl.interval)

    def _on_play(self, _event=None) -> None:
        ctrl = self.active_controller
        if ctrl is None or self._closed:
            return
        if ctrl.is_paused:
            if ctrl.current_render_idx >= ctrl.total_rendered - 1:
                ctrl.render_frame(0)
            ctrl.is_paused = False
            self.btn_play.label.set_text("Pause")
            self._stop_timer()
            self._schedule_next_tick(ctrl.interval)
        else:
            ctrl.is_paused = True
            self.btn_play.label.set_text("Play")
            self._stop_timer()
        self.fig.canvas.draw_idle()

    def _on_step(self, _event=None) -> None:
        ctrl = self.active_controller
        if ctrl is None or self._closed:
            return
        self._stop_timer()
        ctrl.step_once()

    def _on_reset(self, _event=None) -> None:
        ctrl = self.active_controller
        if ctrl is None or self._closed:
            return
        self._stop_timer()
        ctrl.reset()

    def _on_speed(self, val: float) -> None:
        ctrl = self.active_controller
        if ctrl is None or self._closed:
            return
        was_playing = not ctrl.is_paused
        ctrl._on_speed_change(val)
        self._stop_timer()
        self._timer.interval = ctrl.interval
        if was_playing:
            self._schedule_next_tick(ctrl.interval)

    def _on_close_event(self, _event=None) -> None:
        import matplotlib.pyplot as plt

        self.shutdown()
        if not plt.get_fignums():
            _stop_macosx_event_loop()

    def close(self, _event=None) -> None:
        """Stop timers, release input grabs, and close the window safely."""
        import matplotlib.pyplot as plt

        if self._close_pending or self._closed:
            return
        self._close_pending = True
        self.shutdown()

        def _do_close() -> None:
            self._close_timer = None
            if plt.fignum_exists(self.fig.number):
                plt.close(self.fig)
            if not plt.get_fignums():
                _stop_macosx_event_loop()

        if hasattr(self.fig.canvas, "new_timer"):
            # Keep a reference on self so TimerBase.__del__ cannot cancel it early.
            timer = self.fig.canvas.new_timer(interval=10)
            timer.single_shot = True
            timer.add_callback(_do_close)
            self._close_timer = timer
            timer.start()
        else:
            _do_close()

    def shutdown(self) -> None:
        """Stop all timers and disconnect input focus cleanly."""
        self._closed = True
        self._stop_timer()
        if getattr(self, "_timer", None) is not None:
            self._timer.callbacks.clear()
        self.fig.stale = False
        self._commit_text_boxes()
        self.active_controller = None


def launch_gui_studio(
    *,
    initial_mode: str = "sorting",
    default_interval: int | None = None,
    show: bool = True,
) -> SortLabStudio:
    """Open the single-window SortLab Matplotlib Studio."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is optional. Install it with: pip install sortlab[visualization]"
        ) from exc

    fig = plt.figure(figsize=(14.2, 8.4))
    manager = getattr(fig.canvas, "manager", None)
    if manager is not None and hasattr(manager, "set_window_title"):
        manager.set_window_title("SortLab — Desktop Studio")

    studio = SortLabStudio(
        fig,
        initial_mode=initial_mode,
        default_interval=default_interval,
    )

    if show:
        try:
            plt.show()
        finally:
            studio.shutdown()
            if plt.fignum_exists(fig.number):
                plt.close(fig)
            _stop_macosx_event_loop()
    else:
        fig.canvas.draw()

    return studio
