"""Event-producing wrappers for all SortLab sorting algorithms."""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator

from .events import SnapshotTracker, SortEvent, SortEventType


def _validate_integers(values: Iterable, algorithm_name: str) -> list[int]:
    """Materialize ``values`` and ensure every item is a non-boolean integer."""
    items = list(values)
    if any(isinstance(value, bool) or not isinstance(value, int) for value in items):
        raise TypeError(f"{algorithm_name} supports integers only")
    return items


def _validate_finite_numbers(values: Iterable, algorithm_name: str) -> list[float]:
    """Materialize ``values`` and ensure every item is a finite int or float."""
    items = list(values)
    for value in items:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{algorithm_name} supports int and float values only")
        if not math.isfinite(value):
            raise ValueError(f"{algorithm_name} supports finite numbers only")
    return items


def bubble_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Bubble Sort events and snapshots without mutating the input."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    for end in range(len(items) - 1, 0, -1):
        swapped = False
        for index in range(end):
            yield tracker.emit(
                SortEventType.COMPARE,
                (index, index + 1),
                f"Compare indices {index} and {index + 1}",
            )
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]
                swapped = True
                yield tracker.emit(
                    SortEventType.SWAP,
                    (index, index + 1),
                    f"Swap indices {index} and {index + 1}",
                    changes=((index, items[index]), (index + 1, items[index + 1])),
                    mutated=True,
                )
        yield tracker.emit(
            SortEventType.MARK_SORTED,
            (end,),
            f"Index {end} is in final sorted position",
        )
        if not swapped:
            remaining = tuple(range(end))
            if remaining:
                yield tracker.emit(
                    SortEventType.MARK_SORTED,
                    remaining,
                    "No swaps in pass; remaining prefix is sorted",
                )
            yield tracker.complete()
            return

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        (0,),
        "Remaining element at index 0 is sorted",
    )
    yield tracker.complete()


def selection_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Selection Sort events without mutating the input."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    for start in range(len(items)):
        smallest = start
        for index in range(start + 1, len(items)):
            yield tracker.emit(
                SortEventType.COMPARE,
                (smallest, index),
                f"Compare candidate minimum {smallest} with index {index}",
            )
            if items[index] < items[smallest]:
                smallest = index
        if smallest != start:
            items[start], items[smallest] = items[smallest], items[start]
            yield tracker.emit(
                SortEventType.SWAP,
                (start, smallest),
                f"Swap minimum from index {smallest} into index {start}",
                changes=((start, items[start]), (smallest, items[smallest])),
                mutated=True,
            )
        yield tracker.emit(
            SortEventType.MARK_SORTED,
            (start,),
            f"Index {start} is in final sorted position",
        )

    yield tracker.complete()


def insertion_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Insertion Sort events without mutating the input."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if not items:
        yield tracker.complete()
        return

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        (0,),
        "Initial single-element sorted prefix",
    )

    for index in range(1, len(items)):
        current = items[index]
        position = index
        while position > 0:
            yield tracker.emit(
                SortEventType.COMPARE,
                (position - 1, position),
                f"Compare index {position - 1} with key {current}",
            )
            if items[position - 1] > current:
                items[position] = items[position - 1]
                yield tracker.emit(
                    SortEventType.WRITE,
                    (position,),
                    f"Shift element from index {position - 1} to {position}",
                    changes=((position, items[position]),),
                    mutated=True,
                )
                position -= 1
            else:
                break

        items[position] = current
        if position != index:
            yield tracker.emit(
                SortEventType.WRITE,
                (position,),
                f"Insert {current} at index {position}",
                changes=((position, current),),
                mutated=True,
            )

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        tuple(range(len(items))),
        "All elements inserted in sorted order",
    )
    yield tracker.complete()


