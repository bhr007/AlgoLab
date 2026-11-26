# AlgoLab

**Explore. Visualize. Understand Algorithms.**

[![Tests](https://github.com/bhr007/AlgoLab/actions/workflows/tests.yml/badge.svg)](https://github.com/bhr007/AlgoLab/actions/workflows/tests.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-17243A.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-FF9B45.svg)](LICENSE)

**AlgoLab** is an educational and developer-focused, open-source Python platform for algorithm visualization, experimentation, and benchmarking. It brings together readable pure-Python implementations of foundational **sorting** and **graph** algorithms, standardized JSON-serializable event engines, an interactive single-window desktop studio, a guided CLI, performance benchmarks, and clear technical documentation.

> **Project status:** Early development (v0.1.0). APIs may evolve before the first stable release.
>
> **Rebrand & compatibility note:** Formerly *SortLab*. The distribution name and primary CLI command are now `algolab`, while the `sortlab` Python import package (`import sortlab`) and `sortlab` CLI alias are preserved for backward compatibility.

---

## Feature Overview

- **Pure-Python Algorithm Implementations:**
  - **10 Sorting Algorithms** (`sortlab.algorithms`): Comparison, divide-and-conquer, non-comparison, and distribution-based sorts, completely decoupled from Matplotlib.
  - **7 Graph Algorithms** (`sortlab.graphs`): Traversal, shortest-path, minimum spanning tree/forest, and DAG topological ordering, completely decoupled from Matplotlib.
- **Reusable Graph Data Model (`sortlab.graphs.model`):** Supports directed/undirected, weighted/unweighted, empty, and disconnected graphs via deterministic insertion-ordered adjacency lists with explicit self-loop and parallel-edge validation policies.
- **Standardized Event Engines:** Renderer-independent, JSON-serializable `SortEvent` (`sortlab.core`) and `GraphEvent` (`sortlab.graphs.events`) streams with strict `to_dict()` / `from_dict()` / JSON export.
- **Central Registries & Validation:** `ALGORITHM_REGISTRY` and `GRAPH_ALGORITHM_REGISTRY` enforce algorithm-specific input constraints before execution.
- **Single-Window Desktop Studio (`algolab --gui`):** Native Matplotlib desktop UI combining mode selection, algorithm guides, presets, input validation, pure timing, and live animation playback controls in one window.
- **Interactive CLI (`algolab`):** Choose between **CLI-only** (`--mode cli`), **CLI + Visualization** (default), or **Single-Window GUI Studio** (`--gui` / `--mode gui`).
- **Honest Benchmarking (`sortlab.benchmarks`):** Pure algorithm timing kept strictly separate from event generation and GUI rendering.

### Visual Identity

| Role | Color | Hex |
|---|---|---|
| Primary (Deep Navy) | Brand headers, active selections, primary graph nodes | `#17243A` |
| Accent (Orange) | Primary actions, active comparisons & edge explorations | `#FF9B45` |
| Surface (Light Gray) | Studio canvas, HUD counters, constraint badges | `#F3F5F8` |

---

## Installation

```bash
git clone https://github.com/bhr007/AlgoLab.git
cd AlgoLab
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -e ".[dev,visualization]"
```

For full OS-specific setup instructions (macOS, Linux, Windows PowerShell), see [docs/EXECUTION_GUIDE.md](docs/EXECUTION_GUIDE.md).

---

## CLI & GUI Usage

Launch **AlgoLab** in the mode that fits your workflow:

```bash
algolab --gui            # Launch the single-window Desktop GUI Studio (no browser)
algolab                  # Interactive CLI menu + automatic Matplotlib visualization
algolab --mode cli       # Run strictly in terminal (CLI-only, no GUI windows)
algolab --mode cli-gui   # Same as default: interactive CLI + Matplotlib visualization
algolab --mode gui       # Same as --gui: single-window Desktop GUI Studio
algolab --list           # List all sorting and graph algorithms and exit
algolab --interval 200   # Override animation frame delay in milliseconds
algolab --no-vis         # Print algorithm output and timing without opening GUI
```

> Both `algolab` and the legacy `sortlab` command (as well as `python -m sortlab.cli`) invoke the same CLI entrypoint.

### Interactive CLI Workflow

1. At the **Main Menu**, choose:
   - `1` — **Sorting Algorithms (CLI + Visualization)**
   - `2` — **Graph Algorithms (CLI + Visualization)**
   - `3` — **Launch Desktop GUI Studio (Single Window)**
   - `0` — **Exit**
2. **Sorting Algorithms:** Pick an algorithm (`1–10`) and enter space- or comma-separated numbers (e.g., `8, 3, 5, 1, 9, 2`).
3. **Graph Algorithms:** Pick an algorithm (`1–7`), configure directed/weighted options when applicable, optionally enter isolated node names, enter edges (`A B, B C` for unweighted or `A B 4, B C 2` for weighted), and enter a start node when needed.
4. AlgoLab validates inputs, prints the pure algorithm result and execution time, and launches the animated visualization.

### Automated Input Example

```bash
algolab --mode cli < examples/automated_input.txt
```

---

## Python API Quick Start

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

Run standalone examples:

```bash
python examples/visualize_bubble_sort.py
python examples/benchmark_algorithms.py
```

---

## Algorithm Categories

### Sorting Algorithms (10)

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

### Graph Algorithms (7)

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

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full design details. AlgoLab separates concerns cleanly across modules:

- `src/sortlab/algorithms/` — Pure sorting functions (no Matplotlib dependency).
- `src/sortlab/core/` — Sorting `SortEvent` engine, `SnapshotTracker`, event runners, and `ALGORITHM_REGISTRY`.
- `src/sortlab/graphs/` — `Graph` model, 7 graph algorithms, `GraphEvent` engine, event runners, and `GRAPH_ALGORITHM_REGISTRY`.
- `src/sortlab/visualization/` — Shared Matplotlib renderers (`matplotlib.py`, `graph_matplotlib.py`, `_playback.py`) with color-coded states, HUD counters, deterministic lightweight graph layout (no NetworkX), and playback controls.
- `src/sortlab/gui.py` — Single-window `AlgoLabStudio` desktop UI.
- `src/sortlab/cli.py` — Interactive CLI (`algolab` / `sortlab`).
- `src/sortlab/benchmarks/` — Uninstrumented algorithm timing helpers.

---

## Testing & Linting

Run the full test suite and linter:

```bash
pytest -v
ruff check .
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md) before opening a pull request.

## License

AlgoLab is released under the [MIT License](LICENSE).
