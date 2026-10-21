"""Batch benchmark orchestrator. Run from any working directory."""
import os
import shutil
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
CPP_WORKER = PROJECT_DIR / "src" / "cpp" / "benchmarkWorker.exe"
PY_WORKER = PROJECT_DIR / "src" / "python" / "benchmark" / "benchmarkWorker.py"
SIZES = (1_000, 10_000, 100_000, 1_000_000)
VARIANTS = ("random", "ascending", "descending")
ALGORITHMS = (
    "InsertionSort", "MergeSort", "HeapSort", "DualPivotQuickSort",
    "RadixSort", "BucketSort",
)
REPETITIONS = 5
LIMIT_SECONDS = 300
PREDICTION_CUTOFF_SECONDS = 240
FIELDS = [
    "algorithm", "language", "variant", "n",
    "repeat1_ms", "repeat2_ms", "repeat3_ms", "repeat4_ms", "repeat5_ms",
    "average_ms", "stdDev_ms", "status", "method", "reference_n",
    "reference_average_ms", "growth_model", "error",
]


def getGrowthModel(algorithm, variant):
    if algorithm == "InsertionSort":
        return "linear" if variant == "ascending" else "quadratic"
    if algorithm == "DualPivotQuickSort":
        return "nlogn" if variant == "random" else "quadratic"
    if algorithm == "RadixSort":
        return "linear"
    if algorithm == "BucketSort":
        # Fixed number of buckets, insertion sort in each bucket: conservative asymptotic model.
        return "quadratic"
    return "nlogn"


def growthValue(size, model):
    if model == "linear":
        return float(size)
    if model == "quadratic":
        return float(size) ** 2
    return size * math.log2(size)


def datasetPath(size, variant):
    return DATA_DIR / f"{size:,}".replace(",", "_") / f"{variant}_{size}.txt"


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
    temporaryPath.replace(path)


def getReference(rows, algorithm, variant, targetSize):
    matches = []
    for (itemAlgorithm, itemVariant, size), row in rows.items():
        if (itemAlgorithm == algorithm and itemVariant == variant
                and size < targetSize and row["status"] == "measured"):
            matches.append((size, float(row["average_ms"])))
    return max(matches, default=None, key=lambda item: item[0])


def makeRow(algorithm, language, variant, size, times, average,
            stdDev, status, method, model, reference=None, error=""):
    row = dict.fromkeys(FIELDS, "")
    row.update({
        "algorithm": algorithm,
        "language": language,
        "variant": variant,
        "n": size,
        "average_ms": f"{average:.9f}" if average is not None else "",
        "stdDev_ms": f"{stdDev:.9f}" if stdDev is not None else "",
        "status": status,
        "method": method,
        "growth_model": model,
        "error": error.replace("\n", " ")[:500],
    })
    if reference is not None:
        row["reference_n"] = reference[0]
        row["reference_average_ms"] = f"{reference[1]:.9f}"
    for index, elapsed in enumerate(times, start=1):
        row[f"repeat{index}_ms"] = f"{elapsed:.9f}"
    return row



def singleRun(language, algorithm, path, size, timeoutSeconds):
    environment = os.environ.copy()

    if language == "cpp":
        command = [
            str(CPP_WORKER),
            algorithm,
            str(path),
            str(size)
        ]

        if os.name == "nt":
            msysBin = Path("C:/msys64/ucrt64/bin")

            if not msysBin.is_dir():
                raise FileNotFoundError(
                    f"MSYS2 directory not found: {msysBin}"
                )

            environment["PATH"] = (
                str(msysBin)
                + os.pathsep
                + environment.get("PATH", "")
            )
    else:
        command = [
            sys.executable,
            str(PY_WORKER),
            algorithm,
            str(path),
            str(size)
        ]

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
        elapsedNs = int(result.stdout.strip())
    except ValueError as error:
        raise RuntimeError(
            f"Invalid worker output: {result.stdout!r}"
        ) from error

    if elapsedNs < 0:
        raise RuntimeError("Negative worker timing")

    return elapsedNs / 1_000_000

def runBatch(language, algorithms, maxSize, retryEstimated):
    outputPath = RESULTS_DIR / f"results_{language}.csv"
    rows = readRows(outputPath)
    if language == "cpp" and not CPP_WORKER.exists():
        raise FileNotFoundError(f"Compile the C++ worker first: {CPP_WORKER}")

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
                predictedMs = None
                if reference is not None:
                    predictedMs = reference[1] * (
                        growthValue(size, model) / growthValue(reference[0], model)
                    )

                if predictedMs is not None and predictedMs / 1000 > PREDICTION_CUTOFF_SECONDS:
                    row = makeRow(
                        algorithm, language, variant, size, [], predictedMs,
                        None, "estimated", "theoretical_extrapolation", model, reference,
                        "Predicted duration exceeds preventive limit",
                    )
                    rows[key] = row
                    saveRows(outputPath, rows)
                    print(f"ESTIMATED {algorithm} {variant} {size}: {predictedMs:.3f} ms", flush=True)
                    continue

                path = datasetPath(size, variant)
                if not path.is_file():
                    raise FileNotFoundError(f"Missing dataset: {path}")
                times = []
                failure = ""
                for repeatIndex in range(REPETITIONS):
                    print(f"RUN {algorithm} {variant} n={size} repetition={repeatIndex + 1}/5", flush=True)
                    try:
                        elapsedMs = singleRun(
                            language, algorithm, path, size, LIMIT_SECONDS
                        )
                        times.append(elapsedMs)
                        print(f"  {elapsedMs:.6f} ms", flush=True)
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
                        algorithm, language, variant, size, times, average,
                        stdDev, "measured", "five_executions", model,
                    )
                    print(f"MEASURED {algorithm} {variant} {size}: {average:.6f} ms", flush=True)
                elif reference is not None:
                    estimatedMs = predictedMs
                    row = makeRow(
                        algorithm, language, variant, size, times, estimatedMs,
                        None, "estimated", "estimated_after_failure", model,
                        reference, failure,
                    )
                    print(f"ESTIMATED after failure: {failure}", flush=True)
                else:
                    row = makeRow(
                        algorithm, language, variant, size, times, None,
                        None, "failed", "no_reference_available", model,
                        None, failure,
                    )
                    print(f"FAILED, no basis for estimation: {failure}", flush=True)

                rows[key] = row
                saveRows(outputPath, rows)
    print(f"Finished: {outputPath}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Resumable C++ / Python sorting benchmark")
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