def merge_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Merge Sort events without mutating the input."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    def _merge_sort(lo: int, hi: int) -> Iterator[SortEvent]:
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        yield from _merge_sort(lo, mid)
        yield from _merge_sort(mid, hi)

        left_part = items[lo:mid]
        right_part = items[mid:hi]
        left_idx = 0
        right_idx = 0
        write_idx = lo
        span_meta: dict[str, object] = {"range": [lo, hi], "mid": mid}

        while left_idx < len(left_part) and right_idx < len(right_part):
            yield tracker.emit(
                SortEventType.COMPARE,
                (lo + left_idx, mid + right_idx),
                f"Compare left ({left_part[left_idx]}) and right ({right_part[right_idx]})",
                metadata=span_meta,
            )
            if left_part[left_idx] <= right_part[right_idx]:
                chosen = left_part[left_idx]
                left_idx += 1
            else:
                chosen = right_part[right_idx]
                right_idx += 1
            items[write_idx] = chosen
            yield tracker.emit(
                SortEventType.MERGE,
                (write_idx,),
                f"Merge {chosen} into index {write_idx} (range [{lo}, {hi}))",
                changes=((write_idx, chosen),),
                metadata=span_meta,
                mutated=True,
            )
            write_idx += 1

        while left_idx < len(left_part):
            chosen = left_part[left_idx]
            items[write_idx] = chosen
            yield tracker.emit(
                SortEventType.MERGE,
                (write_idx,),
                f"Merge remaining left {chosen} into index {write_idx}",
                changes=((write_idx, chosen),),
                metadata=span_meta,
                mutated=True,
            )
            left_idx += 1
            write_idx += 1

        while right_idx < len(right_part):
            chosen = right_part[right_idx]
            items[write_idx] = chosen
            yield tracker.emit(
                SortEventType.MERGE,
                (write_idx,),
                f"Merge remaining right {chosen} into index {write_idx}",
                changes=((write_idx, chosen),),
                metadata=span_meta,
                mutated=True,
            )
            right_idx += 1
            write_idx += 1

    yield from _merge_sort(0, len(items))
    yield tracker.emit(
        SortEventType.MARK_SORTED,
        tuple(range(len(items))),
        "Full range merged and sorted",
    )
    yield tracker.complete()


def quick_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Quick Sort events (3-way partition with middle pivot)."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    def _quick_sort(lo: int, hi: int) -> Iterator[SortEvent]:
        if hi - lo <= 0:
            return
        if hi - lo == 1:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (lo,),
                f"Single-element partition at index {lo} is sorted",
            )
            return

        pivot_idx = (lo + hi) // 2
        pivot = items[pivot_idx]
        yield tracker.emit(
            SortEventType.PIVOT,
            (pivot_idx,),
            f"Select pivot {pivot} at index {pivot_idx} for [{lo}, {hi})",
            metadata={"range": [lo, hi], "pivot": pivot},
        )

        lt = lo
        index = lo
        gt = hi - 1

        def _track_pivot_after_swap(a: int, b: int) -> None:
            nonlocal pivot_idx
            if pivot_idx == a:
                pivot_idx = b
            elif pivot_idx == b:
                pivot_idx = a

        while index <= gt:
            yield tracker.emit(
                SortEventType.COMPARE,
                (index, pivot_idx),
                f"Compare index {index} ({items[index]}) with pivot {pivot}",
                metadata={"pivot_index": pivot_idx},
            )
            if items[index] < pivot:
                if index != lt:
                    items[lt], items[index] = items[index], items[lt]
                    _track_pivot_after_swap(lt, index)
                    yield tracker.emit(
                        SortEventType.SWAP,
                        (lt, index),
                        f"Move smaller element to index {lt}",
                        changes=((lt, items[lt]), (index, items[index])),
                        mutated=True,
                    )
                lt += 1
                index += 1
            elif items[index] > pivot:
                if index != gt:
                    items[index], items[gt] = items[gt], items[index]
                    _track_pivot_after_swap(index, gt)
                    yield tracker.emit(
                        SortEventType.SWAP,
                        (index, gt),
                        f"Move larger element to index {gt}",
                        changes=((index, items[index]), (gt, items[gt])),
                        mutated=True,
                    )
                gt -= 1
            else:
                index += 1

        yield tracker.emit(
            SortEventType.MARK_SORTED,
            tuple(range(lt, gt + 1)),
            f"Pivot partition [{lt}, {gt + 1}) is in final sorted position",
        )
        yield from _quick_sort(lo, lt)
        yield from _quick_sort(gt + 1, hi)

    yield from _quick_sort(0, len(items))
    yield tracker.complete()


