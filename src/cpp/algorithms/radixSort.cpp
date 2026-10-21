#include "radixSort.hpp"
#include <array>
#include <cstddef>
void radixSort(std::vector<int>& array) {
    constexpr int base = 10;
    constexpr int passes = 8;
    std::vector<int> output(array.size());
    int divisor = 1;
    for (int pass = 0; pass < passes; ++pass) {
        std::array<std::size_t, base> counts{};
        for (int value : array) ++counts[(value / divisor) % base];
        for (int digit = 1; digit < base; ++digit) counts[digit] += counts[digit - 1];
        for (std::size_t i = array.size(); i > 0; --i) {
            int value = array[i - 1];
            int digit = (value / divisor) % base;
            output[--counts[digit]] = value;
        }
        array.swap(output);
        divisor *= base;
    }
}
