"""Event-producing wrappers for all SortLab graph algorithms."""

from __future__ import annotations

import heapq
from collections import deque
from collections.abc import Iterator
from itertools import count

from .algorithms.bellman_ford import _directed_edge_list
from .algorithms.kruskal import _DisjointSet
from .events import (
    GraphEvent,
    GraphEventType,
    make_start_event,
    serialize_distance_map,
)
from .model import Graph, Node, Weight


def _sorted_frontier(frontier_map: dict[Node, Weight]) -> tuple[Node, ...]:
    """Return frontier nodes ordered by priority/key weight."""
    return tuple(
        node for node, _ in sorted(frontier_map.items(), key=lambda item: item[1])
    )


def _resolve_start_node(graph: Graph, start: Node | None) -> Node | None:
    """Validate and resolve a starting node for traversal/path algorithms."""
    if graph.node_count == 0:
        if start is not None:
            raise ValueError(f"Start node {start!r} is not in the graph")
        return None
    resolved = graph.nodes[0] if start is None else start
    if not graph.has_node(resolved):
        raise ValueError(f"Start node {resolved!r} is not in the graph")
    return resolved


def bfs_events(
    graph: Graph,
    start: Node | None = None,
    *,
    traverse_all: bool = False,
) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Breadth-First Search."""
    graph.validate()
    root = _resolve_start_node(graph, start)
    return _bfs_events_stream(graph, root, traverse_all=traverse_all)


def _bfs_events_stream(
    graph: Graph,
    root: Node | None,
    *,
    traverse_all: bool,
) -> Iterator[GraphEvent]:
    if root is None:
        yield make_start_event(graph, "Breadth-First Search (BFS)")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — BFS complete",
        )
        return

    distances: dict[Node, float | None] = {node: None for node in graph.nodes}
    distances[root] = 0
    yield make_start_event(
        graph,
        "Breadth-First Search (BFS)",
        start_node=root,
        distances=distances,
        message=f"Start BFS from node {root}",
    )

    discovered: set[Node] = set()
    completed: list[Node] = []
    traversal_order: list[Node] = []
    selected_edges: list[tuple[Node, Node]] = []

    seeds = [root]
    if traverse_all:
        seeds.extend(node for node in graph.nodes if node != root)

    for seed in seeds:
        if seed in discovered:
            continue
        discovered.add(seed)
        if distances[seed] is None:
            distances[seed] = 0
        queue: deque[Node] = deque([seed])
        yield GraphEvent(
            type=GraphEventType.DISCOVER_NODE,
            node=seed,
            distance=distances[seed],
            distances=serialize_distance_map(distances),
            frontier=tuple(queue),
            visited=tuple(completed),
            traversal_order=tuple(traversal_order),
            selected_edges=tuple(selected_edges),
            message=f"Discover start node {seed} and enqueue it",
        )

        while queue:
            current = queue.popleft()
            traversal_order.append(current)
            yield GraphEvent(
                type=GraphEventType.VISIT_NODE,
                node=current,
                distance=distances[current],
                distances=serialize_distance_map(distances),
                frontier=tuple(queue),
                visited=tuple(completed),
                traversal_order=tuple(traversal_order),
                selected_edges=tuple(selected_edges),
                message=f"Dequeue and visit node {current}",
            )

            for neighbor, weight in graph.neighbors(current):
                yield GraphEvent(
                    type=GraphEventType.EXPLORE_EDGE,
                    node=current,
                    edge=(current, neighbor),
                    weight=weight,
                    distances=serialize_distance_map(distances),
                    frontier=tuple(queue),
                    visited=tuple(completed),
                    traversal_order=tuple(traversal_order),
                    selected_edges=tuple(selected_edges),
                    message=f"Explore edge ({current}, {neighbor})",
                )
                if neighbor not in discovered:
                    discovered.add(neighbor)
                    parent_dist = distances[current]
                    if parent_dist is not None:
                        distances[neighbor] = parent_dist + 1
                    queue.append(neighbor)
                    selected_edges.append((current, neighbor))
                    yield GraphEvent(
                        type=GraphEventType.SELECT_EDGE,
                        node=neighbor,
                        edge=(current, neighbor),
                        weight=weight,
                        distance=distances[neighbor],
                        distances=serialize_distance_map(distances),
                        frontier=tuple(queue),
                        visited=tuple(completed),
                        traversal_order=tuple(traversal_order),
                        selected_edges=tuple(selected_edges),
                        message=f"Select tree edge ({current}, {neighbor})",
                    )
                    yield GraphEvent(
                        type=GraphEventType.DISCOVER_NODE,
                        node=neighbor,
                        distance=distances[neighbor],
                        distances=serialize_distance_map(distances),
                        frontier=tuple(queue),
                        visited=tuple(completed),
                        traversal_order=tuple(traversal_order),
                        selected_edges=tuple(selected_edges),
                        message=(
                            f"Discover node {neighbor} at distance {distances[neighbor]}"
                        ),
                    )
                else:
                    yield GraphEvent(
                        type=GraphEventType.REJECT_EDGE,
                        node=neighbor,
                        edge=(current, neighbor),
                        weight=weight,
                        distances=serialize_distance_map(distances),
                        frontier=tuple(queue),
                        visited=tuple(completed),
                        traversal_order=tuple(traversal_order),
                        selected_edges=tuple(selected_edges),
                        message=(
                            f"Skip edge ({current}, {neighbor}); {neighbor} already discovered"
                        ),
                    )

            completed.append(current)
            yield GraphEvent(
                type=GraphEventType.COMPLETE_NODE,
                node=current,
                distance=distances[current],
                distances=serialize_distance_map(distances),
                frontier=tuple(queue),
                visited=tuple(completed),
                traversal_order=tuple(traversal_order),
                selected_edges=tuple(selected_edges),
                message=f"Finish exploring neighbors of {current}",
            )

    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        distances=serialize_distance_map(distances),
        visited=tuple(completed),
        traversal_order=tuple(traversal_order),
        selected_edges=tuple(selected_edges),
        message=f"BFS complete: visited {len(traversal_order)}/{graph.node_count} nodes",
    )


def dfs_events(
    graph: Graph,
    start: Node | None = None,
    *,
    traverse_all: bool = False,
) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Depth-First Search."""
    graph.validate()
    root = _resolve_start_node(graph, start)
    return _dfs_events_stream(graph, root, traverse_all=traverse_all)


