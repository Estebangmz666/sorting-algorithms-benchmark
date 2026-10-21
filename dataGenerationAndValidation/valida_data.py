
import csv
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "datosYGen" / "data"
RESULTS_DIR = BASE_DIR / "results"

SIZES = (1_000, 10_000, 100_000, 1_000_000)
MIN_VALUE = 10_000_000
MAX_VALUE = 99_999_999
INTERVAL_COUNT = 9


def load_numbers(path: Path) -> list[int]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return [int(line.strip()) for line in file]


def validate_dataset(size: int) -> dict:
    folder_name = f"{size:,}".replace(",", "_")
    folder = DATA_DIR / folder_name

    random_values = load_numbers(folder / f"random_{size}.txt")
    ascending = load_numbers(folder / f"ascending_{size}.txt")
    descending = load_numbers(folder / f"descending_{size}.txt")

    sizes_valid = all(
        len(values) == size
        for values in (random_values, ascending, descending)
    )

    ranges_valid = all(
        MIN_VALUE <= value <= MAX_VALUE
        for values in (random_values, ascending, descending)
        for value in values
    )

    ascending_valid = (
        ascending == sorted(random_values)
    )

    descending_valid = (
        descending == sorted(random_values, reverse=True)
    )

    elements_valid = (
        Counter(random_values) == Counter(ascending)
        == Counter(descending)
    )

    is_valid = all((
        sizes_valid,
        ranges_valid,
        ascending_valid,
        descending_valid,
        elements_valid,
    ))

    frequencies = [0] * INTERVAL_COUNT

    for value in random_values:
        if MIN_VALUE <= value <= MAX_VALUE:
            index = (value - MIN_VALUE) // 10_000_000
            frequencies[index] += 1

    expected = len(random_values) / INTERVAL_COUNT

    chi_square = sum(
        (observed - expected) ** 2 / expected
        for observed in frequencies
    ) if expected > 0 else 0.0

    unique_count = len(set(random_values))

    result = {
        "size": size,
        "status": "VALID" if is_valid else "INVALID",
        "unique_values": unique_count,
        "repeated_values": len(random_values) - unique_count,
        "chi_square": round(chi_square, 4),
        "sizes_valid": sizes_valid,
        "ranges_valid": ranges_valid,
        "ascending_valid": ascending_valid,
        "descending_valid": descending_valid,
        "elements_valid": elements_valid,
    }

    for index, count in enumerate(frequencies, start=1):
        result[f"interval_{index}"] = count

    print(
        f"{size:>10,} | "
        f"{result['status']:<7} | "
        f"Unique: {unique_count:>10,} | "
        f"Chi-square: {chi_square:.4f}"
    )

    return result


def export_results(results: list[dict]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "validation_results.csv"

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )
        writer.writeheader()
        writer.writerows(results)

    return output_path


def main() -> None:
    print("=" * 68)
    print("DATASET VALIDATION REPORT")
    print("=" * 68)

    results = [validate_dataset(size) for size in SIZES]
    output_path = export_results(results)

    print("=" * 68)
    print(f"Report saved: {output_path}")

    if not all(row["status"] == "VALID" for row in results):
        raise SystemExit("Validation failed for one or more datasets.")

    print("All datasets validated successfully.")


if __name__ == "__main__":
    main()