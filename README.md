# SortLab

**Explore. Visualize. Understand Algorithms.**

SortLab is an educational, open-source Python reference library for **sorting algorithms** and **graph algorithms**. It brings together readable pure-Python implementations, standardized JSON-serializable event engines, interactive Matplotlib visualizations, an interactive CLI with automatic visualization launch, performance benchmarks, and learner-focused documentation.

> **Project status:** Early development (v0.1.0). APIs may evolve before the first stable release.

## What is included?

- Clear, pure-Python implementations of **10 sorting algorithms** (`sortlab.algorithms`) and **7 graph algorithms** (`sortlab.graphs`), completely independent of Matplotlib.
- Standardized, JSON-serializable event engines (`sortlab.core` for sorting; `sortlab.graphs.events` for graphs) with strict `to_dict()` / `from_dict()` / JSON export.
- Reusable `Graph` adjacency-list model (`sortlab.graphs.model`) supporting directed/undirected, weighted/unweighted, and disconnected graphs with explicit self-loop and parallel-edge policies.
- Central registries (`ALGORITHM_REGISTRY`, `GRAPH_ALGORITHM_REGISTRY`) with per-algorithm constraint validation.
- Dedicated Matplotlib animation renderers (`sortlab.visualization.matplotlib` and `sortlab.visualization.graph_matplotlib`) with color-coded states, live HUD counters, distance/weight annotations, deterministic graph layout (no NetworkX required), and playback controls (`Pause`/`Play`, `Step`, `Reset`, `Delay (ms)`).
- An interactive CLI (`sortlab`) with a main menu for **Sorting Algorithms**, **Graph Algorithms**, and **Exit**, automatic input validation, pure algorithm timing, and automatic visualization launch.
- Simple sorting benchmarking utilities (`sortlab.benchmarks`) kept strictly separate from visualization timing.

## Quick start

For detailed OS-specific instructions (macOS, Linux, Windows PowerShell), see [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md).

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
sortlab --gui            # Launch the single-window native Desktop GUI Studio (no browser)
sortlab --mode cli       # Run strictly in terminal (CLI-only, no GUI windows)
sortlab --mode cli-gui   # Default: interactive terminal menus + Matplotlib visualization
sortlab --mode gui       # Same as --gui: run entirely in the single-window GUI Studio
sortlab --list           # List all sorting and graph algorithms and exit
sortlab --interval 200   # Override animation frame delay in milliseconds
sortlab --no-vis         # Print algorithm output and pure execution time without opening GUI
```

### Interactive CLI Guide

1. At the **Main Menu**, choose `1` for **Sorting Algorithms (CLI + Visualization)**, `2` for **Graph Algorithms (CLI + Visualization)**, `3` to **Launch Desktop GUI Studio (Single Window)**, or `0` to **Exit**.
2. In **Sorting Algorithms**, choose an algorithm (`1–10`) and enter space- or comma-separated numbers (e.g., `8, 3, 5, 1, 9, 2`).
3. In **Graph Algorithms**, choose an algorithm (`1–7`):
   - Choose directed/undirected and weighted/unweighted when not fixed by the algorithm.
   - Optionally enter node names (useful for isolated nodes in disconnected graphs), or press Enter to infer nodes from edges.
   - Enter edges separated by commas or semicolons:
     - Unweighted: `A B, B C, A C` (or `A->B, B->C`)
     - Weighted: `A B 4, B C 2, A C 7`
   - Enter a starting node when required (BFS, DFS, Dijkstra, Bellman-Ford; optional for Prim).
   - SortLab validates inputs, prints the pure algorithm result and execution time, and opens the animated graph visualization.

Run algorithms directly in Python:

```python
from sortlab.algorithms import bubble_sort, merge_sort
from sortlab.graphs import Graph, bfs, dijkstra, kruskal, topological_sort

numbers = [8, 3, 5, 1, 9, 2]
print(merge_sort(numbers))

graph = Graph.from_edges(
    [("A", "B", 4), ("A", "C", 1), ("C", "B", 2), ("B", "D", 1)],
    directed=True,
    weighted=True,
)
print(bfs(graph, "A"))
shortest = dijkstra(graph, "A")
print(shortest.distances, shortest.path_to("D"))
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

