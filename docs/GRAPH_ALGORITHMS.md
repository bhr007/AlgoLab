# Graph Algorithms in SortLab

This document describes SortLab's `Graph` model, self-loop and parallel-edge policies, standardized graph events, and the seven implemented graph algorithms.

## Graph Model (`sortlab.graphs.Graph`)

The `Graph` class represents directed or undirected, weighted or unweighted graphs using deterministic insertion-ordered adjacency lists.

### Supported Features
- **Node identifiers:** Non-empty `str` or non-boolean `int` identifiers (e.g., `"A"`, `"node_1"`, `0`, `1`).
- **Directed & Undirected:** Controlled by `directed=True | False`.
- **Weighted & Unweighted:** Controlled by `weighted=True | False`. Weighted graphs require finite `int` or `float` weights (`nan` and `inf` are rejected).
- **Disconnected Graphs & Empty Graphs:** Isolated vertices can be added via `nodes=[...]` or `graph.add_node(node)`.

### Self-Loop and Parallel-Edge Policy
- **Self-loops (`allow_self_loops: bool = False`):** Rejected by default with `ValueError` to keep educational graphs simple and acyclic assumptions clear. Set `allow_self_loops=True` to permit `(u, u)` edges (for example, to test cycle detection in Topological Sort).
- **Parallel edges (`allow_parallel_edges: bool = False`):** Rejected by default with `ValueError` (same `(u, v)` in directed graphs; same `{u, v}` pair in undirected graphs). Set `allow_parallel_edges=True` to build multigraphs.

---

## Implemented Algorithms

### 1. Breadth-First Search (`bfs`)
- **Module:** `sortlab.graphs.algorithms.bfs`
- **How it works:** Explores vertices level-by-level from `start` using a FIFO `deque`.
- **Constraints:** Works on directed or undirected, weighted or unweighted graphs (edge weights are ignored). Pass `traverse_all=True` to continue across disconnected components after the starting component completes.
- **Complexity:** Time `O(V + E)`, Auxiliary Space `O(V)`.
- **Key events:** `start`, `discover_node`, `visit_node`, `explore_edge`, `select_edge`, `reject_edge`, `complete_node`, `complete`.

### 2. Depth-First Search (`dfs`)
- **Module:** `sortlab.graphs.algorithms.dfs`
- **How it works:** Explores as deeply as possible along each branch before backtracking, implemented iteratively with an explicit frame stack to avoid Python recursion limits while matching recursive adjacency-list order.
- **Constraints:** Works on directed or undirected, weighted or unweighted graphs (edge weights are ignored). Supports `traverse_all=True` for disconnected components.
- **Complexity:** Time `O(V + E)`, Auxiliary Space `O(V)`.
- **Key events:** `start`, `discover_node`, `visit_node`, `explore_edge`, `select_edge`, `reject_edge`, `complete_node`, `complete`.

### 3. Dijkstra's Shortest Path (`dijkstra`)
- **Module:** `sortlab.graphs.algorithms.dijkstra`
- **How it works:** Maintains a binary min-heap (`heapq`) keyed by tentative distance from `start`, greedily finalizing the closest unvisited vertex and relaxing outgoing edges. Returns a `ShortestPathResult` with `.distances`, `.predecessors`, and `.path_to(target)`.
- **Constraints:** Directed or undirected graphs with **non-negative edge weights (`weight >= 0`)**. Negative weights raise `ValueError`. Unreachable nodes have distance `float('inf')`.
- **Complexity:** Time `O((V + E) log V)`, Space `O(V + E)`.
- **Key events:** `start`, `discover_node`, `visit_node`, `explore_edge`, `relax_edge`, `update_distance`, `select_edge`, `reject_edge`, `complete_node`, `complete`.

### 4. Bellman-Ford Shortest Path (`bellman_ford`)
- **Module:** `sortlab.graphs.algorithms.bellman_ford`
- **How it works:** Relaxes all directed edges up to `|V| - 1` passes (with early termination when no distance improves), then performs a `|V|`-th pass to detect reachable negative-weight cycles. Returns a `ShortestPathResult`.
- **Constraints:** Supports negative edge weights on directed graphs. (Note: any reachable negative-weight edge in an undirected graph forms a negative 2-cycle.) Pure `bellman_ford()` raises `NegativeCycleError(ValueError)` when a reachable negative cycle exists; `bellman_ford_events()` emits `cycle_detected` and `complete` with `metadata["negative_cycle"] = True`.
- **Complexity:** Time `O(V · E)`, Space `O(V)`.
- **Key events:** `start`, `discover_node`, `explore_edge`, `relax_edge`, `update_distance`, `select_edge`, `reject_edge`, `cycle_detected`, `complete_node`, `complete`.

### 5. Prim's Minimum Spanning Tree (`prim`)
- **Module:** `sortlab.graphs.algorithms.prim`
- **How it works:** Grows a tree from `start` (defaulting to the first vertex) by repeatedly selecting the minimum-weight edge connecting a visited vertex to an unvisited vertex via a binary min-heap. Returns an `MSTResult`.
- **Constraints:** **Undirected** graphs only (`directed=True` raises `ValueError`). Supports positive, zero, and negative weights. On disconnected graphs, continues across remaining components to produce a Minimum Spanning Forest (`result.is_spanning == False`).
- **Complexity:** Time `O((V + E) log V)`, Space `O(V + E)`.
- **Key events:** `start`, `discover_node`, `visit_node`, `explore_edge`, `update_distance`, `select_edge`, `reject_edge`, `complete_node`, `complete`.

### 6. Kruskal's Minimum Spanning Tree (`kruskal`)
- **Module:** `sortlab.graphs.algorithms.kruskal`
- **How it works:** Sorts all edges by ascending weight and greedily adds edges that connect distinct components using a Disjoint Set Union (Union-Find with path compression and union by rank). Returns an `MSTResult`.
- **Constraints:** **Undirected** graphs only (`directed=True` raises `ValueError`). Supports positive, zero, and negative weights. On disconnected graphs, returns a Minimum Spanning Forest (`result.is_spanning == False`).
- **Complexity:** Time `O(E log E)` (equivalently `O(E log V)` on simple graphs), Space `O(V + E)`.
- **Key events:** `start`, `explore_edge`, `select_edge`, `reject_edge`, `complete`.

### 7. Topological Sort (`topological_sort`)
- **Module:** `sortlab.graphs.algorithms.topological_sort`
- **How it works:** Uses Kahn's algorithm: computes vertex in-degrees, enqueues vertices with in-degree `0`, and iteratively removes outgoing edges to produce a linear ordering where every directed edge `(u, v)` places `u` before `v`.
- **Constraints:** **Directed acyclic graphs (DAGs)** only. Undirected graphs raise `ValueError`. Pure `topological_sort()` raises `GraphCycleError(ValueError)` if a cycle exists (including self-loops); `topological_sort_events()` emits `cycle_detected` and `complete` with `metadata["has_cycle"] = True`. Supports disconnected DAGs and isolated vertices.
- **Complexity:** Time `O(V + E)`, Space `O(V)`.
- **Key events:** `start`, `discover_node`, `visit_node`, `explore_edge`, `select_edge`, `complete_node`, `cycle_detected`, `complete`.
