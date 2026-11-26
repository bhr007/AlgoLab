from unittest.mock import patch

import pytest

from sortlab import cli
from sortlab.core import ALGORITHM_REGISTRY, ALGORITHM_SPECS, get_algorithm_spec
from sortlab.graphs import (
    GRAPH_ALGORITHM_REGISTRY,
    GRAPH_ALGORITHM_SPECS,
    Graph,
    MSTResult,
    ShortestPathResult,
    get_graph_algorithm_spec,
)


def test_registry_has_all_ten_algorithms():
    assert len(ALGORITHM_SPECS) == 10
    assert list(ALGORITHM_REGISTRY.keys()) == [str(i) for i in range(1, 11)]
    assert get_algorithm_spec("quick_sort").choice == "5"
    assert get_algorithm_spec("Counting Sort").integer_only is True
    assert get_algorithm_spec("Radix Sort").integer_only is True
    with pytest.raises(ValueError):
        get_algorithm_spec("unknown")


def test_graph_registry_has_all_seven_algorithms():
    assert len(GRAPH_ALGORITHM_SPECS) == 7
    assert list(GRAPH_ALGORITHM_REGISTRY.keys()) == [str(i) for i in range(1, 8)]
    assert get_graph_algorithm_spec("dijkstra").choice == "3"
    assert get_graph_algorithm_spec("Topological Sort (DAG)").requires_directed is True
    assert get_graph_algorithm_spec("prim").requires_directed is False
    with pytest.raises(ValueError):
        get_graph_algorithm_spec("unknown_graph_algo")


def test_parse_values_valid_and_invalid():
    assert cli.parse_values("3, 1 2") == [3, 1, 2]
    assert cli.parse_values("3.0, -2.5 0") == [3, -2.5, 0]
    large = 10**25
    assert cli.parse_values(f"{large} 1") == [large, 1]

    for bad in ("", "   ", "1, abc", "nan", "inf", "-inf"):
        with pytest.raises(ValueError):
            cli.parse_values(bad)


def test_parse_graph_edges_and_build_graph():
    unweighted = cli.parse_graph_edges("A B, B->C; C D", weighted=False)
    assert unweighted == [("A", "B"), ("B", "C"), ("C", "D")]

    weighted = cli.parse_graph_edges("A B 4, B->C -2.5", weighted=True)
    assert weighted == [("A", "B", 4), ("B", "C", -2.5)]

    graph = cli.build_graph_from_input("A B C D E", "A B, B C", directed=True, weighted=False)
    assert graph.directed is True
    assert graph.nodes == ("A", "B", "C", "D", "E")

    for bad_unweighted in ("A", "A B 5"):
        with pytest.raises(ValueError):
            cli.parse_graph_edges(bad_unweighted, weighted=False)

    for bad_weighted in ("A B", "A B nan", "A B inf", "A B xyz"):
        with pytest.raises(ValueError):
            cli.parse_graph_edges(bad_weighted, weighted=True)

    with pytest.raises(ValueError):
        cli.build_graph_from_input("", "", directed=False, weighted=False)


@pytest.mark.parametrize("choice", [str(i) for i in range(1, 11)])
def test_run_algorithm_dispatches_all_ten(choice):
    values = [5, -2, 3, 0, 5, 1]
    assert cli.run_algorithm(choice, values) == sorted(values)


@pytest.mark.parametrize("choice", ["8", "9"])
def test_run_algorithm_rejects_floats_for_integer_only_sorts(choice):
    with pytest.raises(ValueError, match="integers only"):
        cli.run_algorithm(choice, [1, 2.5, 3])


def test_run_graph_algorithm_dispatches_and_validates():
    undirected_weighted = Graph.from_edges(
        [("A", "B", 2), ("B", "C", 3), ("A", "C", 10)],
        directed=False,
        weighted=True,
    )
    assert cli.run_graph_algorithm("1", undirected_weighted, "A") == ["A", "B", "C"]
    assert cli.run_graph_algorithm("2", undirected_weighted, "A") == ["A", "B", "C"]

    dijk_res = cli.run_graph_algorithm("3", undirected_weighted, "A")
    assert isinstance(dijk_res, ShortestPathResult)
    assert dijk_res.distances["C"] == 5

    bf_res = cli.run_graph_algorithm("4", undirected_weighted, "A")
    assert isinstance(bf_res, ShortestPathResult)
    assert bf_res.distances["C"] == 5

    prim_res = cli.run_graph_algorithm("5", undirected_weighted, "A")
    kruskal_res = cli.run_graph_algorithm("6", undirected_weighted)
    assert isinstance(prim_res, MSTResult)
    assert isinstance(kruskal_res, MSTResult)
    assert prim_res.total_weight == 5
    assert kruskal_res.total_weight == 5

    dag = Graph.from_edges([("A", "B"), ("B", "C")], directed=True, weighted=False)
    assert cli.run_graph_algorithm("7", dag) == ["A", "B", "C"]

    # Constraint violations
    neg_graph = Graph.from_edges([("A", "B", -1)], directed=True, weighted=True)
    with pytest.raises(ValueError, match="non-negative"):
        cli.run_graph_algorithm("3", neg_graph, "A")

    with pytest.raises(ValueError, match="undirected"):
        cli.run_graph_algorithm("5", dag)

    with pytest.raises(ValueError, match="directed"):
        cli.run_graph_algorithm("7", undirected_weighted)


