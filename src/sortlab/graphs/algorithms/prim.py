"""Prim's Minimum Spanning Tree / Forest algorithm for AlgoLab graphs."""

from __future__ import annotations

import heapq
from itertools import count

from sortlab.graphs.model import Graph, GraphEdge, MSTResult, Node, Weight


def prim(graph: Graph, start: Node | None = None) -> MSTResult:
    """Compute a Minimum Spanning Tree (or Forest if disconnected) using Prim's algorithm.

    Constraints:
        - Requires an **undirected** graph (``graph.directed == False``).
        - Supports positive, zero, and negative edge weights.
        - On disconnected graphs, grows an MST from ``start`` (or the first node)
          and restarts on remaining unvisited components to form a Minimum
          Spanning Forest (``result.is_spanning == False``).

    Complexity:
        - Time: O((V + E) log V) using a binary min-heap
        - Space: O(V + E)
    """
    graph.validate()
    if graph.directed:
        raise ValueError("Prim's algorithm requires an undirected graph")

    if graph.node_count == 0:
        if start is not None:
            raise ValueError(f"Start node {start!r} is not in the graph")
        return MSTResult(edges=(), total_weight=0.0, is_spanning=True, components=0)

    root = graph.nodes[0] if start is None else start
    if not graph.has_node(root):
        raise ValueError(f"Start node {root!r} is not in the graph")

    visited: set[Node] = set()
    mst_edges: list[GraphEdge] = []
    total_weight: float = 0.0
    components = 0
    tie_breaker = count()

    seeds = [root] + [node for node in graph.nodes if node != root]
    for seed in seeds:
        if seed in visited:
            continue
        components += 1
        visited.add(seed)
        heap: list[tuple[Weight, int, Node, Node]] = []
        for neighbor, weight in graph.neighbors(seed):
            if neighbor not in visited:
                heapq.heappush(heap, (weight, next(tie_breaker), seed, neighbor))

        while heap:
            weight, _, u, v = heapq.heappop(heap)
            if v in visited:
                continue
            visited.add(v)
            mst_edges.append(GraphEdge(source=u, target=v, weight=weight))
            total_weight += weight

            for neighbor, next_weight in graph.neighbors(v):
                if neighbor not in visited:
                    heapq.heappush(heap, (next_weight, next(tie_breaker), v, neighbor))

    return MSTResult(
        edges=tuple(mst_edges),
        total_weight=total_weight,
        is_spanning=(components <= 1),
        components=components,
    )
