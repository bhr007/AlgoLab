"""Breadth-First Search (BFS) implementation for SortLab graphs."""

from __future__ import annotations

from collections import deque

from sortlab.graphs.model import Graph, Node


def bfs(
    graph: Graph,
    start: Node | None = None,
    *,
    traverse_all: bool = False,
) -> list[Node]:
    """Return nodes visited by Breadth-First Search starting at ``start``.

    Works on directed or undirected, weighted or unweighted graphs (edge weights
    are ignored). When ``traverse_all=False`` (default), only vertices reachable
    from ``start`` are returned. When ``traverse_all=True``, disconnected
    components are subsequently traversed in graph insertion order.

    Complexity:
        - Time: O(V + E)
        - Space: O(V)
    """
    if graph.node_count == 0:
        if start is not None:
            raise ValueError(f"Start node {start!r} is not in the graph")
        return []

    root = graph.nodes[0] if start is None else start
    if not graph.has_node(root):
        raise ValueError(f"Start node {root!r} is not in the graph")

    visited: set[Node] = set()
    order: list[Node] = []

    seeds = [root]
    if traverse_all:
        seeds.extend(node for node in graph.nodes if node != root)

    for seed in seeds:
        if seed in visited:
            continue
        visited.add(seed)
        queue: deque[Node] = deque([seed])
        while queue:
            current = queue.popleft()
            order.append(current)
            for neighbor, _ in graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

    return order
