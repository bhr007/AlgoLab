def bucket_sort(values, bucket_count=None):
    """Return a sorted copy of finite numeric values using bucket sort.

    This beginner-friendly implementation distributes values between the
    minimum and maximum into buckets, then sorts each bucket with Python's sort.
    Expected performance depends on a reasonably even distribution.
    """
    items = list(values)
    if len(items) <= 1:
        return items
    if any(not isinstance(value, (int, float)) for value in items):
        raise TypeError("bucket_sort supports int and float values only")

    minimum, maximum = min(items), max(items)
    if minimum == maximum:
        return items

    count = len(items) if bucket_count is None else bucket_count
    if count <= 0:
        raise ValueError("bucket_count must be positive")

    buckets = [[] for _ in range(count)]
    span = maximum - minimum
    for value in items:
        index = int((value - minimum) / span * (count - 1))
        buckets[index].append(value)

    result = []
    for bucket in buckets:
        result.extend(sorted(bucket))
    return result
