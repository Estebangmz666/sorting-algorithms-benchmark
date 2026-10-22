#include <algorithm>
#include <iostream>
#include <random>
#include <set>
#include <vector>
#include "src/cpp/algorithms/linearSearch.hpp"
#include "src/cpp/algorithms/binarySearch.hpp"
#include "src/cpp/algorithms/ternarySearch.hpp"
#include "src/cpp/algorithms/jumpSearch.hpp"
#include "src/cpp/algorithms/interpolationSearch.hpp"
#include "src/cpp/algorithms/exponentialSearch.hpp"

int main() {
    using SearchFunction = int (*)(const std::vector<int>&, int);
    std::vector<std::pair<const char*, SearchFunction>> algorithms = {
        {"linearSearch", linearSearch}, {"binarySearch", binarySearch},
        {"ternarySearch", ternarySearch}, {"jumpSearch", jumpSearch},
        {"interpolationSearch", interpolationSearch}, {"exponentialSearch", exponentialSearch}
    };
    std::mt19937 generator(12345);
    std::uniform_int_distribution<int> distribution(10000000, 99999999);
    std::vector<std::vector<int>> cases = {{}, {10000000}, {10000000, 99999999},
        {10000000, 10000000, 10000000}, {10000000, 10000000, 99999999, 99999999}};
    for (int n : {2, 10, 100, 1000}) {
        std::vector<int> sample(n);
        for (int& value : sample) value = distribution(generator);
        std::sort(sample.begin(), sample.end());
        cases.push_back(sample);
    }
    for (auto [name, searchFunction] : algorithms) {
        for (const auto& array : cases) {
            std::set<int> keys = {9999999, 10000000, 55555555, 99999999, 100000000};
            for (int value : array) keys.insert({value - 1, value, value + 1});
            for (int key : keys) {
                int index = searchFunction(array, key);
                bool present = std::binary_search(array.begin(), array.end(), key);
                bool ok = present ? (index >= 0 && array[index] == key) : index == -1;
                if (!ok) { std::cerr << "FAILED: " << name << " key=" << key << '\n'; return 1; }
            }
        }
        std::cout << "PASS: " << name << '\n';
    }
    return 0;
}
