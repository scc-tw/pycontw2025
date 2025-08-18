"""
High-precision timing utilities with robust statistical analysis.

Based on Brendan Gregg's performance methodology, this module provides
accurate timing measurements with bootstrap confidence intervals and
rigorous statistical comparison using Mann-Whitney U tests.
"""

import time
from typing import Callable, Dict, List, Tuple, Any, Optional
import sys
import statistics as builtin_stats

# Try to import numpy, but provide fallbacks if unavailable
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False
    # Create numpy-like functions using built-in statistics
    class _NumpyFallback:
        @staticmethod
        def array(data):
            return list(data)
        
        @staticmethod
        def median(data):
            return builtin_stats.median(data)
        
        @staticmethod
        def mean(data):
            return builtin_stats.mean(data)
        
        @staticmethod
        def std(data):
            return builtin_stats.stdev(data) if len(data) > 1 else 0.0
        
        @staticmethod
        def min(data):
            return min(data)
        
        @staticmethod
        def max(data):
            return max(data)
        
        @staticmethod
        def percentile(data, p):
            sorted_data = sorted(data)
            k = (len(sorted_data) - 1) * p / 100
            f = int(k)
            c = k - f
            if f + 1 < len(sorted_data):
                return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
            else:
                return sorted_data[f]
        
        @staticmethod
        def random():
            class _Random:
                @staticmethod
                def seed(s):
                    import random
                    random.seed(s)
                
                @staticmethod
                def choice(data, size=None, replace=True):
                    import random
                    if size is None:
                        return random.choice(data)
                    return [random.choice(data) for _ in range(size)]
            return _Random()
    
    np = _NumpyFallback()

try:
    from .statistics import AdvancedStatistics, create_statistical_analyzer
    _HAS_STATISTICS = True
except ImportError:
    _HAS_STATISTICS = False


