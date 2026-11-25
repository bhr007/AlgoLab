def radix_sort(values):
    """Stable LSD Radix Sort for integers, including negative integers.

    Time: O(d(n + b)) for d digits and base b=10. Returns a new list.
    """
    items = list(values)
    if any(not isinstance(value, int) for value in items):
        raise TypeError("radix_sort supports integers only")
    if not items:
        return []

    def sort_non_negative(numbers):
        exp = 1
        maximum = max(numbers, default=0)
        while maximum // exp > 0:
            output = [0] * len(numbers)
            counts = [0] * 10
            for number in numbers:
                counts[(number // exp) % 10] += 1
            for index in range(1, 10):
                counts[index] += counts[index - 1]
            for number in reversed(numbers):
                digit = (number // exp) % 10
                counts[digit] -= 1
                output[counts[digit]] = number
            numbers = output
            exp *= 10
        return numbers

    negatives = [-value for value in items if value < 0]
    non_negatives = [value for value in items if value >= 0]
    sorted_negatives = sort_non_negative(negatives)
    return [-value for value in reversed(sorted_negatives)] + sort_non_negative(non_negatives)
