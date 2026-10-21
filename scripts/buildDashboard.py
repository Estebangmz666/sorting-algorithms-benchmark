"""Build an offline dashboard from a snapshot of the canonical benchmark CSVs.

Usage: python scripts/buildDashboard.py [--results-dir PATH] [--output PATH]
Only the Python standard library is required. Benchmark inputs are never modified.
"""

import argparse
import csv
import io
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from runBenchmarks import ALGORITHMS, FIELDS, SIZES, VARIANTS


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results"
OUTPUT_PATH = PROJECT_DIR / "charts" / "dashboard.html"
TEMPLATE_PATH = Path(__file__).resolve().with_name("dashboardTemplate.html")
PAYLOAD_MARKER = "__DASHBOARD_PAYLOAD__"
SOURCES = (("results_cpp.csv", "cpp"), ("results_py.csv", "py"))
REQUIRED_FIELDS = {"algorithm", "language", "variant", "n", "average_ms", "status"}
STATUSES = {"measured", "estimated", "failed"}
GROWTH_MODELS = {"linear", "quadratic", "nlogn"}
LANGUAGE_ALIASES = {"cpp": "cpp", "c++": "cpp", "py": "py", "python": "py"}
DECIMAL_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", re.ASCII)


def isoTimestamp(timestamp=None):
    """Use explicit UTC; ZoneInfo's optional tzdata is not required on Windows."""
    current = (datetime.now(timezone.utc) if timestamp is None
               else datetime.fromtimestamp(timestamp, timezone.utc))
    return current.isoformat(timespec="seconds")


def optionalNumber(value, field, *, minimum=0, strictlyPositive=False):
    text = (value or "").strip()
    if not text:
        return None
    if not DECIMAL_NUMBER.fullmatch(text):
        raise ValueError(f"{field} no es numérico")
    try:
        number = float(text)
    except ValueError as error:
        raise ValueError(f"{field} no es numérico") from error
    if not math.isfinite(number):
        raise ValueError(f"{field} debe ser finito")
    if number < minimum or (strictlyPositive and number <= minimum):
        condition = "mayor que" if strictlyPositive else "mayor o igual que"
        raise ValueError(f"{field} debe ser {condition} {minimum}")
    return number


def optionalSize(value, field):
    number = optionalNumber(value, field, strictlyPositive=True)
    if number is None:
        return None
    if not number.is_integer() or number not in SIZES:
        raise ValueError(f"{field} no es un tamaño de la suite")
    return int(number)


def parseRow(raw, language, source):
    """Validate one row without turning missing timings into zero."""
    if None in raw:
        raise ValueError("la fila tiene más valores que columnas")
    algorithm = (raw.get("algorithm") or "").strip()
    if algorithm not in ALGORITHMS:
        raise ValueError("algoritmo desconocido")
    variant = (raw.get("variant") or "").strip().lower()
    if variant not in VARIANTS:
        raise ValueError("variante desconocida")
    declaredLanguage = LANGUAGE_ALIASES.get((raw.get("language") or "").strip().lower())
    if declaredLanguage != language:
        raise ValueError("el lenguaje no coincide con el nombre del archivo")
    size = optionalSize(raw.get("n"), "n")
    if size is None:
        raise ValueError("falta n")
    status = (raw.get("status") or "").strip().lower()
    if status not in STATUSES:
        raise ValueError("estado desconocido")
    average = optionalNumber(raw.get("average_ms"), "average_ms", strictlyPositive=True)
    if status != "failed" and average is None:
        raise ValueError("falta average_ms para un resultado medido o estimado")
    standardDeviation = optionalNumber(raw.get("stdDev_ms"), "stdDev_ms")
    referenceSize = optionalSize(raw.get("reference_n"), "reference_n")
    referenceAverage = optionalNumber(
        raw.get("reference_average_ms"), "reference_average_ms", strictlyPositive=True,
    )
    if (referenceSize is None) != (referenceAverage is None):
        raise ValueError("la referencia debe incluir tamaño y promedio")
    if referenceSize is not None and referenceSize >= size:
        raise ValueError("reference_n debe ser menor que n")
    growthModel = (raw.get("growth_model") or "").strip()
    if growthModel and growthModel not in GROWTH_MODELS:
        raise ValueError("modelo de crecimiento desconocido")
    repetitions = []
    for index in range(1, 6):
        field = f"repeat{index}_ms"
        elapsed = optionalNumber(raw.get(field), field)
        if elapsed is not None:
            repetitions.append(elapsed)
    return {
        "algorithm": algorithm,
        "language": language,
        "variant": variant,
        "n": size,
        "average_ms": None if status == "failed" else average,
        "stdDev_ms": standardDeviation,
        "status": status,
        "method": raw.get("method") or "",
        "reference_n": referenceSize,
        "reference_average_ms": referenceAverage,
        "growth_model": growthModel,
        "error": raw.get("error") or "",
        "repetitions_ms": repetitions,
        "source": source,
    }


