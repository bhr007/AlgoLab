import math


def bucket_sort(values, bucket_count=None):
    """Return a sorted copy of finite numeric values using bucket sort.

    This beginner-friendly implementation distributes values between the
    minimum and maximum into buckets, then sorts each bucket with Python's sort.
    Expected performance depends on a reasonably even distribution.
    """
    items = list(values)
    for value in items:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("bucket_sort supports int and float values only")
        if not math.isfinite(value):
            raise ValueError("bucket_sort supports finite numbers only")

    if bucket_count is not None and bucket_count <= 0:
        raise ValueError("bucket_count must be positive")

    if len(items) <= 1:
        return items

    minimum, maximum = min(items), max(items)
    if minimum == maximum:
        return items

    count = len(items) if bucket_count is None else bucket_count
    buckets = [[] for _ in range(count)]
    span = maximum - minimum
    for value in items:
        index = int((value - minimum) / span * (count - 1))
        buckets[index].append(value)

    result = []
    for bucket in buckets:
        result.extend(sorted(bucket))
    return result
