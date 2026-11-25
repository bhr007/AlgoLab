def heap_sort(values):
    """Return a sorted copy using Heap Sort. O(n log n) time, O(1) auxiliary space
    apart from the copied input.
    """
    items = list(values)
    size = len(items)

    def sift_down(root, end):
        while True:
            child = 2 * root + 1
            if child >= end:
                return
            if child + 1 < end and items[child] < items[child + 1]:
                child += 1
            if items[root] >= items[child]:
                return
            items[root], items[child] = items[child], items[root]
            root = child

    for root in range(size // 2 - 1, -1, -1):
        sift_down(root, size)

    for end in range(size - 1, 0, -1):
        items[0], items[end] = items[end], items[0]
        sift_down(0, end)

    return items
