#!/usr/bin/env python3
"""
Collect core metrics from perf.data following Brendan Gregg's Systems Performance

What this script does (non-destructive):
- Enumerates essential profiling data for root-cause analysis of GIL vs NoGIL differences
- Collects those data from perf.data using `perf report --stdio` and `perf script`
- Produces a structured JSON with per-file metrics and pairwise diffs (GIL vs NoGIL)
- Includes stacktrace-aware summaries (top stacks, lock/syscall signals, Python/runtime signals)

Requirements:
- Linux perf available in PATH
- Optional: FlameGraph scripts (stackcollapse-perf.pl) NOT required; we parse perf script directly

Usage examples:
  python collect_perf_core_metrics.py --root tests/benchmark-ffi --out metrics.json
  python collect_perf_core_metrics.py --gil tests/.../pyo3_profile_*.perf.data --nogil tests/.../pyo3_profile_*.perf.data --out pyo3_metrics.json

This script DOES NOT modify perf.data files.
"""

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ---------------------- Brendan Gregg: essential data to collect ----------------------
ESSENTIAL_DATA = [
    "CPU on-CPU profile: top symbols and percent",
    "Module/DSO breakdown (libpython, libffi, libc, kernel, your .so)",
    "User vs Kernel time share (approx via DSO classification)",
    "Syscall presence in on-CPU stacks",
    "Lock contention indicators (futex, pthread_mutex, spin/rw locks)",
    "Python runtime indicators (Py*/_Py*, vectorcall, refcount/atomic paths)",
    "FFI/lib boundaries (benchlib.so, libffi, pybind11, pyo3)",
    "Top call stacks (collapsed) for hotspot context",
]

# ---------------------- Helpers ----------------------

def run_cmd(cmd: List[str]) -> str:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        # Some perf subcommands write to stderr; prefer stdout when possible
        output = result.stdout.strip()
        if not output:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
        return output
    return result.stdout

# Heuristics for classification
KERNEL_DSOS = {"[kernel.kallsyms]", "vmlinux"}
LOCK_KEYWORDS = ["futex", "pthread_mutex", "__lll_lock", "rwsem_", "spin_lock", "osq_lock", "mutex_"]
SYSCALL_KEYWORDS = ["__x64_sys_", "do_syscall_", "entry_SYSCALL_", "sys_", "ksys_"]
PYTHON_KEYWORDS = ["Py", "_Py", "vectorcall", "PyObject", "PyEval", "PyFrame", "_Py_atomic"]
FFI_KEYWORDS = ["libffi", "pybind11", "pyo3", "benchlib", "ctypes"]

@dataclass
class SymbolEntry:
    percent: float
    dso: str
    symbol: str

@dataclass
class PerfFileMetrics:
    file: str
    total_overhead_percent: float
    user_percent: float
    kernel_percent: float
    top_dsos: List[Tuple[str, float]]
    top_symbols: List[SymbolEntry]
    lock_percent: float
    syscall_percent: float
    python_percent: float
    ffi_percent: float
    top_stacks: List[Tuple[str, int]]

# ---------------------- Parsing perf report --stdio ----------------------

