#include "exponentialSearch.hpp"
#include <algorithm>
// Reference: https://www.geeksforgeeks.org/dsa/exponential-search/
namespace {
int boundedBinarySearch(const std::vector<int>& array, int low, int high, int key) {
    while (low <= high) {
        int middle = low + (high - low) / 2;
        if (array[middle] == key) return middle;
        if (array[middle] < key) low = middle + 1;
        else high = middle - 1;
    }
    return -1;
}
}
int exponentialSearch(const std::vector<int>& array, int key) {
    const int n = static_cast<int>(array.size());
    if (n == 0) return -1;
    if (array[0] == key) return 0;
    // Double the bound until it passes the key or the end of the array.
    int bound = 1;
    while (bound < n && array[bound] <= key) bound *= 2;
    return boundedBinarySearch(array, bound / 2, std::min(bound, n - 1), key);
}
