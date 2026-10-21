import random
import sys
from pathlib import Path

projectRoot = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(projectRoot / "src" / "python"))
from algorithms.insertionSort import insertionSort
from algorithms.mergeSort import mergeSort
from algorithms.heapSort import heapSort
from algorithms.dualPivotQuickSort import dualPivotQuickSort
from algorithms.radixSort import radixSort
from algorithms.bucketSort import bucketSort


def main():
    generator = random.Random(12345)
    cases = [[], [10_000_000], [99_999_999, 10_000_000],
             [10_000_000] * 3, [99_999_999, 10_000_000, 10_000_000, 99_999_999]]
    for size in (2, 10, 100, 1000):
        sample = [generator.randint(10_000_000, 99_999_999) for _ in range(size)]
        cases.extend([sample, sorted(sample), sorted(sample, reverse=True)])

    for sortFunction in (insertionSort, mergeSort, heapSort,
                         dualPivotQuickSort, radixSort, bucketSort):
        for original in cases:
            actual = original.copy()
            sortFunction(actual)
            assert actual == sorted(original), f"Failed: {sortFunction.__name__}"
        print(f"PASS: {sortFunction.__name__}")


if __name__ == "__main__":
    main()
