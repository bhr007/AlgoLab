"""Reusable graph data model, validation, and result containers for AlgoLab."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Union

Node = Union[str, int]
Weight = Union[int, float]


class GraphCycleError(ValueError):
    """Raised when an acyclic constraint (e.g., DAG for Topological Sort) is violated."""


class NegativeCycleError(ValueError):
    """Raised when a negative-weight cycle is reachable from the source node."""


@dataclass(frozen=True)
class GraphEdge:
    """An immutable weighted edge connecting ``source`` to ``target``."""

    source: Node
    target: Node
    weight: Weight = 1

    def to_list(self) -> list[Any]:
        """Return a JSON-serializable ``[source, target, weight]`` representation."""
        return [self.source, self.target, self.weight]


@dataclass(frozen=True)
class ShortestPathResult:
    """Result container for single-source shortest-path algorithms."""

    start: Node
    distances: dict[Node, float]
    predecessors: dict[Node, Node | None]

    def path_to(self, target: Node) -> list[Node]:
        """Reconstruct the shortest path from ``start`` to ``target``.

        Returns an empty list if ``target`` is unreachable. Raises ``ValueError``
        if ``target`` is not present in ``distances``.
        """
        if target not in self.distances:
            raise ValueError(f"Target node {target!r} is not in the graph")
        if math.isinf(self.distances[target]):
            return []
        path: list[Node] = []
        current: Node | None = target
        while current is not None:
            path.append(current)
            if current == self.start:
                break
            current = self.predecessors.get(current)
        path.reverse()
        if not path or path[0] != self.start:
            return []
        return path


@dataclass(frozen=True)
class MSTResult:
    """Result container for Minimum Spanning Tree / Forest algorithms."""

    edges: tuple[GraphEdge, ...]
    total_weight: float
    is_spanning: bool
    components: int


def validate_node_id(node: object) -> Node:
    """Validate that a node identifier is a non-empty ``str`` or non-boolean ``int``."""
    if isinstance(node, bool):
        raise TypeError("Node identifier cannot be a boolean")
    if isinstance(node, int):
        return node
    if isinstance(node, str):
        if not node.strip():
            raise ValueError("String node identifier cannot be empty or whitespace")
        return node
    raise TypeError(
        f"Node identifier must be a str or int, got {type(node).__name__}"
    )


def validate_edge_weight(weight: object, *, weighted: bool) -> Weight:
    """Validate an edge weight according to the graph's ``weighted`` policy."""
    if not weighted:
        if weight is None:
            return 1
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise TypeError(
                f"Edge weight must be numeric, got {type(weight).__name__}"
            )
        if not math.isfinite(weight):
            raise ValueError("Edge weight must be finite")
        if weight != 1:
            raise ValueError(
                "Unweighted graphs do not accept custom edge weights other than 1"
            )
        return 1

    if weight is None:
        raise ValueError("Weighted graphs require an explicit numeric edge weight")
    if isinstance(weight, bool) or not isinstance(weight, (int, float)):
        raise TypeError(
            f"Edge weight must be a finite int or float, got {type(weight).__name__}"
        )
    if not math.isfinite(weight):
        raise ValueError("Edge weight must be finite (NaN/Inf are not allowed)")
    return weight