def _dfs_events_stream(
    graph: Graph,
    root: Node | None,
    *,
    traverse_all: bool,
) -> Iterator[GraphEvent]:
    if root is None:
        yield make_start_event(graph, "Depth-First Search (DFS)")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — DFS complete",
        )
        return

    yield make_start_event(
        graph,
        "Depth-First Search (DFS)",
        start_node=root,
        message=f"Start DFS from node {root}",
    )

    discovered: set[Node] = set()
    completed: list[Node] = []
    traversal_order: list[Node] = []
    selected_edges: list[tuple[Node, Node]] = []

    seeds = [root]
    if traverse_all:
        seeds.extend(node for node in graph.nodes if node != root)

    for seed in seeds:
        if seed in discovered:
            continue
        discovered.add(seed)
        stack: list[tuple[Node, Iterator[tuple[Node, Weight]]]] = [
            (seed, iter(graph.neighbors(seed)))
        ]
        yield GraphEvent(
            type=GraphEventType.DISCOVER_NODE,
            node=seed,
            frontier=tuple(frame[0] for frame in stack),
            visited=tuple(completed),
            traversal_order=tuple(traversal_order),
            selected_edges=tuple(selected_edges),
            message=f"Discover start node {seed}",
        )
        traversal_order.append(seed)
        yield GraphEvent(
            type=GraphEventType.VISIT_NODE,
            node=seed,
            frontier=tuple(frame[0] for frame in stack),
            visited=tuple(completed),
            traversal_order=tuple(traversal_order),
            selected_edges=tuple(selected_edges),
            message=f"Visit node {seed}",
        )

        while stack:
            current, neighbor_iter = stack[-1]
            try:
                neighbor, weight = next(neighbor_iter)
            except StopIteration:
                stack.pop()
                completed.append(current)
                yield GraphEvent(
                    type=GraphEventType.COMPLETE_NODE,
                    node=current,
                    frontier=tuple(frame[0] for frame in stack),
                    visited=tuple(completed),
                    traversal_order=tuple(traversal_order),
                    selected_edges=tuple(selected_edges),
                    message=f"Backtrack from completed node {current}",
                )
                continue

            yield GraphEvent(
                type=GraphEventType.EXPLORE_EDGE,
                node=current,
                edge=(current, neighbor),
                weight=weight,
                frontier=tuple(frame[0] for frame in stack),
                visited=tuple(completed),
                traversal_order=tuple(traversal_order),
                selected_edges=tuple(selected_edges),
                message=f"Explore edge ({current}, {neighbor})",
            )
            if neighbor not in discovered:
                discovered.add(neighbor)
                selected_edges.append((current, neighbor))
                stack.append((neighbor, iter(graph.neighbors(neighbor))))
                yield GraphEvent(
                    type=GraphEventType.SELECT_EDGE,
                    node=neighbor,
                    edge=(current, neighbor),
                    weight=weight,
                    frontier=tuple(frame[0] for frame in stack),
                    visited=tuple(completed),
                    traversal_order=tuple(traversal_order),
                    selected_edges=tuple(selected_edges),
                    message=f"Select DFS tree edge ({current}, {neighbor})",
                )
                yield GraphEvent(
                    type=GraphEventType.DISCOVER_NODE,
                    node=neighbor,
                    frontier=tuple(frame[0] for frame in stack),
                    visited=tuple(completed),
                    traversal_order=tuple(traversal_order),
                    selected_edges=tuple(selected_edges),
                    message=f"Discover node {neighbor}",
                )
                traversal_order.append(neighbor)
                yield GraphEvent(
                    type=GraphEventType.VISIT_NODE,
                    node=neighbor,
                    frontier=tuple(frame[0] for frame in stack),
                    visited=tuple(completed),
                    traversal_order=tuple(traversal_order),
                    selected_edges=tuple(selected_edges),
                    message=f"Visit node {neighbor}",
                )
            else:
                yield GraphEvent(
                    type=GraphEventType.REJECT_EDGE,
                    node=neighbor,
                    edge=(current, neighbor),
                    weight=weight,
                    frontier=tuple(frame[0] for frame in stack),
                    visited=tuple(completed),
                    traversal_order=tuple(traversal_order),
                    selected_edges=tuple(selected_edges),
                    message=(
                        f"Skip edge ({current}, {neighbor}); {neighbor} already visited"
                    ),
                )

    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        visited=tuple(completed),
        traversal_order=tuple(traversal_order),
        selected_edges=tuple(selected_edges),
        message=f"DFS complete: visited {len(traversal_order)}/{graph.node_count} nodes",
    )


