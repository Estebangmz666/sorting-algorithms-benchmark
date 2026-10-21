#include "dualPivotQuickSort.hpp"
#include <algorithm>
#include <cstdint>
#include <utility>
void dualPivotQuickSort(std::vector<int>& array) {
    if (array.size() < 2) return;
    using Index = std::int64_t;
    std::vector<std::pair<Index, Index>> pending;
    pending.push_back({0, static_cast<Index>(array.size()) - 1});

    while (!pending.empty()) {
        auto [left, right] = pending.back();
        pending.pop_back();
        if (left >= right) continue;

        if (array[left] > array[right]) std::swap(array[left], array[right]);
        const int leftPivot = array[left];
        const int rightPivot = array[right];
        Index less = left + 1;
        Index greater = right - 1;
        Index current = less;

        while (current <= greater) {
            if (array[current] < leftPivot) {
                std::swap(array[current], array[less]);
                ++less;
            } else if (array[current] > rightPivot) {
                while (current < greater && array[greater] > rightPivot)
                    --greater;
                std::swap(array[current], array[greater]);
                --greater;
                if (array[current] < leftPivot) {
                    std::swap(array[current], array[less]);
                    ++less;
                }
            }
            ++current;
        }
        --less;
        ++greater;
        std::swap(array[left], array[less]);
        std::swap(array[right], array[greater]);

        if (left < less - 1) pending.push_back({left, less - 1});
        if (leftPivot < rightPivot && less + 1 < greater - 1)
            pending.push_back({less + 1, greater - 1});
        if (greater + 1 < right) pending.push_back({greater + 1, right});
    }
}
