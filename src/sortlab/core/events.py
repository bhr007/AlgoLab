"""Shared, renderer-independent events used by visualizations."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SortEventType(str, Enum):
    """Canonical operations emitted by AlgoLab sorting event streams."""

    COMPARE = "compare"
    SWAP = "swap"
    WRITE = "write"
    PIVOT = "pivot"
    MERGE = "merge"
    HEAPIFY = "heapify"
    BUCKET_DISTRIBUTE = "bucket_distribute"
    MARK_SORTED = "mark_sorted"
    COMPLETE = "complete"


@dataclass(frozen=True)
class SortEvent:
    """A single observable operation in a sorting algorithm.

    For small arrays, ``values`` can hold a full tuple snapshot. For larger arrays,
    non-mutating events omit ``values`` and mutating events populate ``changes``
    with ``(index, new_value)`` pairs while periodic full snapshots are retained.
    """

    type: SortEventType
    indices: tuple[int, ...] = ()
    values: tuple[object, ...] = ()
    message: str | None = None
    changes: tuple[tuple[int, object], ...] = ()
    metadata: dict[str, object] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize this event into a JSON-compatible dictionary."""
        return {
            "type": self.type.value,
            "indices": list(self.indices),
            "values": list(self.values),
            "changes": [[index, value] for index, value in self.changes],
            "message": self.message,
            "metadata": dict(self.metadata) if self.metadata is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> SortEvent:
        """Deserialize a dictionary produced by :meth:`to_dict`."""
        raw_metadata = payload.get("metadata")
        return cls(
            type=SortEventType(payload["type"]),
            indices=tuple(int(index) for index in payload.get("indices", ())),
            values=tuple(payload.get("values", ())),
            message=payload.get("message"),
            changes=tuple(
                (int(pair[0]), pair[1]) for pair in payload.get("changes", ())
            ),
            metadata=dict(raw_metadata) if raw_metadata is not None else None,
        )


class SnapshotTracker:
    """Emit memory-efficient snapshots and delta changes for event streams."""

    def __init__(self, items: list[object], snapshot_interval: int | None = None):
        self._items = items
        if snapshot_interval is not None:
            if snapshot_interval < 1:
                raise ValueError("snapshot_interval must be at least 1")
            self._snapshot_interval = snapshot_interval
        elif len(items) <= 32:
            self._snapshot_interval = 1
        else:
            # Keep total full-snapshot memory O(n) even on O(n^2) event streams.
            self._snapshot_interval = len(items)

        self._sent_initial = False
        self._mutations_since_snapshot = 0

    def emit(
        self,
        event_type: SortEventType,
        indices: tuple[int, ...] = (),
        message: str | None = None,
        *,
        changes: tuple[tuple[int, object], ...] = (),
        metadata: dict[str, object] | None = None,
        mutated: bool = False,
        force_snapshot: bool = False,
    ) -> SortEvent:
        """Build a :class:`SortEvent` with optimized full/delta snapshots."""
        snapshot: tuple[object, ...] = ()
        if force_snapshot or not self._sent_initial:
            snapshot = tuple(self._items)
            self._sent_initial = True
            self._mutations_since_snapshot = 0
        elif mutated:
            self._mutations_since_snapshot += 1
            if self._mutations_since_snapshot >= self._snapshot_interval:
                snapshot = tuple(self._items)
                self._mutations_since_snapshot = 0

        return SortEvent(
            type=event_type,
            indices=indices,
            values=snapshot,
            message=message,
            changes=changes,
            metadata=metadata,
        )

    def complete(self, message: str = "Sorting complete") -> SortEvent:
        """Build the terminal :attr:`SortEventType.COMPLETE` event with full state."""
        return self.emit(
            SortEventType.COMPLETE,
            (),
            message,
            force_snapshot=True,
        )


def apply_event(state: list[object], event: SortEvent) -> list[object]:
    """Return a new list representing ``state`` updated with ``event``."""
    if event.values:
        return list(event.values)
    next_state = list(state)
    for index, value in event.changes:
        next_state[index] = value
    return next_state


def reconstruct_snapshots(
    events: Iterable[SortEvent],
) -> Iterator[tuple[SortEvent, tuple[object, ...]]]:
    """Yield ``(event, full_snapshot_tuple)`` for every event in a stream."""
    state: list[object] | None = None
    for event in events:
        if event.values:
            state = list(event.values)
        elif state is None:
            state = []
        else:
            for index, value in event.changes:
                state[index] = value
        yield event, tuple(state)


def serialize_events(events: Iterable[SortEvent]) -> list[dict[str, Any]]:
    """Convert an event stream into a list of JSON-serializable dictionaries."""
    return [event.to_dict() for event in events]


def events_to_json(events: Iterable[SortEvent], **json_kwargs: Any) -> str:
    """Serialize an event stream directly to a JSON string."""
    return json.dumps(serialize_events(events), **json_kwargs)
