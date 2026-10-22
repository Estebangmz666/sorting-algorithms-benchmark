#include "interpolationSearch.hpp"
#include <cstdint>
// Reference: https://www.geeksforgeeks.org/dsa/interpolation-search/ (iterative version)
int interpolationSearch(const std::vector<int>& array, int key) {
    int low = 0;
    int high = static_cast<int>(array.size()) - 1;
    while (low <= high && key >= array[low] && key <= array[high]) {
        // Equal bounds would divide by zero (also covers low == high).
        if (array[high] == array[low]) return array[low] == key ? low : -1;
        // 64-bit arithmetic: (key - low value) * (high - low) can exceed int.
        const std::int64_t offset =
            static_cast<std::int64_t>(key - array[low]) * (high - low)
            / (array[high] - array[low]);
        const int position = low + static_cast<int>(offset);
        if (array[position] == key) return position;
        if (array[position] < key) low = position + 1;
        else high = position - 1;
    }
    return -1;
}