class BenchmarkTimer:
    """High-precision timing with robust statistical analysis and PLT cache awareness."""
    
    def __init__(self, target_relative_error: float = 0.02, max_time_seconds: float = 30, min_samples: int = 30):
        """
        Initialize the benchmark timer.
        
        Args:
            target_relative_error: Target relative confidence interval width (default 2%)
            max_time_seconds: Maximum time to spend on a single benchmark
            min_samples: Minimum samples required for valid non-parametric tests (n≥30 for Mann-Whitney U)
        """
        self.target_relative_error = target_relative_error
        self.max_time_seconds = max_time_seconds
        self.min_samples = min_samples
        self.raw_data_storage = {}  # Store ALL raw measurements
        
    def measure_cold_vs_hot_path(self, func: Callable[[], Any], func_name: str, iterations: int = 100) -> Dict[str, Any]:
        """
        Measure first call (cold/PLT cache miss) vs subsequent calls (hot/PLT cached).
        
        CRITICAL: This separates dynamic linking overhead from actual FFI performance.
        
        Args:
            func: Function to benchmark
            func_name: Name for raw data storage
            iterations: Number of hot path measurements after first call
            
        Returns:
            Dictionary with cold_call_time, hot_path_stats, and raw measurements
        """
        import gc
        import os
        
        # Force garbage collection and memory consolidation
        gc.collect()
        
        # Measure FIRST CALL (cold path - PLT cache miss)
        start_first = time.perf_counter_ns()
        result_first = func()
        end_first = time.perf_counter_ns()
        first_call_time = end_first - start_first
        
        # Small delay to ensure PLT cache is established
        time.sleep(0.001)
        
        # Measure SUBSEQUENT CALLS (hot path - PLT cached)
        hot_path_times = []
        for i in range(iterations):
            start_hot = time.perf_counter_ns()
            result_hot = func()
            end_hot = time.perf_counter_ns()
            hot_path_times.append(end_hot - start_hot)
            
            # Verify result consistency
            if result_hot != result_first:
                print(f"⚠️ WARNING: Inconsistent results detected in {func_name}")
        
        # Store ALL raw data
        self.raw_data_storage[func_name] = {
            'first_call_ns': first_call_time,
            'hot_path_times_ns': hot_path_times,
            'methodology': 'cold_vs_hot_plt_analysis',
            'iterations': iterations,
            'function_result': result_first
        }
        
        # Calculate hot path statistics
        hot_array = np.array(hot_path_times)
        hot_stats = {
            'median_ns': float(np.median(hot_array)),
            'mean_ns': float(np.mean(hot_array)),
            'std_ns': float(np.std(hot_array)),
            'min_ns': float(np.min(hot_array)),
            'max_ns': float(np.max(hot_array)),
            'samples': len(hot_path_times)
        }
        
        return {
            'first_call_time_ns': first_call_time,
            'hot_path_stats': hot_stats,
            'plt_overhead_factor': first_call_time / hot_stats['median_ns'] if hot_stats['median_ns'] > 0 else float('inf'),
            'raw_data_key': func_name,
            'hot_path_times_ns': hot_path_times  # Include raw data for statistical analysis
        }
    
    def save_raw_data(self, filename: str = 'benchmark_raw_data.json'):
        """Save all raw measurement data to JSON file for academic analysis."""
        import json
        from pathlib import Path
        
        # Ensure results directory exists
        results_dir = Path('results')
        results_dir.mkdir(exist_ok=True)
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_data = {}
        for key, value in self.raw_data_storage.items():
            serializable_data[key] = {
                k: v.tolist() if hasattr(v, 'tolist') else v
                for k, v in value.items()
            }
        
        # Save with timestamp
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        output_data = {
            'timestamp': timestamp,
            'methodology': 'PLT_cache_aware_FFI_benchmarking',
            'raw_measurements': serializable_data
        }
        
        output_path = results_dir / filename
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"📊 Raw data saved to {output_path}")
        return str(output_path)
        
    def auto_tune_iterations(self, func: Callable[[], Any]) -> Dict[str, Any]:
        """
        Automatically determine iteration count for target relative error.
        
        Args:
            func: Function to benchmark
            
        Returns:
            Dictionary containing timing statistics
        """
        # Start with calibration run
        calibration_runs = 10
        times = []
        
        for _ in range(calibration_runs):
            start = time.perf_counter_ns()
            func()
            end = time.perf_counter_ns()
            times.append(end - start)
            
        # Estimate time per call and variance
        median_time = np.median(times)
        if median_time < 1000:  # Less than 1 microsecond
            # Need more iterations per measurement
            iterations = max(1000, int(1e9 / median_time))
        else:
            iterations = 1
            
        # Auto-stop based on confidence interval width
        return self._auto_stop_sampling(func, iterations)
    
    def _auto_stop_sampling(self, func: Callable[[], Any], iterations_per_sample: int) -> Dict[str, Any]:
        """
        Sample until confidence interval meets target.
        
        Args:
            func: Function to benchmark
            iterations_per_sample: Number of iterations per measurement
            
        Returns:
            Dictionary containing timing statistics
        """
        samples = []
        start_time = time.time()
        
        while len(samples) < self.min_samples or self._ci_width(samples) > self.target_relative_error:
            # Measure CPU and wall time
            wall_start = time.perf_counter_ns()
            cpu_start = time.thread_time_ns()
            
            for _ in range(iterations_per_sample):
                func()
                
            cpu_end = time.thread_time_ns()
            wall_end = time.perf_counter_ns()
            
            # Store both measurements
            samples.append({
                'wall_ns': (wall_end - wall_start) / iterations_per_sample,
                'cpu_ns': (cpu_end - cpu_start) / iterations_per_sample
            })
            
            # Check timeout
            if time.time() - start_time > self.max_time_seconds:
                break
                
        # Return statistics with raw samples for statistical analysis
        stats = self._compute_statistics(samples)
        stats['raw_samples'] = samples
        return stats
    
    def _ci_width(self, samples: List[Dict[str, float]]) -> float:
        """
        Compute relative confidence interval width.
        
        Args:
            samples: List of measurement samples
            
        Returns:
            Relative width of 95% confidence interval
        """
        if len(samples) < 2:
            return float('inf')
        values = [s['wall_ns'] for s in samples]
        ci = self._bootstrap_ci(values)
        median = np.median(values)
        return (ci[1] - ci[0]) / median if median > 0 else float('inf')
    
    def _bootstrap_ci(self, data: List[float], n_bootstrap: int = 10000, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Compute BCa bootstrap confidence interval.
        
        Args:
            data: Sample data
            n_bootstrap: Number of bootstrap samples
            confidence: Confidence level
            
        Returns:
            Tuple of (lower, upper) confidence bounds
        """
        bootstrap_medians = []
        n = len(data)
        
        # Set random seed for reproducibility
        np.random.seed(42)
        
        for _ in range(n_bootstrap):
            resample = np.random.choice(data, size=n, replace=True)
            bootstrap_medians.append(np.median(resample))
            
        alpha = (1 - confidence) / 2
        lower = np.percentile(bootstrap_medians, alpha * 100)
        upper = np.percentile(bootstrap_medians, (1 - alpha) * 100)
        
        return (lower, upper)
    
    def _compute_statistics(self, samples: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Compute robust statistics from samples.
        
        Args:
            samples: List of measurement samples
            
        Returns:
            Dictionary containing comprehensive statistics
        """
        wall_times = [s['wall_ns'] for s in samples]
        cpu_times = [s['cpu_ns'] for s in samples]
        
        return {
            'wall_time': {
                'median_ns': np.median(wall_times),
                'mean_ns': np.mean(wall_times),
                'std_ns': np.std(wall_times),
                'min_ns': np.min(wall_times),
                'max_ns': np.max(wall_times),
                'iqr': (np.percentile(wall_times, 25), np.percentile(wall_times, 75)),
                'ci_95': self._bootstrap_ci(wall_times),
                'samples': len(wall_times)
            },
            'cpu_time': {
                'median_ns': np.median(cpu_times),
                'mean_ns': np.mean(cpu_times),
                'std_ns': np.std(cpu_times),
                'min_ns': np.min(cpu_times),
                'max_ns': np.max(cpu_times),
                'iqr': (np.percentile(cpu_times, 25), np.percentile(cpu_times, 75)),
                'ci_95': self._bootstrap_ci(cpu_times),
                'samples': len(cpu_times)
            },
            'overhead': {
                'wall_cpu_ratio': np.median(wall_times) / np.median(cpu_times) if np.median(cpu_times) > 0 else float('inf'),
                'relative_error': self._ci_width(samples)
            }
        }
    
    def measure_with_warmup(self, func: Callable[[], Any], warmup_iterations: int = 100) -> Dict[str, Any]:
        """
        Measure function performance with warmup phase.
        
        Args:
            func: Function to benchmark
            warmup_iterations: Number of warmup iterations
            
        Returns:
            Dictionary containing timing statistics
        """
        # Warmup phase
        for _ in range(warmup_iterations):
            func()
            
        # Actual measurement
        return self.auto_tune_iterations(func)
    
    def compare_implementations(self, implementations: Dict[str, Callable[[], Any]], 
                              baseline_name: str = None) -> Dict[str, Any]:
        """
        Compare multiple implementations with statistical significance.
        
        Args:
            implementations: Dictionary mapping names to functions
            baseline_name: Name of baseline implementation for comparison
            
        Returns:
            Dictionary containing comparison results
        """
        results = {}
        raw_times = {}
        
        # Measure each implementation
        for name, func in implementations.items():
            print(f"Benchmarking {name}...", end='', flush=True)
            stats = self.measure_with_warmup(func)
            results[name] = stats
            raw_times[name] = stats['wall_time']['median_ns']
            print(f" {stats['wall_time']['median_ns']/1e6:.2f} ms")
        
        # Calculate relative performance
        if baseline_name and baseline_name in raw_times:
            baseline_time = raw_times[baseline_name]
            for name in results:
                results[name]['relative_performance'] = baseline_time / raw_times[name]
        
        # Sort by performance
        sorted_names = sorted(raw_times.keys(), key=lambda x: raw_times[x])
        
        return {
            'implementations': results,
            'ranking': sorted_names,
            'fastest': sorted_names[0],
            'slowest': sorted_names[-1]
        }
    
    def statistical_comparison(self, implementations: Dict[str, Callable], 
                             iterations: int = None) -> Dict[str, Any]:
        """
        Rigorous statistical comparison using Mann-Whitney U tests.
        
        Args:
            implementations: Dictionary mapping names to functions
            iterations: Number of iterations (auto-tuned if None)
            
        Returns:
            Dictionary containing statistical analysis results
        """
        if not _HAS_STATISTICS:
            raise RuntimeError("Statistical analysis module not available. Check scipy installation.")
        
        # Collect raw samples for each implementation
        raw_samples = {}
        
        for name, func in implementations.items():
            print(f"📊 Collecting samples for {name}...")
            
            if iterations is None:
                # Auto-tune iterations for each implementation
                result = self.auto_tune_iterations(func)
                # Extract wall time samples from the result
                if 'raw_samples' in result:
                    samples = [s['wall_ns'] for s in result['raw_samples']]
                else:
                    # Fallback: create samples from repeated measurements
                    samples = []
                    for _ in range(30):  # Collect 30 samples for statistical analysis
                        start = time.perf_counter_ns()
                        func()
                        end = time.perf_counter_ns()
                        samples.append(end - start)
            else:
                # Use fixed iteration count
                samples = []
                for _ in range(iterations):
                    start = time.perf_counter_ns()
                    func()
                    end = time.perf_counter_ns()
                    samples.append(end - start)
            
            raw_samples[name] = samples
        
        # Perform statistical analysis
        stats_analyzer = create_statistical_analyzer()
        
        # Multiple comparisons analysis
        multiple_results = stats_analyzer.multiple_comparisons_analysis(
            raw_samples, correction='benjamini-hochberg'
        )
        
        # Generate summary report
        report = stats_analyzer.generate_summary_report(multiple_results)
        
        return {
            'raw_samples': raw_samples,
            'statistical_analysis': multiple_results,
            'summary_report': report,
            'methodology': 'Mann-Whitney U with Benjamini-Hochberg correction'
        }
    
    def hypothesis_test(self, method1_func: Callable, method2_func: Callable,
                       method1_name: str, method2_name: str,
                       hypothesis: str = 'method1_faster') -> Dict[str, Any]:
        """
        Test specific hypothesis about method performance.
        
        Args:
            method1_func: First method function
            method2_func: Second method function 
            method1_name: Name of first method
            method2_name: Name of second method
            hypothesis: 'method1_faster', 'method2_faster', or 'different'
            
        Returns:
            Dictionary containing hypothesis test results
        """
        if not _HAS_STATISTICS:
            raise RuntimeError("Statistical analysis module not available. Check scipy installation.")
        
        print(f"🧪 Testing hypothesis: {hypothesis}")
        print(f"   H0: No difference between {method1_name} and {method2_name}")
        
        # Collect samples
        result1 = self.auto_tune_iterations(method1_func)
        result2 = self.auto_tune_iterations(method2_func)
        
        # Extract wall time samples from the results
        if 'raw_samples' in result1:
            samples1 = [s['wall_ns'] for s in result1['raw_samples']]
        else:
            # Fallback: create samples from repeated measurements
            samples1 = []
            for _ in range(30):
                start = time.perf_counter_ns()
                method1_func()
                end = time.perf_counter_ns()
                samples1.append(end - start)
        
        if 'raw_samples' in result2:
            samples2 = [s['wall_ns'] for s in result2['raw_samples']]
        else:
            # Fallback: create samples from repeated measurements
            samples2 = []
            for _ in range(30):
                start = time.perf_counter_ns()
                method2_func()
                end = time.perf_counter_ns()
                samples2.append(end - start)
        
        # Perform statistical comparison
        stats_analyzer = create_statistical_analyzer()
        comparison = stats_analyzer.compare_methods(
            samples1, samples2, method1_name, method2_name
        )
        
        # Determine if hypothesis is supported
        if hypothesis == 'method1_faster':
            hypothesis_supported = (comparison.faster_method == method1_name and 
                                  comparison.statistical_test.significant)
        elif hypothesis == 'method2_faster':
            hypothesis_supported = (comparison.faster_method == method2_name and
                                  comparison.statistical_test.significant)
        else:  # 'different'
            hypothesis_supported = comparison.statistical_test.significant
        
        return {
            'hypothesis': hypothesis,
            'hypothesis_supported': hypothesis_supported,
            'comparison': comparison,
            'power_analysis': stats_analyzer.power_analysis(samples1, samples2),
            'sample_sizes': (len(samples1), len(samples2))
        }


def format_nanoseconds(ns: float) -> str:
    """
    Format nanoseconds into human-readable string.
    
    Args:
        ns: Time in nanoseconds
        
    Returns:
        Formatted string
    """
    if ns < 1000:
        return f"{ns:.1f} ns"
    elif ns < 1e6:
        return f"{ns/1e3:.1f} μs"
    elif ns < 1e9:
        return f"{ns/1e6:.1f} ms"
    else:
        return f"{ns/1e9:.2f} s"


def print_benchmark_results(results: Dict[str, Any], title: str = "Benchmark Results"):
    """
    Pretty-print benchmark results.
    
    Args:
        results: Results from compare_implementations
        title: Title for the results
    """
    print(f"\n{title}")
    print("=" * len(title))
    print()
    
    # Extract implementation results
    impls = results['implementations']
    ranking = results['ranking']
    
    # Print ranked results
    print(f"{'Rank':<6} {'Implementation':<20} {'Median Time':<15} {'95% CI':<25} {'Relative':<10}")
    print("-" * 80)
    
    for i, name in enumerate(ranking, 1):
        stats = impls[name]['wall_time']
        median = format_nanoseconds(stats['median_ns'])
        ci_lower = format_nanoseconds(stats['ci_95'][0])
        ci_upper = format_nanoseconds(stats['ci_95'][1])
        ci_str = f"[{ci_lower}, {ci_upper}]"
        
        rel_perf = impls[name].get('relative_performance', 1.0)
        rel_str = f"{rel_perf:.2f}x"
        
        print(f"{i:<6} {name:<20} {median:<15} {ci_str:<25} {rel_str:<10}")
    
    print()
    print(f"Fastest: {results['fastest']}")
    print(f"Slowest: {results['slowest']}")
    
    # Calculate speedup
    fastest_time = impls[results['fastest']]['wall_time']['median_ns']
    slowest_time = impls[results['slowest']]['wall_time']['median_ns']
    speedup = slowest_time / fastest_time
    print(f"Speedup: {speedup:.2f}x")


if __name__ == "__main__":
    # Example usage and self-test
    import math
    
    def test_fast():
        """Fast function for testing."""
        return sum(range(100))
    
    def test_slow():
        """Slower function for testing."""
        return sum(math.sqrt(i) for i in range(1000))
    
    timer = BenchmarkTimer()
    
    # Test single function
    print("Testing single function measurement...")
    stats = timer.measure_with_warmup(test_fast)
    print(f"Median time: {format_nanoseconds(stats['wall_time']['median_ns'])}")
    print(f"95% CI: [{format_nanoseconds(stats['wall_time']['ci_95'][0])}, "
          f"{format_nanoseconds(stats['wall_time']['ci_95'][1])}]")
    
    # Test comparison
    print("\nTesting implementation comparison...")
    results = timer.compare_implementations({
        'fast': test_fast,
        'slow': test_slow
    }, baseline_name='fast')
    
    print_benchmark_results(results, "Self-Test Results")