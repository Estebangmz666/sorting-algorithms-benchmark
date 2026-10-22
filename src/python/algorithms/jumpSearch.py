import math


# Reference: https://www.geeksforgeeks.org/dsa/jump-search/
def jumpSearch(array, key):
    n = len(array)
    if n == 0:
        return -1
    blockSize = max(1, int(math.sqrt(n)))
    step = blockSize
    previous = 0

    # Jump block by block until the last element of the block is >= key.
    while array[min(step, n) - 1] < key:
        previous = step
        step += blockSize
        if previous >= n:
            return -1

    # Linear scan inside the selected block.
    while array[previous] < key:
        previous += 1
        if previous == min(step, n):
            return -1
    return previous if array[previous] == key else -1
