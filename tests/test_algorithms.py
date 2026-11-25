import random
import pytest

from sortlab.algorithms import (
    bubble_sort, bucket_sort, counting_sort, heap_sort, insertion_sort,
    merge_sort, quick_sort, radix_sort, selection_sort, shell_sort,
)

SORTS = [
    bubble_sort, selection_sort, insertion_sort, merge_sort, quick_sort,
    heap_sort, shell_sort, counting_sort, radix_sort,
]


@pytest.mark.parametrize("sort_function", SORTS)
@pytest.mark.parametrize(
    "values",
    [
        [],
        [1],
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [4, 2, 4, 1, 0, -3, 2],
    ],
)
def test_integer_sorts(sort_function, values):
    original = list(values)
    assert sort_function(values) == sorted(values)
    assert values == original


def test_randomized_inputs():
    random.seed(42)
    values = [random.randint(-100, 100) for _ in range(200)]
    for sort_function in SORTS:
        assert sort_function(values) == sorted(values)


def test_bucket_sort():
    values = [0.42, 0.32, 0.23, 0.52, 0.25, 0.47, 0.51]
    assert bucket_sort(values) == sorted(values)


def test_counting_sort_rejects_floats():
    with pytest.raises(TypeError):
        counting_sort([1, 2.5, 3])


def test_radix_sort_rejects_floats():
    with pytest.raises(TypeError):
        radix_sort([1, 2.5, 3])


def test_bucket_sort_rejects_invalid_bucket_count():
    with pytest.raises(ValueError):
        bucket_sort([1, 2, 3], bucket_count=0)
