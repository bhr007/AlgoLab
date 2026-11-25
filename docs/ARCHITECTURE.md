# Architecture

SortLab separates four concerns:

1. **Algorithms:** plain Python functions that accept an iterable and return a sorted list.
2. **Core events:** renderer-independent events describing operations and snapshots.
3. **Visualization:** optional frontends that turn events into animations.
4. **Benchmarks:** helpers that measure elapsed time and validate output.

This separation is intentional. A future web client can consume a serialized event format without importing Matplotlib. The current event API is an initial foundation and may be refined as more algorithms gain event support.

## Input and mutation policy

Public sorting functions return a new list and do not mutate the supplied iterable. Some algorithms require particular input types; their docstrings and tests define those constraints.
