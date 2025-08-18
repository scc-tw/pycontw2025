#!/usr/bin/env python3
"""
viz_bench_from_json.py

Render a benchmark scatter plot + two side tables from a JSON file that already
contains descriptive stats and pairwise test results. We DO NOT recompute
p-values; we only display what's in the JSON. Descriptive stats shown in the
table (and vertical lines) are computed from the *shown data* after outlier
dropping, unless --use-json-stats is specified.

Usage:
  python viz_bench_from_json.py --in path/to/statistical_analysis_results.json --out figure.png
  # Optional:
  python viz_bench_from_json.py --in .../3.13.5-gil/statistical_analysis_results.json --out fig.png --iqr-mult 1.5
  python viz_bench_from_json.py --in ... --out fig.png --use-json-stats

Notes:
- Outliers are dropped per method using Tukey's IQR rule (Q1 - k*IQR, Q3 + k*IQR).
- Right-hand tables have colored method names matching the scatter colors.
- Tables are positioned near the vertical middle.
- Title is inferred from the input path:
    ".../3.13.5-gil/..."  -> "CPython 3.13.5 (GIL)"
    ".../3.13.5-nogil/..."-> "CPython 3.13.5 (Free-threaded)"
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


# ------------------- Helpers -------------------

def infer_title_from_path(path: str) -> str:
    m = re.search(r"(\d+\.\d+\.\d+)-(nogil|gil)", path)
    if not m:
        return "Benchmark"
    ver, tag = m.group(1), m.group(2).lower()
    mode = "Free-threaded" if tag == "nogil" else "GIL"
    return f"CPython {ver} ({mode})"

def drop_outliers_iqr(x: np.ndarray, k: float = 1.5) -> np.ndarray:
    """Return filtered array after removing Tukey IQR outliers."""
    if x.size == 0:
        return x
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return x
    lo, hi = q1 - k * iqr, q3 + k * iqr
    return x[(x >= lo) & (x <= hi)]  # vectorized &/| is wrong; use bitwise
    # Correction:
    # return x[(x >= lo) & (x <= hi)]

def compute_stats_from_shown(x: np.ndarray) -> Dict[str, float]:
    """Compute stats on displayed data (after outlier drop)."""
    if x.size == 0:
        return dict(median=np.nan, mean=np.nan, q25=np.nan, q75=np.nan,
                    cv=np.nan, skewness=np.nan, kurtosis=np.nan, std=np.nan, mad=np.nan)
    mu = float(np.mean(x))
    med = float(np.median(x))
    std = float(np.std(x, ddof=1)) if x.size > 1 else 0.0
    q25, q75 = np.percentile(x, [25, 75])
    cv = (std / mu) if mu else np.nan
    # Central moments for skew/kurt (excess)
    if std > 0 and x.size >= 3:
        m3 = float(np.mean((x - mu) ** 3))
        skew = m3 / (std ** 3)
    else:
        skew = 0.0
    if std > 0 and x.size >= 4:
        m4 = float(np.mean((x - mu) ** 4))
        kurt = m4 / (std ** 4) - 3.0
    else:
        kurt = 0.0
    mad = 1.4826 * float(np.median(np.abs(x - med)))  # ~std for normal
    return dict(median=med, mean=mu, q25=float(q25), q75=float(q75),
                cv=float(cv) if np.isfinite(cv) else np.nan,
                skewness=float(skew), kurtosis=float(kurt),
                std=float(std), mad=float(mad))


# ------------------- Data shapes -------------------

@dataclass
class MethodSeries:
    name: str
    raw: np.ndarray          # original
    shown: np.ndarray        # after outlier drop
    stats: Dict[str, float]  # stats for lines/table (either computed or from JSON)

@dataclass
class PairwiseRow:
    comparison: str
    p_value: Optional[float]
    bh_p_value: Optional[float]
    faster: str


# ------------------- Parsing -------------------

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_series(raw: dict, iqr_mult: float, use_json_stats: bool) -> List[MethodSeries]:
    # Respect insertion order from JSON
    result: List[MethodSeries] = []
    for name, arr in raw["sample_data"].items():
        x = np.asarray(arr, dtype=float)
        xf = drop_outliers_iqr(x, iqr_mult)
        if use_json_stats:
            # Try to pick up stats for this method from the JSON (first occurrence)
            stats = _pick_method_stats_from_json(raw, name) or compute_stats_from_shown(xf)
        else:
            stats = compute_stats_from_shown(xf)
        result.append(MethodSeries(name=name, raw=x, shown=xf, stats=stats))
    return result

def _pick_method_stats_from_json(raw: dict, method: str) -> Optional[Dict[str, float]]:
    mc = raw.get("multiple_comparisons", {}).get("comparisons", [])
    for comp in mc:
        ds = comp.get("descriptive_stats", {})
        if method in ds:
            s = ds[method]
            # Map keys we care about (ignore anything missing)
            out = {k: float(s[k]) for k in ["median", "mean", "q25", "q75"]
                   if k in s and s[k] is not None}
            for k in ["cv", "skewness", "kurtosis", "std", "mad"]:
                if k in s and s[k] is not None:
                    out[k] = float(s[k])
            return out
    # Optional fallback if there is a top-level "method_stats"
    ms = raw.get("method_stats", {}).get(method)
    if ms:
        out = {k: float(ms[k]) for k in ["median", "mean", "q25", "q75"]
               if k in ms and ms[k] is not None}
        for k in ["cv", "skewness", "kurtosis", "std", "mad"]:
            if k in ms and ms[k] is not None:
                out[k] = float(ms[k])
        return out
    return None

def parse_pairwise_table(raw: dict) -> List[PairwiseRow]:
    mc = raw.get("multiple_comparisons", {})
    comps = mc.get("comparisons", []) or []
    corrected = mc.get("corrected_p_values", None)
    rows: List[PairwiseRow] = []
    for i, c in enumerate(comps):
        a, b = c.get("method1", "?"), c.get("method2", "?")
        p = c.get("statistical_test", {}).get("p_value", None)
        bh = None
        if isinstance(corrected, list) and i < len(corrected):
            bh = corrected[i]
        faster = c.get("faster_method", a)
        rows.append(PairwiseRow(f"{a} vs {b}",
                                None if p is None else float(p),
                                None if bh is None else float(bh),
                                faster))
    return rows


# ------------------- Plotting -------------------

def apply_style():
    mpl.rcParams.update({
        "figure.figsize": (19, 10.5),
        "figure.dpi": 120,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "legend.frameon": True,
        "legend.framealpha": 0.95,
        "legend.fancybox": True,
    })

def colorize_table_column(table, col_idx: int, row_colors: List[Tuple[float,float,float]]):
    """Set text color of a given column to match row_colors."""
    for r, color in enumerate(row_colors, start=1):  # +1 skips header row
        cell = table[(r, col_idx)]
        cell.get_text().set_color(color)

def render_figure(raw: dict, infile_path: str, outfile: str, iqr_mult: float,
                  use_json_stats: bool, dpi: int):
    apply_style()

    # Build series and stats (drop outliers here)
    series = build_series(raw, iqr_mult, use_json_stats)
    method_order = [s.name for s in series]

    # Colors
    cmap = plt.get_cmap("tab10").colors
    color_map = {name: cmap[i % len(cmap)] for i, name in enumerate(method_order)}

    # Figure + main axes
    fig, ax = plt.subplots()
    title = infer_title_from_path(infile_path)
    ax.set_title(title, fontweight="bold", fontsize=16, pad=12)
    ax.set_xlabel(raw.get("xlabel", "Execution Time (nanoseconds)"))
    ax.set_ylabel(raw.get("ylabel", "Sample index i"))

    # Scatter per method (shown data after outlier drop)
    for s in series:
        y = np.arange(len(s.shown))
        ax.scatter(s.shown, y, s=14, alpha=0.85, label=s.name, color=color_map[s.name])

    # Vertical lines per method based on stats chosen above
    for s in series:
        st = s.stats
        c = color_map[s.name]
        if "median" in st: ax.axvline(st["median"], color=c, linewidth=2.0, linestyle="-")
        if "mean"   in st: ax.axvline(st["mean"],   color=c, linewidth=1.5, linestyle="--")
        if "q25"    in st: ax.axvline(st["q25"],    color=c, linewidth=1.2, linestyle=":")
        if "q75"    in st: ax.axvline(st["q75"],    color=c, linewidth=1.2, linestyle=":")

    # Legends
    method_legend = ax.legend(title="Method", loc="upper left")
    ax.add_artist(method_legend)
    from matplotlib.lines import Line2D
    lines_legend = ax.legend(
        handles=[
            Line2D([0], [0], color="k", lw=2.0, linestyle="-", label="Median"),
            Line2D([0], [0], color="k", lw=1.5, linestyle="--", label="Mean"),
            Line2D([0], [0], color="k", lw=1.5, linestyle=":", label="Q25/Q75"),
        ],
        title="Lines",
        loc="upper right",
    )
    ax.add_artist(lines_legend)

    # Space for side tables; more room on the right
    plt.subplots_adjust(right=0.70)

    # ---------- Method statistics table (middle-right, colored) ----------
    # Compute table rows in the same order as the scatter legend
    stats_rows = []
    for s in series:
        st = s.stats
        stats_rows.append([
            s.name,
            _fmt(st.get("cv")),
            _fmt(st.get("skewness")),
            _fmt(st.get("kurtosis")),
            _fmt(st.get("std")),
            _fmt(st.get("mad")),
        ])

    stats_ax = fig.add_axes([0.72, 0.50, 0.26, 0.28], frame_on=False)  # moved toward middle
    stats_ax.set_title("Method statistics (shown data)", fontsize=11)
    stats_ax.axis("off")
    table1 = stats_ax.table(
        cellText=stats_rows,
        colLabels=["Indicator", "Cv", "Skewness", "Kurtosis", "Std", "mad"],
        loc="upper center",
        cellLoc="center",
    )
    table1.scale(1.0, 1.2)
    # Colorize "Indicator" column to match scatter colors
    row_colors = [color_map[s.name] for s in series]
    colorize_table_column(table1, col_idx=0, row_colors=row_colors)

    # ---------- Pairwise p-values table (also near middle) ----------
    pr_rows = parse_pairwise_table(raw)
    if pr_rows:
        pv_ax = fig.add_axes([0.70, 0.18, 0.28, 0.28], frame_on=False)  # also near middle
        pv_ax.set_title("Mann–Whitney U p-values and Benjamini–Hochberg adjusted p-values", fontsize=11)
        pv_ax.axis("off")
        pv_cell_rows = []
        for r in pr_rows:
            pv_cell_rows.append([
                r.comparison,
                "" if r.p_value is None else f"{r.p_value:.2e}",
                "" if r.bh_p_value is None else f"{r.bh_p_value:.2e}",
                r.faster
            ])
        table2 = pv_ax.table(
            cellText=pv_cell_rows,
            colLabels=["Comparison", "U p-value", "BH p-value", "Faster"],
            loc="upper center",
            cellLoc="center",
        )
        table2.scale(1.0, 1.2)
        # Colorize the "Faster" column to the method's color (if known)
        faster_colors = [color_map.get(r.faster, (0, 0, 0)) for r in pr_rows]
        colorize_table_column(table2, col_idx=3, row_colors=faster_colors)

    # finalize
    ax.margins(x=0.05)
    fig.savefig(outfile, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return ""
    # keep small numbers readable
    if isinstance(v, float) and abs(v) >= 100:
        return f"{v:.1f}"
    if isinstance(v, float) and abs(v) >= 10:
        return f"{v:.1f}"
    if isinstance(v, float) and abs(v) >= 1:
        return f"{v:.2f}"
    return f"{float(v):.3f}"


# ------------------- CLI -------------------

def main():
    ap = argparse.ArgumentParser(description="Draw benchmark visualization from JSON.")
    ap.add_argument("--in", dest="input", required=True, help="Path to statistical_analysis_results.json")
    ap.add_argument("--out", dest="output", required=True, help="Output figure path (png/pdf/svg)")
    ap.add_argument("--dpi", dest="dpi", type=int, default=150, help="Figure DPI")
    ap.add_argument("--iqr-mult", dest="iqr_mult", type=float, default=1.5,
                    help="IQR multiplier for Tukey outlier rule (default 1.5).")
    ap.add_argument("--use-json-stats", action="store_true",
                    help="Use descriptive stats from JSON instead of recomputing on shown data.")
    args = ap.parse_args()

    raw = load_json(args.input)
    render_figure(raw,
                  infile_path=args.input,
                  outfile=args.output,
                  iqr_mult=args.iqr_mult,
                  use_json_stats=args.use_json_stats,
                  dpi=args.dpi)

if __name__ == "__main__":
    main()