def heap_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Heap Sort events without mutating the input."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)
    size = len(items)

    if size <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    def _sift_down(root: int, end: int) -> Iterator[SortEvent]:
        while True:
            child = 2 * root + 1
            if child >= end:
                return
            yield tracker.emit(
                SortEventType.HEAPIFY,
                (root, child),
                f"Heapify node {root} within heap size {end}",
                metadata={"heap_end": end},
            )
            if child + 1 < end:
                yield tracker.emit(
                    SortEventType.COMPARE,
                    (child, child + 1),
                    f"Compare heap children {child} and {child + 1}",
                )
                if items[child] < items[child + 1]:
                    child += 1
            yield tracker.emit(
                SortEventType.COMPARE,
                (root, child),
                f"Compare heap parent {root} with child {child}",
            )
            if items[root] >= items[child]:
                return
            items[root], items[child] = items[child], items[root]
            yield tracker.emit(
                SortEventType.SWAP,
                (root, child),
                f"Sift down: swap indices {root} and {child}",
                changes=((root, items[root]), (child, items[child])),
                mutated=True,
            )
            root = child

    for root in range(size // 2 - 1, -1, -1):
        yield from _sift_down(root, size)

    for end in range(size - 1, 0, -1):
        items[0], items[end] = items[end], items[0]
        yield tracker.emit(
            SortEventType.SWAP,
            (0, end),
            f"Extract heap max from index 0 to sorted index {end}",
            changes=((0, items[0]), (end, items[end])),
            mutated=True,
        )
        yield tracker.emit(
            SortEventType.MARK_SORTED,
            (end,),
            f"Index {end} is in final sorted position",
        )
        yield from _sift_down(0, end)

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        (0,),
        "Remaining root at index 0 is sorted",
    )
    yield tracker.complete()


def shell_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Shell Sort events with halving gaps without mutating the input."""
    items: list[object] = list(values)
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    gap = len(items) // 2
    while gap > 0:
        for index in range(gap, len(items)):
            current = items[index]
            position = index
            while position >= gap:
                yield tracker.emit(
                    SortEventType.COMPARE,
                    (position - gap, position),
                    f"Gap {gap}: compare indices {position - gap} and {position}",
                    metadata={"gap": gap},
                )
                if items[position - gap] > current:
                    items[position] = items[position - gap]
                    yield tracker.emit(
                        SortEventType.WRITE,
                        (position,),
                        f"Gap {gap}: shift element to index {position}",
                        changes=((position, items[position]),),
                        metadata={"gap": gap},
                        mutated=True,
                    )
                    position -= gap
                else:
                    break

            items[position] = current
            if position != index:
                yield tracker.emit(
                    SortEventType.WRITE,
                    (position,),
                    f"Gap {gap}: place {current} at index {position}",
                    changes=((position, current),),
                    metadata={"gap": gap},
                    mutated=True,
                )
        gap //= 2

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        tuple(range(len(items))),
        "All gapped insertion passes complete",
    )
    yield tracker.complete()


def counting_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield Counting Sort events for integers (including negatives)."""
    items = _validate_integers(values, "counting_sort")
    return _counting_sort_events_stream(items, snapshot_interval)


def _counting_sort_events_stream(
    items: list[int], snapshot_interval: int | None
) -> Iterator[SortEvent]:
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    minimum, maximum = min(items), max(items)
    counts = [0] * (maximum - minimum + 1)

    for index, value in enumerate(items):
        bucket = value - minimum
        counts[bucket] += 1
        yield tracker.emit(
            SortEventType.BUCKET_DISTRIBUTE,
            (index,),
            f"Count value {value} into bucket {bucket} (count={counts[bucket]})",
            metadata={"bucket": bucket, "value": value, "count": counts[bucket]},
        )

    write_idx = 0
    for offset, count in enumerate(counts):
        value = offset + minimum
        for _ in range(count):
            items[write_idx] = value
            yield tracker.emit(
                SortEventType.WRITE,
                (write_idx,),
                f"Write {value} from count bucket {offset} to index {write_idx}",
                changes=((write_idx, value),),
                metadata={"bucket": offset},
                mutated=True,
            )
            write_idx += 1

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        tuple(range(len(items))),
        "All counted values written in sorted order",
    )
    yield tracker.complete()


def radix_sort_events(
    values: Iterable, snapshot_interval: int | None = None
) -> Iterator[SortEvent]:
    """Yield LSD Radix Sort events for integers (including negatives)."""
    items = _validate_integers(values, "radix_sort")
    return _radix_sort_events_stream(items, snapshot_interval)


