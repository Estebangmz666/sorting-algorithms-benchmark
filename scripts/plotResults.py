"""Generate the six required charts and an offline interactive dashboard.

Usage: python scripts/plotResults.py
Dependencies: matplotlib, pandas, numpy
"""
from pathlib import Path
import math
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pathEffects
import numpy as np
import pandas as pd
from matplotlib.ticker import LogLocator, FuncFormatter
from matplotlib.patches import Patch
from buildDashboard import buildDashboard

PROJECT_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_DIR / "results"
OUTPUT_DIR = PROJECT_DIR / "charts"
SIZES = [1_000, 10_000, 100_000, 1_000_000]
ALGORITHMS = ["InsertionSort", "DualPivotQuickSort", "MergeSort", "HeapSort", "RadixSort", "BucketSort"]
COLORS = {
    "InsertionSort": "#F97316", "DualPivotQuickSort": "#E879F9",
    "MergeSort": "#22D3EE", "HeapSort": "#A3E635",
    "RadixSort": "#FACC15", "BucketSort": "#818CF8",
}
DISPLAY = {
    "InsertionSort": "Insertion", "DualPivotQuickSort": "Dual-Pivot Quick",
    "MergeSort": "Merge", "HeapSort": "Heap", "RadixSort": "Radix", "BucketSort": "Bucket",
}
VARIANTS = [("random", "Aleatoria"), ("ascending", "Ascendente"), ("descending", "Descendente")]
VARIANT_COLORS = ["#38BDF8", "#A3E635", "#F472B6"]
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
    frames = []
    for language, filename in [("C++", "results_cpp.csv"), ("Python", "results_py.csv")]:
        path = RESULTS_DIR / filename
        if not path.exists():
            print(f"WAITING: {path.name} does not exist yet")
            continue
        try:
            frame = pd.read_csv(path, dtype={"algorithm": str, "variant": str, "status": str})
        except (pd.errors.EmptyDataError, OSError) as error:
            print(f"WARNING: Cannot read {path.name}: {error}")
            continue
        required = {"algorithm", "variant", "n", "average_ms", "status"}
        if not required.issubset(frame.columns):
            print(f"WARNING: {path.name} has missing columns: {required - set(frame.columns)}")
            continue
        frame["language"] = language
        frame["n"] = pd.to_numeric(frame["n"], errors="coerce")
        frame["average_ms"] = pd.to_numeric(frame["average_ms"], errors="coerce")
        frame["status"] = frame["status"].astype(str).str.lower().str.strip()
        frame = frame.loc[
            frame["status"].isin(["measured", "estimated"])
            & frame["average_ms"].notna() & (frame["average_ms"] > 0)
            & frame["n"].isin(SIZES)
        ].copy()
        duplicates = frame.duplicated(["algorithm", "variant", "n"], keep=False)
        if duplicates.any():
            warnings.warn(f"Duplicate results in {path.name}; using the last matching row")
        frame = frame.drop_duplicates(["algorithm", "variant", "n"], keep="last")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def lookup(frame, language, algorithm, variant, size):
    matches = frame.loc[
        (frame["language"] == language) & (frame["algorithm"] == algorithm)
        & (frame["variant"] == variant) & (frame["n"] == size)
    ]
    return None if matches.empty else matches.iloc[-1]


def formatTime(value):
    if value >= 100_000:
        return f"{value / 1000:.0f}s"
    if value >= 1000:
        return f"{value / 1000:.2f}s"
    if value >= 1:
        return f"{value:.2f}ms"
    return f"{value:.3f}ms"


def styleAxes(ax, xlabel="Elementos (n)", ylabel="Tiempo promedio (ms)"):
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


