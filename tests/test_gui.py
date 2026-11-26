from unittest.mock import patch

import matplotlib
import pytest

matplotlib.use("Agg")

from sortlab.core.registry import get_algorithm_spec
from sortlab.graphs.registry import GRAPH_ALGORITHM_SPECS, get_graph_algorithm_spec
from sortlab.gui import (
    GRAPH_EXAMPLES,
    AlgoLabStudio,
    GraphInputRequest,
    SortingInputRequest,
    SortLabStudio,
    build_graph_request,
    build_sorting_request,
    describe_graph_constraints,
    describe_sort_constraints,
    launch_gui_studio,
    parse_optional_interval,
)


def test_build_sorting_request_valid_and_invalid():
    req = build_sorting_request("Merge Sort", "8, 3, -2, 5", "150")
    assert isinstance(req, SortingInputRequest)
    assert req.spec.key == "merge_sort"
    assert req.values == [8, 3, -2, 5]
    assert req.interval == 150

    req_auto = build_sorting_request("Quick Sort", "3 1 2", "")
    assert req_auto.interval is None

    with pytest.raises(ValueError, match="integers only"):
        build_sorting_request("Counting Sort", "1, 2.5, 3")

    with pytest.raises(ValueError, match="at least 1 ms"):
        parse_optional_interval("0")

    with pytest.raises(ValueError, match="whole number"):
        parse_optional_interval("fast")


def test_build_graph_request_for_all_example_presets():
    for spec in GRAPH_ALGORITHM_SPECS:
        preset = GRAPH_EXAMPLES[spec.key]
        req = build_graph_request(
            spec.name,
            directed=preset.directed,
            weighted=preset.weighted,
            nodes_raw=preset.nodes,
            edges_raw=preset.edges,
            start_raw=preset.start,
            interval_raw="200",
        )
        assert isinstance(req, GraphInputRequest)
        assert req.spec.key == spec.key
        assert req.interval == 200
        assert req.graph.node_count > 0


def test_build_graph_request_enforces_constraints():
    with pytest.raises(ValueError, match="non-negative"):
        build_graph_request(
            "Dijkstra's Shortest Path",
            directed=True,
            weighted=True,
            nodes_raw="",
            edges_raw="A B -2",
            start_raw="A",
        )

    with pytest.raises(ValueError, match="not in the graph"):
        build_graph_request(
            "Breadth-First Search (BFS)",
            directed=False,
            weighted=False,
            nodes_raw="",
            edges_raw="A B, B C",
            start_raw="Z",
        )

    prim_req = build_graph_request(
        "Prim's Minimum Spanning Tree",
        directed=True,
        weighted=False,
        nodes_raw="",
        edges_raw="A B 3, B C 1",
        start_raw="",
    )
    assert prim_req.graph.directed is False
    assert prim_req.graph.weighted is True


def test_constraint_descriptions_are_populated():
    assert "Integers only" in describe_sort_constraints(
        get_algorithm_spec("counting_sort")
    )
    assert "decimals" in describe_sort_constraints(get_algorithm_spec("merge_sort"))
    assert "Weights >= 0" in describe_graph_constraints(
        get_graph_algorithm_spec("dijkstra")
    )
    assert "Directed" in describe_graph_constraints(
        get_graph_algorithm_spec("topological_sort")
    )


def test_single_window_studio_switches_runs_validates_and_closes():
    studio = launch_gui_studio(initial_mode="sorting", default_interval=80, show=False)
    try:
        assert studio.mode == "sorting"
        assert studio.active_controller is not None
        assert studio.active_controller.animation is None
        # Must NOT auto-start simulation before user confirms with Run & Visualize.
        assert studio.active_controller.is_paused is True
        assert "Preview ready" in studio.status_text.get_text()

        # Selecting an algorithm updates preview while remaining paused until Run.
        studio._on_sort_radio_clicked("Quick Sort")
        assert studio.selected_sort_key == "quick_sort"
        assert studio.active_controller.is_paused is True

        studio._set_sort_values("9, -1, 4, 2, 7")
        assert studio.run_current() is True
        assert studio.active_controller.algorithm_name == "Quick Sort"
        assert studio.active_controller.is_paused is False

        # Invalid integer-only input displays inline error without crashing.
        studio._select_sort_algo("counting_sort")
        studio._set_sort_values("1, 2.5, 3")
        assert studio.run_current() is False
        assert "Input error" in studio.status_text.get_text()

        # Switch to Graph mode in the same single window (paused preview until Run).
        studio.switch_mode("graph", run_preview=True)
        assert studio.mode == "graph"
        assert studio.active_controller is not None
        assert studio.active_controller.is_paused is True

        # Selecting a graph algorithm or preset stays paused until Run & Visualize.
        for key in ("dijkstra", "kruskal", "topological_sort", "bellman_ford"):
            studio._select_graph_algo(key, update_preview=True)
            assert studio.active_controller.is_paused is True
            assert studio.run_current() is True
            assert studio.active_controller.is_paused is False

        studio._load_cycle_demo()
        assert studio.run_current() is True
        assert "Cycle detected" in studio.status_text.get_text()

        studio._select_graph_algo("bfs")
        studio._load_disconnected_demo()
        assert studio.run_current() is True

        # Playback controls delegate cleanly without leaking animations.
        assert studio.active_controller.is_paused is False
        studio._on_play()
        assert studio.active_controller.is_paused is True
        studio._on_play()
        assert studio.active_controller.is_paused is False
        studio._on_timer_tick()
        assert studio.active_controller.current_render_idx >= 1
        studio._on_step()
        assert studio.active_controller.is_paused is True
        studio._on_speed(160)
        assert studio.active_controller.interval == 160
        studio._on_reset()
        assert studio.active_controller.current_render_idx == 0

        # RadioButtons switching updates selected algorithm and runs cleanly.
        studio._on_graph_radio_clicked("Prim's Minimum Spanning Tree")
        assert studio.selected_graph_key == "prim"
        assert studio.active_controller.is_paused is True
        studio.switch_mode("sorting", run_preview=True)
        assert studio.active_controller.is_paused is True
        studio._on_sort_radio_clicked("Merge Sort")
        assert studio.selected_sort_key == "merge_sort"
        assert studio.active_controller.is_paused is True

        # Invalid negative edge in Dijkstra reports error cleanly.
        studio.switch_mode("graph")
        studio._select_graph_algo("dijkstra")
        studio.tb_graph_edges.set_val("A B -3")
        studio.tb_graph_start.set_val("A")
        assert studio.run_current() is False
        assert "Input error" in studio.status_text.get_text()

        # Close stops active timers cleanly and marks closed.
        studio.close()
        assert studio._closed is True
    finally:
        studio.shutdown()
        matplotlib.pyplot.close(studio.fig)


def test_launch_gui_studio_calls_plt_show_and_cleans_up():
    with (
        patch("matplotlib.pyplot.show") as mock_show,
        patch("matplotlib.pyplot.close") as mock_close,
    ):
        studio = launch_gui_studio(show=True)

    mock_show.assert_called_once()
    mock_close.assert_called_once()
    assert studio._closed is True
    assert isinstance(studio, AlgoLabStudio)
    assert SortLabStudio is AlgoLabStudio
    assert studio.fig._algolab_studio is studio
    assert studio.fig._sortlab_studio is studio
