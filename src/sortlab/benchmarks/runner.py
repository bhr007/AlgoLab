"""Small, repeatable timing helper for educational comparisons."""

from statistics import median
from time import perf_counter
from typing import Callable, Iterable


def benchmark(sort_function: Callable, values: Iterable, repeats=5):
    """Return median runtime in seconds for sorting a fresh copy of values."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")

    source = list(values)
    timings = []
    for _ in range(repeats):
        sample = list(source)
        start = perf_counter()
        result = sort_function(sample)
        elapsed = perf_counter() - start
        if list(result) != sorted(source):
            raise ValueError("The supplied function did not correctly sort the input")
        timings.append(elapsed)

    return {
        "algorithm": getattr(sort_function, "__name__", repr(sort_function)),
        "input_size": len(source),
        "repeats": repeats,
        "median_seconds": median(timings),
        "all_seconds": timings,
    }
