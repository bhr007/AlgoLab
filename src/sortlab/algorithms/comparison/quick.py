def quick_sort(values):
    """Return a sorted copy using recursive Quick Sort.

    Average time: O(n log n); worst time: O(n²). This simple educational
    implementation uses a middle pivot and creates new partitions.
    """
    items = list(values)
    if len(items) <= 1:
        return items

    pivot = items[len(items) // 2]
    lower = [item for item in items if item < pivot]
    equal = [item for item in items if item == pivot]
    upper = [item for item in items if item > pivot]
    return quick_sort(lower) + equal + quick_sort(upper)
