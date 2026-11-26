from unittest.mock import patch

import matplotlib
import pytest

matplotlib.use("Agg")

from sortlab.graphs import (
    GRAPH_ALGORITHM_SPECS,
    Graph,
    GraphEvent,
    GraphEventType,
    bellman_ford_events,
    bfs_events,
    topological_sort_events,
)
from sortlab.visualization.graph_matplotlib import (
    animate_graph_events,
    compute_graph_layout,
)


def test_compute_graph_layout_is_deterministic_and_handles_edge_cases():
    assert compute_graph_layout(Graph()) == {}
    assert compute_graph_layout(Graph(nodes=["A"])) == {"A": (0.0, 0.0)}

    g = Graph.from_edges(
        [("A", "B"), ("B", "C"), ("C", "A"), ("D", "E")],
        nodes=["A", "B", "C", "D", "E", "F"],
    )
    layout1 = compute_graph_layout(g)
    layout2 = compute_graph_layout(g)
    assert layout1 == layout2
    assert set(layout1.keys()) == set(g.nodes)


@pytest.mark.parametrize("spec", GRAPH_ALGORITHM_SPECS, ids=[s.key for s in GRAPH_ALGORITHM_SPECS])
def test_headless_graph_visualization_renders_all_algorithms(spec):
    if spec.requires_directed is True:
        g = Graph.from_edges(
            [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
            nodes=["A", "B", "C", "D", "E"],
            directed=True,
            weighted=bool(spec.requires_weighted),
        )
    else:
        g = Graph.from_edges(
            [("A", "B", 2), ("B", "C", 3), ("A", "C", 6), ("C", "D", 1)]
            if spec.requires_weighted
            else [("A", "B"), ("B", "C"), ("A", "C"), ("C", "D")],
            nodes=["A", "B", "C", "D", "E"],
            directed=False,
            weighted=bool(spec.requires_weighted),
        )

    events = (
        spec.event_generator(g, "A")
        if (spec.requires_start or spec.optional_start)
        else spec.event_generator(g)
    )
    anim = animate_graph_events(events, interval=10, show=False)
    ctrl = anim._fig._sortlab_graph_controller
    assert ctrl.algorithm_name == spec.name
    assert len(ctrl._node_patches) == g.node_count
    assert len(ctrl._edge_artists) == g.edge_count

    ctrl.render_frame(ctrl.total_rendered - 1)
    assert ctrl.is_paused is True
    matplotlib.pyplot.close(anim._fig)


def test_graph_visualization_controls_bidirectional_and_cycles():
    # Directed weighted graph with bidirectional edge and negative cycle
    g = Graph.from_edges(
        [("A", "B", 2), ("B", "A", -4), ("B", "C", 1)],
        directed=True,
        weighted=True,
        allow_self_loops=True,
    )
    g.add_edge("C", "C", 1)

    events = list(bellman_ford_events(g, "A"))
    anim = animate_graph_events(events, interval=20, show=False, max_frames=20)
    ctrl = anim._fig._sortlab_graph_controller
    assert ctrl.total_rendered <= 20

    ctrl.step_once()
    assert ctrl.is_paused is True
    assert ctrl.current_render_idx == 1

    ctrl._on_speed_change(120)
    assert ctrl.interval == 120

    ctrl.render_frame(ctrl.total_rendered - 1)
    ctrl.toggle_play()
    assert ctrl.current_render_idx == 0
    assert ctrl.is_paused is False

    ctrl.reset()
    assert ctrl.current_render_idx == 0
    assert ctrl.is_paused is True
    matplotlib.pyplot.close(anim._fig)

    # Topological sort cycle rendering
    cyclic = Graph.from_edges([("A", "B"), ("B", "A")], directed=True)
    topo_anim = animate_graph_events(topological_sort_events(cyclic), show=False)
    topo_ctrl = topo_anim._fig._sortlab_graph_controller
    topo_ctrl.render_frame(topo_ctrl.total_rendered - 1)
    matplotlib.pyplot.close(topo_anim._fig)


def test_graph_visualization_empty_and_invalid_streams():
    empty_anim = animate_graph_events(bfs_events(Graph()), show=False)
    assert empty_anim._fig._sortlab_graph_controller.graph.node_count == 0
    matplotlib.pyplot.close(empty_anim._fig)

    with pytest.raises(ValueError, match="at least one event"):
        animate_graph_events([], show=False)

    with pytest.raises(ValueError, match="No graph structure found"):
        animate_graph_events([GraphEvent(GraphEventType.COMPLETE)], show=False)


def test_animate_graph_events_calls_plt_show_and_closes_on_exit():
    g = Graph.from_edges([("A", "B"), ("B", "C")], directed=False)
    with (
        patch("matplotlib.pyplot.show") as mock_show,
        patch("matplotlib.pyplot.close") as mock_close,
    ):
        animate_graph_events(bfs_events(g, "A"), show=True)

    mock_show.assert_called_once()
    mock_close.assert_called_once()
