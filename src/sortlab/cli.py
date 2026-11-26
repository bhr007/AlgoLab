"""Interactive command-line interface for AlgoLab."""

from __future__ import annotations

import argparse
import math
import sys
from time import perf_counter
from typing import Any, Callable

from sortlab.core.registry import (
    ALGORITHM_REGISTRY,
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
    GRAPH_ALGORITHM_REGISTRY,
    GRAPH_ALGORITHM_SPECS,
    GraphAlgorithmSpec,
    get_graph_algorithm_spec,
    validate_graph_for_spec,
)

# Preserved for backward compatibility with callers inspecting cli.ALGORITHMS.
ALGORITHMS: dict[str, tuple[str, Callable]] = {
    spec.choice: (spec.name, spec.algorithm) for spec in ALGORITHM_SPECS
}


def show_main_menu() -> None:
    """Print the top-level AlgoLab mode selection menu."""
    print("\n========== AlgoLab ==========")
    print("Explore. Visualize. Understand Algorithms.\n")
    print("   1. Sorting Algorithms (CLI + Visualization)")
    print("   2. Graph Algorithms (CLI + Visualization)")
    print("   3. Launch Desktop GUI Studio (Single Window)")
    print("   0. Exit")
    print("=============================\n")


def show_sorting_menu() -> None:
    """Print the sorting algorithm selection menu."""
    print("\n===== Sorting Algorithms =====")
    for spec in ALGORITHM_SPECS:
        note = " (integers only)" if spec.integer_only else ""
        print(f"  {spec.choice:>2}. {spec.name}{note}")
    print("   0. Back to Main Menu")
    print("==============================\n")


# Preserved alias for existing callers.
show_menu = show_sorting_menu


def show_graph_menu() -> None:
    """Print the graph algorithm selection menu."""
    print("\n====== Graph Algorithms ======")
    for spec in GRAPH_ALGORITHM_SPECS:
        notes: list[str] = []
        if spec.requires_directed is True:
            notes.append("directed")
        elif spec.requires_directed is False:
            notes.append("undirected")
        if spec.requires_non_negative_weights:
            notes.append("non-negative weights")
        elif spec.requires_weighted:
            notes.append("weighted")
        note_str = f" ({', '.join(notes)})" if notes else ""
        print(f"  {spec.choice:>2}. {spec.name}{note_str}")
    print("   0. Back to Main Menu")
    print("==============================\n")


def _parse_finite_number(token: str) -> float:
    """Parse a single integer or finite float token."""
    if "." not in token and "e" not in token.lower():
        try:
            return int(token)
        except ValueError:
            pass
    try:
        number = float(token)
    except ValueError as exc:
        raise ValueError(f"{token!r} is not a valid number.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{token!r} is not a finite number.")
    return int(number) if number.is_integer() else number


def parse_values(raw: str) -> list[float]:
    """Parse a comma- or whitespace-separated list of finite numbers."""
    parts = raw.replace(",", " ").split()
    if not parts:
        raise ValueError("Please enter at least one number.")
    return [_parse_finite_number(part) for part in parts]


def parse_yes_no(raw: str, *, default: bool = False) -> bool:
    """Parse a yes/no response, returning ``default`` when empty."""
    cleaned = raw.strip().lower()
    if not cleaned:
        return default
    if cleaned in ("y", "yes"):
        return True
    if cleaned in ("n", "no"):
        return False
    raise ValueError("Please enter 'y' or 'n'.")


def parse_node_list(raw: str) -> list[str]:
    """Parse optional comma- or whitespace-separated node identifiers."""
    parts = raw.replace(",", " ").split()
    return [part.strip() for part in parts if part.strip()]


def parse_graph_edges(raw: str, *, weighted: bool) -> list[tuple[Any, ...]]:
    """Parse comma- or semicolon-separated edge entries.

    Each segment has the form ``u v`` for unweighted graphs or ``u v weight``
    for weighted graphs (``->`` is also accepted between ``u`` and ``v``).
    """
    cleaned = raw.strip()
    if not cleaned:
        return []

    segments = [
        segment.strip()
        for segment in cleaned.replace(";", "\n").replace(",", "\n").splitlines()
        if segment.strip()
    ]
    edges: list[tuple[Any, ...]] = []
    for segment in segments:
        tokens = segment.replace("->", " ").split()
        if weighted:
            if len(tokens) != 3:
                raise ValueError(
                    f"Weighted edge {segment!r} must have 3 values: 'u v weight'."
                )
            u, v, w_tok = tokens
            weight = _parse_finite_number(w_tok)
            edges.append((u, v, weight))
        else:
            if len(tokens) != 2:
                raise ValueError(
                    f"Unweighted edge {segment!r} must have 2 values: 'u v'."
                )
            u, v = tokens
            edges.append((u, v))
    return edges


