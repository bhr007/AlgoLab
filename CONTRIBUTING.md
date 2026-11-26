# Contributing to SortLab

Thanks for considering a contribution! SortLab aims to be a welcoming, beginner-friendly reference for sorting and graph algorithms.

## Ways to contribute

- Add or improve a sorting or graph algorithm implementation.
- Add tests for edge cases (disconnected graphs, negative cycles, duplicates, etc.).
- Improve explanations, examples, or complexity notes.
- Add or improve a Matplotlib visualization.
- Improve benchmarks, CLI usability, or developer tooling.

## Development setup

```bash
git clone https://github.com/bhr007/sortlab.git
cd sortlab
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,visualization]"
pytest
```

## Algorithm contribution checklist

### Sorting algorithms
Every sorting algorithm contribution should:

1. Use a descriptive filename and function name in `src/sortlab/algorithms/`.
2. Include a docstring explaining the algorithm and its time/space complexity.
3. Avoid modifying the caller's input unless the function explicitly documents in-place behavior.
4. Handle empty and single-element inputs.
5. Include tests for duplicates, negative values where supported, sorted input, reverse-sorted input, and randomized input.
6. Be exported from `src/sortlab/algorithms/__init__.py` and registered in `src/sortlab/core/registry.py`.
7. Include a `SortEvent` generator in `src/sortlab/core/runner.py`.

### Graph algorithms
Every graph algorithm contribution should:

1. Keep the pure implementation in `src/sortlab/graphs/algorithms/` completely independent of Matplotlib.
2. Document graph constraints (directed/undirected, weight constraints, DAG/cycle handling) and time/space complexities in the docstring and `docs/GRAPH_ALGORITHMS.md`.
3. Never mutate the input `Graph` object.
4. Handle empty graphs, single-node graphs, disconnected graphs, and constraint errors cleanly.
5. Emit standardized, JSON-serializable `GraphEvent` objects in `src/sortlab/graphs/runner.py` and register metadata in `src/sortlab/graphs/registry.py`.
6. Include unit tests for algorithm correctness, constraints, event ordering, and headless Matplotlib visualization.

## Code style

- Prefer readable, beginner-friendly Python.
- Add type hints.
- Keep dependencies optional where possible (avoid adding mandatory third-party packages like NetworkX).
- Run `ruff check .` (or check modified/new files) and `pytest` before submitting.
- Explain non-obvious implementation choices in comments.

## Pull requests

Keep pull requests focused. Describe what changed, why it is useful, and how it was tested. For new algorithms, include authoritative references when practical.

## Code of conduct

Be respectful, constructive, and welcoming. Critique code and ideas, not people.
