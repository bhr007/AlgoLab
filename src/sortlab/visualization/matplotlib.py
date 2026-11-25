"""Shared Matplotlib renderer for SortLab event streams."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from sortlab.core.events import SortEvent, SortEventType

STATE_COLORS: dict[str, str] = {
    "unsorted": "#4C78A8",
    SortEventType.COMPARE.value: "#F58518",
    SortEventType.SWAP.value: "#E45756",
    SortEventType.WRITE.value: "#B279A2",
    SortEventType.PIVOT.value: "#EECA3B",
    SortEventType.MERGE.value: "#54A24B",
    SortEventType.HEAPIFY.value: "#72B7B2",
    SortEventType.BUCKET_DISTRIBUTE.value: "#FF9DA6",
    SortEventType.MARK_SORTED.value: "#2E8B57",
    SortEventType.COMPLETE.value: "#2E8B57",
}

STATE_LABELS: dict[str, str] = {
    "unsorted": "Unsorted",
    SortEventType.COMPARE.value: "Compare",
    SortEventType.SWAP.value: "Swap",
    SortEventType.WRITE.value: "Write",
    SortEventType.PIVOT.value: "Pivot",
    SortEventType.MERGE.value: "Merge",
    SortEventType.HEAPIFY.value: "Heapify",
    SortEventType.BUCKET_DISTRIBUTE.value: "Bucket",
    SortEventType.MARK_SORTED.value: "Sorted",
}


@dataclass(frozen=True)
class EventCounters:
    """Cumulative operation counters for a rendered animation frame."""

    comparisons: int = 0
    swaps: int = 0
    writes: int = 0
    merges: int = 0
    pivots: int = 0
    heap_ops: int = 0
    bucket_ops: int = 0


def _format_value(value: object) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) < 1_000_000_000:
            return str(value)
        return f"{value:.3e}"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _compute_default_interval(frame_count: int) -> int:
    """Choose a responsive playback interval in milliseconds for ``frame_count``."""
    return max(15, min(450, 10_000 // max(1, frame_count)))


def _build_counter_timeline(events: list[SortEvent]) -> list[EventCounters]:
    """Precompute cumulative operation counters for every event."""
    counters: list[EventCounters] = []
    comp = swap = write = merge = pivot = heap = bucket = 0
    for event in events:
        etype = event.type
        if etype == SortEventType.COMPARE:
            comp += 1
        elif etype == SortEventType.SWAP:
            swap += 1
        elif etype == SortEventType.WRITE:
            write += 1
        elif etype == SortEventType.MERGE:
            merge += 1
            write += 1
        elif etype == SortEventType.PIVOT:
            pivot += 1
        elif etype == SortEventType.HEAPIFY:
            heap += 1
        elif etype == SortEventType.BUCKET_DISTRIBUTE:
            bucket += 1
        counters.append(
            EventCounters(
                comparisons=comp,
                swaps=swap,
                writes=write,
                merges=merge,
                pivots=pivot,
                heap_ops=heap,
                bucket_ops=bucket,
            )
        )
    return counters


def _select_rendered_indices(total: int, max_frames: int | None) -> list[int]:
    """Select evenly spaced event indices, always keeping the first and last."""
    if max_frames is None or total <= max_frames or max_frames < 2:
        return list(range(total))
    step = (total - 1) / (max_frames - 1)
    indices = [round(i * step) for i in range(max_frames - 1)]
    indices.append(total - 1)
    # Deduplicate while preserving order.
    deduped: list[int] = []
    for idx in indices:
        if not deduped or deduped[-1] != idx:
            deduped.append(idx)
    return deduped


def _format_counter_line(counter: EventCounters, step: int, total_steps: int) -> str:
    parts = [
        f"Step: {step}/{total_steps}",
        f"Comparisons: {counter.comparisons}",
        f"Swaps: {counter.swaps}",
        f"Writes: {counter.writes}",
    ]
    if counter.merges:
        parts.append(f"Merges: {counter.merges}")
    if counter.pivots:
        parts.append(f"Pivots: {counter.pivots}")
    if counter.heap_ops:
        parts.append(f"Heap ops: {counter.heap_ops}")
    if counter.bucket_ops:
        parts.append(f"Buckets: {counter.bucket_ops}")
    return "   |   ".join(parts)


class SortAnimationController:
    """Interactive controller managing Matplotlib bars, counters, and controls."""

    def __init__(
        self,
        fig,
        ax,
        events: list[SortEvent],
        algorithm_name: str,
        interval: int,
        max_frames: int | None = None,
    ) -> None:
        from matplotlib.animation import FuncAnimation
        from matplotlib.patches import Patch
        from matplotlib.widgets import Button, Slider

        self.fig = fig
        self.ax = ax
        self.events = events
        self.algorithm_name = algorithm_name
        self.interval = interval
        self.counters = _build_counter_timeline(events)
        self.rendered_map = _select_rendered_indices(len(events), max_frames)
        self.total_rendered = len(self.rendered_map)

        initial_snapshot = next((e.values for e in events if e.values), ())
        self.array_len = len(initial_snapshot)
        self.initial_values = list(initial_snapshot)

        # Build sparse state checkpoints across the full event stream for O(1)
        # forward stepping and fast seek/reset.
        checkpoint_stride = max(1, len(events) // 50)
        self._checkpoints: dict[int, tuple[list[object], set[int]]] = {}
        sim_values = list(initial_snapshot)
        sim_sorted: set[int] = set()
        for idx, event in enumerate(events):
            if idx % checkpoint_stride == 0:
                self._checkpoints[idx] = (list(sim_values), set(sim_sorted))
            if event.values:
                sim_values = list(event.values)
            elif event.changes:
                for pos, val in event.changes:
                    sim_values[pos] = val
            if event.type == SortEventType.MARK_SORTED:
                sim_sorted.update(event.indices)
            elif event.type == SortEventType.COMPLETE:
                sim_sorted = set(range(len(sim_values)))
        self._checkpoint_stride = checkpoint_stride

        # Determine global y-axis limits across all snapshots and changes.
        min_val = 0.0
        max_val = 1.0
        if sim_values or initial_snapshot:
            seen_values: list[float] = [float(v) for v in initial_snapshot]
            for event in events:
                if event.values:
                    seen_values.extend(float(v) for v in event.values)
                for _, val in event.changes:
                    seen_values.append(float(val))
            low = min(seen_values)
            high = max(seen_values)
            span = high - low
            pad = max(1.0, span * 0.14) if span == 0 else span * 0.14
            min_val = min(0.0, low - pad)
            max_val = max(0.0, high + pad)
            if min_val == max_val:
                min_val, max_val = -1.0, 1.0

        self.y_min = min_val
        self.y_max = max_val
        self.label_offset = (max_val - min_val) * 0.02

        self.fig.subplots_adjust(top=0.77, bottom=0.19, left=0.08, right=0.96)
        self.bars = list(
            self.ax.bar(
                range(self.array_len),
                self.initial_values,
                color=STATE_COLORS["unsorted"],
                edgecolor="#263238",
                linewidth=0.6 if self.array_len <= 60 else 0.0,
            )
        )
        self.ax.axhline(0, color="#666666", linewidth=0.8)
        self.ax.set_ylim(self.y_min, self.y_max)
        if self.array_len > 0:
            self.ax.set_xlim(-0.6, self.array_len - 0.4)
        self.ax.set_xlabel("Index")
        self.ax.set_ylabel("Value")
        self.ax.grid(axis="y", linestyle="--", alpha=0.25)

        if self.array_len == 0:
            self.ax.text(
                0.5,
                0.5,
                "Empty input — nothing to sort",
                transform=self.ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
                color="#555555",
            )

        self.value_texts = []
        if 0 < self.array_len <= 30:
            for index, val in enumerate(self.initial_values):
                y_pos = float(val) + self.label_offset if val >= 0 else float(val) - self.label_offset
                va = "bottom" if val >= 0 else "top"
                text = self.ax.text(
                    index,
                    y_pos,
                    _format_value(val),
                    ha="center",
                    va=va,
                    fontsize=8,
                    color="#222222",
                )
                self.value_texts.append(text)

        # Header HUD: algorithm name, current operation, and live counters.
        self.title_text = self.fig.text(
            0.5,
            0.945,
            f"SortLab — {self.algorithm_name}",
            ha="center",
            va="top",
            fontsize=14,
            fontweight="bold",
        )
        self.operation_text = self.fig.text(
            0.5,
            0.895,
            "",
            ha="center",
            va="top",
            fontsize=10.5,
            color="#333333",
        )
        self.counter_text = self.fig.text(
            0.5,
            0.85,
            "",
            ha="center",
            va="top",
            fontsize=9.5,
            color="#1F2933",
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "#F3F4F6", "edgecolor": "#D1D5DB"},
        )

        # Build compact legend containing states present in this event stream.
        present_types = {event.type for event in events}
        legend_items = [Patch(facecolor=STATE_COLORS["unsorted"], label=STATE_LABELS["unsorted"])]
        for etype in (
            SortEventType.COMPARE,
            SortEventType.SWAP,
            SortEventType.WRITE,
            SortEventType.PIVOT,
            SortEventType.MERGE,
            SortEventType.HEAPIFY,
            SortEventType.BUCKET_DISTRIBUTE,
        ):
            if etype in present_types:
                legend_items.append(
                    Patch(facecolor=STATE_COLORS[etype.value], label=STATE_LABELS[etype.value])
                )
        legend_items.append(
            Patch(
                facecolor=STATE_COLORS[SortEventType.MARK_SORTED.value],
                label=STATE_LABELS[SortEventType.MARK_SORTED.value],
            )
        )
        self.ax.legend(
            handles=legend_items,
            loc="upper center",
            bbox_to_anchor=(0.5, 1.11),
            ncol=min(len(legend_items), 6),
            frameon=False,
            fontsize=8.5,
        )

        # Interactive playback controls.
        ax_play = self.fig.add_axes([0.10, 0.04, 0.13, 0.055])
        ax_step = self.fig.add_axes([0.25, 0.04, 0.10, 0.055])
        ax_reset = self.fig.add_axes([0.37, 0.04, 0.10, 0.055])
        ax_speed = self.fig.add_axes([0.57, 0.048, 0.31, 0.04])

        self.btn_play = Button(ax_play, "Pause")
        self.btn_step = Button(ax_step, "Step")
        self.btn_reset = Button(ax_reset, "Reset")
        self.slider_speed = Slider(
            ax_speed,
            "Delay (ms)",
            10,
            1000,
            valinit=max(10, min(1000, interval)),
            valstep=10,
        )

        self.btn_play.on_clicked(self.toggle_play)
        self.btn_step.on_clicked(self.step_once)
        self.btn_reset.on_clicked(self.reset)
        self.slider_speed.on_changed(self._on_speed_change)

        self.is_paused = False
        self.current_render_idx = -1
        self._current_event_idx = -1
        self._state_values: list[object] = list(self.initial_values)
        self._sorted_indices: set[int] = set()
        self._prev_highlighted: set[int] = set()

        self.render_frame(0)

        self.animation = FuncAnimation(
            self.fig,
            self._tick,
            init_func=self._init_frame,
            frames=self._frame_iterator,
            interval=self.interval,
            blit=False,
            cache_frame_data=False,
            repeat=False,
        )
        self.fig._sortlab_controller = self

    def _init_frame(self):
        return self.render_frame(0)

    def _frame_iterator(self):
        idx = 1
        while idx < self.total_rendered:
            yield idx
            idx = self.current_render_idx + 1

    def _tick(self, _frame: int):
        if self.is_paused:
            return tuple(self.bars)
        next_idx = self.current_render_idx + 1
        if next_idx >= self.total_rendered:
            self.is_paused = True
            self.btn_play.label.set_text("Play")
            if self.animation.event_source is not None:
                self.animation.event_source.stop()
            return tuple(self.bars)
        return self.render_frame(next_idx)

    def _seek_to_event(self, target_event_idx: int) -> bool:
        """Advance or rewind internal array state to ``target_event_idx``.

        Returns True if a full bar refresh is needed (seek/rewind), False for
        incremental forward transitions.
        """
        full_refresh = False
        if (
            self._current_event_idx < 0
            or target_event_idx <= self._current_event_idx
        ):
            checkpoint_idx = (
                target_event_idx // self._checkpoint_stride
            ) * self._checkpoint_stride
            base_vals, base_sorted = self._checkpoints[checkpoint_idx]
            self._state_values = list(base_vals)
            self._sorted_indices = set(base_sorted)
            self._current_event_idx = checkpoint_idx - 1
            full_refresh = True

        changed_indices: set[int] = set()
        for idx in range(self._current_event_idx + 1, target_event_idx + 1):
            event = self.events[idx]
            if event.values:
                self._state_values = list(event.values)
                full_refresh = True
            elif event.changes:
                for pos, val in event.changes:
                    self._state_values[pos] = val
                    changed_indices.add(pos)
            if event.type == SortEventType.MARK_SORTED:
                self._sorted_indices.update(event.indices)
                changed_indices.update(event.indices)
            elif event.type == SortEventType.COMPLETE:
                self._sorted_indices = set(range(len(self._state_values)))
                full_refresh = True

        self._current_event_idx = target_event_idx
        self._apply_visual_state(
            self.events[target_event_idx],
            full_refresh=full_refresh,
            changed_indices=changed_indices,
        )
        return full_refresh

    def _apply_visual_state(
        self,
        event: SortEvent,
        *,
        full_refresh: bool,
        changed_indices: set[int],
    ) -> None:
        if full_refresh:
            indices_to_update = range(self.array_len)
        else:
            indices_to_update = self._prev_highlighted | changed_indices

        for idx in indices_to_update:
            if 0 <= idx < self.array_len:
                val = self._state_values[idx]
                bar = self.bars[idx]
                bar.set_height(val)
                bar.set_color(
                    STATE_COLORS[SortEventType.MARK_SORTED.value]
                    if idx in self._sorted_indices
                    else STATE_COLORS["unsorted"]
                )
                if self.value_texts:
                    txt = self.value_texts[idx]
                    y_pos = (
                        float(val) + self.label_offset
                        if val >= 0
                        else float(val) - self.label_offset
                    )
                    txt.set_position((idx, y_pos))
                    txt.set_va("bottom" if val >= 0 else "top")
                    txt.set_text(_format_value(val))

        if event.type == SortEventType.COMPLETE:
            for bar in self.bars:
                bar.set_color(STATE_COLORS[SortEventType.COMPLETE.value])
            self._prev_highlighted = set()
        else:
            highlight_color = STATE_COLORS.get(
                event.type.value, STATE_COLORS["unsorted"]
            )
            highlighted: set[int] = set()
            for idx in event.indices:
                if 0 <= idx < self.array_len:
                    self.bars[idx].set_color(highlight_color)
                    highlighted.add(idx)
            self._prev_highlighted = highlighted

    def render_frame(self, render_idx: int):
        """Render a specific keyframe index in ``[0, total_rendered)``."""
        render_idx = max(0, min(render_idx, self.total_rendered - 1))
        event_idx = self.rendered_map[render_idx]
        event = self.events[event_idx]
        self._seek_to_event(event_idx)
        self.current_render_idx = render_idx

        op_desc = event.message or event.type.value.replace("_", " ").title()
        self.operation_text.set_text(
            f"Operation: {event.type.value.replace('_', ' ').title()} — {op_desc}"
        )
        self.counter_text.set_text(
            _format_counter_line(
                self.counters[event_idx], event_idx + 1, len(self.events)
            )
        )
        if event.type == SortEventType.COMPLETE and render_idx == self.total_rendered - 1:
            self.is_paused = True
            self.btn_play.label.set_text("Play")
        return tuple(self.bars)

    def toggle_play(self, _event=None) -> None:
        if self.is_paused:
            if self.current_render_idx >= self.total_rendered - 1:
                self.render_frame(0)
                self.animation.frame_seq = self.animation.new_frame_seq()
            self.is_paused = False
            self.btn_play.label.set_text("Pause")
            if self.animation.event_source is not None:
                self.animation.event_source.start()
        else:
            self.is_paused = True
            self.btn_play.label.set_text("Play")
            if self.animation.event_source is not None:
                self.animation.event_source.stop()
        self.fig.canvas.draw_idle()

    def step_once(self, _event=None) -> None:
        self.is_paused = True
        self.btn_play.label.set_text("Play")
        if self.animation.event_source is not None:
            self.animation.event_source.stop()
        if self.current_render_idx + 1 < self.total_rendered:
            self.render_frame(self.current_render_idx + 1)
            self.fig.canvas.draw_idle()

    def reset(self, _event=None) -> None:
        self.is_paused = True
        self.btn_play.label.set_text("Play")
        if self.animation.event_source is not None:
            self.animation.event_source.stop()
        self.render_frame(0)
        self.animation.frame_seq = self.animation.new_frame_seq()
        self.fig.canvas.draw_idle()

    def _on_speed_change(self, val: float) -> None:
        self.interval = int(val)
        if self.animation.event_source is not None:
            self.animation.event_source.interval = self.interval


def animate_events(
    events: Iterable[SortEvent],
    interval: int | None = None,
    *,
    algorithm_name: str = "Sorting Algorithm",
    show: bool = True,
    max_frames: int | None = None,
):
    """Animate SortLab events. Requires the optional Matplotlib dependency."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is optional. Install it with: pip install sortlab[visualization]"
        ) from exc

    event_list = list(events)
    if not event_list:
        raise ValueError("events must contain at least one event")

    has_snapshots = any(event.values for event in event_list)
    is_empty_complete = (
        event_list[-1].type == SortEventType.COMPLETE and event_list[-1].values == ()
    )
    if not has_snapshots and not is_empty_complete:
        raise ValueError("No array snapshots were found in the event stream")

    resolved_interval = (
        interval
        if interval is not None
        else _compute_default_interval(
            min(len(event_list), max_frames) if max_frames else len(event_list)
        )
    )

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    controller = SortAnimationController(
        fig=fig,
        ax=ax,
        events=event_list,
        algorithm_name=algorithm_name,
        interval=resolved_interval,
        max_frames=max_frames,
    )

    if show:
        try:
            plt.show()
        finally:
            plt.close(fig)
    else:
        fig.canvas.draw()

    return controller.animation
