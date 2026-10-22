import argparse
import bisect
import sys
import time
from pathlib import Path

ALGORITHMS_DIR = Path(__file__).resolve().parents[1] / "algorithms"
sys.path.insert(0, str(ALGORITHMS_DIR))

from linearSearch import linearSearch
from binarySearch import binarySearch
from ternarySearch import ternarySearch
from jumpSearch import jumpSearch
from interpolationSearch import interpolationSearch
from exponentialSearch import exponentialSearch

ALGORITHMS = {
    "LinearSearch": linearSearch,
    "BinarySearch": binarySearch,
    "TernarySearch": ternarySearch,
    "JumpSearch": jumpSearch,
    "InterpolationSearch": interpolationSearch,
    "ExponentialSearch": exponentialSearch,
}
SEARCH_COUNT = 1000
POSITION_INDEX = {"start": 0, "center": 1, "end": 2}


def readNumbers(path):
    with path.open("r", encoding="utf-8") as file:
        return [int(line) for line in file]


def buildKeys(keysPath, mode):
    """keys: the 1000 keys of keys_<n>.txt. start/center/end: the matching key
    of position_keys_<n>.txt repeated 1000 times."""
    fileKeys = readNumbers(keysPath)
    if mode == "keys":
        if len(fileKeys) != SEARCH_COUNT:
            raise ValueError("Expected 1000 keys")
        return fileKeys
    if len(fileKeys) != 3:
        raise ValueError("Expected 3 position keys")
    return [fileKeys[POSITION_INDEX[mode]]] * SEARCH_COUNT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("algorithm", choices=ALGORITHMS)
    parser.add_argument("datasetPath", type=Path)
    parser.add_argument("keysPath", type=Path)
    parser.add_argument("expectedCount", type=int)
    parser.add_argument("mode", choices=("keys", *POSITION_INDEX))
    args = parser.parse_args()

    array = readNumbers(args.datasetPath)
    keys = buildKeys(args.keysPath, args.mode)
    if len(array) != args.expectedCount or any(
            array[i] > array[i + 1] for i in range(len(array) - 1)):
        raise ValueError("Dataset must contain expectedCount ascending values")

    searchFunction = ALGORITHMS[args.algorithm]
    results = [0] * len(keys)

    start = time.perf_counter_ns()
    for i in range(len(keys)):
        results[i] = searchFunction(array, keys[i])
    elapsedNs = time.perf_counter_ns() - start

    # Verification is excluded from the measurement.
    found = 0
    for key, index in zip(keys, results):
        position = bisect.bisect_left(array, key)
        present = position < len(array) and array[position] == key
        if present:
            if index < 0 or array[index] != key:
                raise ValueError(f"Present key not found: {key}")
            found += 1
        elif index != -1:
            raise ValueError(f"Absent key reported as found: {key}")
    print(elapsedNs, found)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
