def shell_sort(values):
    """Return a sorted copy using Shell Sort with halving gaps.

    Complexity depends on the gap sequence; this implementation is commonly
    described as O(n²) worst case with the halving sequence.
    """
    items = list(values)
    gap = len(items) // 2
    while gap > 0:
        for index in range(gap, len(items)):
            current = items[index]
            position = index
            while position >= gap and items[position - gap] > current:
                items[position] = items[position - gap]
                position -= gap
            items[position] = current
        gap //= 2
    return items
