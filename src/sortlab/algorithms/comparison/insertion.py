def insertion_sort(values):
    """Return a sorted copy using stable Insertion Sort. O(n²) worst time."""
    items = list(values)
    for index in range(1, len(items)):
        current = items[index]
        position = index
        while position > 0 and items[position - 1] > current:
            items[position] = items[position - 1]
            position -= 1
        items[position] = current
    return items
