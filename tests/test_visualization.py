from unittest.mock import patch

import matplotlib
import pytest

matplotlib.use("Agg")

from sortlab.core import ALGORITHM_SPECS, SortEvent, SortEventType, bubble_sort_events
from sortlab.visualization.matplotlib import STATE_COLORS, animate_events


@pytest.mark.parametrize("spec", ALGORITHM_SPECS, ids=[s.key for s in ALGORITHM_SPECS])
def test_headless_visualization_renders_all_algorithms(spec):
    sample = [8, -3, 5, 0, 8, 2, -1, 4]
    anim = animate_events(
        spec.event_generator(sample),
        interval=10,
        algorithm_name=spec.name,
        show=False,
    )
    ctrl = anim._fig._sortlab_controller
    assert ctrl.algorithm_name == spec.name
    assert len(ctrl.bars) == len(sample)

    # Jump to final frame and verify bar heights and sorted green coloring.
    ctrl.render_frame(ctrl.total_rendered - 1)
    heights = [bar.get_height() for bar in ctrl.bars]
    assert heights == sorted(sample)
    expected_rgba = matplotlib.colors.to_rgba(STATE_COLORS[SortEventType.COMPLETE.value])
    assert all(bar.get_facecolor() == expected_rgba for bar in ctrl.bars)
    matplotlib.pyplot.close(anim._fig)


def test_visualization_controls_and_downsampling():
    values = list(range(35, 0, -1))
    events = list(bubble_sort_events(values))
    anim = animate_events(
        events,
        interval=20,
        algorithm_name="Bubble Sort",
        show=False,
        max_frames=25,
    )
    ctrl = anim._fig._sortlab_controller
    assert ctrl.total_rendered <= 25
    assert ctrl.value_texts == []

    ctrl.step_once()
    assert ctrl.is_paused is True
    assert ctrl.current_render_idx == 1

    ctrl._on_speed_change(100)
    assert ctrl.interval == 100

    ctrl.render_frame(ctrl.total_rendered - 1)
    assert [bar.get_height() for bar in ctrl.bars] == sorted(values)

    # Toggling play at the end rewinds to frame 0 for replay.
    ctrl.toggle_play()
    assert ctrl.current_render_idx == 0
    assert ctrl.is_paused is False

    ctrl.reset()
    assert ctrl.current_render_idx == 0
    assert ctrl.is_paused is True
    matplotlib.pyplot.close(anim._fig)


def test_visualization_empty_and_invalid_streams():
    anim = animate_events(bubble_sort_events([]), algorithm_name="Bubble Sort", show=False)
    ctrl = anim._fig._sortlab_controller
    assert ctrl.array_len == 0
    matplotlib.pyplot.close(anim._fig)

    with pytest.raises(ValueError, match="at least one event"):
        animate_events([], show=False)

    with pytest.raises(ValueError, match="No array snapshots"):
        animate_events([SortEvent(SortEventType.COMPARE, (0, 1))], show=False)


def test_animate_events_calls_plt_show_and_closes_on_exit():
    with (
        patch("matplotlib.pyplot.show") as mock_show,
        patch("matplotlib.pyplot.close") as mock_close,
    ):
        animate_events(bubble_sort_events([3, 1, 2]), algorithm_name="Bubble Sort", show=True)

    mock_show.assert_called_once()
    mock_close.assert_called_once()
