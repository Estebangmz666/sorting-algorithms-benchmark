#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "../algorithms/linearSearch.hpp"
#include "../algorithms/binarySearch.hpp"
#include "../algorithms/ternarySearch.hpp"
#include "../algorithms/jumpSearch.hpp"
#include "../algorithms/interpolationSearch.hpp"
#include "../algorithms/exponentialSearch.hpp"

namespace fs = std::filesystem;
using SearchFunction = int (*)(const std::vector<int>&, int);

constexpr std::size_t SEARCH_COUNT = 1000;

SearchFunction getAlgorithm(const std::string& name) {
    if (name == "LinearSearch") return linearSearch;
    if (name == "BinarySearch") return binarySearch;
    if (name == "TernarySearch") return ternarySearch;
    if (name == "JumpSearch") return jumpSearch;
    if (name == "InterpolationSearch") return interpolationSearch;
    if (name == "ExponentialSearch") return exponentialSearch;
    throw std::invalid_argument("Unknown algorithm: " + name);
}

std::vector<int> readNumbers(const fs::path& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("Cannot read " + path.string());
    std::vector<int> numbers;
    int value;
    while (input >> value) numbers.push_back(value);
    if (!input.eof()) throw std::runtime_error("Unreadable number in " + path.string());
    return numbers;
}

// keys: the 1000 keys of keys_<n>.txt. start/center/end: the matching key of
// position_keys_<n>.txt repeated 1000 times.
std::vector<int> buildKeys(const fs::path& keysPath, const std::string& mode) {
    std::vector<int> fileKeys = readNumbers(keysPath);
    if (mode == "keys") {
        if (fileKeys.size() != SEARCH_COUNT) throw std::runtime_error("Expected 1000 keys");
        return fileKeys;
    }
    if (fileKeys.size() != 3) throw std::runtime_error("Expected 3 position keys");
    std::size_t index;
    if (mode == "start") index = 0;
    else if (mode == "center") index = 1;
    else if (mode == "end") index = 2;
    else throw std::invalid_argument("Unknown mode: " + mode);
    return std::vector<int>(SEARCH_COUNT, fileKeys[index]);
}

int main(int argc, char* argv[]) {
    try {
        if (argc != 6) {
            throw std::invalid_argument(
                "Usage: searchWorker.exe ALGORITHM ASCENDING.txt KEYS.txt EXPECTED_COUNT MODE");
        }
        const std::string algorithmName = argv[1];
        const SearchFunction searchFunction = getAlgorithm(algorithmName);
        const std::vector<int> array = readNumbers(argv[2]);
        const std::size_t expectedCount = std::stoull(argv[4]);
        const std::vector<int> keys = buildKeys(argv[3], argv[5]);

        if (array.size() != expectedCount || !std::is_sorted(array.begin(), array.end())) {
            throw std::runtime_error("Dataset must contain EXPECTED_COUNT ascending values");
        }

        // Results are stored so the compiler cannot discard the searches.
        std::vector<int> results(keys.size());

        const auto start = std::chrono::steady_clock::now();
        for (std::size_t i = 0; i < keys.size(); ++i) {
            results[i] = searchFunction(array, keys[i]);
        }
        const auto end = std::chrono::steady_clock::now();

        // Verification is excluded from the measurement.
        std::size_t found = 0;
        for (std::size_t i = 0; i < keys.size(); ++i) {
            const bool present = std::binary_search(array.begin(), array.end(), keys[i]);
            const int index = results[i];
            if (present) {
                if (index < 0 || array[index] != keys[i]) {
                    throw std::runtime_error("Present key not found: " + std::to_string(keys[i]));
                }
                ++found;
            } else if (index != -1) {
                throw std::runtime_error("Absent key reported as found: " + std::to_string(keys[i]));
            }
        }

        const auto elapsedNs = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        std::cout << elapsedNs << ' ' << found << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR: " << error.what() << '\n';
        return 1;
    }
}