def build_graph_from_input(
    nodes_raw: str,
    edges_raw: str,
    *,
    directed: bool,
    weighted: bool,
) -> Graph:
    """Build and validate a :class:`Graph` from raw CLI text inputs."""
    nodes = parse_node_list(nodes_raw)
    edges = parse_graph_edges(edges_raw, weighted=weighted)
    if not nodes and not edges:
        raise ValueError("Please enter at least one node or edge.")
    return Graph(directed=directed, weighted=weighted, nodes=nodes, edges=edges)


def resolve_cli_start_node(raw: str, graph: Graph, *, optional: bool) -> Node | None:
    """Resolve and validate a user-entered start node against ``graph``."""
    cleaned = raw.strip()
    if not cleaned:
        if optional:
            return None
        raise ValueError("Please enter a starting node.")
    if graph.has_node(cleaned):
        return cleaned
    try:
        as_int = int(cleaned)
    except ValueError:
        as_int = None
    if as_int is not None and graph.has_node(as_int):
        return as_int
    raise ValueError(f"Start node {cleaned!r} is not in the graph.")


def run_algorithm(choice: str, values: list[float]) -> list[float]:
    """Validate inputs and dispatch to the selected sorting implementation."""
    spec = get_algorithm_spec(choice)
    validate_inputs_for_spec(spec, values)
    return spec.algorithm(values)


def run_graph_algorithm(
    choice: str, graph: Graph, start: Node | None = None
) -> Any:
    """Validate inputs and dispatch to the selected graph implementation."""
    spec = get_graph_algorithm_spec(choice)
    validate_graph_for_spec(spec, graph, start)
    if spec.requires_start or spec.optional_start:
        return spec.algorithm(graph, start)
    return spec.algorithm(graph)


def visualize_algorithm(
    spec: AlgorithmSpec,
    values: list[float],
    *,
    interval: int | None = None,
    max_frames: int | None = 1500,
    show: bool = True,
):
    """Generate events for ``spec`` and launch the sorting Matplotlib animation."""
    from sortlab.visualization.matplotlib import animate_events

    events = spec.event_generator(values)
    return animate_events(
        events,
        interval=interval,
        algorithm_name=spec.name,
        show=show,
        max_frames=max_frames,
    )


def visualize_graph_algorithm(
    spec: GraphAlgorithmSpec,
    graph: Graph,
    start: Node | None = None,
    *,
    interval: int | None = None,
    max_frames: int | None = 1500,
    show: bool = True,
):
    """Generate graph events for ``spec`` and launch the Matplotlib animation."""
    from sortlab.visualization.graph_matplotlib import animate_graph_events

    if spec.requires_start or spec.optional_start:
        events = spec.event_generator(graph, start)
    else:
        events = spec.event_generator(graph)

    return animate_graph_events(
        events,
        graph=graph,
        interval=interval,
        algorithm_name=spec.name,
        show=show,
        max_frames=max_frames,
    )


def _print_graph_result(
    spec: GraphAlgorithmSpec,
    graph: Graph,
    start: Node | None,
    result: Any,
) -> None:
    """Pretty-print pure graph algorithm output."""
    if isinstance(result, ShortestPathResult):
        print(f"Shortest paths from {result.start}:")
        for node in graph.nodes:
            dist = result.distances[node]
            if math.isinf(dist):
                print(f"  {result.start} -> {node}: unreachable")
            else:
                path = " -> ".join(str(p) for p in result.path_to(node))
                dist_str = (
                    str(int(dist))
                    if float(dist).is_integer()
                    else f"{dist:g}"
                )
                print(f"  {result.start} -> {node} (distance={dist_str}): {path}")
    elif isinstance(result, MSTResult):
        kind = (
            "Minimum Spanning Tree"
            if result.is_spanning
            else f"Minimum Spanning Forest ({result.components} components)"
        )
        print(f"{kind} edges ({len(result.edges)}):")
        for edge in result.edges:
            print(f"  {edge.source} -- {edge.target} (weight={edge.weight})")
        print(f"Total weight: {result.total_weight:g}")
    elif isinstance(result, list):
        label = (
            "Topological order"
            if spec.key == "topological_sort"
            else f"Traversal order from {start}"
        )
        print(f"{label}: {' -> '.join(str(node) for node in result)}")


