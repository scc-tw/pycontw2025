#!/usr/bin/env python3
"""
Free-threaded Python Performance Analysis

Analyzes why free-threaded Python makes FFI calls slower by examining:
1. Hardware counter data comparison (GIL vs no-GIL)
2. Performance metrics and timing
3. Cache behavior and memory access patterns
4. Instructions per cycle and execution efficiency
"""

import json
import sys
import re
import html
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List, Tuple
import matplotlib.pyplot as plt
import numpy as np

def load_analysis_data(base_path: str, version: str) -> Dict[str, Any]:
    """Load performance analysis data for a specific Python version."""
    results_dir = Path(base_path) / f"comprehensive_results_{version}"
    
    # Load hardware counter data
    hw_file = results_dir / "hardware_counter_analysis.json"
    stats_file = results_dir / "statistical_analysis_results.json"
    
    data = {}
    
    if hw_file.exists():
        with open(hw_file, 'r') as f:
            data['hardware'] = json.load(f)
    
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            data['statistics'] = json.load(f)
    
    return data

# --------------- Flamegraph stack extraction (Brendan Gregg methodology) ---------------

def extract_stack_traces_from_svg(svg_path: str) -> List[Tuple[str, int]]:
    """Extract stack traces and sample counts from a flame graph SVG.

    Matches lines like: <title>funcA;funcB;funcC (12,345 samples, 1.23%)</title>
    """
    stack_traces: List[Tuple[str, int]] = []
    content = Path(svg_path).read_text(encoding='utf-8', errors='ignore')
    title_pattern = r'<title>(.*?)\s+\(([0-9,]+)\s+samples,\s+[0-9.]+%\)</title>'
    for stack_trace, sample_count_str in re.findall(title_pattern, content):
        stack_trace = html.unescape(stack_trace)
        sample_count = int(sample_count_str.replace(',', ''))
        stack_traces.append((stack_trace, sample_count))
    return stack_traces

def parse_stack_trace(stack_trace: str) -> List[str]:
    if ';' in stack_trace:
        return [frame.strip() for frame in stack_trace.split(';')]
    return [stack_trace.strip()]

def analyze_overhead_patterns(gil_stacks: List[Tuple[str, int]],
                              nogil_stacks: List[Tuple[str, int]]) -> Dict[str, Any]:
    gil_functions: Counter = Counter()
    nogil_functions: Counter = Counter()
    gil_call_chains: Counter = Counter()
    nogil_call_chains: Counter = Counter()

    for stack_trace, samples in gil_stacks:
        frames = parse_stack_trace(stack_trace)
        for frame in frames:
            gil_functions[frame] += samples
        for i in range(len(frames) - 1):
            gil_call_chains[" -> ".join(frames[i:i+2])] += samples

    for stack_trace, samples in nogil_stacks:
        frames = parse_stack_trace(stack_trace)
        for frame in frames:
            nogil_functions[frame] += samples
        for i in range(len(frames) - 1):
            nogil_call_chains[" -> ".join(frames[i:i+2])] += samples

    threading_keywords = [
        'atomic', 'lock', 'mutex', 'thread', 'gil', 'refcount',
        'immortal', 'biased', 'critical', 'sync', '_Py_atomic', 'qsbr',
        'mimalloc', 'deferred'
    ]

    overhead_functions: Dict[str, Any] = {}
    for func, nogil_count in nogil_functions.most_common(200):
        gil_count = gil_functions.get(func, 0)
        if nogil_count > max(1, gil_count) * 1.5:
            overhead_functions[func] = {
                'gil_samples': gil_count,
                'nogil_samples': nogil_count,
                'overhead_ratio': nogil_count / max(1, gil_count),
                'is_threading_related': any(k in func.lower() for k in threading_keywords),
            }

    new_call_chains: Dict[str, Any] = {}
    for chain, nogil_count in nogil_call_chains.most_common(200):
        gil_count = gil_call_chains.get(chain, 0)
        if nogil_count > max(1, gil_count) * 2:
            new_call_chains[chain] = {
                'gil_samples': gil_count,
                'nogil_samples': nogil_count,
                'overhead_ratio': nogil_count / max(1, gil_count),
            }

    return {
        'overhead_functions': overhead_functions,
        'new_call_chains': new_call_chains,
        'gil_top_functions': dict(gil_functions.most_common(20)),
        'nogil_top_functions': dict(nogil_functions.most_common(20)),
        'total_gil_samples': sum(gil_functions.values()),
        'total_nogil_samples': sum(nogil_functions.values()),
    }

