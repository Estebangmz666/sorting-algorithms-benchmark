# Reference: https://www.geeksforgeeks.org/dsa/exponential-search/
def boundedBinarySearch(array, low, high, key):
    while low <= high:
        middle = low + (high - low) // 2
        if array[middle] == key:
            return middle
        if array[middle] < key:
            low = middle + 1
        else:
            high = middle - 1
    return -1


def exponentialSearch(array, key):
    n = len(array)
    if n == 0:
        return -1
    if array[0] == key:
        return 0
    # Double the bound until it passes the key or the end of the array.
    bound = 1
    while bound < n and array[bound] <= key:
        bound *= 2
    return boundedBinarySearch(array, bound // 2, min(bound, n - 1), key)