def plotGrowth(frame, language):
    fig, ax = plt.subplots(figsize=(13, 7.2))
    found = False
    for algorithm in ALGORITHMS:
        points = []
        for size in SIZES:
            row = lookup(frame, language, algorithm, "random", size)
            if row is not None:
                points.append((size, float(row["average_ms"]), row["status"]))
        if not points:
            continue
        found = True
        color = COLORS[algorithm]
        actual = [(n, t) for n, t, status in points if status == "measured"]
        if actual:
            ax.plot([p[0] for p in actual], [p[1] for p in actual],
                    color=color, marker="o", linewidth=2.4, markersize=7, label=DISPLAY[algorithm])
        else:
            ax.plot([], [], color=color, marker="o", label=DISPLAY[algorithm])
        for n, t, status in points:
            if status == "estimated":
                previous = [p for p in points if p[0] < n]
                if previous:
                    start = previous[-1]
                    ax.plot([start[0], n], [start[1], t], color=color, linestyle="--", linewidth=2.4)
                ax.scatter(n, t, s=95, marker="D", facecolor=BACKGROUND,
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
    ax.set_title(f"CRECIMIENTO DE ALGORITMOS  |  {language.upper()}\nEntrada aleatoria · ambos ejes logarítmicos",
                 loc="left", pad=20)
    ax.legend(loc="best", ncol=2, fontsize=10)
    fig.text(0.11, 0.02, "● medido     ◇ estimado · tramo discontinuo", color=MUTED, fontsize=9)
    saveFigure(fig, "01_growth_cpp.png" if language == "C++" else "02_growth_python.png")


def plotVariants(frame, size, index):
    fig, ax = plt.subplots(figsize=(15.5, 8))
    x = np.arange(len(ALGORITHMS), dtype=float)
    width = 0.25
    present = []
    for variantIndex, (variant, label) in enumerate(VARIANTS):
        xs, values, statuses = [], [], []
        for algorithmIndex, algorithm in enumerate(ALGORITHMS):
            row = lookup(frame, "C++", algorithm, variant, size)
            if row is None:
                continue
            xs.append(x[algorithmIndex] + (variantIndex - 1) * width)
            values.append(float(row["average_ms"]))
            statuses.append(row["status"])
        if not xs:
            continue
        present.extend(values)
        bars = ax.bar(xs, values, width=width, color=VARIANT_COLORS[variantIndex],
                      edgecolor=VARIANT_COLORS[variantIndex], alpha=0.86, label=label)
        for bar, value, status in zip(bars, values, statuses):
            if status == "estimated":
                bar.set_hatch("///")
                bar.set_facecolor("none")
            ax.annotate(formatTime(value), (bar.get_x() + bar.get_width()/2, value),
                        xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                        rotation=90, fontsize=7.8, color=WHITE)
    if not present:
        plt.close(fig)
        return
    ax.set_yscale("log")
    ax.set_ylim(bottom=min(present) / 3, top=max(present) * 9)
    ax.set_xticks(x, [DISPLAY[a] for a in ALGORITHMS], rotation=15, ha="right")
    styleAxes(ax, xlabel="Algoritmo")
    ax.set_title(f"IMPACTO DEL ORDEN INICIAL  |  C++  |  n = {size:,}\nTres variantes por algoritmo · eje temporal logarítmico",
                 loc="left", pad=20)
    ax.legend(ncol=3, loc="upper left")
    fig.text(0.11, 0.015, "Barras rayadas = estimaciones · ausencia de barra = resultado pendiente", color=MUTED, fontsize=9)
    saveFigure(fig, f"{index:02d}_variants_{size}.png")


def plotLanguages(frame):
    size = 1_000_000
    fig, ax = plt.subplots(figsize=(15.5, 8))
    x = np.arange(len(ALGORITHMS), dtype=float)
    width = 0.36
    present = []
    for languageIndex, (language, color) in enumerate([("C++", "#38BDF8"), ("Python", "#F472B6")]):
        xs, values, statuses = [], [], []
        for algorithmIndex, algorithm in enumerate(ALGORITHMS):
            row = lookup(frame, language, algorithm, "random", size)
            if row is None:
                continue
            xs.append(x[algorithmIndex] + (languageIndex - 0.5) * width)
            values.append(float(row["average_ms"]))
            statuses.append(row["status"])
        if not xs:
            continue
        present.extend(values)
        bars = ax.bar(xs, values, width, color=color, edgecolor=color,
                      alpha=0.9, label=language)
        for bar, value, status in zip(bars, values, statuses):
            if status == "estimated":
                bar.set_hatch("///")
                bar.set_facecolor("none")
            ax.annotate(formatTime(value), (bar.get_x() + bar.get_width()/2, value),
                        xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                        rotation=90, fontsize=8, color=WHITE)
    if not present:
        plt.close(fig)
        return
    ax.set_yscale("log")
    ax.set_ylim(bottom=min(present) / 3, top=max(present) * 9)
    ax.set_xticks(x, [DISPLAY[a] for a in ALGORITHMS], rotation=15, ha="right")
    styleAxes(ax, xlabel="Algoritmo")
    ax.set_title("C++ VS PYTHON  |  1.000.000 ELEMENTOS\nEntrada aleatoria · eje temporal logarítmico",
                 loc="left", pad=20)
    ax.legend(handles=[
        Patch(facecolor="#38BDF8", edgecolor="#38BDF8", label="C++"),
        Patch(facecolor="#F472B6", edgecolor="#F472B6", label="Python"),
    ], loc="upper left", ncol=2)
    fig.text(0.11, 0.015, "Barras rayadas = estimaciones · ausencia de barra = resultado pendiente", color=MUTED, fontsize=9)
    saveFigure(fig, "06_cpp_vs_python_1000000.png")


def main():
    dashboardPath = buildDashboard()
    print(f"CREATED: {dashboardPath.relative_to(PROJECT_DIR)}")
    setTheme()
    frame = loadResults()
    if frame.empty:
        print("No measured or estimated results are available yet.")
        return
    plotGrowth(frame, "C++")
    plotGrowth(frame, "Python")
    for index, size in enumerate([1_000, 10_000, 100_000], start=3):
        plotVariants(frame, size, index)
    plotLanguages(frame)
    print("Done. Incomplete figures will become more complete as the CSV files grow.")


if __name__ == "__main__":
    main()