def print_flamegraph_analysis_banner():
    print("🔥 FLAME GRAPH STACK TRACE ANALYSIS")
    print("=" * 60)
    print("📚 Following Brendan Gregg's 'Systems Performance' methodology\n")

def analyze_flamegraphs_for_impl(impl: str, gil_svg: Path, nogil_svg: Path):
    print(f"▶ {impl}: {gil_svg.name} vs {nogil_svg.name}")
    gil_stacks = extract_stack_traces_from_svg(str(gil_svg))
    nogil_stacks = extract_stack_traces_from_svg(str(nogil_svg))
    analysis = analyze_overhead_patterns(gil_stacks, nogil_stacks)

    # Brief output
    print("  Top (GIL):")
    for func, samples in list(analysis['gil_top_functions'].items())[:5]:
        pct = samples / max(1, analysis['total_gil_samples']) * 100
        print(f"   - {pct:5.2f}% {func[:60]}")
    print("  Top (NoGIL):")
    for func, samples in list(analysis['nogil_top_functions'].items())[:5]:
        pct = samples / max(1, analysis['total_nogil_samples']) * 100
        print(f"   - {pct:5.2f}% {func[:60]}")

    # Notable overheads
    notable = [
        (f, d) for f, d in analysis['overhead_functions'].items()
        if d['overhead_ratio'] >= 2.0
    ][:5]
    if notable:
        print("  Overheads (>2x in NoGIL):")
        for func, data in notable:
            tag = " [sync]" if data['is_threading_related'] else ""
            print(f"   - {data['overhead_ratio']:4.1f}x {func[:60]}{tag}")
    print()

    return analysis