def dijkstra_events(
    graph: Graph,
    start: Node | None = None,
) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Dijkstra's algorithm."""
    graph.validate()
    if any(edge.weight < 0 for edge in graph.edges):
        raise ValueError("Dijkstra's algorithm requires non-negative edge weights")
    root = _resolve_start_node(graph, start)
    return _dijkstra_events_stream(graph, root)


def _dijkstra_events_stream(
    graph: Graph,
    root: Node | None,
) -> Iterator[GraphEvent]:
    if root is None:
        yield make_start_event(graph, "Dijkstra's Shortest Path")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — Dijkstra complete",
        )
        return

    distances: dict[Node, float | None] = {node: None for node in graph.nodes}
    distances[root] = 0
    parent_edge: dict[Node, tuple[Node, Node]] = {}

    yield make_start_event(
        graph,
        "Dijkstra's Shortest Path",
        start_node=root,
        distances=distances,
        message=f"Initialize Dijkstra from source {root} (d[{root}] = 0)",
    )

    tie_breaker = count()
    heap: list[tuple[float, int, Node]] = [(0, next(tie_breaker), root)]
    finalized: set[Node] = set()
    finalized_order: list[Node] = []
    frontier_dist: dict[Node, float] = {root: 0}
    cached_frontier: tuple[Node, ...] = (root,)

    def _frontier_nodes() -> tuple[Node, ...]:
        nonlocal cached_frontier
        return cached_frontier

    def _refresh_frontier() -> None:
        nonlocal cached_frontier
        cached_frontier = _sorted_frontier(frontier_dist)

    def _spt_edges() -> tuple[tuple[Node, Node], ...]:
        return tuple(parent_edge.values())

    yield GraphEvent(
        type=GraphEventType.DISCOVER_NODE,
        node=root,
        distance=0,
        distances=serialize_distance_map(distances),
        frontier=(root,),
        message=f"Add source node {root} to priority queue",
    )

    while heap:
        current_dist, _, current = heapq.heappop(heap)
        if current in finalized:
            continue

        finalized.add(current)
        frontier_dist.pop(current, None)
        _refresh_frontier()
        finalized_order.append(current)
        yield GraphEvent(
            type=GraphEventType.VISIT_NODE,
            node=current,
            distance=current_dist,
            distances=serialize_distance_map(distances),
            frontier=_frontier_nodes(),
            visited=tuple(finalized_order),
            traversal_order=tuple(finalized_order),
            selected_edges=_spt_edges(),
            message=f"Pop minimum-distance node {current} (d={current_dist})",
        )

        for neighbor, weight in graph.neighbors(current):
            yield GraphEvent(
                type=GraphEventType.EXPLORE_EDGE,
                node=current,
                edge=(current, neighbor),
                weight=weight,
                distances=serialize_distance_map(distances),
                frontier=_frontier_nodes(),
                visited=tuple(finalized_order),
                traversal_order=tuple(finalized_order),
                selected_edges=_spt_edges(),
                message=f"Inspect edge ({current}, {neighbor}) with weight {weight}",
            )
            if neighbor in finalized:
                yield GraphEvent(
                    type=GraphEventType.REJECT_EDGE,
                    node=neighbor,
                    edge=(current, neighbor),
                    weight=weight,
                    distances=serialize_distance_map(distances),
                    frontier=_frontier_nodes(),
                    visited=tuple(finalized_order),
                    traversal_order=tuple(finalized_order),
                    selected_edges=_spt_edges(),
                    message=f"Skip edge ({current}, {neighbor}); {neighbor} is finalized",
                )
                continue

            candidate = current_dist + weight
            yield GraphEvent(
                type=GraphEventType.RELAX_EDGE,
                node=neighbor,
                edge=(current, neighbor),
                weight=weight,
                distance=candidate,
                distances=serialize_distance_map(distances),
                frontier=_frontier_nodes(),
                visited=tuple(finalized_order),
                traversal_order=tuple(finalized_order),
                selected_edges=_spt_edges(),
                message=f"Check relaxation: {current_dist} + {weight} = {candidate}",
            )

            existing = distances[neighbor]
            if existing is None or candidate < existing:
                distances[neighbor] = candidate
                parent_edge[neighbor] = (current, neighbor)
                heapq.heappush(heap, (candidate, next(tie_breaker), neighbor))
                frontier_dist[neighbor] = candidate
                _refresh_frontier()
                yield GraphEvent(
                    type=GraphEventType.UPDATE_DISTANCE,
                    node=neighbor,
                    edge=(current, neighbor),
                    weight=weight,
                    distance=candidate,
                    distances=serialize_distance_map(distances),
                    frontier=_frontier_nodes(),
                    visited=tuple(finalized_order),
                    traversal_order=tuple(finalized_order),
                    selected_edges=_spt_edges(),
                    message=f"Update distance d[{neighbor}] = {candidate} via {current}",
                )
                yield GraphEvent(
                    type=GraphEventType.SELECT_EDGE,
                    node=neighbor,
                    edge=(current, neighbor),
                    weight=weight,
                    distance=candidate,
                    distances=serialize_distance_map(distances),
                    frontier=_frontier_nodes(),
                    visited=tuple(finalized_order),
                    traversal_order=tuple(finalized_order),
                    selected_edges=_spt_edges(),
                    message=f"Select shortest-path edge ({current}, {neighbor})",
                )
                yield GraphEvent(
                    type=GraphEventType.DISCOVER_NODE,
                    node=neighbor,
                    distance=candidate,
                    distances=serialize_distance_map(distances),
                    frontier=_frontier_nodes(),
                    visited=tuple(finalized_order),
                    traversal_order=tuple(finalized_order),
                    selected_edges=_spt_edges(),
                    message=f"Enqueue {neighbor} with priority {candidate}",
                )
            else:
                yield GraphEvent(
                    type=GraphEventType.REJECT_EDGE,
                    node=neighbor,
                    edge=(current, neighbor),
                    weight=weight,
                    distances=serialize_distance_map(distances),
                    frontier=_frontier_nodes(),
                    visited=tuple(finalized_order),
                    traversal_order=tuple(finalized_order),
                    selected_edges=_spt_edges(),
                    message=f"No improvement for {neighbor} ({candidate} >= {existing})",
                )

        yield GraphEvent(
            type=GraphEventType.COMPLETE_NODE,
            node=current,
            distance=current_dist,
            distances=serialize_distance_map(distances),
            frontier=_frontier_nodes(),
            visited=tuple(finalized_order),
            traversal_order=tuple(finalized_order),
            selected_edges=_spt_edges(),
            message=f"Finalize shortest distance to {current}: {current_dist}",
        )

    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        distances=serialize_distance_map(distances),
        visited=tuple(finalized_order),
        traversal_order=tuple(finalized_order),
        selected_edges=_spt_edges(),
        message=f"Dijkstra complete from {root}",
    )


