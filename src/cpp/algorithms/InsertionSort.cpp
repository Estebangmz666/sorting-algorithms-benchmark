
#include "insertionSort.hpp"

// Function definition
void insertionSort(std::vector<int>& array) {
    for (std::size_t i = 1; i < array.size(); ++i) {
        int key = array[i];
        std::size_t j = i;

        while (j > 0 && array[j - 1] > key) {
            array[j] = array[j - 1];
            --j;
        }

        array[j] = key;
    }
}
