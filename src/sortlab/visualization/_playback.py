"""Shared playback helpers for SortLab Matplotlib animation controllers."""

from __future__ import annotations


def compute_default_interval(
    frame_count: int, *, min_ms: int = 15, max_ms: int = 450, target_total_ms: int = 10_000
) -> int:
    """Choose a responsive playback interval in milliseconds for ``frame_count``."""
    return max(min_ms, min(max_ms, target_total_ms // max(1, frame_count)))


def select_rendered_indices(total: int, max_frames: int | None) -> list[int]:
    """Select evenly spaced event indices, always keeping the first and last."""
    if max_frames is None or total <= max_frames or max_frames < 2:
        return list(range(total))
    step = (total - 1) / (max_frames - 1)
    indices = [round(i * step) for i in range(max_frames - 1)]
    indices.append(total - 1)
    deduped: list[int] = []
    for idx in indices:
        if not deduped or deduped[-1] != idx:
            deduped.append(idx)
    return deduped


class PlaybackControllerMixin:
    """Shared Play/Pause, Step, Reset, and Speed handlers for Matplotlib controllers."""

    is_paused: bool
    current_render_idx: int
    total_rendered: int
    interval: int

    def _frame_iterator(self):
        idx = 1
        while idx < self.total_rendered:
            yield idx
            idx = self.current_render_idx + 1

    def toggle_play(self, _event=None) -> None:
        anim = getattr(self, "animation", None)
        if self.is_paused:
            if self.current_render_idx >= self.total_rendered - 1:
                self.render_frame(0)
                if anim is not None:
                    anim.frame_seq = anim.new_frame_seq()
            self.is_paused = False
            self.btn_play.label.set_text("Pause")
            if anim is not None and anim.event_source is not None:
                anim.event_source.start()
        else:
            self.is_paused = True
            self.btn_play.label.set_text("Play")
            if anim is not None and anim.event_source is not None:
                anim.event_source.stop()
        self.fig.canvas.draw_idle()

    def step_once(self, _event=None) -> None:
        anim = getattr(self, "animation", None)
        self.is_paused = True
        self.btn_play.label.set_text("Play")
        if anim is not None and anim.event_source is not None:
            anim.event_source.stop()
        if self.current_render_idx + 1 < self.total_rendered:
            self.render_frame(self.current_render_idx + 1)
            self.fig.canvas.draw_idle()

    def reset(self, _event=None) -> None:
        anim = getattr(self, "animation", None)
        self.is_paused = True
        self.btn_play.label.set_text("Play")
        if anim is not None and anim.event_source is not None:
            anim.event_source.stop()
        self.render_frame(0)
        if anim is not None:
            anim.frame_seq = anim.new_frame_seq()
        self.fig.canvas.draw_idle()

    def _on_speed_change(self, val: float) -> None:
        self.interval = int(val)
        anim = getattr(self, "animation", None)
        if anim is not None and anim.event_source is not None:
            anim.event_source.interval = self.interval