def _radix_sort_events_stream(
    items: list[int], snapshot_interval: int | None
) -> Iterator[SortEvent]:
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    maximum = max(abs(value) for value in items)
    exp = 1
    while maximum // exp > 0:
        # 19 signed-digit buckets (-9..+9) preserve stability across negative and
        # non-negative integers in a single unified pass per digit position.
        buckets: list[list[int]] = [[] for _ in range(19)]
        for index, value in enumerate(items):
            digit = -((-value // exp) % 10) if value < 0 else (value // exp) % 10
            buckets[digit + 9].append(value)
            yield tracker.emit(
                SortEventType.BUCKET_DISTRIBUTE,
                (index,),
                f"Place {value} into digit-{digit} bucket (exp={exp})",
                metadata={"bucket": digit, "exp": exp, "digit": digit},
            )

        write_idx = 0
        for bucket in buckets:
            for value in bucket:
                items[write_idx] = value
                yield tracker.emit(
                    SortEventType.WRITE,
                    (write_idx,),
                    f"Gather {value} into index {write_idx} (exp={exp})",
                    changes=((write_idx, value),),
                    metadata={"exp": exp},
                    mutated=True,
                )
                write_idx += 1
        exp *= 10

    yield tracker.emit(
        SortEventType.MARK_SORTED,
        tuple(range(len(items))),
        "All radix digit passes complete",
    )
    yield tracker.complete()


def bucket_sort_events(
    values: Iterable,
    bucket_count: int | None = None,
    snapshot_interval: int | None = None,
) -> Iterator[SortEvent]:
    """Yield Bucket Sort events for finite numbers without mutating the input."""
    items = _validate_finite_numbers(values, "bucket_sort")
    if bucket_count is not None and bucket_count <= 0:
        raise ValueError("bucket_count must be positive")
    return _bucket_sort_events_stream(items, bucket_count, snapshot_interval)


def _bucket_sort_events_stream(
    items: list[float],
    bucket_count: int | None,
    snapshot_interval: int | None,
) -> Iterator[SortEvent]:
    tracker = SnapshotTracker(items, snapshot_interval=snapshot_interval)

    if len(items) <= 1:
        if items:
            yield tracker.emit(
                SortEventType.MARK_SORTED,
                (0,),
                "Single element is already sorted",
            )
        yield tracker.complete()
        return

    minimum, maximum = min(items), max(items)
    if minimum == maximum:
        yield tracker.emit(
            SortEventType.MARK_SORTED,
            tuple(range(len(items))),
            "All elements are equal",
        )
        yield tracker.complete()
        return

    count = len(items) if bucket_count is None else bucket_count
    buckets: list[list[float]] = [[] for _ in range(count)]
    span = maximum - minimum

    for index, value in enumerate(items):
        b_idx = int((value - minimum) / span * (count - 1))
        buckets[b_idx].append(value)
        yield tracker.emit(
            SortEventType.BUCKET_DISTRIBUTE,
            (index,),
            f"Distribute {value} into bucket {b_idx}",
            metadata={"bucket": b_idx, "bucket_count": count},
        )

    bucket_ranges: list[tuple[int, int]] = []
    write_idx = 0
    for b_idx, bucket in enumerate(buckets):
        if not bucket:
            continue
        start = write_idx
        for value in bucket:
            items[write_idx] = value
            yield tracker.emit(
                SortEventType.WRITE,
                (write_idx,),
                f"Write bucket {b_idx} value {value} to index {write_idx}",
                changes=((write_idx, value),),
                metadata={"bucket": b_idx},
                mutated=True,
            )
            write_idx += 1
        bucket_ranges.append((start, write_idx))

    for start, end in bucket_ranges:
        for index in range(start + 1, end):
            current = items[index]
            position = index
            while position > start:
                yield tracker.emit(
                    SortEventType.COMPARE,
                    (position - 1, position),
                    f"Sort within bucket [{start}, {end}): compare {position - 1} and {position}",
                )
                if items[position - 1] > current:
                    items[position] = items[position - 1]
                    yield tracker.emit(
                        SortEventType.WRITE,
                        (position,),
                        f"Shift element within bucket to index {position}",
                        changes=((position, items[position]),),
                        mutated=True,
                    )
                    position -= 1
                else:
                    break
            items[position] = current
            if position != index:
                yield tracker.emit(
                    SortEventType.WRITE,
                    (position,),
                    f"Insert {current} at bucket position {position}",
                    changes=((position, current),),
                    mutated=True,
                )

        yield tracker.emit(
            SortEventType.MARK_SORTED,
            tuple(range(start, end)),
            f"Bucket range [{start}, {end}) is sorted",
        )

    yield tracker.complete()
