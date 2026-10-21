#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "../algorithms/insertionSort.hpp"
#include "../algorithms/mergeSort.hpp"
#include "../algorithms/heapSort.hpp"
#include "../algorithms/dualPivotQuickSort.hpp"
#include "../algorithms/radixSort.hpp"
#include "../algorithms/bucketSort.hpp"

namespace fs = std::filesystem;
using SortFunction = void (*)(std::vector<int>&);

SortFunction getAlgorithm(const std::string& name) {
    if (name == "InsertionSort") return insertionSort;
    if (name == "MergeSort") return mergeSort;
    if (name == "HeapSort") return heapSort;
    if (name == "DualPivotQuickSort") return dualPivotQuickSort;
    if (name == "RadixSort") return radixSort;
    if (name == "BucketSort") return bucketSort;
    throw std::invalid_argument("Unknown algorithm: " + name);
}

int main(int argc, char* argv[]) {
    try {
        if (argc != 4) {
            throw std::invalid_argument("Usage: benchmarkWorker.exe ALGORITHM DATASET.txt EXPECTED_COUNT");
        }
        const std::string algorithmName = argv[1];
        const fs::path datasetPath = argv[2];
        const std::size_t expectedCount = std::stoull(argv[3]);
        const SortFunction sortFunction = getAlgorithm(algorithmName);
        std::ifstream input(datasetPath);
        if (!input) throw std::runtime_error("Cannot read " + datasetPath.string());

        std::vector<int> original;
        original.reserve(expectedCount);
        int value;
        while (input >> value) original.push_back(value);
        if (!input.eof() || original.size() != expectedCount) {
            throw std::runtime_error("Invalid input size or unreadable number");
        }

        std::vector<int> expected = original;
        std::sort(expected.begin(), expected.end());
        std::vector<int> working = original;

        const auto start = std::chrono::steady_clock::now();
        sortFunction(working);
        const auto end = std::chrono::steady_clock::now();

        if (working != expected) throw std::runtime_error("Incorrect sorting result");
        const auto elapsedNs = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        std::cout << elapsedNs << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR: " << error.what() << '\n';
        return 1;
    }
}