def bellman_ford_events(
    graph: Graph,
    start: Node | None = None,
) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Bellman-Ford.

    If a reachable negative-weight cycle is detected, yields
    :attr:`GraphEventType.CYCLE_DETECTED` followed by :attr:`GraphEventType.COMPLETE`
    with ``metadata["negative_cycle"] = True`` so visualizations can highlight the
    cycle cleanly.
    """
    graph.validate()
    root = _resolve_start_node(graph, start)
    return _bellman_ford_events_stream(graph, root)


def _bellman_ford_events_stream(
    graph: Graph,
    root: Node | None,
) -> Iterator[GraphEvent]:
    if root is None:
        yield make_start_event(graph, "Bellman-Ford Shortest Path")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — Bellman-Ford complete",
            metadata={"negative_cycle": False},
        )
        return

    distances: dict[Node, float | None] = {node: None for node in graph.nodes}
    distances[root] = 0
    predecessors: dict[Node, Node | None] = {node: None for node in graph.nodes}
    parent_edge: dict[Node, tuple[Node, Node]] = {}

    yield make_start_event(
        graph,
        "Bellman-Ford Shortest Path",
        start_node=root,
        distances=distances,
        message=f"Initialize Bellman-Ford from source {root} (d[{root}] = 0)",
    )
    yield GraphEvent(
        type=GraphEventType.DISCOVER_NODE,
        node=root,
        distance=0,
        distances=serialize_distance_map(distances),
        visited=(root,),
        message=f"Source node {root} initialized at distance 0",
    )

    relax_edges = _directed_edge_list(graph)
    node_count = graph.node_count

    def _spt_edges() -> tuple[tuple[Node, Node], ...]:
        return tuple(parent_edge.values())

    def _reachable_nodes() -> tuple[Node, ...]:
        return tuple(n for n in graph.nodes if distances[n] is not None)

    for pass_num in range(1, node_count):
        updated = False
        for u, v, weight in relax_edges:
            if distances[u] is None:
                continue
            yield GraphEvent(
                type=GraphEventType.EXPLORE_EDGE,
                node=u,
                edge=(u, v),
                weight=weight,
                distances=serialize_distance_map(distances),
                visited=_reachable_nodes(),
                selected_edges=_spt_edges(),
                message=f"Pass {pass_num}: inspect edge ({u}, {v}) (w={weight})",
                metadata={"pass": pass_num},
            )
            candidate = distances[u] + weight
            yield GraphEvent(
                type=GraphEventType.RELAX_EDGE,
                node=v,
                edge=(u, v),
                weight=weight,
                distance=candidate,
                distances=serialize_distance_map(distances),
                visited=_reachable_nodes(),
                selected_edges=_spt_edges(),
                message=f"Pass {pass_num}: relax ({u}, {v}) -> {candidate}",
                metadata={"pass": pass_num},
            )
            current_v = distances[v]
            if current_v is None or candidate < current_v:
                distances[v] = candidate
                predecessors[v] = u
                parent_edge[v] = (u, v)
                updated = True
                yield GraphEvent(
                    type=GraphEventType.UPDATE_DISTANCE,
                    node=v,
                    edge=(u, v),
                    weight=weight,
                    distance=candidate,
                    distances=serialize_distance_map(distances),
                    visited=_reachable_nodes(),
                    selected_edges=_spt_edges(),
                    message=f"Update d[{v}] = {candidate} via {u}",
                    metadata={"pass": pass_num},
                )
                yield GraphEvent(
                    type=GraphEventType.SELECT_EDGE,
                    node=v,
                    edge=(u, v),
                    weight=weight,
                    distance=candidate,
                    distances=serialize_distance_map(distances),
                    visited=_reachable_nodes(),
                    selected_edges=_spt_edges(),
                    message=f"Select edge ({u}, {v}) in shortest-path tree",
                    metadata={"pass": pass_num},
                )
            else:
                yield GraphEvent(
                    type=GraphEventType.REJECT_EDGE,
                    node=v,
                    edge=(u, v),
                    weight=weight,
                    distances=serialize_distance_map(distances),
                    visited=_reachable_nodes(),
                    selected_edges=_spt_edges(),
                    message=f"No improvement for {v} ({candidate} >= {current_v})",
                    metadata={"pass": pass_num},
                )
        if not updated:
            break

    # Pass |V|: detect reachable negative-weight cycles.
    for u, v, weight in relax_edges:
        dist_u = distances[u]
        dist_v = distances[v]
        if dist_u is not None and (dist_v is None or dist_u + weight < dist_v):
            cycle_cursor: Node | None = v
            for _ in range(node_count):
                if cycle_cursor is None:
                    break
                cycle_cursor = predecessors.get(cycle_cursor)
            cycle_nodes: list[Node] = []
            if cycle_cursor is not None:
                start_cycle = cycle_cursor
                curr: Node | None = start_cycle
                while curr is not None and curr not in cycle_nodes:
                    cycle_nodes.append(curr)
                    curr = predecessors.get(curr)
                    if curr == start_cycle:
                        break
            if not cycle_nodes:
                cycle_nodes = [u, v]

            yield GraphEvent(
                type=GraphEventType.CYCLE_DETECTED,
                node=v,
                edge=(u, v),
                weight=weight,
                distances=serialize_distance_map(distances),
                visited=_reachable_nodes(),
                selected_edges=_spt_edges(),
                message=f"Negative-weight cycle detected via edge ({u}, {v})!",
                metadata={"cycle_nodes": cycle_nodes},
            )
            yield GraphEvent(
                type=GraphEventType.COMPLETE,
                distances=serialize_distance_map(distances),
                visited=_reachable_nodes(),
                selected_edges=_spt_edges(),
                message="Bellman-Ford stopped: negative-weight cycle detected",
                metadata={"negative_cycle": True, "cycle_nodes": cycle_nodes},
            )
            return

    reachable = _reachable_nodes()
    for node in reachable:
        yield GraphEvent(
            type=GraphEventType.COMPLETE_NODE,
            node=node,
            distance=distances[node],
            distances=serialize_distance_map(distances),
            visited=reachable,
            selected_edges=_spt_edges(),
            message=f"Finalize shortest distance d[{node}] = {distances[node]}",
        )

    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        distances=serialize_distance_map(distances),
        visited=reachable,
        traversal_order=reachable,
        selected_edges=_spt_edges(),
        message=f"Bellman-Ford complete from {root}",
        metadata={"negative_cycle": False},
    )


def prim_events(
    graph: Graph,
    start: Node | None = None,
) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Prim's MST algorithm."""
    graph.validate()
    if graph.directed:
        raise ValueError("Prim's algorithm requires an undirected graph")
    root = _resolve_start_node(graph, start)
    return _prim_events_stream(graph, root)


