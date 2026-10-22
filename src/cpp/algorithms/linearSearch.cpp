#include "linearSearch.hpp"
// Reference: https://www.geeksforgeeks.org/dsa/linear-search/
int linearSearch(const std::vector<int>& array, int key) {
    const int n = static_cast<int>(array.size());
    for (int i = 0; i < n; ++i) {
        if (array[i] == key) return i;
    }
    return -1;
}
