#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <vector>
#include "../src/cpp/algorithms/insertionSort.hpp"
#include "../src/cpp/algorithms/mergeSort.hpp"
#include "../src/cpp/algorithms/heapSort.hpp"
#include "../src/cpp/algorithms/dualPivotQuickSort.hpp"
#include "../src/cpp/algorithms/radixSort.hpp"
#include "../src/cpp/algorithms/bucketSort.hpp"

int main() {
    using SortFunction = void (*)(std::vector<int>&);
    std::vector<std::pair<const char*, SortFunction>> algorithms = {
        {"insertionSort", insertionSort}, {"mergeSort", mergeSort},
        {"heapSort", heapSort}, {"dualPivotQuickSort", dualPivotQuickSort},
        {"radixSort", radixSort}, {"bucketSort", bucketSort}
    };
    std::mt19937 generator(12345);
    std::uniform_int_distribution<int> distribution(10000000, 99999999);
    std::vector<std::vector<int>> cases = {{}, {10000000}, {99999999,10000000},
        {10000000,10000000,10000000}, {99999999,10000000,10000000,99999999}};
    for (int n : {2, 10, 100, 1000}) {
        std::vector<int> sample(n);
        for (int& value : sample) value = distribution(generator);
        cases.push_back(sample);
        std::sort(sample.begin(), sample.end());
        cases.push_back(sample);
        std::reverse(sample.begin(), sample.end());
        cases.push_back(sample);
    }
    for (auto [name, sortFunction] : algorithms) {
        for (auto original : cases) {
            std::vector<int> expected = original;
            std::sort(expected.begin(), expected.end());
            sortFunction(original);
            if (original != expected) { std::cerr << "FAILED: " << name << '\n'; return 1; }
        }
        std::cout << "PASS: " << name << '\n';
    }
    return 0;
}