def _prim_events_stream(
    graph: Graph,
    root: Node | None,
) -> Iterator[GraphEvent]:
    if root is None:
        yield make_start_event(graph, "Prim's Minimum Spanning Tree")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — Prim complete",
            metadata={"total_weight": 0.0, "is_spanning": True, "components": 0},
        )
        return

    keys: dict[Node, float | None] = {node: None for node in graph.nodes}
    keys[root] = 0
    yield make_start_event(
        graph,
        "Prim's Minimum Spanning Tree",
        start_node=root,
        distances=keys,
        message=f"Start Prim's MST from node {root}",
    )

    visited: set[Node] = set()
    visited_order: list[Node] = []
    mst_edges: list[tuple[Node, Node]] = []
    total_weight: float = 0.0
    components = 0
    tie_breaker = count()

    seeds = [root] + [node for node in graph.nodes if node != root]
    for seed in seeds:
        if seed in visited:
            continue
        components += 1
        visited.add(seed)
        visited_order.append(seed)
        keys[seed] = 0

        heap: list[tuple[Weight, int, Node, Node]] = []
        frontier_keys: dict[Node, Weight] = {}
        cached_frontier: tuple[Node, ...] = ()
        yield GraphEvent(
            type=GraphEventType.DISCOVER_NODE,
            node=seed,
            distance=0,
            distances=serialize_distance_map(keys),
            visited=tuple(visited_order),
            traversal_order=tuple(visited_order),
            selected_edges=tuple(mst_edges),
            message=f"Select component root {seed}",
        )
        yield GraphEvent(
            type=GraphEventType.VISIT_NODE,
            node=seed,
            distance=0,
            distances=serialize_distance_map(keys),
            visited=tuple(visited_order),
            traversal_order=tuple(visited_order),
            selected_edges=tuple(mst_edges),
            message=f"Add {seed} to MST",
        )

        for neighbor, weight in graph.neighbors(seed):
            if neighbor not in visited:
                heapq.heappush(heap, (weight, next(tie_breaker), seed, neighbor))
                if keys[neighbor] is None or weight < keys[neighbor]:
                    keys[neighbor] = weight
                    frontier_keys[neighbor] = weight
                    cached_frontier = _sorted_frontier(frontier_keys)
                    yield GraphEvent(
                        type=GraphEventType.UPDATE_DISTANCE,
                        node=neighbor,
                        edge=(seed, neighbor),
                        weight=weight,
                        distance=weight,
                        distances=serialize_distance_map(keys),
                        frontier=cached_frontier,
                        visited=tuple(visited_order),
                        traversal_order=tuple(visited_order),
                        selected_edges=tuple(mst_edges),
                        message=f"Update candidate key for {neighbor}: {weight} via {seed}",
                    )

        while heap:
            weight, _, u, v = heapq.heappop(heap)
            yield GraphEvent(
                type=GraphEventType.EXPLORE_EDGE,
                node=v,
                edge=(u, v),
                weight=weight,
                distances=serialize_distance_map(keys),
                frontier=cached_frontier,
                visited=tuple(visited_order),
                traversal_order=tuple(visited_order),
                selected_edges=tuple(mst_edges),
                message=f"Consider lightest candidate edge ({u}, {v}) with weight {weight}",
            )
            if v in visited:
                yield GraphEvent(
                    type=GraphEventType.REJECT_EDGE,
                    node=v,
                    edge=(u, v),
                    weight=weight,
                    distances=serialize_distance_map(keys),
                    frontier=cached_frontier,
                    visited=tuple(visited_order),
                    traversal_order=tuple(visited_order),
                    selected_edges=tuple(mst_edges),
                    message=f"Skip edge ({u}, {v}); {v} is already in the MST",
                )
                continue

            visited.add(v)
            frontier_keys.pop(v, None)
            cached_frontier = _sorted_frontier(frontier_keys)
            visited_order.append(v)
            mst_edges.append((u, v))
            total_weight += weight
            yield GraphEvent(
                type=GraphEventType.SELECT_EDGE,
                node=v,
                edge=(u, v),
                weight=weight,
                distance=weight,
                distances=serialize_distance_map(keys),
                frontier=cached_frontier,
                visited=tuple(visited_order),
                traversal_order=tuple(visited_order),
                selected_edges=tuple(mst_edges),
                message=f"Select MST edge ({u}, {v}) (w={weight}, total={total_weight:g})",
            )
            yield GraphEvent(
                type=GraphEventType.VISIT_NODE,
                node=v,
                distance=keys[v],
                distances=serialize_distance_map(keys),
                frontier=cached_frontier,
                visited=tuple(visited_order),
                traversal_order=tuple(visited_order),
                selected_edges=tuple(mst_edges),
                message=f"Add node {v} to MST",
            )

            for neighbor, next_weight in graph.neighbors(v):
                if neighbor not in visited:
                    heapq.heappush(heap, (next_weight, next(tie_breaker), v, neighbor))
                    if keys[neighbor] is None or next_weight < keys[neighbor]:
                        keys[neighbor] = next_weight
                        frontier_keys[neighbor] = next_weight
                        cached_frontier = _sorted_frontier(frontier_keys)
                        yield GraphEvent(
                            type=GraphEventType.UPDATE_DISTANCE,
                            node=neighbor,
                            edge=(v, neighbor),
                            weight=next_weight,
                            distance=next_weight,
                            distances=serialize_distance_map(keys),
                            frontier=cached_frontier,
                            visited=tuple(visited_order),
                            traversal_order=tuple(visited_order),
                            selected_edges=tuple(mst_edges),
                            message=f"Update candidate key for {neighbor}: {next_weight} via {v}",
                        )

            yield GraphEvent(
                type=GraphEventType.COMPLETE_NODE,
                node=v,
                distance=keys[v],
                distances=serialize_distance_map(keys),
                frontier=cached_frontier,
                visited=tuple(visited_order),
                traversal_order=tuple(visited_order),
                selected_edges=tuple(mst_edges),
                message=f"Finish adding edges from {v}",
            )

    is_spanning = components <= 1
    kind_label = "MST" if is_spanning else f"Minimum Spanning Forest ({components} components)"
    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        distances=serialize_distance_map(keys),
        visited=tuple(visited_order),
        traversal_order=tuple(visited_order),
        selected_edges=tuple(mst_edges),
        message=f"Prim complete: {kind_label}, total weight = {total_weight:g}",
        metadata={
            "total_weight": total_weight,
            "is_spanning": is_spanning,
            "components": components,
        },
    )