@pytest.mark.parametrize("choice", [str(i) for i in range(1, 11)])
def test_cli_automatically_launches_visualization_and_returns_to_menu(
    choice, capsys
):
    inputs = iter(["1", choice, "4, 1, -2, 3", "0", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_algorithm") as mock_vis,
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    mock_vis.assert_called_once()
    called_spec, called_values = mock_vis.call_args.args
    assert called_spec.choice == choice
    assert called_values == [4, 1, -2, 3]
    out = capsys.readouterr().out
    assert "Sorted:    [-2, 1, 3, 4]" in out
    assert "Goodbye!" in out


def test_cli_rejects_floats_for_counting_and_radix_before_visualizing(capsys):
    inputs = iter(["1", "8", "1 2.5 3", "9", "4 1.2", "0", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_algorithm") as mock_vis,
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    mock_vis.assert_not_called()
    out = capsys.readouterr().out
    assert "Counting Sort accepts integers only" in out
    assert "Radix Sort accepts integers only" in out


def test_cli_handles_invalid_menu_choice_and_missing_matplotlib(capsys):
    inputs = iter(["9", "1", "99", "1", "3 1 2", "0", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch(
            "sortlab.cli.visualize_algorithm",
            side_effect=ImportError("Matplotlib is optional"),
        ),
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Invalid choice" in out
    assert "Visualization unavailable" in out
    assert "Goodbye!" in out


def test_cli_graph_menu_bfs_dijkstra_kruskal_topological(capsys):
    # Enter Graph Menu ("2"), run BFS ("1"), Dijkstra ("3"), Kruskal ("6"),
    # Topological Sort ("7"), return to main menu ("0"), exit ("0").
    inputs = iter([
        "2",
        # 1. BFS (undirected, unweighted)
        "1", "n", "n", "", "A B, B C", "A",
        # 3. Dijkstra (directed, weighted)
        "3", "y", "", "A B 2, B C 3, A C 10", "A",
        # 6. Kruskal (undirected, weighted)
        "6", "", "A B 4, B C 1, A C 3",
        # 7. Topological Sort (directed, unweighted)
        "7", "n", "", "A B, B C",
        "0",
        "0",
    ])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_graph_algorithm") as mock_graph_vis,
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    assert mock_graph_vis.call_count == 4
    out = capsys.readouterr().out
    assert "Traversal order from A: A -> B -> C" in out
    assert "A -> C (distance=5): A -> B -> C" in out
    assert "Total weight: 4" in out
    assert "Topological order: A -> B -> C" in out


def test_cli_graph_menu_rejects_invalid_inputs_before_visualizing(capsys):
    inputs = iter([
        "2",
        "99",
        # Dijkstra with negative edge weight -> rejected
        "3", "y", "", "A B -5", "A",
        # BFS with unknown start node -> rejected
        "1", "n", "n", "", "A B", "Z",
        "0",
        "0",
    ])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_graph_algorithm") as mock_graph_vis,
    ):
        exit_code = cli.main([])

    assert exit_code == 0
    mock_graph_vis.assert_not_called()
    out = capsys.readouterr().out
    assert "Invalid choice" in out
    assert "requires non-negative edge weights" in out
    assert "is not in the graph" in out


def test_cli_list_and_no_vis_flags(capsys):
    assert cli.main(["--list"]) == 0
    listed = capsys.readouterr().out
    assert "1. Bubble Sort" in listed
    assert "10. Bucket Sort" in listed
    assert "1. Breadth-First Search (BFS)" in listed
    assert "7. Topological Sort (DAG)" in listed

    inputs = iter(["1", "4", "3 1 2", "0", "2", "1", "n", "n", "", "A B", "A", "0", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.cli.visualize_algorithm") as mock_sort_vis,
        patch("sortlab.cli.visualize_graph_algorithm") as mock_graph_vis,
    ):
        assert cli.main(["--no-vis"]) == 0
    mock_sort_vis.assert_not_called()
    mock_graph_vis.assert_not_called()


def test_cli_gui_flag_and_menu_option(capsys):
    with patch("sortlab.gui.launch_gui_studio") as mock_studio:
        assert cli.main(["--gui"]) == 0
    mock_studio.assert_called_once_with(default_interval=None, show=True)

    with patch("sortlab.gui.launch_gui_studio") as mock_studio_mode:
        assert cli.main(["--mode", "gui", "--interval", "150"]) == 0
    mock_studio_mode.assert_called_once_with(default_interval=150, show=True)

    # --mode cli disables visualization (CLI only)
    inputs_cli_only = iter(["1", "4", "3 1 2", "0", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs_cli_only)),
        patch("sortlab.cli.visualize_algorithm") as mock_vis,
    ):
        assert cli.main(["--mode", "cli"]) == 0
    mock_vis.assert_not_called()

    # Option 3 from main menu launches the single-window GUI studio and returns to main menu.
    inputs = iter(["3", "0"])
    with (
        patch("builtins.input", side_effect=lambda _prompt="": next(inputs)),
        patch("sortlab.gui.launch_gui_studio") as mock_gui,
    ):
        assert cli.main([]) == 0
    mock_gui.assert_called_once_with(default_interval=None, show=True)
    out = capsys.readouterr().out
    assert "AlgoLab" in out
    assert "Goodbye!" in out


def test_cli_algolab_branding_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])
    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "algolab" in help_text
    assert "AlgoLab" in help_text
    assert "Explore. Visualize. Understand Algorithms." in help_text
