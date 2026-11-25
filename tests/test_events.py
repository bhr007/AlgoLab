from sortlab.core import SortEventType, bubble_sort_events


def test_bubble_sort_events_finish_sorted():
    events = list(bubble_sort_events([4, 2, 3, 1]))
    assert events[-1].type == SortEventType.COMPLETE
    assert events[-1].values == (1, 2, 3, 4)


def test_empty_event_stream():
    events = list(bubble_sort_events([]))
    assert events[-1].type == SortEventType.COMPLETE
    assert events[-1].values == ()
