"""Topological Sort (Kahn's algorithm) for AlgoLab Directed Acyclic Graphs."""

from __future__ import annotations

from collections import deque

from sortlab.graphs.model import Graph, GraphCycleError, Node


def topological_sort(graph: Graph) -> list[Node]:
    """Return a topological ordering of vertices using Kahn's algorithm.

    Constraints:
        - Requires a **directed acyclic graph (DAG)**.
        - Raises ``ValueError`` if ``graph.directed`` is ``False``.
        - Raises :class:`GraphCycleError` (a ``ValueError`` subclass) if the
          graph contains a cycle (including self-loops).
        - Supports disconnected DAGs and isolated vertices.

    Complexity:
        - Time: O(V + E)
        - Space: O(V)
    """
    graph.validate()
    if not graph.directed:
        raise ValueError("Topological sort requires a directed graph")

    if graph.node_count == 0:
        return []

    in_degree: dict[Node, int] = {node: 0 for node in graph.nodes}
    for node in graph.nodes:
        for neighbor, _ in graph.neighbors(node):
            in_degree[neighbor] += 1

    queue: deque[Node] = deque(
        node for node in graph.nodes if in_degree[node] == 0
    )
    order: list[Node] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor, _ in graph.neighbors(current):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != graph.node_count:
        raise GraphCycleError(
            "Graph contains a cycle; topological ordering does not exist"
        )

    return order
