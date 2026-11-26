"""Optional visualization tools. Install with: pip install algolab[visualization]."""

from .graph_matplotlib import animate_graph_events
from .matplotlib import animate_events

__all__ = ["animate_events", "animate_graph_events"]