def _execute_sorting_request(
    spec: AlgorithmSpec,
    values: list[float],
    args: argparse.Namespace,
    *,
    interval_override: int | None = None,
) -> None:
    """Run, print timing/output, and optionally visualize a sorting request."""
    validate_inputs_for_spec(spec, values)

    # Time only the pure sorting implementation, separate from event
    # generation and Matplotlib visualization overhead.
    start_time = perf_counter()
    result = spec.algorithm(values)
    elapsed = perf_counter() - start_time

    print(f"\nAlgorithm: {spec.name}")
    print(f"Original:  {values}")
    print(f"Sorted:    {result}")
    print(f"Sort time: {elapsed:.6f} seconds (algorithm only)\n")

    if not args.no_vis:
        print(
            f"Opening Matplotlib visualization for {spec.name} "
            "(close the window to return to the menu)..."
        )
        try:
            visualize_algorithm(
                spec,
                values,
                interval=interval_override if interval_override is not None else args.interval,
            )
        except ImportError as exc:
            print(f"Visualization unavailable: {exc}\n")


def _execute_graph_request(
    spec: GraphAlgorithmSpec,
    graph: Graph,
    start_node: Node | None,
    args: argparse.Namespace,
    *,
    interval_override: int | None = None,
) -> None:
    """Run, print timing/output, and optionally visualize a graph request."""
    validate_graph_for_spec(spec, graph, start_node)

    print(
        f"\nAlgorithm: {spec.name} "
        f"({'Directed' if graph.directed else 'Undirected'}, "
        f"{'Weighted' if graph.weighted else 'Unweighted'}, "
        f"{graph.node_count} nodes, {graph.edge_count} edges)"
    )

    try:
        start_time = perf_counter()
        if spec.requires_start or spec.optional_start:
            result = spec.algorithm(graph, start_node)
        else:
            result = spec.algorithm(graph)
        elapsed = perf_counter() - start_time

        _print_graph_result(spec, graph, start_node, result)
        print(f"Execution time: {elapsed:.6f} seconds (algorithm only)\n")
    except (NegativeCycleError, GraphCycleError) as exc:
        # Cycle-detection algorithms still visualize the cycle cleanly.
        print(f"Cycle notice: {exc}\n")

    if not args.no_vis:
        print(
            f"Opening Matplotlib visualization for {spec.name} "
            "(close the window to return to the menu)..."
        )
        try:
            visualize_graph_algorithm(
                spec,
                graph,
                start_node,
                interval=interval_override if interval_override is not None else args.interval,
            )
        except ImportError as exc:
            print(f"Visualization unavailable: {exc}\n")


def _run_sorting_menu(args: argparse.Namespace) -> None:
    """Interactive loop for the Sorting Algorithms submenu."""
    while True:
        show_sorting_menu()
        try:
            choice = input("Choose a sorting algorithm (0-10): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to main menu...")
            return

        if choice == "0":
            return
        if choice not in ALGORITHM_REGISTRY:
            print("Invalid choice. Please select a number from 0 to 10.")
            continue

        spec = ALGORITHM_REGISTRY[choice]
        try:
            raw_values = input(
                "\nEnter numbers separated by spaces or commas: "
            )
            values = parse_values(raw_values)
            _execute_sorting_request(spec, values, args)
        except (ValueError, TypeError) as exc:
            print(f"Could not sort these values: {exc}\n")
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to the sorting menu...\n")


