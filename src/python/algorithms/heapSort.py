def siftDown(array, root, heapSize):
    while root < heapSize // 2:
        child = 2 * root + 1
        if child >= heapSize:
            break
        if child + 1 < heapSize and array[child] < array[child + 1]:
            child += 1
        if array[root] >= array[child]:
            break
        array[root], array[child] = array[child], array[root]
        root = child


def heapSort(array):
    n = len(array)
    for start in range(n // 2, 0, -1):
        siftDown(array, start - 1, n)
    for end in range(n, 1, -1):
        array[0], array[end - 1] = array[end - 1], array[0]
        siftDown(array, 0, end - 1)
