"""Build an offline search dashboard (Punto 2) from the search benchmark CSVs.

Usage: python scripts/buildSearchDashboard.py
Only the Python standard library is required. The CSVs are never modified.
Output: charts/search_dashboard.html (open it with a double click in the browser).

The visual style is taken from scripts/dashboardTemplate.html (Punto 1), so both
dashboards look alike without duplicating the CSS.
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from runSearchBenchmarks import ALGORITHMS, FIELDS, SIZES, VARIANTS

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results"
OUTPUT_PATH = PROJECT_DIR / "charts" / "search_dashboard.html"
TEMPLATE_PATH = Path(__file__).resolve().with_name("searchDashboardTemplate.html")
SHARED_STYLE_PATH = Path(__file__).resolve().with_name("dashboardTemplate.html")
SOURCES = (("search_results_cpp.csv", "cpp"), ("search_results_py.csv", "py"))
STATUSES = {"measured", "estimated", "failed"}


def optionalFloat(value):
    text = (value or "").strip()
    return float(text) if text else None


def loadRows():
    rows, sources, warnings = [], [], []
    for filename, language in SOURCES:
        path = RESULTS_DIR / filename
        if not path.exists():
            warnings.append(f"No existe {filename}; faltan los resultados de {language}.")
            continue
        count = 0
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != FIELDS:
                raise ValueError(f"Esquema inesperado en {path}")
            for record in reader:
                if (record["language"] != language or record["algorithm"] not in ALGORITHMS
                        or record["variant"] not in VARIANTS or int(record["n"]) not in SIZES
                        or record["status"] not in STATUSES):
                    warnings.append(f"Registro ignorado en {filename}: {record['algorithm']} "
                                    f"{record['variant']} {record['n']}.")
                    continue
                rows.append({
                    "algorithm": record["algorithm"],
                    "language": language,
                    "variant": record["variant"],
                    "n": int(record["n"]),
                    "average_ns": optionalFloat(record["average_ns"]),
                    "stdDev_ns": optionalFloat(record["stdDev_ns"]),
                    "repetitions_ns": [float(record[f"repeat{i}_ns"]) for i in range(1, 6)
                                       if record[f"repeat{i}_ns"]],
                    "found": int(record["found"]) if record["found"] else None,
                    "status": record["status"],
                    "method": record["method"],
                    "error": record["error"],
                })
                count += 1
        sources.append({"file": f"results/{filename}", "rows": count})
    return rows, sources, warnings


def buildSearchDashboard():
    rows, sources, warnings = loadRows()
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "algorithms": list(ALGORITHMS),
        "variants": list(VARIANTS),
        "sizes": list(SIZES),
        "rows": rows,
        "sources": sources,
        "warnings": warnings,
    }
    sharedStyle = re.search(r"<style>(.*?)</style>",
                            SHARED_STYLE_PATH.read_text(encoding="utf-8"), re.DOTALL)
    if sharedStyle is None:
        raise ValueError(f"No se encontró el bloque <style> en {SHARED_STYLE_PATH}")
    # "</" is escaped so the data can never close the <script> element early.
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = (TEMPLATE_PATH.read_text(encoding="utf-8")
            .replace("/*__SHARED_STYLE__*/", sharedStyle.group(1).strip())
            .replace("__SEARCH_PAYLOAD__", data))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8", newline="\n")
    return OUTPUT_PATH


if __name__ == "__main__":
    path = buildSearchDashboard()
    print(f"CREATED: {path.relative_to(PROJECT_DIR)}")
