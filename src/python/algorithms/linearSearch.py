# Reference: https://www.geeksforgeeks.org/dsa/linear-search/
def linearSearch(array, key):
    for i in range(len(array)):
        if array[i] == key:
            return i
    return -1
