"""Depth-First Search (DFS) implementation for AlgoLab graphs."""

from __future__ import annotations

from collections.abc import Iterator

from sortlab.graphs.model import Graph, Node, Weight


def dfs(
    graph: Graph,
    start: Node | None = None,
    *,
    traverse_all: bool = False,
) -> list[Node]:
    """Return nodes visited by Depth-First Search starting at ``start``.

    Works on directed or undirected, weighted or unweighted graphs (edge weights
    are ignored). Uses an explicit frame stack so traversal order matches
    recursive DFS in adjacency-list order without hitting Python's recursion
    limit on large graphs.

    When ``traverse_all=False`` (default), only vertices reachable from
    ``start`` are returned. When ``traverse_all=True``, disconnected components
    are subsequently traversed in graph insertion order.

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
        order.append(seed)
        stack: list[tuple[Node, Iterator[tuple[Node, Weight]]]] = [
            (seed, iter(graph.neighbors(seed)))
        ]
        while stack:
            _current, neighbor_iter = stack[-1]
            try:
                neighbor, _ = next(neighbor_iter)
            except StopIteration:
                stack.pop()
                continue
            if neighbor not in visited:
                visited.add(neighbor)
                order.append(neighbor)
                stack.append((neighbor, iter(graph.neighbors(neighbor))))

    return order
