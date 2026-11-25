from sortlab.algorithms import bubble_sort, insertion_sort, merge_sort, quick_sort
from sortlab.benchmarks import benchmark

if __name__ == "__main__":
    data = list(range(1500, 0, -1))
    for algorithm in (insertion_sort, merge_sort, quick_sort, bubble_sort):
        result = benchmark(algorithm, data, repeats=3)
        print(f"{result['algorithm']:>14}: {result['median_seconds']:.6f}s")
