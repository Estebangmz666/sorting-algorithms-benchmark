
#include <exception>
#include <iostream>
#include <string>
#include <vector>

#include "algorithms/insertionSort.hpp"
#include "algorithms/mergeSort.hpp"
#include "algorithms/heapSort.hpp"
#include "algorithms/dualPivotQuickSort.hpp"
#include "algorithms/radixSort.hpp"
#include "algorithms/bucketSort.hpp"

#include "benchmark/benchmark.hpp"

int main() {
    const std::vector<std::size_t> sizes = {
        1'000,
        10'000,
        100'000,
        1'000'000
    };

    const std::vector<InputVariant> quadraticVariants = {
        {"random", GrowthModel::Quadratic},
        {"ascending", GrowthModel::Linear},
        {"descending", GrowthModel::Quadratic}
    };

    const std::vector<InputVariant> nLogNVariants = {
        {"random", GrowthModel::NLogN},
        {"ascending", GrowthModel::NLogN},
        {"descending", GrowthModel::NLogN}
    };

    const std::vector<InputVariant> dualPivotVariants = {
        {"random", GrowthModel::NLogN},
        {"ascending", GrowthModel::Quadratic},
        {"descending", GrowthModel::Quadratic}
    };

    const std::vector<InputVariant> linearVariants = {
        {"random", GrowthModel::Linear},
        {"ascending", GrowthModel::Linear},
        {"descending", GrowthModel::Linear}
    };

    struct AlgorithmEntry {
        BenchmarkConfig config;
        std::vector<InputVariant> variants;
    };

    const std::vector<AlgorithmEntry> algorithms = {
        {
            {"InsertionSort", "C++", insertionSort, 240.0, 5},
            quadraticVariants
        },
        {
            {"MergeSort", "C++", mergeSort, 240.0, 5},
            nLogNVariants
        },
        {
            {"HeapSort", "C++", heapSort, 240.0, 5},
            nLogNVariants
        },
        {
            {"DualPivotQuickSort", "C++",
             dualPivotQuickSort, 240.0, 5},
            dualPivotVariants
        },
        {
            {"RadixSort", "C++", radixSort, 240.0, 5},
            linearVariants
        },
        {
            {"BucketSort", "C++", bucketSort, 240.0, 5},
            quadraticVariants
        }
    };

    std::cout << "====================================\n";
    std::cout << "SORTING ALGORITHMS - C++ BENCHMARK\n";
    std::cout << "Algorithms: " << algorithms.size() << "\n";
    std::cout << "Repetitions: 5\n";
    std::cout << "====================================\n";

    int failedAlgorithms = 0;

    for (const auto& algorithm : algorithms) {
        std::cout << "\n------------------------------------\n";
        std::cout << "Running: "
                  << algorithm.config.algorithmName << "\n";
        std::cout << "------------------------------------\n";

        try {
            runBenchmarks(
                algorithm.config,
                algorithm.variants,
                sizes
            );
        } catch (const std::exception& error) {
            ++failedAlgorithms;

            std::cerr << "FAILED: "
                      << algorithm.config.algorithmName
                      << " - " << error.what() << "\n";
        }
    }

    std::cout << "\n====================================\n";
    std::cout << "BENCHMARK FINISHED\n";
    std::cout << "Failed algorithms: "
              << failedAlgorithms << "\n";
    std::cout << "====================================\n";

    return failedAlgorithms == 0 ? 0 : 1;
}
