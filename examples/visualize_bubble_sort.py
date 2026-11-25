"""Run with: pip install -e '.[visualization]' && python examples/visualize_bubble_sort.py"""

from sortlab.core import bubble_sort_events
from sortlab.visualization.matplotlib import animate_events

if __name__ == "__main__":
    sample = [8, 3, 5, 1, 9, 2, 6, 4]
    animate_events(bubble_sort_events(sample), interval=450)
