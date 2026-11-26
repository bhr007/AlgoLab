"""Central registry for SortLab graph algorithms and their event generators."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

from sortlab.graphs.algorithms import (
    bellman_ford,
    bfs,
    dfs,
    dijkstra,
    kruskal,
    prim,
    topological_sort,
)
from sortlab.graphs.events import GraphEvent
from sortlab.graphs.model import Graph, Node
from sortlab.graphs.runner import (
    bellman_ford_events,
    bfs_events,
    dfs_events,
    dijkstra_events,
    kruskal_events,
    prim_events,
    topological_sort_events,
)


@dataclass(frozen=True)
class GraphAlgorithmSpec:
    """Metadata and callable entry points for one registered graph algorithm."""

    choice: str
    key: str
    name: str
    category: str
    requires_start: bool
    optional_start: bool = False
    requires_directed: bool | None = None
    requires_weighted: bool | None = None
    requires_non_negative_weights: bool = False
    algorithm: Callable[..., Any] = bfs
    event_generator: Callable[..., Iterator[GraphEvent]] = bfs_events


GRAPH_ALGORITHM_SPECS: tuple[GraphAlgorithmSpec, ...] = (
    GraphAlgorithmSpec(
        choice="1",
        key="bfs",
        name="Breadth-First Search (BFS)",
        category="Traversal",
        requires_start=True,
        algorithm=bfs,
        event_generator=bfs_events,
    ),
    GraphAlgorithmSpec(
        choice="2",
        key="dfs",
        name="Depth-First Search (DFS)",
        category="Traversal",
        requires_start=True,
        algorithm=dfs,
        event_generator=dfs_events,
    ),
    GraphAlgorithmSpec(
        choice="3",
        key="dijkstra",
        name="Dijkstra's Shortest Path",
        category="Shortest Path",
        requires_start=True,
        requires_weighted=True,
        requires_non_negative_weights=True,
        algorithm=dijkstra,
        event_generator=dijkstra_events,
    ),
    GraphAlgorithmSpec(
        choice="4",
        key="bellman_ford",
        name="Bellman-Ford Shortest Path",
        category="Shortest Path",
        requires_start=True,
        requires_weighted=True,
        algorithm=bellman_ford,
        event_generator=bellman_ford_events,
    ),
    GraphAlgorithmSpec(
        choice="5",
        key="prim",
        name="Prim's Minimum Spanning Tree",
        category="Minimum Spanning Tree",
        requires_start=False,
        optional_start=True,
        requires_directed=False,
        requires_weighted=True,
        algorithm=prim,
        event_generator=prim_events,
    ),
    GraphAlgorithmSpec(
        choice="6",
        key="kruskal",
        name="Kruskal's Minimum Spanning Tree",
        category="Minimum Spanning Tree",
        requires_start=False,
        requires_directed=False,
        requires_weighted=True,
        algorithm=kruskal,
        event_generator=kruskal_events,
    ),
    GraphAlgorithmSpec(
        choice="7",
        key="topological_sort",
        name="Topological Sort (DAG)",
        category="DAG Ordering",
        requires_start=False,
        requires_directed=True,
        algorithm=topological_sort,
        event_generator=topological_sort_events,
    ),
)

GRAPH_ALGORITHM_REGISTRY: dict[str, GraphAlgorithmSpec] = {
    spec.choice: spec for spec in GRAPH_ALGORITHM_SPECS
}

_BY_KEY: dict[str, GraphAlgorithmSpec] = {
    spec.key: spec for spec in GRAPH_ALGORITHM_SPECS
}
_BY_NAME: dict[str, GraphAlgorithmSpec] = {
    spec.name.lower(): spec for spec in GRAPH_ALGORITHM_SPECS
}


def get_graph_algorithm_spec(identifier: str) -> GraphAlgorithmSpec:
    """Look up a :class:`GraphAlgorithmSpec` by menu number, key, or display name."""
    cleaned = identifier.strip()
    if cleaned in GRAPH_ALGORITHM_REGISTRY:
        return GRAPH_ALGORITHM_REGISTRY[cleaned]
    lowered = cleaned.lower()
    if lowered in _BY_KEY:
        return _BY_KEY[lowered]
    if lowered in _BY_NAME:
        return _BY_NAME[lowered]
    raise ValueError(f"Unknown graph algorithm selection: {identifier!r}")


def validate_graph_for_spec(
    spec: GraphAlgorithmSpec,
    graph: Graph,
    start: Node | None = None,
) -> None:
    """Validate graph topology, edge weights, and start node against ``spec``."""
    graph.validate()
    if spec.requires_directed is True and not graph.directed:
        raise ValueError(f"{spec.name} requires a directed graph.")
    if spec.requires_directed is False and graph.directed:
        raise ValueError(f"{spec.name} requires an undirected graph.")
    if spec.requires_non_negative_weights and any(
        edge.weight < 0 for edge in graph.edges
    ):
        raise ValueError(f"{spec.name} requires non-negative edge weights.")
    if spec.requires_start:
        if graph.node_count == 0:
            raise ValueError(f"{spec.name} requires a non-empty graph.")
        if start is None or not graph.has_node(start):
            raise ValueError(
                f"Start node {start!r} is not present in the graph."
            )
    elif spec.optional_start and start is not None and not graph.has_node(start):
        raise ValueError(f"Start node {start!r} is not present in the graph.")
