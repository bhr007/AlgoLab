from sortlab.algorithms import insertion_sort
from sortlab.benchmarks import benchmark


def test_benchmark_result():
    result = benchmark(insertion_sort, [4, 1, 3, 2], repeats=2)
    assert result["input_size"] == 4
    assert result["repeats"] == 2
    assert result["median_seconds"] >= 0
