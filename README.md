# SortLab

**Explore. Visualize. Understand Sorting.**

SortLab is an educational, open-source reference library for sorting algorithms. It brings together readable Python implementations, a standardized event engine covering all 10 algorithms, an interactive CLI with automatic Matplotlib visualization, performance benchmarks, and beginner-friendly documentation.

> **Project status:** Early development (v0.1.0). APIs may evolve before the first stable release.

## What is included?

- Clear, pure-Python implementations of 10 sorting algorithms (independent of Matplotlib).
- A standardized, JSON-serializable event engine (`sortlab.core`) covering all 10 algorithms.
- A central algorithm registry (`ALGORITHM_REGISTRY`) with input validation.
- A shared Matplotlib animation renderer (`sortlab.visualization.matplotlib`) with color-coded operation states, value labels, live operation HUD, counters, and playback controls (`Pause`/`Play`, `Step`, `Reset`, `Delay (ms)`).
- An interactive CLI (`sortlab`) that validates input, prints pure sorting output/timing, automatically opens the animated visualization, and returns to the menu when the window closes.
- Simple benchmarking utilities (`sortlab.benchmarks`) kept strictly separate from visualization timing.

## Quick start

```bash
git clone https://github.com/bhr007/SortLab.git
cd sortlab
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -e ".[dev,visualization]"
```

Run the interactive CLI (automatically launches Matplotlib visualization):

```bash
sortlab
# or without installing the entrypoint:
python -m sortlab.cli
```

Useful CLI options:

```bash
sortlab --list           # List all 10 algorithms and exit
sortlab --interval 200   # Override animation frame delay in milliseconds
sortlab --no-vis         # Print sorted output and pure sort time without opening GUI
```

Run an algorithm directly in Python:

```python
from sortlab.algorithms import bubble_sort, merge_sort

numbers = [8, 3, 5, 1, 9, 2]
print(bubble_sort(numbers))
print(merge_sort(numbers))
```

Run an example visualization or benchmark:

```bash
python examples/visualize_bubble_sort.py
python examples/benchmark_algorithms.py
```

Run the test suite and linter:

```bash
pytest
ruff check .
```

## Algorithm collection

| # | Algorithm | Category | Input constraints | Stable | Typical time |
|---:|---|---|---|---:|---:|
| 1 | Bubble Sort | Comparison | Finite numbers (`int`, `float`) | Yes | O(n²) |
| 2 | Selection Sort | Comparison | Finite numbers (`int`, `float`) | No | O(n²) |
| 3 | Insertion Sort | Comparison | Finite numbers (`int`, `float`) | Yes | O(n²) |
| 4 | Merge Sort | Divide and conquer | Finite numbers (`int`, `float`) | Yes | O(n log n) |
| 5 | Quick Sort | Divide and conquer | Finite numbers (`int`, `float`) | Usually no | O(n log n) average |
| 6 | Heap Sort | Comparison | Finite numbers (`int`, `float`) | No | O(n log n) |
| 7 | Shell Sort | Comparison | Finite numbers (`int`, `float`) | No | Depends on gap sequence |
| 8 | Counting Sort | Non-comparison | **Integers only** (negatives supported) | Yes, in this implementation | O(n + k) |
| 9 | Radix Sort | Non-comparison | **Integers only** (negatives supported) | Yes, in this implementation | O(d(n + b)) |
| 10 | Bucket Sort | Distribution-based | Finite numbers (`int`, `float`) | Depends on bucket sort | Expected linear under assumptions |

Complexities and properties depend on implementation details and input assumptions. See each algorithm's documentation.

## Visualization features

The shared Matplotlib renderer consumes `SortEvent` streams for every algorithm without algorithm-specific rendering logic:

- **Color-coded states:** `unsorted`, `compare`, `swap`, `write`, `pivot`, `merge`, `heapify`, `bucket_distribute`, and `mark_sorted`/`complete`.
- **Live HUD:** algorithm title, active operation description, and cumulative counters (`Step`, `Comparisons`, `Swaps`, `Writes`, plus `Merges`/`Pivots`/`Heap ops`/`Buckets` when applicable).
- **Value labels:** displayed on bars for arrays of up to 30 elements; negative and zero values are supported.
- **Interactive controls:** `Pause`/`Play`, `Step`, `Reset`, and a `Delay (ms)` slider.

## Design principles

1. **Readable first:** implementations should be approachable to learners.
2. **Correctness matters:** every algorithm and event stream is verified against `sorted()`.
3. **One shared event model:** visualizers consume `SortEvent` streams without algorithm-specific rendering code.
4. **Honest benchmarks:** pure algorithm timing is kept separate from event generation and GUI rendering.
5. **Contributions welcome:** follow `CONTRIBUTING.md`.

## Roadmap

- [x] Initial package structure and development tooling
- [x] Ten foundational sorting algorithms
- [x] Shared, serializable visualization event model across all 10 algorithms
- [x] Shared Matplotlib visualizer with controls and CLI auto-launch
- [x] Basic benchmark utilities
- [ ] More algorithms and edge-case documentation
- [ ] Algorithm comparison views
- [ ] Browser-based interactive playground (future direction using `serialize_events` / `events_to_json`)

## License

SortLab is released under the [MIT License](LICENSE).

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