def parse_perf_report_symbols(perf_file: str, percent_limit: float = 0.0) -> Tuple[List[SymbolEntry], Dict[str, float]]:
    """Parse perf report data using two stable passes:
    - Pass 1: sort by symbol to collect symbol-level percentages
    - Pass 2: sort by dso to collect module totals

    Returns (symbol_entries, dso_totals).
    """

    def _parse_table(sort_key: str) -> List[Tuple[float, str]]:
        # Use --no-children for stability and --percent-limit 0 for full table
        cmd = [
            "perf", "report", "--stdio", "--no-children",
            "--percent-limit", str(percent_limit),
            "--sort", sort_key, "-i", perf_file,
        ]
        out = run_cmd(cmd)
        rows: List[Tuple[float, str]] = []
        # Match: " 12.34%  <rest of line>"
        line_re = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)%\s+(.+)$")
        for raw in out.splitlines():
            m = line_re.match(raw)
            if not m:
                continue
            try:
                pct = float(m.group(1))
            except ValueError:
                continue
            tail = m.group(2).strip()
            # perf aligns with at least two spaces between columns; use that to get the last column
            cols = re.split(r"\s{2,}", tail)
            if not cols:
                continue
            last = cols[-1].strip()
            rows.append((pct, last))
        return rows

    # Pass 1: symbols
    symbol_rows = _parse_table("symbol")
    symbol_entries: List[SymbolEntry] = []
    for pct, sym in symbol_rows:
        # Drop perf markers like "[.] " or "[k] " at start
        cleaned = re.sub(r"^\[[^\]]+\]\s*", "", sym)
        symbol_entries.append(SymbolEntry(percent=pct, dso="", symbol=cleaned))

    # Sort symbols by percent desc for top-N consumers
    symbol_entries.sort(key=lambda e: e.percent, reverse=True)

    # Pass 2: DSOs
    dso_rows = _parse_table("dso")
    dso_totals: Dict[str, float] = {}
    for pct, dso in dso_rows:
        dso_totals[dso] = dso_totals.get(dso, 0.0) + pct

    return symbol_entries, dso_totals

# ---------------------- Parsing perf script (stack traces) ----------------------

def parse_perf_script_stacks(perf_file: str, max_samples: int = 500000) -> Dict[str, int]:
    """Parse `perf script` output and build collapsed stacks with simple heuristics.
    Returns mapping: "frame1;frame2;...;frameN" -> count
    """
    cmd = ["perf", "script", "-i", perf_file]
    out = run_cmd(cmd)

    stacks: Dict[str, int] = {}
    current_frames: List[str] = []

    lines = out.splitlines()
    for line in lines:
        if not line.strip():
            # End of a sample block
            if current_frames:
                # Keep order as root->leaf (reverse typical perf script leaf-first listing)
                collapsed = ";".join(reversed(current_frames))
                stacks[collapsed] = stacks.get(collapsed, 0) + 1
                current_frames = []
            continue

        # Frame lines in perf script are typically indented with whitespace and function name
        if line.startswith("\t") or line.startswith("        "):
            frame = line.strip()
            # Remove trailing addresses and annotations like (+0x..)
            frame = re.sub(r"\s+\(.*\)$", "", frame)
            stacks.setdefault("", 0)  # ensure dict initialized
            current_frames.append(frame)
        else:
            # header line for the sample (pid/tid/timestamp). Commit current frames if any
            if current_frames:
                collapsed = ";".join(reversed(current_frames))
                stacks[collapsed] = stacks.get(collapsed, 0) + 1
                current_frames = []

        if len(stacks) > max_samples:
            break

    # flush last
    if current_frames:
        collapsed = ";".join(reversed(current_frames))
        stacks[collapsed] = stacks.get(collapsed, 0) + 1

    return stacks

# ---------------------- Metric computation ----------------------

def classify_percent(entries: List[SymbolEntry]) -> Tuple[float, float, float, float]:
    """Compute lock/syscall/python/ffi percents from symbol entries by keyword heuristics."""
    lock = syscall = python = ffi = 0.0
    for e in entries:
        s = e.symbol.lower()
        d = e.dso.lower()
        if any(k in s for k in LOCK_KEYWORDS):
            lock += e.percent
        if any(k in s for k in SYSCALL_KEYWORDS):
            syscall += e.percent
        if any(k.lower() in s or k.lower() in d for k in PYTHON_KEYWORDS):
            python += e.percent
        if any(k in d or k in s for k in FFI_KEYWORDS):
            ffi += e.percent
    return lock, syscall, python, ffi


def compute_user_kernel_share(dso_totals: Dict[str, float]) -> Tuple[float, float, float]:
    kernel = sum(p for d, p in dso_totals.items() if d in KERNEL_DSOS)
    total = sum(dso_totals.values())
    user = max(0.0, total - kernel)
    return total, user, kernel


