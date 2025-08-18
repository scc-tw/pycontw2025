#!/usr/bin/env python3
"""Crossover Analysis - FFI Method Performance vs Problem Size"""

import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from implementations import get_available_implementations
import time

def benchmark_at_scale(impl, scale_factor):
    """Benchmark implementation at different scales."""
    # Simple scale test - number of operations
    operations = scale_factor * 100
    
    start_time = time.perf_counter_ns()
    for _ in range(operations):
        impl.return_int()
    end_time = time.perf_counter_ns()
    
    return (end_time - start_time) / operations  # ns per operation

def generate_crossover_analysis():
    """Generate crossover analysis showing where FFI methods cross over."""
    
    implementations = get_available_implementations()
    if len(implementations) < 2:
        print("Need at least 2 implementations for crossover analysis")
        return False
    
    # Test at different scales
    scales = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
    results = {}
    
    print("🔬 Running crossover analysis...")
    
    for impl_name, impl_obj in implementations.items():
        print(f"   Testing {impl_name}...")
        results[impl_name] = []
        
        for scale in scales:
            try:
                time_per_op = benchmark_at_scale(impl_obj, scale)
                results[impl_name].append(time_per_op)
                print(f"      Scale {scale}: {time_per_op:.1f} ns/op")
            except Exception as e:
                print(f"      Scale {scale}: ERROR - {e}")
                results[impl_name].append(float('nan'))
    
    # Generate crossover graph
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, (impl_name, times) in enumerate(results.items()):
        color = colors[i % len(colors)]
        plt.plot(scales, times, 'o-', label=impl_name, color=color, linewidth=2, markersize=6)
    
    plt.xlabel('Scale Factor (operations × 100)', fontsize=12)
    plt.ylabel('Time per Operation (nanoseconds)', fontsize=12)
    plt.title('FFI Method Performance Crossover Analysis\nWhere do different methods become optimal?', fontsize=14)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    plt.yscale('log')
    
    # Save graph
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    graph_file = results_dir / "crossover_analysis_graph.png"
    plt.savefig(graph_file, dpi=300, bbox_inches='tight')
    print(f"📊 Crossover analysis graph saved: {graph_file}")
    
    # Save raw data
    data_file = results_dir / "crossover_analysis_data.json"
    with open(data_file, 'w') as f:
        json.dump({
            'scales': scales,
            'results': results,
            'methodology': 'crossover_analysis_variable_scale'
        }, f, indent=2)
    
    print(f"📊 Crossover analysis data saved: {data_file}")
    return True

if __name__ == "__main__":
    try:
        success = generate_crossover_analysis()
        if success:
            print("✅ Crossover analysis completed successfully")
        else:
            print("❌ Crossover analysis failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
