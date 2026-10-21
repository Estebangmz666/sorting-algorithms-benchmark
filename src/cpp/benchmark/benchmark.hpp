
#ifndef BENCHMARK_HPP
#define BENCHMARK_HPP

#include <cstddef>
#include <string>
#include <vector>

using SortFunction = void (*)(std::vector<int>&);

enum class GrowthModel {
    Linear,
    NLogN,
    Quadratic
};

struct BenchmarkConfig {
    std::string algorithmName;
    std::string language;
    SortFunction sortFunction;
    double maxPredictedSeconds = 240.0;
    int repetitions = 5;
};

struct InputVariant {
    std::string name;
    GrowthModel growthModel;
};

void runBenchmarks(
    const BenchmarkConfig& config,
    const std::vector<InputVariant>& variants,
    const std::vector<std::size_t>& sizes
);

#endif