def summarize_perf_file(perf_path: str, top_n: int = 30) -> PerfFileMetrics:
    symbols, dso_totals = parse_perf_report_symbols(perf_path)
    total_pct, user_pct, kernel_pct = compute_user_kernel_share(dso_totals)
    lock_pct, syscall_pct, python_pct, ffi_pct = classify_percent(symbols)
    stacks = parse_perf_script_stacks(perf_path)

    # Prepare outputs
    top_dsos = sorted(dso_totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_symbols = symbols[:top_n]
    top_stacks = sorted(stacks.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return PerfFileMetrics(
        file=str(perf_path),
        total_overhead_percent=total_pct,
        user_percent=user_pct,
        kernel_percent=kernel_pct,
        top_dsos=top_dsos,
        top_symbols=top_symbols,
        lock_percent=lock_pct,
        syscall_percent=syscall_pct,
        python_percent=python_pct,
        ffi_percent=ffi_pct,
        top_stacks=top_stacks,
    )

# ---------------------- Pairing and diff ----------------------

def diff_metrics(gil: PerfFileMetrics, nogil: PerfFileMetrics) -> Dict[str, Any]:
    def pct(x: float) -> float:
        return round(x, 3)

    return {
        "files": {"gil": gil.file, "nogil": nogil.file},
        "user_percent_delta": pct(nogil.user_percent - gil.user_percent),
        "kernel_percent_delta": pct(nogil.kernel_percent - gil.kernel_percent),
        "lock_percent_delta": pct(nogil.lock_percent - gil.lock_percent),
        "syscall_percent_delta": pct(nogil.syscall_percent - gil.syscall_percent),
        "python_percent_delta": pct(nogil.python_percent - gil.python_percent),
        "ffi_percent_delta": pct(nogil.ffi_percent - gil.ffi_percent),
        "top_dso_deltas": _top_dso_deltas(gil.top_dsos, nogil.top_dsos),
        "notes": _quick_notes(gil, nogil),
    }


def _top_dso_deltas(g_top: List[Tuple[str, float]], n_top: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
    g_map = {d: p for d, p in g_top}
    n_map = {d: p for d, p in n_top}
    dsos = set(g_map) | set(n_map)
    out = []
    for d in sorted(dsos, key=lambda d: n_map.get(d, 0.0) - g_map.get(d, 0.0), reverse=True)[:15]:
        out.append({
            "dso": d,
            "gil": round(g_map.get(d, 0.0), 3),
            "nogil": round(n_map.get(d, 0.0), 3),
            "delta": round(n_map.get(d, 0.0) - g_map.get(d, 0.0), 3),
        })
    return out


def _quick_notes(g: PerfFileMetrics, n: PerfFileMetrics) -> List[str]:
    notes = []
    if n.lock_percent > g.lock_percent * 1.2:
        notes.append("Increased lock/futex activity in NoGIL")
    if n.kernel_percent > g.kernel_percent * 1.2:
        notes.append("More time in kernel (syscalls/scheduling) in NoGIL")
    if n.python_percent > g.python_percent * 1.2:
        notes.append("More time in Python runtime internals in NoGIL")
    if n.ffi_percent > g.ffi_percent * 1.2:
        notes.append("More time at FFI/bridge boundaries in NoGIL")
    return notes

# ---------------------- Discovery ----------------------

def discover_perf_pairs(root: Path) -> List[Tuple[Path, Path]]:
    """Find pairs of perf.data files for (GIL, NoGIL) by implementation name."""
    # Assumes directory names include comprehensive_results_*-(gil|nogil)
    # and filenames like <impl>_profile_*.perf.data
    gil_dirs = list(root.glob("comprehensive_results_*_gil")) + list(root.glob("comprehensive_results_* -gil"))
    nogil_dirs = list(root.glob("comprehensive_results_*_nogil")) + list(root.glob("comprehensive_results_* -nogil"))

    impl_to_gil: Dict[str, Path] = {}
    impl_to_nogil: Dict[str, Path] = {}

    for d in gil_dirs:
        for f in d.glob("*_profile_*.perf.data"):
            impl = f.name.split("_profile_")[0]
            impl_to_gil[impl] = f
    for d in nogil_dirs:
        for f in d.glob("*_profile_*.perf.data"):
            impl = f.name.split("_profile_")[0]
            impl_to_nogil[impl] = f

    pairs: List[Tuple[Path, Path]] = []
    for impl, gfile in impl_to_gil.items():
        nfile = impl_to_nogil.get(impl)
        if nfile and gfile.exists() and nfile.exists():
            pairs.append((gfile, nfile))
    return pairs

# ---------------------- Main ----------------------

def main():
    parser = argparse.ArgumentParser(description="Collect core perf metrics and diffs for GIL vs NoGIL")
    parser.add_argument("--root", type=str, default="tests/benchmark-ffi", help="Root to search for perf.data")
    parser.add_argument("--gil", type=str, help="Path to a GIL perf.data file")
    parser.add_argument("--nogil", type=str, help="Path to a NoGIL perf.data file")
    parser.add_argument("--out", type=str, default="perf_core_metrics.json", help="Output JSON path")
    parser.add_argument("--top", type=int, default=30, help="Top N entries to keep")
    args = parser.parse_args()

    root = Path(args.root)

    results: Dict[str, Any] = {
        "essential_data": ESSENTIAL_DATA,
        "files": [],
        "pairs": [],
    }

    pairs: List[Tuple[Path, Path]] = []
    if args.gil and args.nogil:
        pairs = [(Path(args.gil), Path(args.nogil))]
    else:
        pairs = discover_perf_pairs(root)

    # Collect per-file metrics
    seen_files = set()
    for pair in pairs:
        for f in pair:
            if str(f) in seen_files:
                continue
            try:
                m = summarize_perf_file(str(f), top_n=args.top)
                results["files"].append({
                    **asdict(m),
                    "top_symbols": [asdict(s) for s in m.top_symbols],
                })
                seen_files.add(str(f))
            except Exception as e:
                results["files"].append({"file": str(f), "error": str(e)})

    # Pairwise diffs
    for gfile, nfile in pairs:
        gm = next((x for x in results["files"] if x.get("file") == str(gfile)), None)
        nm = next((x for x in results["files"] if x.get("file") == str(nfile)), None)
        if not gm or not nm:
            continue
        try:
            g = PerfFileMetrics(
                file=gm["file"],
                total_overhead_percent=gm["total_overhead_percent"],
                user_percent=gm["user_percent"],
                kernel_percent=gm["kernel_percent"],
                top_dsos=[tuple(x) for x in gm["top_dsos"]],
                top_symbols=[SymbolEntry(**s) for s in gm["top_symbols"]],
                lock_percent=gm["lock_percent"],
                syscall_percent=gm["syscall_percent"],
                python_percent=gm["python_percent"],
                ffi_percent=gm["ffi_percent"],
                top_stacks=[tuple(x) for x in gm["top_stacks"]],
            )
            n = PerfFileMetrics(
                file=nm["file"],
                total_overhead_percent=nm["total_overhead_percent"],
                user_percent=nm["user_percent"],
                kernel_percent=nm["kernel_percent"],
                top_dsos=[tuple(x) for x in nm["top_dsos"]],
                top_symbols=[SymbolEntry(**s) for s in nm["top_symbols"]],
                lock_percent=nm["lock_percent"],
                syscall_percent=nm["syscall_percent"],
                python_percent=nm["python_percent"],
                ffi_percent=nm["ffi_percent"],
                top_stacks=[tuple(x) for x in nm["top_stacks"]],
            )
            results["pairs"].append({
                "gil": g.file,
                "nogil": n.file,
                "diff": diff_metrics(g, n),
            })
        except Exception as e:
            results["pairs"].append({"gil": str(gfile), "nogil": str(nfile), "error": str(e)})

    # Write output
    out_path = Path(args.out)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote core metrics to {out_path}")

if __name__ == "__main__":
    raise SystemExit(main())