def readSource(resultsDirectory, filename, language, warnings):
    """Read through one open handle so an atomic benchmark checkpoint stays whole."""
    path = resultsDirectory / filename
    source = {
        "filename": filename,
        "language": language,
        "exists": False,
        "rowCount": 0,
        "modifiedAt": None,
    }
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            source["exists"] = True
            source["modifiedAt"] = isoTimestamp(os.fstat(file.fileno()).st_mtime)
            snapshot = file.read()
    except FileNotFoundError:
        warnings.append(f"Fuente ausente: {filename}. Sus combinaciones siguen pendientes.")
        return source, []
    except (OSError, UnicodeError) as error:
        source["exists"] = path.exists()
        warnings.append(f"No se pudo leer {filename}: {error}.")
        return source, []

    reader = csv.DictReader(io.StringIO(snapshot, newline=""), strict=True)
    rows = {}
    try:
        fieldnames = reader.fieldnames or []
        if len(fieldnames) != len(set(fieldnames)):
            warnings.append(f"{filename}: encabezado con columnas duplicadas; fuente omitida.")
            return source, []
        missing = REQUIRED_FIELDS - set(fieldnames)
        if missing:
            warnings.append(
                f"{filename}: faltan columnas básicas ({', '.join(sorted(missing))}); fuente omitida."
            )
            return source, []
        unknown = set(fieldnames) - set(FIELDS)
        if unknown:
            warnings.append(
                f"{filename}: se ignoraron columnas desconocidas ({', '.join(sorted(unknown))})."
            )
        for raw in reader:
            try:
                row = parseRow(raw, language, filename)
            except (ValueError, TypeError) as error:
                warnings.append(f"{filename}, línea {reader.line_num}: fila omitida ({error}).")
                continue
            key = (row["algorithm"], row["variant"], row["n"])
            if key in rows:
                warnings.append(
                    f"{filename}, línea {reader.line_num}: combinación duplicada; "
                    "se conserva la última fila válida."
                )
            rows[key] = row
    except csv.Error as error:
        warnings.append(
            f"{filename}, línea {reader.line_num}: CSV incompleto o mal formado ({error}); "
            "se conservaron las filas válidas anteriores."
        )
    source["rowCount"] = len(rows)
    return source, list(rows.values())


def collectPayload(resultsDirectory):
    """Create the versioned dashboard contract from the current CSV snapshot."""
    resultsDirectory = Path(resultsDirectory).expanduser().resolve()
    warnings = []
    sources = []
    rows = []
    for filename, language in SOURCES:
        source, sourceRows = readSource(resultsDirectory, filename, language, warnings)
        sources.append(source)
        rows.extend(sourceRows)
    algorithmOrder = {algorithm: index for index, algorithm in enumerate(ALGORITHMS)}
    languageOrder = {language: index for index, (_, language) in enumerate(SOURCES)}
    variantOrder = {variant: index for index, variant in enumerate(VARIANTS)}
    rows.sort(key=lambda row: (
        algorithmOrder[row["algorithm"]], languageOrder[row["language"]],
        variantOrder[row["variant"]], row["n"],
    ))
    return {
        "schemaVersion": 1,
        "generatedAt": isoTimestamp(),
        "algorithms": list(ALGORITHMS),
        "languages": [language for _, language in SOURCES],
        "variants": list(VARIANTS),
        "sizes": list(SIZES),
        "expectedCount": len(ALGORITHMS) * len(SOURCES) * len(VARIANTS) * len(SIZES),
        "sources": sources,
        "warnings": warnings,
        "rows": rows,
    }


def serializePayload(payload):
    """Keep CSV text inert inside a script element, including closing tags."""
    serialized = json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return (serialized.replace("&", "\\u0026").replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029"))


def buildDashboard(resultsDirectory=None, outputPath=None, templatePath=None):
    """Write a standalone HTML atomically and return its absolute output path."""
    resultsDirectory = Path(resultsDirectory or RESULTS_DIR).expanduser().resolve()
    outputPath = Path(outputPath or OUTPUT_PATH).expanduser().resolve()
    templatePath = Path(templatePath or TEMPLATE_PATH).expanduser().resolve()
    template = templatePath.read_text(encoding="utf-8")
    if template.count(PAYLOAD_MARKER) != 1:
        raise ValueError(f"Dashboard template must contain exactly one {PAYLOAD_MARKER} marker")
    if outputPath == templatePath or outputPath in {
        resultsDirectory / filename for filename, _ in SOURCES
    }:
        raise ValueError("Dashboard output cannot replace its template or benchmark sources")
    payload = collectPayload(resultsDirectory)
    html = template.replace(PAYLOAD_MARKER, serializePayload(payload))
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    temporaryPath = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=outputPath.parent,
            prefix=f".{outputPath.name}.", suffix=".tmp", delete=False,
        ) as temporaryFile:
            temporaryPath = Path(temporaryFile.name)
            temporaryFile.write(html)
            temporaryFile.flush()
            os.fsync(temporaryFile.fileno())
        temporaryPath.replace(outputPath)
    finally:
        if temporaryPath is not None:
            temporaryPath.unlink(missing_ok=True)
    return outputPath


def main():
    parser = argparse.ArgumentParser(
        description="Genera un dashboard HTML autónomo con los resultados de C++ y Python."
    )
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR,
                        help="Carpeta de results_cpp.csv y results_py.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help="Archivo HTML de salida (predeterminado: charts/dashboard.html)")
    arguments = parser.parse_args()
    try:
        output = buildDashboard(arguments.results_dir, arguments.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"No se pudo generar el dashboard: {error}\n")
    print(f"Dashboard creado: {output}")


if __name__ == "__main__":
    main()
