# Reference: https://www.geeksforgeeks.org/dsa/interpolation-search/ (iterative version)
def interpolationSearch(array, key):
    low = 0
    high = len(array) - 1
    while low <= high and array[low] <= key <= array[high]:
        # Equal bounds would divide by zero (also covers low == high).
        if array[high] == array[low]:
            return low if array[low] == key else -1
        position = low + (key - array[low]) * (high - low) // (array[high] - array[low])
        if array[position] == key:
            return position
        if array[position] < key:
            low = position + 1
        else:
            high = position - 1
    return -1
