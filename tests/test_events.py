import json
import random

import pytest

from sortlab.core import (
    ALGORITHM_SPECS,
    SortEvent,
    SortEventType,
    apply_event,
    bubble_sort_events,
    bucket_sort_events,
    counting_sort_events,
    events_to_json,
    heap_sort_events,
    insertion_sort_events,
    merge_sort_events,
    quick_sort_events,
    radix_sort_events,
    reconstruct_snapshots,
    selection_sort_events,
    serialize_events,
    shell_sort_events,
)

ALL_EVENT_GENERATORS = [spec.event_generator for spec in ALGORITHM_SPECS]
FLOAT_CAPABLE_GENERATORS = [
    spec.event_generator for spec in ALGORITHM_SPECS if not spec.integer_only
]


@pytest.mark.parametrize("event_generator", ALL_EVENT_GENERATORS)
@pytest.mark.parametrize(
    "values",
    [
        [],
        [1],
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [4, 4, 4, 4],
        [4, 2, 4, 1, 0, -3, 2],
        [-12, 5, 0, -3, 15, -12],
    ],
)
def test_all_event_streams_finish_sorted_without_mutating_input(
    event_generator, values
):
    original = list(values)
    events = list(event_generator(values))
    assert values == original
    assert events
    assert events[-1].type == SortEventType.COMPLETE
    assert events[-1].values == tuple(sorted(original))

    # Reconstructing the stream step-by-step must also end in sorted order.
    snapshots = list(reconstruct_snapshots(events))
    assert snapshots[-1][1] == tuple(sorted(original))


@pytest.mark.parametrize("event_generator", ALL_EVENT_GENERATORS)
def test_all_event_streams_randomized_integers(event_generator):
    random.seed(123)
    values = [random.randint(-150, 150) for _ in range(80)]
    events = list(event_generator(values))
    assert events[-1].type == SortEventType.COMPLETE
    assert events[-1].values == tuple(sorted(values))


@pytest.mark.parametrize("event_generator", FLOAT_CAPABLE_GENERATORS)
def test_float_capable_event_streams(event_generator):
    values = [0.42, -1.5, 0.32, 0.0, 0.52, -0.25, 0.42]
    events = list(event_generator(values))
    assert events[-1].type == SortEventType.COMPLETE
    assert events[-1].values == tuple(sorted(values))


def test_algorithm_specific_event_types():
    sample = [8, 3, 5, 1, 9, 2, 6, 4]

    bubble_types = {e.type for e in bubble_sort_events(sample)}
    assert {SortEventType.COMPARE, SortEventType.SWAP, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= bubble_types

    selection_types = {e.type for e in selection_sort_events(sample)}
    assert {SortEventType.COMPARE, SortEventType.SWAP, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= selection_types

    insertion_types = {e.type for e in insertion_sort_events(sample)}
    assert {SortEventType.COMPARE, SortEventType.WRITE, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= insertion_types

    merge_types = {e.type for e in merge_sort_events(sample)}
    assert {SortEventType.COMPARE, SortEventType.MERGE, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= merge_types

    quick_types = {e.type for e in quick_sort_events(sample)}
    assert {SortEventType.PIVOT, SortEventType.COMPARE, SortEventType.SWAP, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= quick_types

    heap_types = {e.type for e in heap_sort_events(sample)}
    assert {SortEventType.HEAPIFY, SortEventType.COMPARE, SortEventType.SWAP, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= heap_types

    shell_types = {e.type for e in shell_sort_events(sample)}
    assert {SortEventType.COMPARE, SortEventType.WRITE, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= shell_types

    counting_types = {e.type for e in counting_sort_events(sample)}
    assert {SortEventType.BUCKET_DISTRIBUTE, SortEventType.WRITE, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= counting_types

    radix_types = {e.type for e in radix_sort_events(sample)}
    assert {SortEventType.BUCKET_DISTRIBUTE, SortEventType.WRITE, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= radix_types

    bucket_types = {e.type for e in bucket_sort_events(sample)}
    assert {SortEventType.BUCKET_DISTRIBUTE, SortEventType.WRITE, SortEventType.COMPARE, SortEventType.MARK_SORTED, SortEventType.COMPLETE} <= bucket_types


@pytest.mark.parametrize("bad_values", [[1, 2.5, 3], [True, 1, 2]])
def test_integer_only_event_generators_reject_invalid_types(bad_values):
    with pytest.raises(TypeError):
        counting_sort_events(bad_values)
    with pytest.raises(TypeError):
        radix_sort_events(bad_values)


def test_bucket_sort_events_constraints():
    with pytest.raises(TypeError):
        bucket_sort_events([1, "2", 3])
    with pytest.raises(TypeError):
        bucket_sort_events([True, 1])
    with pytest.raises(ValueError):
        bucket_sort_events([1.0, float("nan"), 2.0])
    with pytest.raises(ValueError):
        bucket_sort_events([1.0, float("inf"), 2.0])
    with pytest.raises(ValueError):
        bucket_sort_events([1, 2, 3], bucket_count=0)


def test_large_array_snapshot_optimization_and_reconstruction():
    random.seed(99)
    values = [random.randint(-500, 500) for _ in range(300)]
    events = list(bubble_sort_events(values))

    full_snapshot_count = sum(1 for event in events if event.values)
    assert len(events) > 1000
    assert full_snapshot_count < len(events) // 10

    state = []
    for event, reconstructed in reconstruct_snapshots(events):
        state = apply_event(state, event)
        assert tuple(state) == reconstructed
        if event.values:
            assert event.values == reconstructed

    assert events[-1].values == tuple(sorted(values))
    assert tuple(state) == tuple(sorted(values))


def test_event_json_serialization_roundtrip():
    events = list(quick_sort_events([5, 1, 4, 2, 3]))
    payload = serialize_events(events)
    assert isinstance(payload, list)
    raw_json = events_to_json(events)
    decoded = json.loads(raw_json)
    restored = [SortEvent.from_dict(item) for item in decoded]
    assert restored == events
