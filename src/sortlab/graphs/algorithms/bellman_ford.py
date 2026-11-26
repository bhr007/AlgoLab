"""Bellman-Ford shortest-path algorithm for AlgoLab graphs."""

from __future__ import annotations

import math

from sortlab.graphs.model import (
    Graph,
    NegativeCycleError,
    Node,
    ShortestPathResult,
    Weight,
)


def _directed_edge_list(graph: Graph) -> list[tuple[Node, Node, Weight]]:
    """Expand edges into directed relaxation pairs."""
    pairs: list[tuple[Node, Node, Weight]] = []
    for edge in graph.edges:
        pairs.append((edge.source, edge.target, edge.weight))
        if not graph.directed and edge.source != edge.target:
            pairs.append((edge.target, edge.source, edge.weight))
    return pairs


def bellman_ford(graph: Graph, start: Node | None = None) -> ShortestPathResult:
    """Compute single-source shortest paths using the Bellman-Ford algorithm.

    Constraints:
        - Supports directed and undirected graphs (note: any reachable negative
          edge in an undirected graph forms a 2-cycle of negative total weight).
        - Supports negative edge weights on directed graphs.
        - Raises :class:`NegativeCycleError` (a ``ValueError`` subclass) if a
          negative-weight cycle is reachable from ``start``.

    Complexity:
        - Time: O(V * E)
        - Space: O(V)
    """
    graph.validate()
    if graph.node_count == 0:
        if start is not None:
            raise ValueError(f"Start node {start!r} is not in the graph")
        return ShortestPathResult(start="", distances={}, predecessors={})

    root = graph.nodes[0] if start is None else start
    if not graph.has_node(root):
        raise ValueError(f"Start node {root!r} is not in the graph")

    distances: dict[Node, float] = {node: math.inf for node in graph.nodes}
    predecessors: dict[Node, Node | None] = {node: None for node in graph.nodes}
    distances[root] = 0

    relax_edges = _directed_edge_list(graph)
    node_count = graph.node_count

    for _ in range(node_count - 1):
        updated = False
        for u, v, weight in relax_edges:
            if math.isinf(distances[u]):
                continue
            candidate = distances[u] + weight
            if candidate < distances[v]:
                distances[v] = candidate
                predecessors[v] = u
                updated = True
        if not updated:
            break

    for u, v, weight in relax_edges:
        if not math.isinf(distances[u]) and distances[u] + weight < distances[v]:
            raise NegativeCycleError(
                "Graph contains a negative-weight cycle reachable from the start node"
            )

    return ShortestPathResult(
        start=root,
        distances=distances,
        predecessors=predecessors,
    )