## Sorting Algorithm Collection

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

## Graph Algorithm Collection

See [docs/GRAPH_ALGORITHMS.md](docs/GRAPH_ALGORITHMS.md) for full details, constraints, and edge-case policies.

| # | Algorithm | Category | Constraints | Time | Space |
|---:|---|---|---|---|---|
| 1 | Breadth-First Search (BFS) | Traversal | Directed or undirected; ignores weights | O(V + E) | O(V) |
| 2 | Depth-First Search (DFS) | Traversal | Directed or undirected; ignores weights | O(V + E) | O(V) |
| 3 | Dijkstra's Shortest Path | Shortest Path | Directed or undirected; **non-negative weights** | O((V + E) log V) | O(V + E) |
| 4 | Bellman-Ford Shortest Path | Shortest Path | Supports negative weights; detects reachable negative cycles | O(V · E) | O(V) |
| 5 | Prim's Minimum Spanning Tree | MST / Forest | **Undirected** graphs; supports negative weights | O((V + E) log V) | O(V + E) |
| 6 | Kruskal's Minimum Spanning Tree | MST / Forest | **Undirected** graphs; supports negative weights | O(E log E) | O(V + E) |
| 7 | Topological Sort (Kahn's) | DAG Ordering | **Directed acyclic graphs (DAGs)** only; detects cycles | O(V + E) | O(V) |

## Visualization Features

### Sorting Visualizer (`sortlab.visualization.matplotlib`)
- **Color-coded states:** `unsorted`, `compare`, `swap`, `write`, `pivot`, `merge`, `heapify`, `bucket_distribute`, and `mark_sorted`/`complete`.
- **Live HUD:** algorithm title, active operation description, and cumulative counters (`Step`, `Comparisons`, `Swaps`, `Writes`, plus `Merges`/`Pivots`/`Heap ops`/`Buckets` when applicable).
- **Value labels:** displayed on bars for arrays of up to 30 elements; negative and zero values are supported.
- **Interactive controls:** `Pause`/`Play`, `Step`, `Reset`, and a `Delay (ms)` slider.

### Graph Visualizer (`sortlab.visualization.graph_matplotlib`)
- **Deterministic lightweight layout:** pure-Python circular + force-directed layout (`compute_graph_layout`) with no NetworkX dependency.
- **Graph elements:** directed arrows (with curved arcs for bidirectional pairs and self-loops), undirected edges, weight badges, node state colors (`unvisited`, `frontier`, `current`, `visited`, `cycle`), and live per-node distance/key badges.
- **Edge highlights:** active exploration/relaxation edges, selected tree/path edges, rejected edges, and detected cycle edges.
- **Live HUD & controls:** step/visited/edge counters, traversal/topological order, frontier, distances, and `Pause`/`Play`, `Step`, `Reset`, `Delay (ms)` playback controls.

## Design principles

1. **Readable first:** implementations should be approachable to learners.
2. **Correctness matters:** algorithms, edge cases, and event streams are thoroughly tested.
3. **Renderer-independent events:** visualizers consume `SortEvent` and `GraphEvent` streams without embedding algorithm logic.
4. **Honest timing:** pure algorithm timing in the CLI and benchmarks is kept separate from event generation and GUI rendering.
5. **Contributions welcome:** follow [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

- [x] Initial package structure and development tooling
- [x] Ten foundational sorting algorithms with shared `SortEvent` engine
- [x] Shared Matplotlib sorting visualizer with controls and CLI auto-launch
- [x] Graph model, 7 foundational graph algorithms, `GraphEvent` engine, and Matplotlib graph visualizer
- [x] Unified interactive CLI main menu for Sorting and Graph algorithms
- [x] Basic sorting benchmark utilities
- [ ] Graph benchmarking utilities and algorithm comparison views
- [ ] Browser-based interactive playground (future direction using JSON-serialized event streams)

## License

SortLab is released under the [MIT License](LICENSE).

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
