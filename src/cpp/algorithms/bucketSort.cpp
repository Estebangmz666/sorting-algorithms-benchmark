#include "bucketSort.hpp"
#include <cstddef>
#include <cstdint>
void bucketSort(std::vector<int>& array) {
    constexpr int minValue = 10000000;
    constexpr std::int64_t range = 90000000;
    constexpr std::size_t bucketCount = 4096;
    std::vector<std::vector<int>> buckets(bucketCount);

    for (int value : array) {
        std::size_t index = static_cast<std::size_t>(
            (static_cast<std::int64_t>(value) - minValue) * bucketCount / range
        );
        buckets[index].push_back(value);
    }

    std::size_t position = 0;
    for (auto& bucket : buckets) {
        for (std::size_t i = 1; i < bucket.size(); ++i) {
            int key = bucket[i];
            std::size_t j = i;
            while (j > 0 && bucket[j - 1] > key) {
                bucket[j] = bucket[j - 1];
                --j;
            }
            bucket[j] = key;
        }
        for (int value : bucket) array[position++] = value;
    }
}
