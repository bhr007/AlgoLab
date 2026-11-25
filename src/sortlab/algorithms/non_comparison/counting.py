def counting_sort(values):
    """Stable Counting Sort for integers, including negative integers.

    Time: O(n + k), where k is the integer range. Space: O(n + k).
    """
    items = list(values)
    if not items:
        return []

    if any(not isinstance(value, int) for value in items):
        raise TypeError("counting_sort supports integers only")

    minimum, maximum = min(items), max(items)
    counts = [0] * (maximum - minimum + 1)

    for value in items:
        counts[value - minimum] += 1

    result = []
    for offset, count in enumerate(counts):
        result.extend([offset + minimum] * count)
    return result