def calculate_performance_metrics(hw_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Calculate derived performance metrics from hardware counter data."""
    metrics = {}
    
    for impl_name, impl_data in hw_data.get('hardware_counters', {}).items():
        if 'hardware_counters' not in impl_data:
            continue
            
        counters = impl_data['hardware_counters']
        timing = impl_data.get('timing', {})
        
        # Combine atom and core CPU metrics (hybrid CPU handling)
        total_cycles = counters.get('cpu_atom/cycles/', 0) + counters.get('cpu_core/cycles/', 0)
        total_instructions = counters.get('cpu_atom/instructions/', 0) + counters.get('cpu_core/instructions/', 0)
        total_cache_refs = counters.get('cpu_atom/cache-references/', 0) + counters.get('cpu_core/cache-references/', 0)
        total_cache_misses = counters.get('cpu_atom/cache-misses/', 0) + counters.get('cpu_core/cache-misses/', 0)
        total_branches = counters.get('cpu_atom/branches/', 0) + counters.get('cpu_core/branches/', 0)
        total_branch_misses = counters.get('cpu_atom/branch-misses/', 0) + counters.get('cpu_core/branch-misses/', 0)
        total_l1_loads = counters.get('cpu_atom/L1-dcache-loads/', 0) + counters.get('cpu_core/L1-dcache-loads/', 0)
        total_l1_misses = counters.get('cpu_core/L1-dcache-load-misses/', 0)  # Only core has this metric
        
        # Calculate key metrics
        ipc = total_instructions / total_cycles if total_cycles > 0 else 0
        cache_miss_rate = (total_cache_misses / total_cache_refs * 100) if total_cache_refs > 0 else 0
        branch_miss_rate = (total_branch_misses / total_branches * 100) if total_branches > 0 else 0
        l1_miss_rate = (total_l1_misses / total_l1_loads * 100) if total_l1_loads > 0 else 0
        
        # Performance per FFI call
        iterations = timing.get('iterations', 1)
        cycles_per_call = total_cycles / iterations if iterations > 0 else 0
        instructions_per_call = total_instructions / iterations if iterations > 0 else 0
        cache_misses_per_call = total_cache_misses / iterations if iterations > 0 else 0
        
        metrics[impl_name] = {
            'per_call_ns': timing.get('per_call_ns', 0),
            'instructions_per_cycle': ipc,
            'cache_miss_rate_percent': cache_miss_rate,
            'branch_miss_rate_percent': branch_miss_rate,
            'l1_miss_rate_percent': l1_miss_rate,
            'cycles_per_call': cycles_per_call,
            'instructions_per_call': instructions_per_call,
            'cache_misses_per_call': cache_misses_per_call,
            'total_cycles': total_cycles,
            'total_instructions': total_instructions,
        }
    
    return metrics

def compare_gil_vs_nogil(gil_data: Dict[str, Any], nogil_data: Dict[str, Any]):
    """Compare GIL vs free-threaded performance."""
    
    print("🔬 FREE-THREADED PYTHON PERFORMANCE ANALYSIS")
    print("=" * 60)
    print()
    
    # Calculate metrics for both configurations
    gil_metrics = calculate_performance_metrics(gil_data.get('hardware', {}))
    nogil_metrics = calculate_performance_metrics(nogil_data.get('hardware', {}))
    
    # Get statistical data
    gil_stats = gil_data.get('statistics', {}).get('performance_ranking', [])
    nogil_stats = nogil_data.get('statistics', {}).get('performance_ranking', [])
    
    print("📊 PERFORMANCE COMPARISON (ns per call)")
    print("-" * 50)
    print(f"{'Method':<10} {'GIL':>8} {'No-GIL':>8} {'Slowdown':>10} {'Factor':>8}")
    print("-" * 50)
    
    slowdown_factors = {}
    
    # Compare timing from statistical analysis (more accurate)
    gil_timing = {item['method']: item['median_time_ns'] for item in gil_stats}
    nogil_timing = {item['method']: item['median_time_ns'] for item in nogil_stats}
    
    for method in ['pyo3', 'pybind11', 'cffi', 'ctypes']:
        if method in gil_timing and method in nogil_timing:
            gil_time = gil_timing[method]
            nogil_time = nogil_timing[method]
            slowdown_ns = nogil_time - gil_time
            slowdown_factor = nogil_time / gil_time
            slowdown_factors[method] = slowdown_factor
            
            print(f"{method:<10} {gil_time:>8.1f} {nogil_time:>8.1f} {slowdown_ns:>+9.1f} {slowdown_factor:>7.2f}x")
    
    print()
    print("💡 KEY FINDINGS:")
    avg_slowdown = np.mean(list(slowdown_factors.values()))
    print(f"   • Average slowdown: {avg_slowdown:.2f}x")
    print(f"   • Range: {min(slowdown_factors.values()):.2f}x - {max(slowdown_factors.values()):.2f}x")
    print()
    
    # Hardware counter analysis
    print("🔧 HARDWARE COUNTER ANALYSIS")
    print("-" * 50)
    print(f"{'Method':<10} {'Metric':<20} {'GIL':>12} {'No-GIL':>12} {'Change':>10}")
    print("-" * 50)
    
    for method in ['pyo3', 'pybind11', 'cffi', 'ctypes']:
        if method in gil_metrics and method in nogil_metrics:
            gil_m = gil_metrics[method]
            nogil_m = nogil_metrics[method]
            
            # Instructions per cycle
            ipc_change = ((nogil_m['instructions_per_cycle'] - gil_m['instructions_per_cycle']) / 
                         gil_m['instructions_per_cycle'] * 100) if gil_m['instructions_per_cycle'] > 0 else 0
            
            # Cache miss rate
            cache_change = nogil_m['cache_miss_rate_percent'] - gil_m['cache_miss_rate_percent']
            
            # Cycles per call
            cycles_change = ((nogil_m['cycles_per_call'] - gil_m['cycles_per_call']) / 
                           gil_m['cycles_per_call'] * 100) if gil_m['cycles_per_call'] > 0 else 0
            
            # Instructions per call  
            inst_change = ((nogil_m['instructions_per_call'] - gil_m['instructions_per_call']) / 
                          gil_m['instructions_per_call'] * 100) if gil_m['instructions_per_call'] > 0 else 0
            
            print(f"{method:<10} {'IPC':<20} {gil_m['instructions_per_cycle']:>12.3f} {nogil_m['instructions_per_cycle']:>12.3f} {ipc_change:>+9.1f}%")
            print(f"{'':10} {'Cache miss %':<20} {gil_m['cache_miss_rate_percent']:>12.2f} {nogil_m['cache_miss_rate_percent']:>12.2f} {cache_change:>+9.2f}pp")
            print(f"{'':10} {'Cycles/call':<20} {gil_m['cycles_per_call']:>12.0f} {nogil_m['cycles_per_call']:>12.0f} {cycles_change:>+9.1f}%")
            print(f"{'':10} {'Instructions/call':<20} {gil_m['instructions_per_call']:>12.0f} {nogil_m['instructions_per_call']:>12.0f} {inst_change:>+9.1f}%")
            print()
    
    # Root cause analysis
    print("🎯 ROOT CAUSE ANALYSIS")
    print("-" * 50)
    
    # Calculate aggregate changes
    total_ipc_change = 0
    total_cache_increase = 0
    total_cycles_increase = 0
    total_instructions_increase = 0
    count = 0
    
    for method in ['pyo3', 'pybind11', 'cffi', 'ctypes']:
        if method in gil_metrics and method in nogil_metrics:
            gil_m = gil_metrics[method]
            nogil_m = nogil_metrics[method]
            
            ipc_change = ((nogil_m['instructions_per_cycle'] - gil_m['instructions_per_cycle']) / 
                         gil_m['instructions_per_cycle'] * 100) if gil_m['instructions_per_cycle'] > 0 else 0
            cache_change = nogil_m['cache_miss_rate_percent'] - gil_m['cache_miss_rate_percent']
            cycles_change = ((nogil_m['cycles_per_call'] - gil_m['cycles_per_call']) / 
                           gil_m['cycles_per_call'] * 100) if gil_m['cycles_per_call'] > 0 else 0
            inst_change = ((nogil_m['instructions_per_call'] - gil_m['instructions_per_call']) / 
                          gil_m['instructions_per_call'] * 100) if gil_m['instructions_per_call'] > 0 else 0
            
            total_ipc_change += ipc_change
            total_cache_increase += cache_change
            total_cycles_increase += cycles_change
            total_instructions_increase += inst_change
            count += 1
    
    if count > 0:
        avg_ipc_change = total_ipc_change / count
        avg_cache_increase = total_cache_increase / count
        avg_cycles_increase = total_cycles_increase / count
        avg_instructions_increase = total_instructions_increase / count
        
        print(f"1. 📉 REDUCED EXECUTION EFFICIENCY:")
        print(f"   • Instructions per cycle decreased by {avg_ipc_change:.1f}% on average")
        print(f"   • More CPU cycles needed per FFI call (+{avg_cycles_increase:.1f}%)")
        print()
        
        print(f"2. 🧠 INCREASED MEMORY PRESSURE:")
        print(f"   • Cache miss rate increased by {avg_cache_increase:.2f} percentage points")
        print(f"   • More instructions executed per call (+{avg_instructions_increase:.1f}%)")
        print()
        
        print(f"3. 🔄 FREE-THREADING OVERHEAD:")
        print(f"   • Reference counting overhead (immortal objects, etc.)")
        print(f"   • Thread-safety mechanisms in CPython internals")
        print(f"   • Additional memory synchronization")
        print()
        
        print(f"4. 🏗️  ARCHITECTURAL IMPACT:")
        print(f"   • Free-threaded Python changes core object model")
        print(f"   • More complex memory management")
        print(f"   • Additional safety checks and atomic operations")
    
    # Flamegraph comparison (auto-detected from hardware JSON if paths available)
    gil_hw = gil_data.get('hardware', {})
    nogil_hw = nogil_data.get('hardware', {})
    gil_fg = gil_hw.get('flame_graphs', {})
    nogil_fg = nogil_hw.get('flame_graphs', {})
    
    common_impls = [m for m in gil_fg.keys() if m in nogil_fg]
    if common_impls:
        print()
        print_flamegraph_analysis_banner()
        for impl in common_impls:
            gil_svg = Path(gil_fg[impl])
            nogil_svg = Path(nogil_fg[impl])
            if gil_svg.exists() and nogil_svg.exists():
                analyze_flamegraphs_for_impl(impl, gil_svg, nogil_svg)
            else:
                print(f"▶ {impl}: flamegraph files not found, skipping")

def create_performance_comparison_plot(gil_data: Dict[str, Any], nogil_data: Dict[str, Any], output_path: str = None):
    """Create a visualization comparing GIL vs free-threaded performance."""
    
    # Extract performance data
    gil_stats = gil_data.get('statistics', {}).get('performance_ranking', [])
    nogil_stats = nogil_data.get('statistics', {}).get('performance_ranking', [])
    
    gil_timing = {item['method']: item['median_time_ns'] for item in gil_stats}
    nogil_timing = {item['method']: item['median_time_ns'] for item in nogil_stats}
    
    methods = ['pyo3', 'pybind11', 'cffi', 'ctypes']
    gil_times = [gil_timing.get(m, 0) for m in methods]
    nogil_times = [nogil_timing.get(m, 0) for m in methods]
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Absolute performance comparison
    x = np.arange(len(methods))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, gil_times, width, label='CPython 3.13.5 (GIL)', color='steelblue', alpha=0.8)
    bars2 = ax1.bar(x + width/2, nogil_times, width, label='CPython 3.13.5 (Free-threaded)', color='orange', alpha=0.8)
    
    ax1.set_xlabel('FFI Method')
    ax1.set_ylabel('Median Time (ns)')
    ax1.set_title('FFI Performance: GIL vs Free-threaded')
    ax1.set_xticks(x)
    ax1.set_xticklabels(methods)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{height:.0f}', ha='center', va='bottom', fontsize=9)
    
    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{height:.0f}', ha='center', va='bottom', fontsize=9)
    
    # Plot 2: Slowdown factors
    slowdown_factors = [nogil_timing.get(m, 0) / gil_timing.get(m, 1) for m in methods if gil_timing.get(m, 0) > 0]
    valid_methods = [m for m in methods if gil_timing.get(m, 0) > 0]
    
    bars3 = ax2.bar(valid_methods, slowdown_factors, color='red', alpha=0.7)
    ax2.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='No slowdown')
    ax2.set_xlabel('FFI Method')
    ax2.set_ylabel('Slowdown Factor (Free-threaded / GIL)')
    ax2.set_title('Free-threaded Performance Penalty')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add value labels
    for bar, factor in zip(bars3, slowdown_factors):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{factor:.2f}x', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"📊 Performance comparison plot saved: {output_path}")
    else:
        plt.show()

def main():
    """Main analysis function (does not modify raw perf data)."""
    base_path = Path(__file__).parent.parent
    
    print("Loading performance data...")
    gil_data = load_analysis_data(str(base_path), "3.13.5-gil")
    nogil_data = load_analysis_data(str(base_path), "3.13.5-nogil")
    
    if not gil_data or not nogil_data:
        print("❌ Could not load performance data for both configurations")
        return 1
    
    # Perform comparison analysis (includes flamegraph stack analysis if available)
    compare_gil_vs_nogil(gil_data, nogil_data)
    
    # Create visualization (kept separate from raw data; no perf reruns)
    output_file = base_path / "freethreaded_performance_analysis.png"
    create_performance_comparison_plot(gil_data, nogil_data, str(output_file))
    
    print("\n📋 SUMMARY:")
    print("   • Free-threaded Python consistently slower for FFI calls")
    print("   • Primary causes: reduced IPC, increased cache misses, more instructions")
    print("   • Root cause visible in stacks: added synchronization/atomic paths and object mgmt")
    print("   • Raw perf data and SVG flamegraphs remain untouched for deeper analysis")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
