import argparse
import sys
import time
from pathlib import Path

ALGORITHMS_DIR = Path(__file__).resolve().parents[1] / "algorithms"
sys.path.insert(0, str(ALGORITHMS_DIR))

from insertionSort import insertionSort
from mergeSort import mergeSort
from heapSort import heapSort
from dualPivotQuickSort import dualPivotQuickSort
from radixSort import radixSort
from bucketSort import bucketSort

ALGORITHMS = {
    "InsertionSort": insertionSort,
    "MergeSort": mergeSort,
    "HeapSort": heapSort,
    "DualPivotQuickSort": dualPivotQuickSort,
    "RadixSort": radixSort,
    "BucketSort": bucketSort,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm")
    parser.add_argument("datasetPath", type=Path)
    parser.add_argument("expectedCount", type=int)
    args = parser.parse_args()

    if args.algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {args.algorithm}")

    with args.datasetPath.open("r", encoding="utf-8") as file:
        original = [int(line) for line in file]

    if len(original) != args.expectedCount:
        raise ValueError(f"Expected {args.expectedCount} values; got {len(original)}")

    expected = sorted(original)
    working = original.copy()

    start = time.perf_counter_ns()
    ALGORITHMS[args.algorithm](working)
    elapsedNs = time.perf_counter_ns() - start

    if working != expected:
        raise ValueError("Incorrect sorting result")
    print(elapsedNs)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
