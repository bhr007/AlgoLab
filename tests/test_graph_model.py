import pytest

from sortlab.graphs import Graph, GraphEdge


def test_graph_undirected_and_directed_adjacency_lists():
    undirected = Graph.from_edges([("A", "B"), ("B", "C")], directed=False)
    assert undirected.node_count == 3
    assert undirected.edge_count == 2
    assert undirected.neighbors("A") == (("B", 1),)
    assert undirected.neighbors("B") == (("A", 1), ("C", 1))
    assert undirected.degree if hasattr(undirected, "degree") else undirected.out_degree("B") == 2
    assert undirected.in_degree("B") == 2
    assert undirected.has_edge("A", "B")
    assert undirected.has_edge("B", "A")

    directed = Graph.from_edges([("A", "B"), ("B", "C")], directed=True)
    assert directed.has_edge("A", "B")
    assert not directed.has_edge("B", "A")
    assert directed.out_degree("B") == 1
    assert directed.in_degree("B") == 1
    assert directed.in_degree("A") == 0


def test_graph_supports_disconnected_and_isolated_nodes():
    g = Graph(nodes=["A", "B", "C", "D"], edges=[("A", "B")])
    assert g.nodes == ("A", "B", "C", "D")
    assert g.neighbors("C") == ()
    assert g.neighbors("D") == ()
    assert "C" in g
    assert len(g) == 4

    empty = Graph()
    assert empty.node_count == 0
    assert empty.edge_count == 0
    empty.validate()


def test_graph_supports_mixed_str_and_int_nodes_and_round_trip():
    g = Graph.from_edges([(0, "A", 2.5), ("A", 1, -3)], nodes=[0, "A", 1, 99], directed=True, weighted=True)
    payload = g.to_dict()
    rebuilt = Graph.from_dict(payload)
    assert rebuilt == g
    assert rebuilt.copy() == g
    assert rebuilt.edges == (GraphEdge(0, "A", 2.5), GraphEdge("A", 1, -3))


def test_graph_self_loop_policy():
    g = Graph(directed=True)
    with pytest.raises(ValueError, match="Self-loop"):
        g.add_edge("A", "A")

    g_loops = Graph(directed=True, allow_self_loops=True)
    g_loops.add_edge("A", "A")
    assert g_loops.has_edge("A", "A")
    g_loops.validate()


def test_graph_parallel_edge_policy():
    undirected = Graph(directed=False)
    undirected.add_edge("A", "B")
    with pytest.raises(ValueError, match="Parallel undirected edge"):
        undirected.add_edge("B", "A")

    directed = Graph(directed=True)
    directed.add_edge("A", "B")
    # Reverse direction is distinct in directed graphs.
    directed.add_edge("B", "A")
    with pytest.raises(ValueError, match="Parallel directed edge"):
        directed.add_edge("A", "B")

    multigraph = Graph(directed=False, weighted=True, allow_parallel_edges=True)
    multigraph.add_edge("A", "B", 5)
    multigraph.add_edge("B", "A", 2)
    assert multigraph.edge_count == 2


def test_graph_validation_errors():
    with pytest.raises(TypeError):
        Graph(nodes=[True])
    with pytest.raises(ValueError):
        Graph(nodes=["   "])

    unweighted = Graph(weighted=False)
    with pytest.raises(ValueError, match="Unweighted"):
        unweighted.add_edge("A", "B", 5)

    weighted = Graph(weighted=True)
    with pytest.raises(ValueError, match="explicit numeric"):
        weighted.add_edge("A", "B")
    with pytest.raises(TypeError):
        weighted.add_edge("A", "B", True)
    with pytest.raises(ValueError, match="finite"):
        weighted.add_edge("A", "B", float("nan"))
    with pytest.raises(ValueError, match="finite"):
        weighted.add_edge("A", "B", float("inf"))

    strict_nodes = Graph(nodes=["A"])
    with pytest.raises(ValueError, match="not in the graph"):
        strict_nodes.add_edge("A", "B", auto_add_nodes=False)
