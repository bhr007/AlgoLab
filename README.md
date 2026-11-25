# SortLab

**Explore. Visualize. Understand Sorting.**

SortLab is an educational, open-source reference library for sorting algorithms. It brings together readable Python implementations, step-by-step visualizations, performance benchmarks, and beginner-friendly documentation.

> **Project status:** Early development (v0.1.0). APIs may evolve before the first stable release.

## What is included?

- Clear implementations of common sorting algorithms.
- A shared event format for explaining algorithm operations.
- Optional Matplotlib visualizations.
- Simple benchmarking utilities.
- Automated correctness tests and contribution guidelines.

## Quick start

```bash
git clone https://github.com/YOUR-USERNAME/sortlab.git
cd sortlab
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -e ".[dev,visualization]"
```

Run an algorithm:

```python
from sortlab.algorithms import bubble_sort, merge_sort

numbers = [8, 3, 5, 1, 9, 2]
print(bubble_sort(numbers))
print(merge_sort(numbers))
```

Run a local visualization:

```bash
python examples/visualize_bubble_sort.py
```

Run the tests:

```bash
pytest
```

## Algorithm collection

| Algorithm | Category | Stable | Typical time |
|---|---|---:|---:|
| Bubble Sort | Comparison | Yes | O(n²) |
| Selection Sort | Comparison | No | O(n²) |
| Insertion Sort | Comparison | Yes | O(n²) |
| Merge Sort | Divide and conquer | Yes | O(n log n) |
| Quick Sort | Divide and conquer | Usually no | O(n log n) average |
| Heap Sort | Comparison | No | O(n log n) |
| Shell Sort | Comparison | No | Depends on gap sequence |
| Counting Sort | Non-comparison | Yes, in this implementation | O(n + k) |
| Radix Sort | Non-comparison | Yes, in this implementation | O(d(n + b)) |
| Bucket Sort | Distribution-based | Depends on bucket sort | Expected linear under assumptions |

Complexities and properties depend on implementation details and input assumptions. See each algorithm's documentation.

## Design principles

1. **Readable first:** implementations should be approachable to learners.
2. **Correctness matters:** every algorithm should have automated tests.
3. **One shared event model:** visualizers should not need algorithm-specific rendering code.
4. **Honest benchmarks:** results are measurements, not universal rankings.
5. **Contributions welcome:** follow `CONTRIBUTING.md`.

## Roadmap

- [x] Initial package structure and development tooling
- [x] Ten foundational sorting algorithms
- [x] Shared visualization event model
- [x] Optional Matplotlib visualizer
- [x] Basic benchmark utilities
- [ ] More algorithms and edge-case documentation
- [ ] Richer visualizations and algorithm comparisons
- [ ] Browser-based interactive playground (future direction)

## License

SortLab is released under the [MIT License](LICENSE).

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.
