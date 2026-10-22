"""Batch search benchmark orchestrator (Punto 2). Run from any working directory.

Each repetition runs 1000 searches in a fresh worker process and records the
average time per search. Variants:
- keys: the 1000 keys of keys_<n>.txt (500 present, 500 absent).
- start / center / end: one key at that position, searched 1000 times.
"""
import os
import argparse
import csv
import math
import statistics
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "dataGenerationAndValidation" / "data"
RESULTS_DIR = PROJECT_DIR / "results"
CPP_WORKER = PROJECT_DIR / "src" / "cpp" / "searchWorker.exe"
PY_WORKER = PROJECT_DIR / "src" / "python" / "benchmark" / "searchWorker.py"
SIZES = (1_000, 10_000, 100_000, 1_000_000)
VARIANTS = ("keys", "start", "center", "end")
ALGORITHMS = (
    "LinearSearch", "BinarySearch", "TernarySearch", "JumpSearch",
    "InterpolationSearch", "ExponentialSearch",
)
SEARCH_COUNT = 1000
REPETITIONS = 5
LIMIT_SECONDS = 300
PREDICTION_CUTOFF_SECONDS = 240
FIELDS = [
    "algorithm", "language", "variant", "n", "searches",
    "repeat1_ns", "repeat2_ns", "repeat3_ns", "repeat4_ns", "repeat5_ns",
    "average_ns", "stdDev_ns", "total_average_ms", "found", "status", "method",
    "reference_n", "reference_average_ns", "growth_model", "error",
]


def getGrowthModel(algorithm, variant):
    """Expected growth of the time per search, used only for estimations."""
    if variant == "start" and algorithm in (
            "LinearSearch", "JumpSearch", "InterpolationSearch", "ExponentialSearch"):
        return "constant"
    if algorithm == "LinearSearch":
        return "linear"
    if algorithm == "JumpSearch":
        return "sqrt"
    if algorithm == "InterpolationSearch":
        # Uniformly distributed keys; the first and last element are found in one probe.
        return "constant" if variant == "end" else "loglog"
    return "log"


def growthValue(size, model):
    if model == "constant":
        return 1.0
    if model == "linear":
        return float(size)
    if model == "sqrt":
        return math.sqrt(size)
    if model == "loglog":
        return math.log2(math.log2(size))
    return math.log2(size)


def folderPath(size):
    return DATA_DIR / f"{size:,}".replace(",", "_")


def datasetPath(size):
    return folderPath(size) / f"ascending_{size}.txt"


def keysPath(size, variant):
    name = "keys" if variant == "keys" else "position_keys"
    return folderPath(size) / f"{name}_{size}.txt"


