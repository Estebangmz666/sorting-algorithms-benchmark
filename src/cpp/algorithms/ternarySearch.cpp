#include "ternarySearch.hpp"
// Reference: https://www.geeksforgeeks.org/dsa/ternary-search/ (iterative version)
int ternarySearch(const std::vector<int>& array, int key) {
    int left = 0;
    int right = static_cast<int>(array.size()) - 1;
    while (left <= right) {
        int middle1 = left + (right - left) / 3;
        int middle2 = right - (right - left) / 3;
        if (array[middle1] == key) return middle1;
        if (array[middle2] == key) return middle2;
        if (key < array[middle1]) right = middle1 - 1;
        else if (key > array[middle2]) left = middle2 + 1;
        else {
            left = middle1 + 1;
            right = middle2 - 1;
        }
    }
    return -1;
}
