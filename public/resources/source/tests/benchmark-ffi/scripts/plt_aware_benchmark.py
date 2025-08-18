#!/usr/bin/env python3
"""
PLT Cache Aware FFI Benchmark - Academic Rigor Implementation

This script implements proper methodology to separate dynamic linking overhead
from actual FFI performance, addressing critical issues with PLT cache effects.

CRITICAL FIXES:
1. Separates first call (PLT cache miss) from subsequent calls (PLT cached)
2. Saves ALL raw measurement data for academic analysis
3. Implements proper warmup strategy to isolate effects
4. Provides statistically valid comparisons

Based on Brendan Gregg's performance methodology and academic rigor standards.
"""

import sys
import os
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.timer import BenchmarkTimer
from implementations import get_available_implementations
import time
import json

def run_plt_aware_benchmarks():
    """Run PLT cache aware benchmarks with proper methodology."""
    
    print("🔬 PLT Cache Aware FFI Benchmark - Academic Methodology")
    print("=" * 60)
    
    # Initialize timer with academic rigor settings
    timer = BenchmarkTimer(
        target_relative_error=0.01,  # 1% precision
        max_time_seconds=60,         # Allow more time for rigorous analysis
        min_samples=30               # n≥30 for statistical significance
    )
    
    # Get all available implementations
    implementations = get_available_implementations()
    
    if not implementations:
        print("❌ No FFI implementations available!")
        return
    
    print(f"📊 Testing {len(implementations)} FFI implementations:")
    for name in implementations.keys():
        print(f"  ✅ {name}")
    print()
    
    # Test basic function call (return_int) with PLT awareness
    print("🧪 PLT Cache Analysis: Basic Function Call (return_int)")
    print("-" * 50)
    
    results = {}
    
    for impl_name, impl_obj in implementations.items():
        print(f"📈 Analyzing {impl_name}...")
        
        # Define the function to benchmark
        test_func = lambda: impl_obj.return_int()
        
        # Run PLT cache aware measurement
        measurement = timer.measure_cold_vs_hot_path(
            func=test_func,
            func_name=f"{impl_name}_return_int",
            iterations=100  # More iterations for better statistics
        )
        
        results[impl_name] = measurement
        
        # Display results immediately
        first_call = measurement['first_call_time_ns']
        hot_median = measurement['hot_path_stats']['median_ns']
        plt_factor = measurement['plt_overhead_factor']
        
        print(f"  🥶 First call (cold):  {first_call:8.1f} ns")
        print(f"  🔥 Hot path (median):  {hot_median:8.1f} ns")
        print(f"  📊 PLT overhead:       {plt_factor:8.2f}x")
        print()
    
    # Save all raw data for academic analysis
    data_file = timer.save_raw_data('plt_aware_benchmark_data.json')
    
    # Generate academic comparison table (HOT PATH ONLY)
    print("🏆 Academic Results: Hot Path Performance (PLT Cached)")
    print("=" * 70)
    
    # Sort by hot path median time
    sorted_results = sorted(
        results.items(),
        key=lambda x: x[1]['hot_path_stats']['median_ns']
    )
    
    print(f"{'Rank':<6} {'FFI Method':<12} {'Hot Path':<12} {'First Call':<12} {'PLT Factor':<12}")
    print("-" * 70)
    
    fastest_time = sorted_results[0][1]['hot_path_stats']['median_ns']
    
    for rank, (impl_name, measurement) in enumerate(sorted_results, 1):
        hot_time = measurement['hot_path_stats']['median_ns']
        first_time = measurement['first_call_time_ns']
        plt_factor = measurement['plt_overhead_factor']
        relative_speed = hot_time / fastest_time
        
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        
        print(f"{medal} {rank:<3} {impl_name:<12} {hot_time:8.1f} ns    {first_time:8.1f} ns    {plt_factor:8.2f}x")
    
    print()
    print("📋 Key Insights:")
    print(f"   • Raw data saved to: {data_file}")
    print(f"   • Sample size: n={sorted_results[0][1]['hot_path_stats']['samples']} per implementation")
    print(f"   • Methodology: Cold vs Hot path PLT cache analysis")
    print(f"   • Statistical rigor: n≥30 for Mann-Whitney U test validity")
    
    # Show PLT overhead analysis
    print()
    print("🔍 PLT Cache Overhead Analysis:")
    print("-" * 40)
    for impl_name, measurement in sorted_results:
        plt_factor = measurement['plt_overhead_factor']
        print(f"   {impl_name:<12}: {plt_factor:6.2f}x first-call penalty")
    
    return results, data_file

def main():
    """Main entry point."""
    try:
        results, data_file = run_plt_aware_benchmarks()
        
        print()
        print("✅ PLT Cache Aware Benchmark Complete!")
        print(f"📊 Academic-quality raw data saved to: {data_file}")
        print()
        print("🔬 Next Steps for Academic Analysis:")
        print("   1. Load raw data from JSON file")
        print("   2. Perform Mann-Whitney U tests on hot path data")
        print("   3. Calculate Cliff's delta effect sizes")
        print("   4. Generate bootstrap confidence intervals")
        print("   5. Analyze PLT overhead patterns across FFI methods")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())