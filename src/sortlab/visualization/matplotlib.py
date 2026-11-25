"""Matplotlib animation for SortLab event streams."""

def animate_events(events, interval=250):
    """Animate SortLab events. Requires the optional Matplotlib dependency."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is optional. Install it with: pip install sortlab[visualization]"
        ) from exc

    event_list = list(events)
    if not event_list:
        raise ValueError("events must contain at least one event")

    snapshots = [event.values for event in event_list if event.values]
    if not snapshots:
        raise ValueError("No array snapshots were found in the event stream")

    fig, ax = plt.subplots()
    bars = ax.bar(range(len(snapshots[0])), snapshots[0])
    ax.set_title("SortLab — Bubble Sort")
    ax.set_xlabel("Index")
    ax.set_ylabel("Value")

    def update(frame):
        event = event_list[frame]
        values = event.values
        if values:
            for bar, value in zip(bars, values):
                bar.set_height(value)
                bar.set_color("C0")
        for index in event.indices:
            if 0 <= index < len(bars):
                bars[index].set_color("C1" if event.type.value == "compare" else "C2")
        ax.set_title("SortLab — " + (event.message or event.type.value))
        return tuple(bars)

    animation = FuncAnimation(
        fig, update, frames=len(event_list), interval=interval, blit=False,
        repeat=False,
    )
    plt.tight_layout()
    plt.show()
    return animation