class Graph:
    """Adjacency-list graph supporting directed/undirected and weighted/unweighted graphs.

    Self-loop and parallel-edge policy:
        - By default (``allow_self_loops=False``), self-loops ``(u, u)`` are
          rejected with ``ValueError`` to keep educational visualizations clear
          and enforce simple-graph semantics. Setting ``allow_self_loops=True``
          permits self-loops (e.g., for testing cycle detection).
        - By default (``allow_parallel_edges=False``), duplicate edges between the
          same pair of vertices (same ordered ``(u, v)`` for directed graphs, or
          same unordered ``{u, v}`` for undirected graphs) are rejected with
          ``ValueError``. Setting ``allow_parallel_edges=True`` allows multigraphs.

    Disconnected graphs and isolated vertices are supported by registering nodes
    explicitly via :meth:`add_node` or passing ``nodes`` to the constructor.
    """

    def __init__(
        self,
        *,
        directed: bool = False,
        weighted: bool = False,
        allow_self_loops: bool = False,
        allow_parallel_edges: bool = False,
        nodes: Iterable[Node] = (),
        edges: Iterable[tuple[Any, ...]] = (),
    ) -> None:
        self.directed = bool(directed)
        self.weighted = bool(weighted)
        self.allow_self_loops = bool(allow_self_loops)
        self.allow_parallel_edges = bool(allow_parallel_edges)

        self._adj: dict[Node, list[tuple[Node, Weight]]] = {}
        self._edges: list[GraphEdge] = []
        self._seen_pairs: set[tuple[Node, Node]] = set()

        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self._add_edge_tuple(edge)

    @classmethod
    def from_edges(
        cls,
        edges: Iterable[tuple[Any, ...]],
        *,
        nodes: Iterable[Node] = (),
        directed: bool = False,
        weighted: bool = False,
        allow_self_loops: bool = False,
        allow_parallel_edges: bool = False,
    ) -> Graph:
        """Construct a :class:`Graph` from an iterable of edge tuples."""
        return cls(
            directed=directed,
            weighted=weighted,
            allow_self_loops=allow_self_loops,
            allow_parallel_edges=allow_parallel_edges,
            nodes=nodes,
            edges=edges,
        )

    def _add_edge_tuple(self, edge: tuple[Any, ...]) -> GraphEdge:
        if not isinstance(edge, (tuple, list)):
            raise TypeError("Each edge must be a (u, v) or (u, v, weight) tuple")
        if len(edge) == 2:
            u, v = edge
            return self.add_edge(u, v)
        if len(edge) == 3:
            u, v, weight = edge
            return self.add_edge(u, v, weight)
        raise ValueError(
            f"Edge tuple must have 2 or 3 elements, got {len(edge)}: {edge!r}"
        )

    def add_node(self, node: Node) -> Node:
        """Add an isolated vertex if not already present and return it."""
        valid = validate_node_id(node)
        if valid not in self._adj:
            self._adj[valid] = []
        return valid

    def add_edge(
        self,
        source: Node,
        target: Node,
        weight: Weight | None = None,
        *,
        auto_add_nodes: bool = True,
    ) -> GraphEdge:
        """Validate and insert an edge into the graph."""
        u = validate_node_id(source)
        v = validate_node_id(target)
        valid_weight = validate_edge_weight(weight, weighted=self.weighted)

        if not auto_add_nodes:
            if u not in self._adj:
                raise ValueError(f"Source node {u!r} is not in the graph")
            if v not in self._adj:
                raise ValueError(f"Target node {v!r} is not in the graph")

        if u == v and not self.allow_self_loops:
            raise ValueError(
                f"Self-loop ({u!r}, {v!r}) is not allowed when allow_self_loops=False"
            )

        if not self.allow_parallel_edges and (u, v) in self._seen_pairs:
            kind = "directed" if self.directed else "undirected"
            raise ValueError(
                f"Parallel {kind} edge between {u!r} and {v!r} is not allowed "
                "when allow_parallel_edges=False"
            )

        if auto_add_nodes:
            self.add_node(u)
            self.add_node(v)

        edge_obj = GraphEdge(source=u, target=v, weight=valid_weight)
        self._edges.append(edge_obj)
        self._adj[u].append((v, valid_weight))
        self._seen_pairs.add((u, v))

        if not self.directed:
            self._seen_pairs.add((v, u))
            if u != v:
                self._adj[v].append((u, valid_weight))

        return edge_obj

    @property
    def nodes(self) -> tuple[Node, ...]:
        """Return all vertices in deterministic insertion order."""
        return tuple(self._adj.keys())

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        """Return all stored edges in insertion order."""
        return tuple(self._edges)

    @property
    def node_count(self) -> int:
        """Number of vertices in the graph."""
        return len(self._adj)

    @property
    def edge_count(self) -> int:
        """Number of edges in the graph."""
        return len(self._edges)

    def has_node(self, node: object) -> bool:
        """Return ``True`` if ``node`` belongs to this graph."""
        if isinstance(node, bool) or not isinstance(node, (str, int)):
            return False
        return node in self._adj

    def has_edge(self, source: Node, target: Node) -> bool:
        """Return ``True`` if an edge from ``source`` to ``target`` exists."""
        if not (self.has_node(source) and self.has_node(target)):
            return False
        return (source, target) in self._seen_pairs

    def neighbors(self, node: Node) -> tuple[tuple[Node, Weight], ...]:
        """Return outgoing ``(neighbor, weight)`` pairs for ``node``."""
        if node not in self._adj:
            raise ValueError(f"Node {node!r} is not in the graph")
        return tuple(self._adj[node])

    def adjacency_list(self) -> dict[Node, tuple[tuple[Node, Weight], ...]]:
        """Return an immutable snapshot of the adjacency list mapping."""
        return {node: tuple(adj) for node, adj in self._adj.items()}

    def out_degree(self, node: Node) -> int:
        """Return the out-degree (or degree for undirected graphs) of ``node``."""
        if node not in self._adj:
            raise ValueError(f"Node {node!r} is not in the graph")
        return len(self._adj[node])

    def in_degree(self, node: Node) -> int:
        """Return the in-degree (or degree for undirected graphs) of ``node``."""
        if node not in self._adj:
            raise ValueError(f"Node {node!r} is not in the graph")
        if not self.directed:
            return len(self._adj[node])
        count = 0
        for edge in self._edges:
            if edge.target == node:
                count += 1
        return count

    def validate(self) -> None:
        """Verify internal consistency of nodes, edges, and adjacency lists."""
        for node in self._adj:
            validate_node_id(node)
        for edge in self._edges:
            validate_node_id(edge.source)
            validate_node_id(edge.target)
            validate_edge_weight(edge.weight, weighted=self.weighted)
            if edge.source not in self._adj or edge.target not in self._adj:
                raise ValueError(f"Edge {edge} references an unknown node")
            if edge.source == edge.target and not self.allow_self_loops:
                raise ValueError(f"Self-loop {edge} violates allow_self_loops=False")

    def copy(self) -> Graph:
        """Return a deep copy of this graph."""
        return Graph(
            directed=self.directed,
            weighted=self.weighted,
            allow_self_loops=self.allow_self_loops,
            allow_parallel_edges=self.allow_parallel_edges,
            nodes=self._adj.keys(),
            edges=[(e.source, e.target, e.weight) for e in self._edges]
            if self.weighted
            else [(e.source, e.target) for e in self._edges],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize this graph into a JSON-compatible dictionary."""
        return {
            "directed": self.directed,
            "weighted": self.weighted,
            "allow_self_loops": self.allow_self_loops,
            "allow_parallel_edges": self.allow_parallel_edges,
            "nodes": list(self._adj.keys()),
            "edges": [edge.to_list() for edge in self._edges],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Graph:
        """Deserialize a dictionary produced by :meth:`to_dict`."""
        weighted = bool(payload.get("weighted", False))
        raw_edges = payload.get("edges", ())
        parsed_edges: list[tuple[Any, ...]] = []
        for entry in raw_edges:
            if weighted:
                parsed_edges.append((entry[0], entry[1], entry[2]))
            else:
                parsed_edges.append((entry[0], entry[1]))
        return cls(
            directed=bool(payload.get("directed", False)),
            weighted=weighted,
            allow_self_loops=bool(payload.get("allow_self_loops", False)),
            allow_parallel_edges=bool(payload.get("allow_parallel_edges", False)),
            nodes=payload.get("nodes", ()),
            edges=parsed_edges,
        )

    def __contains__(self, node: object) -> bool:
        return self.has_node(node)

    def __len__(self) -> int:
        return len(self._adj)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Graph):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        return (
            f"Graph(directed={self.directed!r}, weighted={self.weighted!r}, "
            f"nodes={len(self._adj)}, edges={len(self._edges)})"
        )
