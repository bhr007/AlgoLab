import json

from sortlab.graphs import (
    Graph,
    GraphEvent,
    GraphEventType,
    bellman_ford_events,
    bfs_events,
    dfs_events,
    dijkstra_events,
    extract_graph_from_events,
    graph_events_to_json,
    kruskal_events,
    prim_events,
    topological_sort_events,
)


def test_graph_events_serialization_round_trip():
    g = Graph.from_edges(
        [("A", "B", 2), ("B", "C", 3), ("A", "C", 10)],
        directed=True,
        weighted=True,
    )
    events = list(dijkstra_events(g, "A"))
    assert events[0].type == GraphEventType.START
    assert events[-1].type == GraphEventType.COMPLETE
    assert extract_graph_from_events(events) == g

    raw_json = graph_events_to_json(events)
    parsed = json.loads(raw_json)
    rehydrated = [GraphEvent.from_dict(item) for item in parsed]
    assert rehydrated == events


def test_bfs_and_dfs_event_ordering():
    g = Graph.from_edges([("A", "B"), ("A", "C"), ("B", "D")], directed=False)
    for gen in (bfs_events, dfs_events):
        events = list(gen(g, "A"))
        types = [e.type for e in events]
        assert types[0] == GraphEventType.START
        assert types[-1] == GraphEventType.COMPLETE
        assert {
            GraphEventType.DISCOVER_NODE,
            GraphEventType.VISIT_NODE,
            GraphEventType.EXPLORE_EDGE,
            GraphEventType.SELECT_EDGE,
            GraphEventType.COMPLETE_NODE,
        } <= set(types)
        assert set(events[-1].traversal_order) == {"A", "B", "C", "D"}


def test_dijkstra_and_bellman_ford_events():
    g = Graph.from_edges(
        [("A", "B", 4), ("A", "C", 1), ("C", "B", 2)],
        directed=True,
        weighted=True,
    )
    dijk = list(dijkstra_events(g, "A"))
    dijk_types = {e.type for e in dijk}
    assert {
        GraphEventType.START,
        GraphEventType.DISCOVER_NODE,
        GraphEventType.VISIT_NODE,
        GraphEventType.EXPLORE_EDGE,
        GraphEventType.RELAX_EDGE,
        GraphEventType.UPDATE_DISTANCE,
        GraphEventType.SELECT_EDGE,
        GraphEventType.COMPLETE_NODE,
        GraphEventType.COMPLETE,
    } <= dijk_types
    assert dijk[-1].distances == {"A": 0, "B": 3, "C": 1}

    bf = list(bellman_ford_events(g, "A"))
    assert bf[-1].distances == {"A": 0, "B": 3, "C": 1}
    assert bf[-1].metadata["negative_cycle"] is False

    neg_cycle = Graph.from_edges(
        [("A", "B", 1), ("B", "C", -3), ("C", "A", 1)],
        directed=True,
        weighted=True,
    )
    bf_neg = list(bellman_ford_events(neg_cycle, "A"))
    assert any(e.type == GraphEventType.CYCLE_DETECTED for e in bf_neg)
    assert bf_neg[-1].type == GraphEventType.COMPLETE
    assert bf_neg[-1].metadata["negative_cycle"] is True


def test_prim_and_kruskal_events():
    g = Graph.from_edges(
        [("A", "B", 1), ("B", "C", 2), ("A", "C", 5)],
        directed=False,
        weighted=True,
    )
    p_events = list(prim_events(g, "A"))
    assert p_events[0].type == GraphEventType.START
    assert p_events[-1].type == GraphEventType.COMPLETE
    assert p_events[-1].metadata["total_weight"] == 3
    assert GraphEventType.UPDATE_DISTANCE in {e.type for e in p_events}

    k_events = list(kruskal_events(g))
    assert k_events[0].type == GraphEventType.START
    assert k_events[-1].type == GraphEventType.COMPLETE
    assert k_events[-1].metadata["total_weight"] == 3
    assert GraphEventType.SELECT_EDGE in {e.type for e in k_events}

    # With 4-node cycle so Kruskal rejects at least one edge
    g2 = Graph.from_edges(
        [("A", "B", 1), ("B", "C", 2), ("A", "C", 3), ("C", "D", 4)],
        directed=False,
        weighted=True,
    )
    k2 = list(kruskal_events(g2))
    assert GraphEventType.REJECT_EDGE in {e.type for e in k2}


def test_topological_sort_events_and_cycle_events():
    dag = Graph.from_edges([("A", "B"), ("B", "C"), ("A", "C")], directed=True)
    events = list(topological_sort_events(dag))
    assert events[0].type == GraphEventType.START
    assert events[-1].type == GraphEventType.COMPLETE
    assert events[-1].traversal_order == ("A", "B", "C")
    assert events[-1].metadata["has_cycle"] is False

    cyclic = Graph.from_edges([("A", "B"), ("B", "A")], directed=True)
    c_events = list(topological_sort_events(cyclic))
    assert any(e.type == GraphEventType.CYCLE_DETECTED for e in c_events)
    assert c_events[-1].metadata["has_cycle"] is True
