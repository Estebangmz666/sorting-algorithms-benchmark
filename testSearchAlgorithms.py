import bisect
import random
import sys
from pathlib import Path

projectRoot = Path(__file__).resolve().parent
sys.path.insert(0, str(projectRoot / "src" / "python"))
from algorithms.linearSearch import linearSearch
from algorithms.binarySearch import binarySearch
from algorithms.ternarySearch import ternarySearch
from algorithms.jumpSearch import jumpSearch
from algorithms.interpolationSearch import interpolationSearch
from algorithms.exponentialSearch import exponentialSearch


def main():
    generator = random.Random(12345)
    cases = [[], [10_000_000], [10_000_000, 99_999_999], [10_000_000] * 3,
             [10_000_000, 10_000_000, 99_999_999, 99_999_999]]
    for size in (2, 10, 100, 1000):
        cases.append(sorted(generator.randint(10_000_000, 99_999_999) for _ in range(size)))

    for searchFunction in (linearSearch, binarySearch, ternarySearch,
                           jumpSearch, interpolationSearch, exponentialSearch):
        for array in cases:
            keys = set(array) | {9_999_999, 10_000_000, 55_555_555, 99_999_999, 100_000_000}
            keys |= {value + 1 for value in array} | {value - 1 for value in array}
            for key in keys:
                index = searchFunction(array, key)
                position = bisect.bisect_left(array, key)
                present = position < len(array) and array[position] == key
                if present:
                    assert index >= 0 and array[index] == key, f"{searchFunction.__name__} missed {key}"
                else:
                    assert index == -1, f"{searchFunction.__name__} false positive {key}"
        print(f"PASS: {searchFunction.__name__}")


if __name__ == "__main__":
    main()
