"""Central registry for SortLab algorithms and their event generators."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass

from sortlab.algorithms import (
    bubble_sort,
    bucket_sort,
    counting_sort,
    heap_sort,
    insertion_sort,
    merge_sort,
    quick_sort,
    radix_sort,
    selection_sort,
    shell_sort,
)

from .events import SortEvent
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


@dataclass(frozen=True)
class AlgorithmSpec:
    """Metadata and callable entry points for one registered sorting algorithm."""

    choice: str
    key: str
    name: str
    category: str
    algorithm: Callable[[Iterable], list]
    event_generator: Callable[[Iterable], Iterator[SortEvent]]
    integer_only: bool = False


ALGORITHM_SPECS: tuple[AlgorithmSpec, ...] = (
    AlgorithmSpec(
        choice="1",
        key="bubble_sort",
        name="Bubble Sort",
        category="Comparison",
        algorithm=bubble_sort,
        event_generator=bubble_sort_events,
    ),
    AlgorithmSpec(
        choice="2",
        key="selection_sort",
        name="Selection Sort",
        category="Comparison",
        algorithm=selection_sort,
        event_generator=selection_sort_events,
    ),
    AlgorithmSpec(
        choice="3",
        key="insertion_sort",
        name="Insertion Sort",
        category="Comparison",
        algorithm=insertion_sort,
        event_generator=insertion_sort_events,
    ),
    AlgorithmSpec(
        choice="4",
        key="merge_sort",
        name="Merge Sort",
        category="Divide and conquer",
        algorithm=merge_sort,
        event_generator=merge_sort_events,
    ),
    AlgorithmSpec(
        choice="5",
        key="quick_sort",
        name="Quick Sort",
        category="Divide and conquer",
        algorithm=quick_sort,
        event_generator=quick_sort_events,
    ),
    AlgorithmSpec(
        choice="6",
        key="heap_sort",
        name="Heap Sort",
        category="Comparison",
        algorithm=heap_sort,
        event_generator=heap_sort_events,
    ),
    AlgorithmSpec(
        choice="7",
        key="shell_sort",
        name="Shell Sort",
        category="Comparison",
        algorithm=shell_sort,
        event_generator=shell_sort_events,
    ),
    AlgorithmSpec(
        choice="8",
        key="counting_sort",
        name="Counting Sort",
        category="Non-comparison",
        algorithm=counting_sort,
        event_generator=counting_sort_events,
        integer_only=True,
    ),
    AlgorithmSpec(
        choice="9",
        key="radix_sort",
        name="Radix Sort",
        category="Non-comparison",
        algorithm=radix_sort,
        event_generator=radix_sort_events,
        integer_only=True,
    ),
    AlgorithmSpec(
        choice="10",
        key="bucket_sort",
        name="Bucket Sort",
        category="Distribution-based",
        algorithm=bucket_sort,
        event_generator=bucket_sort_events,
    ),
)

ALGORITHM_REGISTRY: dict[str, AlgorithmSpec] = {
    spec.choice: spec for spec in ALGORITHM_SPECS
}

_BY_KEY: dict[str, AlgorithmSpec] = {spec.key: spec for spec in ALGORITHM_SPECS}
_BY_NAME: dict[str, AlgorithmSpec] = {
    spec.name.lower(): spec for spec in ALGORITHM_SPECS
}


def get_algorithm_spec(identifier: str) -> AlgorithmSpec:
    """Look up an :class:`AlgorithmSpec` by menu number, key, or display name."""
    cleaned = identifier.strip()
    if cleaned in ALGORITHM_REGISTRY:
        return ALGORITHM_REGISTRY[cleaned]
    lowered = cleaned.lower()
    if lowered in _BY_KEY:
        return _BY_KEY[lowered]
    if lowered in _BY_NAME:
        return _BY_NAME[lowered]
    raise ValueError(f"Unknown algorithm selection: {identifier!r}")


def validate_inputs_for_spec(spec: AlgorithmSpec, values: list[float]) -> None:
    """Validate input values against the selected algorithm's constraints."""
    if spec.integer_only and any(
        isinstance(value, bool) or not isinstance(value, int) for value in values
    ):
        raise ValueError(
            f"{spec.name} accepts integers only. Please enter whole numbers."
        )
