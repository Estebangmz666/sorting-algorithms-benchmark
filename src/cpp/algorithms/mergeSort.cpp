
#include "mergeSort.hpp"

#include <cstddef>
#include <vector>

namespace {

void merge(
    std::vector<int>& array,
    std::vector<int>& buffer,
    std::size_t left,
    std::size_t middle,
    std::size_t right
) {
    std::size_t i = left;
    std::size_t j = middle;
    std::size_t k = left;

    while (i < middle && j < right) {
        if (array[i] <= array[j]) {
            buffer[k++] = array[i++];
        } else {
            buffer[k++] = array[j++];
        }
    }

    while (i < middle) {
        buffer[k++] = array[i++];
    }

    while (j < right) {
        buffer[k++] = array[j++];
    }

    for (std::size_t index = left; index < right; ++index) {
        array[index] = buffer[index];
    }
}

void mergeSortRecursive(
    std::vector<int>& array,
    std::vector<int>& buffer,
    std::size_t left,
    std::size_t right
) {
    if (right - left <= 1) {
        return;
    }

    std::size_t middle = left + (right - left) / 2;

    mergeSortRecursive(array, buffer, left, middle);
    mergeSortRecursive(array, buffer, middle, right);

    merge(array, buffer, left, middle, right);
}

} // namespace

void mergeSort(std::vector<int>& array) {
    if (array.size() < 2) {
        return;
    }

    std::vector<int> buffer(array.size());

    mergeSortRecursive(
        array,
        buffer,
        0,
        array.size()
    );
}