"""Kruskal's Minimum Spanning Tree / Forest algorithm for SortLab graphs."""

from __future__ import annotations

from sortlab.graphs.model import Graph, GraphEdge, MSTResult, Node


class _DisjointSet:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""

    def __init__(self, nodes: tuple[Node, ...]) -> None:
        self._parent: dict[Node, Node] = {node: node for node in nodes}
        self._rank: dict[Node, int] = {node: 0 for node in nodes}

    def find(self, node: Node) -> Node:
        parent = self._parent[node]
        if parent != node:
            self._parent[node] = self.find(parent)
        return self._parent[node]

    def union(self, a: Node, b: Node) -> bool:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a == root_b:
            return False
        if self._rank[root_a] < self._rank[root_b]:
            self._parent[root_a] = root_b
        elif self._rank[root_a] > self._rank[root_b]:
            self._parent[root_b] = root_a
        else:
            self._parent[root_b] = root_a
            self._rank[root_a] += 1
        return True


def kruskal(graph: Graph) -> MSTResult:
    """Compute a Minimum Spanning Tree (or Forest if disconnected) using Kruskal's algorithm.

    Constraints:
        - Requires an **undirected** graph (``graph.directed == False``).
        - Supports positive, zero, and negative edge weights.
        - Self-loops are naturally skipped (same root in Union-Find).
        - On disconnected graphs, returns a Minimum Spanning Forest with
          ``result.is_spanning == False``.

    Complexity:
        - Time: O(E log E) (equivalently O(E log V) on simple graphs)
        - Space: O(V + E)
    """
    graph.validate()
    if graph.directed:
        raise ValueError("Kruskal's algorithm requires an undirected graph")

    if graph.node_count == 0:
        return MSTResult(edges=(), total_weight=0.0, is_spanning=True, components=0)

    dsu = _DisjointSet(graph.nodes)
    sorted_edges = [
        edge
        for _, edge in sorted(
            enumerate(graph.edges), key=lambda pair: (pair[1].weight, pair[0])
        )
    ]

    mst_edges: list[GraphEdge] = []
    total_weight: float = 0.0
    components = graph.node_count

    for edge in sorted_edges:
        if dsu.union(edge.source, edge.target):
            mst_edges.append(edge)
            total_weight += edge.weight
            components -= 1
            if components == 1:
                break

    return MSTResult(
        edges=tuple(mst_edges),
        total_weight=total_weight,
        is_spanning=(components <= 1),
        components=components,
    )