def kruskal_events(graph: Graph) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Kruskal's MST algorithm."""
    graph.validate()
    if graph.directed:
        raise ValueError("Kruskal's algorithm requires an undirected graph")
    return _kruskal_events_stream(graph)


def _kruskal_events_stream(graph: Graph) -> Iterator[GraphEvent]:
    if graph.node_count == 0:
        yield make_start_event(graph, "Kruskal's Minimum Spanning Tree")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — Kruskal complete",
            metadata={"total_weight": 0.0, "is_spanning": True, "components": 0},
        )
        return

    yield make_start_event(
        graph,
        "Kruskal's Minimum Spanning Tree",
        message="Sort edges by ascending weight for Kruskal's algorithm",
    )

    dsu = _DisjointSet(graph.nodes)
    sorted_edges = [
        edge
        for _, edge in sorted(
            enumerate(graph.edges), key=lambda pair: (pair[1].weight, pair[0])
        )
    ]

    mst_edges: list[tuple[Node, Node]] = []
    touched_nodes: list[Node] = []
    touched_set: set[Node] = set()
    total_weight: float = 0.0
    components = graph.node_count

    for edge in sorted_edges:
        pair = (edge.source, edge.target)
        yield GraphEvent(
            type=GraphEventType.EXPLORE_EDGE,
            edge=pair,
            weight=edge.weight,
            visited=tuple(touched_nodes),
            selected_edges=tuple(mst_edges),
            message=f"Inspect sorted edge ({edge.source}, {edge.target}) with weight {edge.weight}",
        )
        if dsu.union(edge.source, edge.target):
            mst_edges.append(pair)
            total_weight += edge.weight
            components -= 1
            for endpoint in pair:
                if endpoint not in touched_set:
                    touched_set.add(endpoint)
                    touched_nodes.append(endpoint)
            yield GraphEvent(
                type=GraphEventType.SELECT_EDGE,
                node=edge.target,
                edge=pair,
                weight=edge.weight,
                visited=tuple(touched_nodes),
                selected_edges=tuple(mst_edges),
                message=f"Select edge ({edge.source}, {edge.target}) (w={edge.weight}, total={total_weight:g})",
            )
            if components == 1:
                break
        else:
            yield GraphEvent(
                type=GraphEventType.REJECT_EDGE,
                edge=pair,
                weight=edge.weight,
                visited=tuple(touched_nodes),
                selected_edges=tuple(mst_edges),
                message=f"Reject edge ({edge.source}, {edge.target}); forms a cycle",
            )

    is_spanning = components <= 1
    kind_label = "MST" if is_spanning else f"Minimum Spanning Forest ({components} components)"
    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        visited=graph.nodes,
        selected_edges=tuple(mst_edges),
        message=f"Kruskal complete: {kind_label}, total weight = {total_weight:g}",
        metadata={
            "total_weight": total_weight,
            "is_spanning": is_spanning,
            "components": components,
        },
    )


