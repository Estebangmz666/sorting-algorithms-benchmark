def mergeRange(array, buffer, left, middle, right):
    i, j, k = left, middle, left
    while i < middle and j < right:
        if array[i] <= array[j]:
            buffer[k] = array[i]
            i += 1
        else:
            buffer[k] = array[j]
            j += 1
        k += 1
    while i < middle:
        buffer[k] = array[i]
        i += 1
        k += 1
    while j < right:
        buffer[k] = array[j]
        j += 1
        k += 1
    for index in range(left, right):
        array[index] = buffer[index]


def mergeRecursive(array, buffer, left, right):
    if right - left <= 1:
        return
    middle = left + (right - left) // 2
    mergeRecursive(array, buffer, left, middle)
    mergeRecursive(array, buffer, middle, right)
    mergeRange(array, buffer, left, middle, right)


def mergeSort(array):
    if len(array) < 2:
        return
    buffer = [0] * len(array)
    mergeRecursive(array, buffer, 0, len(array))
