"""Generate the Punto 2 (search) charts and key-position tables.

Usage: python scripts/plotSearchResults.py
Dependencies: matplotlib, numpy (pandas is not required)

Outputs:
- charts/07_search_growth_cpp.png
- charts/08_search_growth_python.png
- charts/09_search_cpp_vs_python_1000000.png
- results/search_position_tables.md
"""
from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import LogLocator

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results"
OUTPUT_DIR = PROJECT_DIR / "charts"
SIZES = [1_000, 10_000, 100_000, 1_000_000]
LANGUAGES = [("C++", "search_results_cpp.csv"), ("Python", "search_results_py.csv")]
ALGORITHMS = ["LinearSearch", "BinarySearch", "TernarySearch", "JumpSearch",
              "InterpolationSearch", "ExponentialSearch"]
# Categorical palette validated for the dark surface (CVD and normal-vision
# separation); the marker shape is a second encoding of the algorithm.
COLORS = {
    "LinearSearch": "#3987E5", "BinarySearch": "#D95926",
    "TernarySearch": "#199E70", "JumpSearch": "#C98500",
    "InterpolationSearch": "#D55181", "ExponentialSearch": "#008300",
}
MARKERS = {
    "LinearSearch": "o", "BinarySearch": "s", "TernarySearch": "^",
    "JumpSearch": "D", "InterpolationSearch": "v", "ExponentialSearch": "P",
}
DISPLAY = {
    "LinearSearch": "Lineal", "BinarySearch": "Binaria", "TernarySearch": "Ternaria",
    "JumpSearch": "Saltos", "InterpolationSearch": "Interpolación",
    "ExponentialSearch": "Exponencial",
}
LANGUAGE_COLORS = {"C++": "#3987E5", "Python": "#D95926"}
POSITIONS = [("start", "Inicio"), ("center", "Centro"), ("end", "Final")]
BACKGROUND = "#0B1020"
PANEL = "#151D32"
WHITE = "#E8EDF8"
MUTED = "#A3B0C7"


def setTheme():
    plt.rcParams.update({
        "figure.facecolor": BACKGROUND, "axes.facecolor": PANEL,
        "savefig.facecolor": BACKGROUND, "text.color": WHITE,
        "axes.labelcolor": WHITE, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": "#46516B", "grid.color": "#495672",
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.titleweight": "bold", "axes.titlesize": 15,
        "legend.frameon": False, "figure.dpi": 130,
    })


