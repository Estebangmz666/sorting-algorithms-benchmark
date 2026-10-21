#include "heapSort.hpp"
#include <algorithm>
#include <cstddef>
namespace {
void siftDown(std::vector<int>& array, std::size_t root, std::size_t heapSize) {
    while (root < heapSize / 2) {
        std::size_t child = 2 * root + 1;
        if (child >= heapSize) break;
        if (child + 1 < heapSize && array[child] < array[child + 1]) ++child;
        if (array[root] >= array[child]) break;
        std::swap(array[root], array[child]);
        root = child;
    }
}
}
void heapSort(std::vector<int>& array) {
    const std::size_t n = array.size();
    for (std::size_t start = n / 2; start > 0; --start)
        siftDown(array, start - 1, n);
    for (std::size_t end = n; end > 1; --end) {
        std::swap(array[0], array[end - 1]);
        siftDown(array, 0, end - 1);
    }
}