def readRows(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != FIELDS:
            raise ValueError(
                f"Incompatible CSV schema: {path}. Back it up and use a fresh file."
            )
        return {(row["algorithm"], row["variant"], int(row["n"])): row
                for row in reader}


def saveRows(path, rows):
    """Atomically checkpoint complete results, avoiding duplicated combinations."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporaryPath = path.with_suffix(".tmp")
    with temporaryPath.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows.values():
            writer.writerow(row)
        file.flush()
    # OneDrive or an open editor can lock the CSV for a moment on Windows.
    for attempt in range(20):
        try:
            temporaryPath.replace(path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.5)


def getReference(rows, algorithm, variant, targetSize):
    matches = []
    for (itemAlgorithm, itemVariant, size), row in rows.items():
        if (itemAlgorithm == algorithm and itemVariant == variant
                and size < targetSize and row["status"] == "measured"):
            matches.append((size, float(row["average_ns"])))
    return max(matches, default=None, key=lambda item: item[0])


def makeRow(algorithm, language, variant, size, times, average, stdDev,
            found, status, method, model, reference=None, error=""):
    row = dict.fromkeys(FIELDS, "")
    row.update({
        "algorithm": algorithm,
        "language": language,
        "variant": variant,
        "n": size,
        "searches": SEARCH_COUNT,
        "average_ns": f"{average:.3f}" if average is not None else "",
        "stdDev_ns": f"{stdDev:.3f}" if stdDev is not None else "",
        "total_average_ms": f"{average * SEARCH_COUNT / 1_000_000:.9f}"
        if average is not None else "",
        "found": found if found is not None else "",
        "status": status,
        "method": method,
        "growth_model": model,
        "error": error.replace("\n", " ")[:500],
    })
    if reference is not None:
        row["reference_n"] = reference[0]
        row["reference_average_ns"] = f"{reference[1]:.3f}"
    for index, elapsed in enumerate(times, start=1):
        row[f"repeat{index}_ns"] = f"{elapsed:.3f}"
    return row


def singleRun(language, algorithm, size, variant, timeoutSeconds):
    """Returns (nanoseconds per search, number of keys found)."""
    environment = os.environ.copy()
    arguments = [algorithm, str(datasetPath(size)), str(keysPath(size, variant)),
                 str(size), variant]

    if language == "cpp":
        command = [str(CPP_WORKER), *arguments]
        msysBin = Path("C:/msys64/ucrt64/bin")
        if os.name == "nt" and msysBin.is_dir():
            environment["PATH"] = str(msysBin) + os.pathsep + environment.get("PATH", "")
    else:
        command = [sys.executable, str(PY_WORKER), *arguments]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeoutSeconds,
        cwd=PROJECT_DIR,
        env=environment
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Worker exit {result.returncode}: "
            f"{result.stderr.strip()}"
        )

    try:
        elapsedNs, found = (int(value) for value in result.stdout.split())
    except ValueError as error:
        raise RuntimeError(
            f"Invalid worker output: {result.stdout!r}"
        ) from error

    if elapsedNs < 0:
        raise RuntimeError("Negative worker timing")

    return elapsedNs / SEARCH_COUNT, found


def runBatch(language, algorithms, maxSize, retryEstimated):
    outputPath = RESULTS_DIR / f"search_results_{language}.csv"
    rows = readRows(outputPath)
    if language == "cpp" and not CPP_WORKER.exists():
        raise FileNotFoundError(f"Compile the C++ search worker first: {CPP_WORKER}")

    print(f"Language: {language.upper()} | CSV: {outputPath}", flush=True)
    for algorithm in algorithms:
        for variant in VARIANTS:
            for size in SIZES:
                if size > maxSize:
                    continue
                key = (algorithm, variant, size)
                previous = rows.get(key)
                if previous and (previous["status"] == "measured"
                                 or not retryEstimated):
                    print(f"SKIP {algorithm} {variant} {size}: {previous['status']}", flush=True)
                    continue

                model = getGrowthModel(algorithm, variant)
                reference = getReference(rows, algorithm, variant, size)
                predictedNs = None
                if reference is not None:
                    predictedNs = reference[1] * (
                        growthValue(size, model) / growthValue(reference[0], model)
                    )

                # The limit applies to one repetition: 1000 searches.
                if (predictedNs is not None
                        and predictedNs * SEARCH_COUNT / 1e9 > PREDICTION_CUTOFF_SECONDS):
                    row = makeRow(
                        algorithm, language, variant, size, [], predictedNs, None, None,
                        "estimated", "theoretical_extrapolation", model, reference,
                        "Predicted duration exceeds preventive limit",
                    )
                    rows[key] = row
                    saveRows(outputPath, rows)
                    print(f"ESTIMATED {algorithm} {variant} {size}: {predictedNs:.3f} ns/search", flush=True)
                    continue

                for path in (datasetPath(size), keysPath(size, variant)):
                    if not path.is_file():
                        raise FileNotFoundError(f"Missing data file: {path}")
                times = []
                found = None
                failure = ""
                for repeatIndex in range(REPETITIONS):
                    print(f"RUN {algorithm} {variant} n={size} repetition={repeatIndex + 1}/5", flush=True)
                    try:
                        elapsedNs, found = singleRun(
                            language, algorithm, size, variant, LIMIT_SECONDS
                        )
                        times.append(elapsedNs)
                        print(f"  {elapsedNs:.3f} ns/search | found={found}", flush=True)
                    except subprocess.TimeoutExpired:
                        failure = f"Time limit exceeded ({LIMIT_SECONDS}s)"
                        break
                    except Exception as error:
                        failure = str(error)
                        break

                if not failure:
                    average = statistics.mean(times)
                    stdDev = statistics.stdev(times)
                    row = makeRow(
                        algorithm, language, variant, size, times, average, stdDev,
                        found, "measured", "five_executions", model,
                    )
                    print(f"MEASURED {algorithm} {variant} {size}: {average:.3f} ns/search", flush=True)
                elif reference is not None:
                    row = makeRow(
                        algorithm, language, variant, size, times, predictedNs, None, None,
                        "estimated", "estimated_after_failure", model, reference, failure,
                    )
                    print(f"ESTIMATED after failure: {failure}", flush=True)
                else:
                    row = makeRow(
                        algorithm, language, variant, size, times, None, None, None,
                        "failed", "no_reference_available", model, None, failure,
                    )
                    print(f"FAILED, no basis for estimation: {failure}", flush=True)

                rows[key] = row
                saveRows(outputPath, rows)
    print(f"Finished: {outputPath}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Resumable C++ / Python search benchmark")
    parser.add_argument("--language", choices=("cpp", "py", "all"), required=True)
    parser.add_argument("--algorithms", nargs="+", choices=ALGORITHMS, default=list(ALGORITHMS))
    parser.add_argument("--maxSize", type=int, default=1_000_000, choices=SIZES)
    parser.add_argument("--retryEstimated", action="store_true")
    args = parser.parse_args()
    languages = ("cpp", "py") if args.language == "all" else (args.language,)
    for language in languages:
        runBatch(language, args.algorithms, args.maxSize, args.retryEstimated)


if __name__ == "__main__":
    main()
