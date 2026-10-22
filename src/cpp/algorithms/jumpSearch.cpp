#include "jumpSearch.hpp"
#include <algorithm>
#include <cmath>
// Reference: https://www.geeksforgeeks.org/dsa/jump-search/
int jumpSearch(const std::vector<int>& array, int key) {
    const int n = static_cast<int>(array.size());
    if (n == 0) return -1;
    const int blockSize = std::max(1, static_cast<int>(std::sqrt(static_cast<double>(n))));
    int step = blockSize;
    int previous = 0;

    // Jump block by block until the last element of the block is >= key.
    while (array[std::min(step, n) - 1] < key) {
        previous = step;
        step += blockSize;
        if (previous >= n) return -1;
    }

    // Linear scan inside the selected block.
    while (array[previous] < key) {
        ++previous;
        if (previous == std::min(step, n)) return -1;
    }
    return array[previous] == key ? previous : -1;
}
