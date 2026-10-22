#include "binarySearch.hpp"
// Reference: https://www.geeksforgeeks.org/dsa/binary-search/ (iterative version)
int binarySearch(const std::vector<int>& array, int key) {
    int low = 0;
    int high = static_cast<int>(array.size()) - 1;
    while (low <= high) {
        int middle = low + (high - low) / 2;
        if (array[middle] == key) return middle;
        if (array[middle] < key) low = middle + 1;
        else high = middle - 1;
    }
    return -1;
}
