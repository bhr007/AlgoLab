"""Renderer-independent, JSON-serializable event engine for graph algorithms."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .model import Graph, Node


class GraphEventType(str, Enum):
    """Canonical operations emitted by AlgoLab graph algorithm event streams."""

    START = "start"
    DISCOVER_NODE = "discover_node"
    VISIT_NODE = "visit_node"
    COMPLETE_NODE = "complete_node"
    EXPLORE_EDGE = "explore_edge"
    SELECT_EDGE = "select_edge"
    REJECT_EDGE = "reject_edge"
    RELAX_EDGE = "relax_edge"
    UPDATE_DISTANCE = "update_distance"
    CYCLE_DETECTED = "cycle_detected"
    COMPLETE = "complete"


def _normalize_distance_value(value: float | None) -> float | None:
    """Convert infinite distances to ``None`` for strict JSON compatibility."""
    if value is None:
        return None
    if math.isinf(value):
        return None
    return value


def serialize_distance_map(
    distances: Mapping[Node, float | None],
) -> dict[Node, float | None]:
    """Return a JSON-safe distance map where ``inf`` is encoded as ``None``."""
    return {node: _normalize_distance_value(val) for node, val in distances.items()}


@dataclass(frozen=True)
class GraphEvent:
    """A single observable step in a graph algorithm's execution."""

    type: GraphEventType
    node: Node | None = None
    edge: tuple[Node, Node] | None = None
    weight: float | None = None
    distance: float | None = None
    distances: dict[Node, float | None] | None = None
    frontier: tuple[Node, ...] = ()
    visited: tuple[Node, ...] = ()
    traversal_order: tuple[Node, ...] = ()
    selected_edges: tuple[tuple[Node, Node], ...] = ()
    message: str | None = None
    metadata: dict[str, object] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize this event into a JSON-compatible dictionary."""
        return {
            "type": self.type.value,
            "node": self.node,
            "edge": list(self.edge) if self.edge is not None else None,
            "weight": self.weight,
            "distance": _normalize_distance_value(self.distance),
            "distances": (
                [[node, _normalize_distance_value(val)] for node, val in self.distances.items()]
                if self.distances is not None
                else None
            ),
            "frontier": list(self.frontier),
            "visited": list(self.visited),
            "traversal_order": list(self.traversal_order),
            "selected_edges": [list(pair) for pair in self.selected_edges],
            "message": self.message,
            "metadata": dict(self.metadata) if self.metadata is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> GraphEvent:
        """Deserialize a dictionary produced by :meth:`to_dict`."""
        raw_edge = payload.get("edge")
        raw_distances = payload.get("distances")
        distances: dict[Node, float | None] | None = None
        if isinstance(raw_distances, list):
            distances = {pair[0]: pair[1] for pair in raw_distances}
        elif isinstance(raw_distances, Mapping):
            distances = dict(raw_distances)

        raw_metadata = payload.get("metadata")
        return cls(
            type=GraphEventType(payload["type"]),
            node=payload.get("node"),
            edge=(raw_edge[0], raw_edge[1]) if raw_edge is not None else None,
            weight=payload.get("weight"),
            distance=payload.get("distance"),
            distances=distances,
            frontier=tuple(payload.get("frontier", ())),
            visited=tuple(payload.get("visited", ())),
            traversal_order=tuple(payload.get("traversal_order", ())),
            selected_edges=tuple(
                (pair[0], pair[1]) for pair in payload.get("selected_edges", ())
            ),
            message=payload.get("message"),
            metadata=dict(raw_metadata) if raw_metadata is not None else None,
        )


def make_start_event(
    graph: Graph,
    algorithm_name: str,
    *,
    start_node: Node | None = None,
    distances: Mapping[Node, float | None] | None = None,
    message: str | None = None,
    metadata: dict[str, object] | None = None,
) -> GraphEvent:
    """Create a canonical initial :attr:`GraphEventType.START` event with graph payload."""
    combined_meta: dict[str, object] = {
        "algorithm": algorithm_name,
        "graph": graph.to_dict(),
    }
    if start_node is not None:
        combined_meta["start_node"] = start_node
    if metadata:
        combined_meta.update(metadata)

    return GraphEvent(
        type=GraphEventType.START,
        node=start_node,
        distances=serialize_distance_map(distances) if distances is not None else None,
        message=message or f"Initialize {algorithm_name}",
        metadata=combined_meta,
    )


def extract_graph_from_events(events: Iterable[GraphEvent]) -> Graph | None:
    """Extract the embedded :class:`Graph` from the first ``START`` event, if present."""
    for event in events:
        if event.metadata and "graph" in event.metadata:
            raw_graph = event.metadata["graph"]
            if isinstance(raw_graph, Mapping):
                return Graph.from_dict(raw_graph)
    return None


def serialize_graph_events(events: Iterable[GraphEvent]) -> list[dict[str, Any]]:
    """Convert a graph event stream into a list of JSON-serializable dictionaries."""
    return [event.to_dict() for event in events]


def graph_events_to_json(events: Iterable[GraphEvent], **json_kwargs: Any) -> str:
    """Serialize a graph event stream directly to a strict JSON string."""
    json_kwargs.setdefault("allow_nan", False)
    return json.dumps(serialize_graph_events(events), **json_kwargs)
