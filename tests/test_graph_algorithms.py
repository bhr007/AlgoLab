import math

import pytest

from sortlab.graphs import (
    Graph,
    GraphCycleError,
    NegativeCycleError,
    bellman_ford,
    bfs,
    dfs,
    dijkstra,
    kruskal,
    prim,
    topological_sort,
)


def test_bfs_and_dfs_connected_disconnected_directed_and_cycles():
    # Undirected graph with a cycle and an isolated component
    g = Graph.from_edges(
        [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("E", "F")],
        nodes=["A", "B", "C", "D", "E", "F", "G"],
        directed=False,
    )
    snapshot = g.copy()

    assert bfs(g, "A") == ["A", "B", "C", "D"]
    assert bfs(g, "A", traverse_all=True) == ["A", "B", "C", "D", "E", "F", "G"]
    assert dfs(g, "A") == ["A", "B", "D", "C"]
    assert dfs(g, "A", traverse_all=True) == ["A", "B", "D", "C", "E", "F", "G"]
    assert g == snapshot

    # Directed graph with cycle A -> B -> C -> A
    dg = Graph.from_edges([("A", "B"), ("B", "C"), ("C", "A"), ("C", "D")], directed=True)
    assert bfs(dg, "A") == ["A", "B", "C", "D"]
    assert dfs(dg, "A") == ["A", "B", "C", "D"]
    assert bfs(dg, "D") == ["D"]

    # Empty graph & invalid start
    empty = Graph()
    assert bfs(empty) == []
    assert dfs(empty) == []
    with pytest.raises(ValueError):
        bfs(g, "MISSING")
    with pytest.raises(ValueError):
        dfs(empty, "A")


def test_dijkstra_shortest_paths_and_constraints():
    g = Graph.from_edges(
        [
            ("A", "B", 4),
            ("A", "C", 1),
            ("C", "B", 2),
            ("B", "D", 1),
            ("C", "D", 5),
            ("E", "F", 3),
        ],
        nodes=["A", "B", "C", "D", "E", "F"],
        directed=True,
        weighted=True,
    )
    res = dijkstra(g, "A")
    assert res.distances["A"] == 0
    assert res.distances["C"] == 1
    assert res.distances["B"] == 3
    assert res.distances["D"] == 4
    assert math.isinf(res.distances["E"])
    assert res.path_to("D") == ["A", "C", "B", "D"]
    assert res.path_to("E") == []

    # Undirected weighted graph with cycle
    ug = Graph.from_edges(
        [("S", "A", 7), ("S", "B", 2), ("A", "B", 3), ("A", "T", 1), ("B", "T", 8)],
        directed=False,
        weighted=True,
    )
    ures = dijkstra(ug, "S")
    assert ures.distances == {"S": 0, "A": 5, "B": 2, "T": 6}
    assert ures.path_to("T") == ["S", "B", "A", "T"]

    # Rejects negative weights
    neg = Graph.from_edges([("A", "B", -1)], directed=True, weighted=True)
    with pytest.raises(ValueError, match="non-negative"):
        dijkstra(neg, "A")


def test_bellman_ford_negative_weights_and_negative_cycles():
    # Directed graph with negative edge weights but no negative cycle
    g = Graph.from_edges(
        [
            ("S", "A", 4),
            ("S", "B", 5),
            ("A", "C", 6),
            ("B", "A", -3),
            ("C", "B", -1),
        ],
        nodes=["S", "A", "B", "C", "Z"],
        directed=True,
        weighted=True,
    )
    res = bellman_ford(g, "S")
    assert res.distances["S"] == 0
    assert res.distances["B"] == 5
    assert res.distances["A"] == 2
    assert res.distances["C"] == 8
    assert math.isinf(res.distances["Z"])
    assert res.path_to("A") == ["S", "B", "A"]

    # Reachable negative-weight cycle
    neg_cycle = Graph.from_edges(
        [("A", "B", 1), ("B", "C", -2), ("C", "A", -2)],
        directed=True,
        weighted=True,
    )
    with pytest.raises(NegativeCycleError):
        bellman_ford(neg_cycle, "A")

    # Unreachable negative cycle from "S" should succeed
    unreachable_cycle = Graph.from_edges(
        [("S", "T", 3), ("X", "Y", -1), ("Y", "X", -1)],
        directed=True,
        weighted=True,
    )
    ok_res = bellman_ford(unreachable_cycle, "S")
    assert ok_res.distances["T"] == 3
    assert math.isinf(ok_res.distances["X"])


def test_prim_and_kruskal_mst_and_disconnected_forest():
    g = Graph.from_edges(
        [
            ("A", "B", 4),
            ("A", "H", 8),
            ("B", "H", 11),
            ("B", "C", 8),
            ("H", "I", 7),
            ("H", "G", 1),
            ("I", "G", 6),
            ("I", "C", 2),
            ("C", "D", 7),
            ("C", "F", 4),
            ("G", "F", 2),
            ("D", "F", 14),
            ("D", "E", 9),
            ("F", "E", 10),
        ],
        directed=False,
        weighted=True,
    )
    p_res = prim(g, "A")
    k_res = kruskal(g)
    assert p_res.is_spanning is True
    assert k_res.is_spanning is True
    assert p_res.components == 1
    assert k_res.components == 1
    assert len(p_res.edges) == g.node_count - 1
    assert len(k_res.edges) == g.node_count - 1
    assert p_res.total_weight == 37
    assert k_res.total_weight == 37

    # Disconnected weighted graph with negative edges -> Minimum Spanning Forest
    forest = Graph.from_edges(
        [("A", "B", -3), ("B", "C", 2), ("A", "C", 5), ("D", "E", 4)],
        nodes=["A", "B", "C", "D", "E", "F"],
        directed=False,
        weighted=True,
    )
    pf = prim(forest, "A")
    kf = kruskal(forest)
    assert pf.is_spanning is False
    assert kf.is_spanning is False
    assert pf.components == 3
    assert kf.components == 3
    assert pf.total_weight == 3
    assert kf.total_weight == 3

    # Reject directed graphs
    dg = Graph.from_edges([("A", "B", 1)], directed=True, weighted=True)
    with pytest.raises(ValueError, match="undirected"):
        prim(dg)
    with pytest.raises(ValueError, match="undirected"):
        kruskal(dg)


def test_topological_sort_dag_disconnected_and_cycle_detection():
    dag = Graph.from_edges(
        [
            ("prep", "cook"),
            ("prep", "plate"),
            ("cook", "serve"),
            ("plate", "serve"),
            ("clean", "dry"),
        ],
        nodes=["prep", "cook", "plate", "serve", "clean", "dry", "isolated"],
        directed=True,
    )
    order = topological_sort(dag)
    assert set(order) == set(dag.nodes)
    assert len(order) == dag.node_count
    pos = {node: idx for idx, node in enumerate(order)}
    for edge in dag.edges:
        assert pos[edge.source] < pos[edge.target]

    # Cycle detection
    cyclic = Graph.from_edges([("A", "B"), ("B", "C"), ("C", "A")], directed=True)
    with pytest.raises(GraphCycleError):
        topological_sort(cyclic)

    # Self-loop cycle detection
    self_loop = Graph.from_edges([("A", "A")], directed=True, allow_self_loops=True)
    with pytest.raises(GraphCycleError):
        topological_sort(self_loop)

    # Rejects undirected graphs
    ug = Graph.from_edges([("A", "B")], directed=False)
    with pytest.raises(ValueError, match="directed"):
        topological_sort(ug)
