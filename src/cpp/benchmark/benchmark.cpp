
#include "benchmark.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace fs = std::filesystem;

namespace {

constexpr double NANOSECONDS_PER_MILLISECOND = 1'000'000.0;
constexpr double NANOSECONDS_PER_SECOND = 1'000'000'000.0;

std::string formatSize(std::size_t size) {
    std::string value = std::to_string(size);

    for (int index = static_cast<int>(value.size()) - 3;
         index > 0; index -= 3) {
        value.insert(index, "_");
    }

    return value;
}

std::vector<int> loadData(
    std::size_t size,
    const std::string& variant
) {
    fs::path path = fs::path("datosYGen") / "data"
        / formatSize(size)
        / (variant + "_" + std::to_string(size) + ".txt");

    std::ifstream file(path);

    if (!file) {
        throw std::runtime_error(
            "Cannot open dataset: " + path.string()
        );
    }

    std::vector<int> numbers;
    numbers.reserve(size);

    int value;

    while (file >> value) {
        numbers.push_back(value);
    }

    if (!file.eof() || numbers.size() != size) {
        throw std::runtime_error(
            "Invalid dataset: " + path.string()
        );
    }

    return numbers;
}

double growthValue(std::size_t size, GrowthModel model) {
    double n = static_cast<double>(size);

    switch (model) {
        case GrowthModel::Linear:
            return n;

        case GrowthModel::NLogN:
            return n * std::log2(n);

        case GrowthModel::Quadratic:
            return n * n;
    }

    throw std::runtime_error("Unknown growth model");
}

double predictMilliseconds(
    double referenceMilliseconds,
    std::size_t referenceSize,
    std::size_t targetSize,
    GrowthModel model
) {
    return referenceMilliseconds
        * growthValue(targetSize, model)
        / growthValue(referenceSize, model);
}

double calculateMean(const std::vector<double>& times) {
    double total = std::accumulate(
        times.begin(), times.end(), 0.0
    );

    return total / times.size();
}

double calculateStdDev(
    const std::vector<double>& times,
    double mean
) {
    if (times.size() < 2) {
        return 0.0;
    }

    double sum = 0.0;

    for (double time : times) {
        double difference = time - mean;
        sum += difference * difference;
    }

    return std::sqrt(sum / (times.size() - 1));
}

void writeResult(
    std::ofstream& file,
    const BenchmarkConfig& config,
    const std::string& variant,
    std::size_t size,
    const std::vector<double>& times,
    double average,
    double stdDev,
    bool estimated,
    const std::string& method
) {
    file << config.algorithmName << ","
         << config.language << ","
         << variant << ","
         << size << ",";

    for (int index = 0; index < 5; ++index) {
        if (index < static_cast<int>(times.size())) {
            file << times[index];
        }

        file << ",";
    }

    file << average << ",";

    if (!estimated) {
        file << stdDev;
    }

    file << ","
         << (estimated ? "estimated" : "measured")
         << "," << method << "\n";
}

} // namespace

void runBenchmarks(
    const BenchmarkConfig& config,
    const std::vector<InputVariant>& variants,
    const std::vector<std::size_t>& sizes
) {
    if (config.repetitions != 5) {
        throw std::runtime_error(
            "This CSV schema requires five repetitions"
        );
    }

    fs::create_directories("results");

    fs::path outputPath = "results/results_cpp.csv";

    bool writeHeader = !fs::exists(outputPath)
        || fs::file_size(outputPath) == 0;

    std::ofstream output(outputPath, std::ios::app);

    if (!output) {
        throw std::runtime_error("Cannot open results CSV");
    }

    output << std::fixed << std::setprecision(6);

    if (writeHeader) {
        output
            << "algorithm,language,variant,n,"
            << "repeat1_ms,repeat2_ms,repeat3_ms,"
            << "repeat4_ms,repeat5_ms,"
            << "average_ms,stdDev_ms,status,method\n";
    }

    for (const InputVariant& variant : variants) {
        std::size_t referenceSize = 0;
        double referenceAverage = 0.0;

        std::cout << "\nVariant: " << variant.name << "\n";

        for (std::size_t size : sizes) {
            double predictedMs = 0.0;

            if (referenceSize > 0) {
                predictedMs = predictMilliseconds(
                    referenceAverage,
                    referenceSize,
                    size,
                    variant.growthModel
                );
            }

            if (
                referenceSize > 0 &&
                predictedMs / 1000.0 >
                    config.maxPredictedSeconds
            ) {
                std::cout << "n=" << size
                          << " | ESTIMATED | "
                          << predictedMs << " ms\n";

                writeResult(
                    output, config, variant.name, size,
                    {}, predictedMs, 0.0, true,
                    "theoretical_extrapolation"
                );

                continue;
            }

            std::vector<int> original = loadData(
                size, variant.name
            );

            std::vector<int> expected = original;
            std::sort(expected.begin(), expected.end());

            std::vector<double> times;
            times.reserve(config.repetitions);

            for (int run = 0; run < config.repetitions; ++run) {
                // Copy is excluded from the measurement.
                std::vector<int> working = original;

                auto start = std::chrono::steady_clock::now();

                config.sortFunction(working);

                auto end = std::chrono::steady_clock::now();

                // Verification is excluded from the measurement.
                if (working != expected) {
                    throw std::runtime_error(
                        "Sorting verification failed"
                    );
                }

                auto elapsedNs =
                    std::chrono::duration_cast<
                        std::chrono::nanoseconds
                    >(end - start).count();

                double elapsedMs =
                    elapsedNs / NANOSECONDS_PER_MILLISECOND;

                times.push_back(elapsedMs);
            }

            double average = calculateMean(times);
            double stdDev = calculateStdDev(times, average);

            writeResult(
                output, config, variant.name, size,
                times, average, stdDev, false,
                "five_executions"
            );

            std::cout << "n=" << size
                      << " | MEASURED | "
                      << average << " ms"
                      << " | SD=" << stdDev << " ms\n";

            referenceSize = size;
            referenceAverage = average;
        }
    }

    std::cout << "\nResults saved: "
              << outputPath.string() << "\n";
}