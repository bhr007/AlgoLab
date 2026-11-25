def selection_sort(values):
    """Return a sorted copy using Selection Sort. O(n²) time, O(1) extra space."""
    items = list(values)
    for start in range(len(items)):
        smallest = start
        for index in range(start + 1, len(items)):
            if items[index] < items[smallest]:
                smallest = index
        if smallest != start:
            items[start], items[smallest] = items[smallest], items[start]
    return items