def topological_sort_events(graph: Graph) -> Iterator[GraphEvent]:
    """Yield standardized :class:`GraphEvent` objects for Kahn's Topological Sort.

    If a cycle prevents ordering all vertices, yields
    :attr:`GraphEventType.CYCLE_DETECTED` and :attr:`GraphEventType.COMPLETE`
    with ``metadata["has_cycle"] = True``.
    """
    graph.validate()
    if not graph.directed:
        raise ValueError("Topological sort requires a directed graph")
    return _topological_sort_events_stream(graph)


def _topological_sort_events_stream(graph: Graph) -> Iterator[GraphEvent]:
    if graph.node_count == 0:
        yield make_start_event(graph, "Topological Sort (DAG)")
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            message="Graph is empty — Topological Sort complete",
            metadata={"has_cycle": False},
        )
        return

    yield make_start_event(
        graph,
        "Topological Sort (DAG)",
        message="Compute in-degrees for all vertices",
    )

    in_degree: dict[Node, int] = {node: 0 for node in graph.nodes}
    for node in graph.nodes:
        for neighbor, _ in graph.neighbors(node):
            in_degree[neighbor] += 1

    queue: deque[Node] = deque(
        node for node in graph.nodes if in_degree[node] == 0
    )
    for node in queue:
        yield GraphEvent(
            type=GraphEventType.DISCOVER_NODE,
            node=node,
            frontier=tuple(queue),
            message=f"Node {node} has in-degree 0; enqueue it",
        )

    order: list[Node] = []
    completed: list[Node] = []
    selected_edges: list[tuple[Node, Node]] = []

    while queue:
        current = queue.popleft()
        order.append(current)
        yield GraphEvent(
            type=GraphEventType.VISIT_NODE,
            node=current,
            frontier=tuple(queue),
            visited=tuple(completed),
            traversal_order=tuple(order),
            selected_edges=tuple(selected_edges),
            message=f"Dequeue {current} and append to topological order",
        )

        for neighbor, weight in graph.neighbors(current):
            yield GraphEvent(
                type=GraphEventType.EXPLORE_EDGE,
                node=current,
                edge=(current, neighbor),
                weight=weight,
                frontier=tuple(queue),
                visited=tuple(completed),
                traversal_order=tuple(order),
                selected_edges=tuple(selected_edges),
                message=f"Remove outgoing edge ({current}, {neighbor})",
            )
            selected_edges.append((current, neighbor))
            in_degree[neighbor] -= 1
            yield GraphEvent(
                type=GraphEventType.SELECT_EDGE,
                node=neighbor,
                edge=(current, neighbor),
                weight=weight,
                frontier=tuple(queue),
                visited=tuple(completed),
                traversal_order=tuple(order),
                selected_edges=tuple(selected_edges),
                message=f"Decrement in-degree of {neighbor} to {in_degree[neighbor]}",
            )
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                yield GraphEvent(
                    type=GraphEventType.DISCOVER_NODE,
                    node=neighbor,
                    frontier=tuple(queue),
                    visited=tuple(completed),
                    traversal_order=tuple(order),
                    selected_edges=tuple(selected_edges),
                    message=f"Node {neighbor} reached in-degree 0; enqueue it",
                )

        completed.append(current)
        yield GraphEvent(
            type=GraphEventType.COMPLETE_NODE,
            node=current,
            frontier=tuple(queue),
            visited=tuple(completed),
            traversal_order=tuple(order),
            selected_edges=tuple(selected_edges),
            message=f"Finish processing {current}",
        )

    if len(order) != graph.node_count:
        completed_set = set(completed)
        cycle_nodes = [node for node in graph.nodes if node not in completed_set]
        yield GraphEvent(
            type=GraphEventType.CYCLE_DETECTED,
            node=cycle_nodes[0],
            visited=tuple(completed),
            traversal_order=tuple(order),
            selected_edges=tuple(selected_edges),
            message=f"Cycle detected! Remaining nodes have non-zero in-degree: {cycle_nodes}",
            metadata={"cycle_nodes": cycle_nodes},
        )
        yield GraphEvent(
            type=GraphEventType.COMPLETE,
            visited=tuple(completed),
            traversal_order=tuple(order),
            selected_edges=tuple(selected_edges),
            message="Topological Sort halted: graph contains a cycle",
            metadata={"has_cycle": True, "cycle_nodes": cycle_nodes},
        )
        return

    yield GraphEvent(
        type=GraphEventType.COMPLETE,
        visited=tuple(completed),
        traversal_order=tuple(order),
        selected_edges=tuple(selected_edges),
        message="Topological Sort complete",
        metadata={"has_cycle": False},
    )
