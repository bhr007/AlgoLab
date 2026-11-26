"""Dijkstra's shortest-path algorithm for AlgoLab graphs."""

from __future__ import annotations

import heapq
import math
from itertools import count

from sortlab.graphs.model import Graph, Node, ShortestPathResult


def dijkstra(graph: Graph, start: Node | None = None) -> ShortestPathResult:
    """Compute single-source shortest paths using Dijkstra's algorithm.

    Constraints:
        - Supports directed and undirected graphs.
        - Requires all edge weights to be non-negative (``weight >= 0``).
        - Unreachable vertices receive distance ``float('inf')`` and predecessor ``None``.

    Complexity:
        - Time: O((V + E) log V) with a binary min-heap
        - Space: O(V + E)
    """
    graph.validate()
    if any(edge.weight < 0 for edge in graph.edges):
        raise ValueError("Dijkstra's algorithm requires non-negative edge weights")

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

    tie_breaker = count()
    heap: list[tuple[float, int, Node]] = [(0, next(tie_breaker), root)]
    finalized: set[Node] = set()

    while heap:
        current_dist, _, current = heapq.heappop(heap)
        if current in finalized:
            continue
        finalized.add(current)

        for neighbor, weight in graph.neighbors(current):
            if neighbor in finalized:
                continue
            candidate = current_dist + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                predecessors[neighbor] = current
                heapq.heappush(heap, (candidate, next(tie_breaker), neighbor))

    return ShortestPathResult(
        start=root,
        distances=distances,
        predecessors=predecessors,
    )
