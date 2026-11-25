"""Event-producing algorithm examples."""

from typing import Iterable, Iterator, List

from .events import SortEvent, SortEventType


def bubble_sort_events(values: Iterable):
    """Yield Bubble Sort events and snapshots without mutating the input.

    Each event's values field contains an immutable snapshot of the current list.
    """
    items: List = list(values)
    for end in range(len(items) - 1, 0, -1):
        swapped = False
        for index in range(end):
            yield SortEvent(
                SortEventType.COMPARE,
                (index, index + 1),
                tuple(items),
                "Compare adjacent elements",
            )
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]
                swapped = True
                yield SortEvent(
                    SortEventType.SWAP,
                    (index, index + 1),
                    tuple(items),
                    "Swap the elements",
                )
        yield SortEvent(
            SortEventType.MARK_SORTED,
            (end,),
            tuple(items),
            "The rightmost unsorted element is in its final position",
        )
        if not swapped:
            break

    if items:
        yield SortEvent(
            SortEventType.MARK_SORTED,
            (0,),
            tuple(items),
            "The remaining element is sorted",
        )
    yield SortEvent(SortEventType.COMPLETE, (), tuple(items), "Sorting complete")
