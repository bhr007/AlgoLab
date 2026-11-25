"""Shared, renderer-independent events used by visualizations."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class SortEventType(str, Enum):
    COMPARE = "compare"
    SWAP = "swap"
    WRITE = "write"
    MARK_SORTED = "mark_sorted"
    COMPLETE = "complete"


@dataclass(frozen=True)
class SortEvent:
    """A single observable operation in a sorting algorithm."""

    type: SortEventType
    indices: Tuple[int, ...] = ()
    values: Tuple[object, ...] = ()
    message: Optional[str] = None
