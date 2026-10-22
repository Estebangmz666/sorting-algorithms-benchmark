# Reference: https://www.geeksforgeeks.org/dsa/ternary-search/ (iterative version)
def ternarySearch(array, key):
    left = 0
    right = len(array) - 1
    while left <= right:
        middle1 = left + (right - left) // 3
        middle2 = right - (right - left) // 3
        if array[middle1] == key:
            return middle1
        if array[middle2] == key:
            return middle2
        if key < array[middle1]:
            right = middle1 - 1
        elif key > array[middle2]:
            left = middle2 + 1
        else:
            left = middle1 + 1
            right = middle2 - 1
    return -1
