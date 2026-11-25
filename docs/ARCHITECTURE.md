# Architecture

SortLab separates five distinct concerns so algorithms remain readable, benchmarks remain accurate, and visualization frontends stay decoupled:

1. **Algorithms (`src/sortlab/algorithms/`):** Plain Python functions that accept an iterable and return a new sorted list without mutating the input or importing Matplotlib.
2. **Core Event Engine (`src/sortlab/core/events.py`, `src/sortlab/core/runner.py`):** Renderer-independent `SortEvent` streams covering all 10 algorithms.
3. **Algorithm Registry (`src/sortlab/core/registry.py`):** Central metadata and dispatch table (`ALGORITHM_SPECS`, `ALGORITHM_REGISTRY`) mapping menu choices, keys, and names to `(algorithm, event_generator, constraints)`.
4. **Visualization (`src/sortlab/visualization/matplotlib.py`):** Optional Matplotlib frontend (`SortAnimationController`, `animate_events`) that renders any algorithm's `SortEvent` stream with color-coded states, counters, value labels, and interactive playback controls.
5. **Benchmarks (`src/sortlab/benchmarks/runner.py`):** Pure timing helper (`benchmark`) measuring uninstrumented sorting functions, kept completely separate from event generation and GUI rendering.
6. **Interactive CLI (`src/sortlab/cli.py`):** Parses and validates numeric inputs, enforces per-algorithm constraints (such as integer-only Counting Sort and Radix Sort), runs and times the pure algorithm, launches the Matplotlib animation automatically, and returns to the menu when the window closes.

## Event Engine and Snapshot Optimization

Every event is a frozen `SortEvent` dataclass with a canonical `SortEventType`:

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
- Non-mutating events (`compare`, `pivot`, `heapify`, `mark_sorted`, `bucket_distribute`) omit `values` after the initial snapshot.
- Mutating events (`swap`, `write`, `merge`) always record `O(1)` delta pairs in `changes` (`((index, value), ...)`), and emit periodic full `values` snapshots every `snapshot_interval` mutations (every mutation for `n <= 32`, every `n` mutations for larger arrays).
- `apply_event` and `reconstruct_snapshots` allow any consumer or test to reconstruct full array state at every frame in `O(1)` per delta.

### Future web visualizer compatibility

All `SortEvent` fields use basic Python primitives and expose `SortEvent.to_dict()`, `SortEvent.from_dict()`, `serialize_events()`, and `events_to_json()`. A future web UI can consume JSON-serialized event streams directly without any Matplotlib dependency.

## Input and mutation policy

Public sorting functions and event generators return a new list or stream without mutating the supplied iterable. Constraints enforced across algorithms, event generators, and the CLI:

- **Counting Sort & Radix Sort:** Non-boolean `int` values only (negative integers supported); floats and booleans raise `TypeError` (or `ValueError` in CLI validation).
- **Bucket Sort & Comparison Sorts:** Finite `int` and `float` values; booleans raise `TypeError`, and `nan`/`inf` raise `ValueError`.
- **CLI timing:** The CLI times only the pure `algorithm(values)` execution and excludes event generation and Matplotlib window duration.
