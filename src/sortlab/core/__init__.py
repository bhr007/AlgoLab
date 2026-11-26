"""Core event engine and algorithm registry for AlgoLab."""

from .events import (
    SnapshotTracker,
    SortEvent,
    SortEventType,
    apply_event,
    events_to_json,
    reconstruct_snapshots,
    serialize_events,
)
from .registry import (
    ALGORITHM_REGISTRY,
    ALGORITHM_SPECS,
    AlgorithmSpec,
    get_algorithm_spec,
    validate_inputs_for_spec,
)
from .runner import (
    bubble_sort_events,
    bucket_sort_events,
    counting_sort_events,
    heap_sort_events,
    insertion_sort_events,
    merge_sort_events,
    quick_sort_events,
    radix_sort_events,
    selection_sort_events,
    shell_sort_events,
)

__all__ = [
    "ALGORITHM_REGISTRY",
    "ALGORITHM_SPECS",
    "AlgorithmSpec",
    "SnapshotTracker",
    "SortEvent",
    "SortEventType",
    "apply_event",
    "bubble_sort_events",
    "bucket_sort_events",
    "counting_sort_events",
    "events_to_json",
    "get_algorithm_spec",
    "heap_sort_events",
    "insertion_sort_events",
    "merge_sort_events",
    "quick_sort_events",
    "radix_sort_events",
    "reconstruct_snapshots",
    "selection_sort_events",
    "serialize_events",
    "shell_sort_events",
    "validate_inputs_for_spec",
]
