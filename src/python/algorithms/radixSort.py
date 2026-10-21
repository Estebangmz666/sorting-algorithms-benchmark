def radixSort(array):
    base = 10
    passes = 8
    output = [0] * len(array)
    divisor = 1
    for _ in range(passes):
        counts = [0] * base
        for value in array:
            counts[(value // divisor) % base] += 1
        for digit in range(1, base):
            counts[digit] += counts[digit - 1]
        for i in range(len(array) - 1, -1, -1):
            value = array[i]
            digit = (value // divisor) % base
            counts[digit] -= 1
            output[counts[digit]] = value
        array[:] = output
        divisor *= base
