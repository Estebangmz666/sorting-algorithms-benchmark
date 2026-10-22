# Reference: https://www.geeksforgeeks.org/dsa/binary-search/ (iterative version)
def binarySearch(array, key):
    low = 0
    high = len(array) - 1
    while low <= high:
        middle = low + (high - low) // 2
        if array[middle] == key:
            return middle
        if array[middle] < key:
            low = middle + 1
        else:
            high = middle - 1
    return -1