def _run_graph_menu(args: argparse.Namespace) -> None:
    """Interactive loop for the Graph Algorithms submenu."""
    while True:
        show_graph_menu()
        try:
            choice = input("Choose a graph algorithm (0-7): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to main menu...")
            return

        if choice == "0":
            return
        if choice not in GRAPH_ALGORITHM_REGISTRY:
            print("Invalid choice. Please select a number from 0 to 7.")
            continue

        spec = GRAPH_ALGORITHM_REGISTRY[choice]
        try:
            if spec.requires_directed is None:
                directed = parse_yes_no(
                    input("\nDirected graph? (y/n) [n]: "), default=False
                )
            else:
                directed = spec.requires_directed
                kind_note = "directed" if directed else "undirected"
                print(f"\nNote: {spec.name} uses a {kind_note} graph.")

            if spec.requires_weighted is None:
                weighted = parse_yes_no(
                    input("Weighted graph? (y/n) [n]: "), default=False
                )
            else:
                weighted = spec.requires_weighted
                print(f"Note: {spec.name} uses a weighted graph.")

            nodes_raw = input(
                "Enter node names (optional, space/comma separated, or Enter to infer from edges): "
            )
            edge_hint = "A B 4, B C 2" if weighted else "A B, B C"
            edges_raw = input(
                f"Enter edges separated by commas/semicolons (e.g. {edge_hint}): "
            )
            graph = build_graph_from_input(
                nodes_raw, edges_raw, directed=directed, weighted=weighted
            )

            start_node: Node | None = None
            if spec.requires_start:
                start_raw = input(
                    f"Enter starting node (available: {', '.join(str(n) for n in graph.nodes)}): "
                )
                start_node = resolve_cli_start_node(start_raw, graph, optional=False)
            elif spec.optional_start:
                default_node = graph.nodes[0] if graph.nodes else ""
                start_raw = input(
                    f"Enter optional starting node [{default_node}]: "
                )
                start_node = resolve_cli_start_node(start_raw, graph, optional=True)

            _execute_graph_request(spec, graph, start_node, args)
        except (ValueError, TypeError) as exc:
            print(f"Invalid graph input: {exc}\n")
        except (EOFError, KeyboardInterrupt):
            print("\nReturning to the graph menu...\n")


def _run_gui_loop(args: argparse.Namespace) -> None:
    """Launch the single-window native Matplotlib desktop GUI studio."""
    from sortlab.gui import launch_gui_studio

    try:
        launch_gui_studio(default_interval=args.interval, show=True)
    except ImportError as exc:
        print(f"GUI Studio unavailable: {exc}\n")


def main(argv=None) -> int:
    """Run the interactive AlgoLab CLI."""
    parser = argparse.ArgumentParser(
        prog="algolab",
        description=(
            "AlgoLab — Explore. Visualize. Understand Algorithms. "
            "Choose and visualize sorting or graph algorithms."
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list all available sorting and graph algorithms and exit",
    )
    parser.add_argument(
        "--no-vis",
        action="store_true",
        help="run algorithms without opening the Matplotlib visualization window",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="animation delay between frames in milliseconds",
    )
    parser.add_argument(
        "--mode",
        choices=("cli", "cli-gui", "gui"),
        default=None,
        help=(
            "operating mode: 'cli' (terminal only), 'cli-gui' (terminal + visualization), "
            "or 'gui' (single-window desktop GUI)"
        ),
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="launch the single-window desktop GUI studio directly",
    )
    args = parser.parse_args(argv)

    if args.mode == "cli":
        args.no_vis = True
    elif args.mode == "gui":
        args.gui = True

    if args.list:
        print("Sorting Algorithms:")
        for spec in ALGORITHM_SPECS:
            note = " (integers only)" if spec.integer_only else ""
            print(f"{spec.choice:>2}. {spec.name}{note}")
        print("\nGraph Algorithms:")
        for spec in GRAPH_ALGORITHM_SPECS:
            print(f"{spec.choice:>2}. {spec.name}")
        return 0

    if args.interval is not None and args.interval < 1:
        parser.error("--interval must be at least 1 ms")

    if args.gui:
        _run_gui_loop(args)
        print("Goodbye!")
        return 0

    while True:
        show_main_menu()
        try:
            mode = input("Choose a module (0-3): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if mode == "0":
            print("Goodbye!")
            return 0
        if mode == "1":
            _run_sorting_menu(args)
        elif mode == "2":
            _run_graph_menu(args)
        elif mode == "3":
            _run_gui_loop(args)
        else:
            print("Invalid choice. Please select 0, 1, 2, or 3.")


if __name__ == "__main__":
    sys.exit(main())