def loadResults():
    """Returns {(language, algorithm, variant, n): row} for measured/estimated rows."""
    results = {}
    for language, filename in LANGUAGES:
        path = RESULTS_DIR / filename
        if not path.exists():
            print(f"WAITING: {path.name} does not exist yet")
            continue
        with path.open("r", encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                if row["status"] not in ("measured", "estimated") or not row["average_ns"]:
                    continue
                row["average_ns"] = float(row["average_ns"])
                row["stdDev_ns"] = float(row["stdDev_ns"]) if row["stdDev_ns"] else None
                results[(language, row["algorithm"], row["variant"], int(row["n"]))] = row
    return results


def formatTime(nanoseconds):
    if nanoseconds >= 1_000_000:
        return f"{nanoseconds / 1_000_000:.2f} ms"
    if nanoseconds >= 1_000:
        return f"{nanoseconds / 1_000:.2f} µs"
    return f"{nanoseconds:.1f} ns"


def styleAxes(ax, xlabel="Elementos (n)", ylabel="Tiempo promedio por búsqueda (ns)"):
    ax.set_xlabel(xlabel, labelpad=10)
    ax.set_ylabel(ylabel, labelpad=10)
    ax.grid(True, which="major", linestyle="--", alpha=0.27)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_alpha(0.35)


def saveFigure(fig, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    fig.savefig(path, dpi=210, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"CREATED: {path.relative_to(PROJECT_DIR)}")


def plotGrowth(results, language, filename):
    fig, ax = plt.subplots(figsize=(13, 7.2))
    found = False
    for algorithm in ALGORITHMS:
        points = [(size, results[key]["average_ns"], results[key]["status"])
                  for size in SIZES
                  if (key := (language, algorithm, "keys", size)) in results]
        if not points:
            continue
        found = True
        color, marker = COLORS[algorithm], MARKERS[algorithm]
        measured = [(n, t) for n, t, status in points if status == "measured"]
        ax.plot([p[0] for p in measured], [p[1] for p in measured], color=color,
                marker=marker, linewidth=2.2, markersize=8, label=DISPLAY[algorithm],
                markeredgecolor=PANEL, markeredgewidth=1.5)
        for index, (n, t, status) in enumerate(points):
            if status == "estimated":
                if index > 0:
                    ax.plot([points[index - 1][0], n], [points[index - 1][1], t],
                            color=color, linestyle="--", linewidth=2.2)
                ax.scatter(n, t, s=95, marker=marker, facecolor=BACKGROUND,
                           edgecolor=color, linewidth=2, zorder=5)
    if not found:
        plt.close(fig)
        return
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(SIZES, labels=[f"{s:,}".replace(",", ".") for s in SIZES])
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.yaxis.set_major_locator(LogLocator(base=10, numticks=10))
    styleAxes(ax)
    ax.set_title(f"CRECIMIENTO DE ALGORITMOS DE BÚSQUEDA  |  {language.upper()}\n"
                 "1.000 claves (500 presentes, 500 ausentes) · ambos ejes logarítmicos",
                 loc="left", pad=20)
    ax.legend(loc="upper left", ncol=2, fontsize=10)
    fig.text(0.11, 0.02, "Marcador relleno = medido     marcador hueco y tramo discontinuo = estimado",
             color=MUTED, fontsize=9)
    saveFigure(fig, filename)


def plotLanguages(results):
    size = 1_000_000
    fig, ax = plt.subplots(figsize=(15.5, 8))
    x = np.arange(len(ALGORITHMS), dtype=float)
    width = 0.36
    present = []
    for languageIndex, (language, _) in enumerate(LANGUAGES):
        color = LANGUAGE_COLORS[language]
        xs, values, statuses = [], [], []
        for algorithmIndex, algorithm in enumerate(ALGORITHMS):
            row = results.get((language, algorithm, "keys", size))
            if row is None:
                continue
            xs.append(x[algorithmIndex] + (languageIndex - 0.5) * width)
            values.append(row["average_ns"])
            statuses.append(row["status"])
        if not xs:
            continue
        present.extend(values)
        # The panel-colored edge leaves a visible gap between adjacent bars.
        bars = ax.bar(xs, values, width, color=color, edgecolor=PANEL, linewidth=2,
                      label=language)
        for bar, value, status in zip(bars, values, statuses):
            if status == "estimated":
                bar.set_hatch("///")
                bar.set_facecolor("none")
                bar.set_edgecolor(color)
            ax.annotate(formatTime(value), (bar.get_x() + bar.get_width() / 2, value),
                        xytext=(0, 4), textcoords="offset points", ha="center",
                        va="bottom", rotation=90, fontsize=8.5, color=WHITE)
    if not present:
        plt.close(fig)
        return
    ax.set_yscale("log")
    ax.set_ylim(bottom=min(present) / 3, top=max(present) * 30)
    ax.set_xticks(x, [DISPLAY[a] for a in ALGORITHMS])
    styleAxes(ax, xlabel="Algoritmo")
    ax.set_title("BÚSQUEDA  |  C++ VS PYTHON  |  1.000.000 ELEMENTOS\n"
                 "Tiempo promedio por búsqueda (1.000 claves) · eje temporal logarítmico",
                 loc="left", pad=20)
    ax.legend(handles=[Patch(facecolor=LANGUAGE_COLORS[name], label=name)
                       for name, _ in LANGUAGES], loc="upper right", ncol=2)
    fig.text(0.11, 0.015, "Barras rayadas = estimaciones · ausencia de barra = resultado pendiente",
             color=MUTED, fontsize=9)
    saveFigure(fig, "09_search_cpp_vs_python_1000000.png")


def writePositionTables(results):
    """One table per language: n = 1.000.000, one row per algorithm, one column per position."""
    lines = ["# Tiempo promedio por búsqueda según la posición de la clave (n = 1.000.000)", "",
             "Cada valor es la media de 5 repeticiones de 1.000 búsquedas de la misma clave "
             "(media ± desviación estándar muestral, por búsqueda).", ""]
    for language, _ in LANGUAGES:
        lines += [f"## {language}", "",
                  "| Algoritmo | " + " | ".join(label for _, label in POSITIONS) + " |",
                  "|---|" + "---|" * len(POSITIONS)]
        for algorithm in ALGORITHMS:
            cells = []
            for variant, _ in POSITIONS:
                row = results.get((language, algorithm, variant, 1_000_000))
                if row is None:
                    cells.append("pendiente")
                elif row["status"] == "estimated":
                    cells.append(f"{formatTime(row['average_ns'])} E")
                else:
                    cells.append(f"{formatTime(row['average_ns'])} ± {formatTime(row['stdDev_ns'])}")
            lines.append(f"| {DISPLAY[algorithm]} | " + " | ".join(cells) + " |")
        lines.append("")
    path = RESULTS_DIR / "search_position_tables.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"CREATED: {path.relative_to(PROJECT_DIR)}")


def main():
    setTheme()
    results = loadResults()
    if not results:
        print("No measured or estimated search results are available yet.")
        return
    plotGrowth(results, "C++", "07_search_growth_cpp.png")
    plotGrowth(results, "Python", "08_search_growth_python.png")
    plotLanguages(results)
    writePositionTables(results)


if __name__ == "__main__":
    main()
