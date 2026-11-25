def bubble_sort(values):
    """Return a sorted copy using Bubble Sort. Stable; O(n²) worst time."""
    items = list(values)
    for end in range(len(items) - 1, 0, -1):
        swapped = False
        for index in range(end):
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]
                swapped = True
        if not swapped:
            break
    return items
