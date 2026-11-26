# Architecture

SortLab separates algorithm logic, event streams, registries, visualization frontends, and CLI interaction across both Sorting and Graph modules so implementations stay readable, timings stay accurate, and visualizers remain decoupled.

## Package Overview

1. **Sorting Algorithms (`src/sortlab/algorithms/`):** Plain Python functions accepting an iterable and returning a new sorted list without mutating the input or importing Matplotlib.
2. **Sorting Event Engine & Registry (`src/sortlab/core/`):**
   - `events.py`: Renderer-independent `SortEvent` streams and `SnapshotTracker`.
   - `runner.py`: Event-producing wrappers for all 10 sorting algorithms.
   - `registry.py`: `ALGORITHM_SPECS`, `ALGORITHM_REGISTRY`, and input validation.
3. **Graph Algorithms & Event Engine (`src/sortlab/graphs/`):**
   - `model.py`: Reusable `Graph` adjacency-list model, `GraphEdge`, `ShortestPathResult`, `MSTResult`, cycle exceptions (`GraphCycleError`, `NegativeCycleError`), and validation.
   - `algorithms/`: Pure-Python implementations of `bfs`, `dfs`, `dijkstra`, `bellman_ford`, `prim`, `kruskal`, and `topological_sort` (independent of Matplotlib).
   - `events.py`: Renderer-independent `GraphEvent` and `GraphEventType` definitions plus JSON serialization helpers.
   - `runner.py`: Event-producing wrappers (`bfs_events`, `dfs_events`, `dijkstra_events`, `bellman_ford_events`, `prim_events`, `kruskal_events`, `topological_sort_events`).
   - `registry.py`: `GRAPH_ALGORITHM_SPECS`, `GRAPH_ALGORITHM_REGISTRY`, and `validate_graph_for_spec`.
4. **Visualization (`src/sortlab/visualization/`):**
   - `_playback.py`: Shared `PlaybackControllerMixin`, `compute_default_interval`, and `select_rendered_indices` helpers.
   - `matplotlib.py`: Optional Matplotlib sorting renderer (`SortAnimationController`, `animate_events`).
   - `graph_matplotlib.py`: Optional Matplotlib graph renderer (`GraphAnimationController`, `animate_graph_events`, and deterministic `compute_graph_layout` without NetworkX).
5. **Benchmarks (`src/sortlab/benchmarks/runner.py`):** Pure timing helper (`benchmark`) measuring uninstrumented sorting functions, kept separate from event generation and GUI rendering.
6. **Interactive CLI (`src/sortlab/cli.py`):** Provides a top-level menu (`1. Sorting Algorithms`, `2. Graph Algorithms`, `0. Exit`), validates inputs per algorithm, times pure algorithm execution, and automatically launches the corresponding Matplotlib visualizer.

---

## Sorting Event Engine and Snapshot Optimization

Every sorting event is a frozen `SortEvent` dataclass with a canonical `SortEventType`:

- `compare`: Element comparison (`indices` compared)
- `swap`: Two elements exchanged (`indices`, `changes`)
- `write`: Value written to an index (`indices`, `changes`)
- `pivot`: Quick Sort pivot selection (`indices`, `metadata`)
- `merge`: Merge Sort placement (`indices`, `changes`, `metadata`)
- `heapify`: Heap Sort sift-down inspection (`indices`, `metadata`)
- `bucket_distribute`: Counting, Radix, or Bucket distribution step (`indices`, `metadata`)
- `mark_sorted`: Indices confirmed in final sorted position (`indices`)
- `complete`: Terminal event carrying the final sorted `values` tuple

### Memory-efficient snapshots for large arrays

Copying the full `tuple(items)` on every comparison or write is `O(n^2)` or `O(n^3)` memory on large inputs. `SnapshotTracker` avoids this:

- The initial event and terminal `complete` event always include full `values` snapshots.
- Non-mutating events omit `values` after the initial snapshot.
- Mutating events record `O(1)` delta pairs in `changes` (`((index, value), ...)`) and emit periodic full `values` snapshots every `snapshot_interval` mutations.
- `apply_event` and `reconstruct_snapshots` allow any consumer or test to reconstruct full array state at every frame in `O(1)` per delta.

---

## Graph Model and Policy (`src/sortlab/graphs/model.py`)

`Graph` stores vertices in deterministic insertion order using an adjacency list (`dict[Node, list[tuple[Node, Weight]]]`) alongside an edge list (`tuple[GraphEdge, ...]`).

- **Node identifiers:** Non-empty `str` or non-boolean `int` values.
- **Directed & undirected:** Undirected edges populate both endpoints' adjacency lists while storing one canonical `GraphEdge` in `graph.edges`.
- **Weighted & unweighted:** Weighted graphs require explicit finite `int`/`float` weights (`NaN` and `Inf` are rejected). Unweighted graphs default weights to `1` and reject custom weights.
- **Disconnected graphs:** Supported via explicit `nodes` registration / `add_node()` for isolated vertices and multiple components.
- **Self-loop & parallel-edge policy:**
  - `allow_self_loops=False` (default): self-loops `(u, u)` raise `ValueError`. Pass `allow_self_loops=True` to permit them (e.g., for testing cycle detection).
  - `allow_parallel_edges=False` (default): duplicate edges between the same endpoints raise `ValueError`. Pass `allow_parallel_edges=True` to enable multigraphs.

---

## Graph Event Engine (`src/sortlab/graphs/events.py`)

Every graph event is a frozen `GraphEvent` dataclass using `GraphEventType`:

- `start`: Initial event carrying embedded `graph` dictionary in `metadata["graph"]` and optional initial `distances`
- `discover_node`: Node discovered / added to frontier (queue, stack, or priority queue)
- `visit_node`: Node popped / selected for processing
- `complete_node`: Node finished processing / finalized
- `explore_edge`: Edge inspected during traversal, relaxation, or MST scan
- `select_edge`: Edge accepted into traversal tree, shortest-path tree, or MST
- `reject_edge`: Edge skipped (already visited, no relaxation improvement, or cycle-forming in Kruskal)
- `relax_edge`: Candidate relaxation check in Dijkstra or Bellman-Ford
- `update_distance`: Distance or candidate MST key updated (`node`, `distance`, `distances`)
- `cycle_detected`: Cycle identified by Bellman-Ford (negative cycle) or Topological Sort
- `complete`: Terminal event summarizing final distances, traversal/topological order, or selected edges

### Future web visualizer compatibility

Both `SortEvent` and `GraphEvent` expose `to_dict()`, `from_dict()`, and JSON stream serializers (`serialize_events`/`events_to_json` and `serialize_graph_events`/`graph_events_to_json`). Infinite graph distances (`float('inf')`) are encoded as `None` in JSON (`allow_nan=False`) for strict cross-language JSON compatibility.

## Input, Mutation, and Timing Policy

- Public sorting and graph algorithms never mutate caller-supplied iterables or `Graph` objects.
- The CLI times only pure algorithm execution (`perf_counter()`) and excludes event generation and Matplotlib window duration.
