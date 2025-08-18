"""
Crossover Point Analysis for FFI Benchmarks

This module implements crossover point analysis to identify where FFI overhead
becomes negligible compared to computation time. Based on the principle that
as computational complexity increases, FFI overhead becomes proportionally smaller.

Key analyses:
- Matrix multiplication scaling (O(n³) computation)
- Vector operations scaling (O(n) computation)  
- Iterative algorithm scaling (O(n²) or O(n log n))
- Memory bandwidth vs computation trade-offs
"""

import os
import sys
import time
import numpy as np
try:
    import matplotlib.pyplot as plt
    _HAS_MATPLOTLIB = True
except ImportError:
    _HAS_MATPLOTLIB = False
    plt = None
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
import warnings

# Add parent directory for framework imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.timer import BenchmarkTimer, format_nanoseconds
import numpy as np
import ctypes


@dataclass
class CrossoverPoint:
    """Represents a crossover point where FFI overhead becomes negligible."""
    problem_size: int
    ffi_method: str
    baseline_method: str
    ffi_time_ns: float
    baseline_time_ns: float
    overhead_ratio: float  # ffi_time / baseline_time
    overhead_percentage: float  # (ffi_time - baseline_time) / baseline_time * 100
    is_crossover: bool  # True if overhead < threshold


@dataclass
class CrossoverAnalysis:
    """Complete crossover analysis results."""
    analysis_name: str
    algorithm_complexity: str  # O(n), O(n²), O(n³), etc.
    problem_sizes: List[int]
    crossover_points: List[CrossoverPoint]
    threshold_percentage: float
    fastest_method: str
    crossover_size: Optional[int] = None


class CrossoverAnalyzer:
    """Analyzer for finding FFI overhead crossover points."""
    
    def __init__(self, overhead_threshold: float = 10.0):
        """
        Initialize crossover analyzer.
        
        Args:
            overhead_threshold: Threshold percentage for considering overhead negligible
        """
        self.timer = BenchmarkTimer()
        self.overhead_threshold = overhead_threshold
        
        print(f"🔬 Crossover analyzer initialized")
        print(f"📏 Overhead threshold: {overhead_threshold}%")
    
    def analyze_matrix_multiplication_crossover(self, 
                                              implementations: Dict[str, Callable],
                                              sizes: Optional[List[int]] = None,
                                              baseline: str = 'numpy') -> CrossoverAnalysis:
        """
        Analyze crossover point for matrix multiplication (O(n³) complexity).
        
        Args:
            implementations: Dict mapping method names to matrix multiplication functions
            sizes: List of matrix sizes to test (default: [8, 16, 32, 64, 128, 256])
            baseline: Name of baseline implementation for comparison
        """
        print("\n🧮 Analyzing matrix multiplication crossover (O(n³))...")
        
        if sizes is None:
            sizes = [8, 16, 32, 64, 128, 256]
        
        crossover_points = []
        
        # Add numpy baseline if not provided
        if baseline not in implementations:
            implementations[baseline] = lambda size: self._numpy_matmul_benchmark(size)
        
        for size in sizes:
            print(f"  📊 Testing matrix size {size}x{size}...")
            
            size_results = {}
            
            # Test each implementation
            for name, func in implementations.items():
                try:
                    # Create test function for this size
                    def test_func():
                        return func(size)
                    
                    # Measure performance
                    result = self.timer.measure_with_warmup(test_func)
                    size_results[name] = result['wall_time']['median_ns']
                    
                except Exception as e:
                    print(f"    ❌ {name} failed for size {size}: {e}")
                    size_results[name] = float('inf')
            
            # Calculate crossover points relative to baseline
            if baseline in size_results and size_results[baseline] != float('inf'):
                baseline_time = size_results[baseline]
                
                for name, ffi_time in size_results.items():
                    if name == baseline or ffi_time == float('inf'):
                        continue
                    
                    overhead_ratio = ffi_time / baseline_time
                    overhead_percentage = ((ffi_time - baseline_time) / baseline_time) * 100
                    is_crossover = overhead_percentage <= self.overhead_threshold
                    
                    crossover_point = CrossoverPoint(
                        problem_size=size,
                        ffi_method=name,
                        baseline_method=baseline,
                        ffi_time_ns=ffi_time,
                        baseline_time_ns=baseline_time,
                        overhead_ratio=overhead_ratio,
                        overhead_percentage=overhead_percentage,
                        is_crossover=is_crossover
                    )
                    
                    crossover_points.append(crossover_point)
                    
                    print(f"    {name}: {format_nanoseconds(ffi_time)} ({overhead_percentage:+.1f}% vs {baseline})")
        
        # Find crossover size
        crossover_size = self._find_crossover_size(crossover_points)
        
        # Determine fastest method overall
        fastest_method = self._determine_fastest_method(crossover_points)
        
        return CrossoverAnalysis(
            analysis_name="matrix_multiplication",
            algorithm_complexity="O(n³)",
            problem_sizes=sizes,
            crossover_points=crossover_points,
            threshold_percentage=self.overhead_threshold,
            fastest_method=fastest_method,
            crossover_size=crossover_size
        )
    
    def analyze_vector_operations_crossover(self, 
                                          implementations: Dict[str, Callable],
                                          sizes: Optional[List[int]] = None,
                                          baseline: str = 'numpy') -> CrossoverAnalysis:
        """
        Analyze crossover point for vector operations (O(n) complexity).
        
        Args:
            implementations: Dict mapping method names to vector operation functions
            sizes: List of vector sizes to test
            baseline: Name of baseline implementation
        """
        print("\n📊 Analyzing vector operations crossover (O(n))...")
        
        if sizes is None:
            sizes = [100, 500, 1000, 5000, 10000, 50000, 100000]
        
        crossover_points = []
        
        # Add numpy baseline if not provided
        if baseline not in implementations:
            implementations[baseline] = self._create_numpy_vector_add
        
        for size in sizes:
            print(f"  📊 Testing vector size {size}...")
            
            size_results = {}
            
            # Test each implementation
            for name, func in implementations.items():
                try:
                    # Create test function for this size
                    def test_func():
                        return func(size)
                    
                    # Measure performance  
                    result = self.timer.measure_with_warmup(test_func)
                    size_results[name] = result['wall_time']['median_ns']
                    
                except Exception as e:
                    print(f"    ❌ {name} failed for size {size}: {e}")
                    size_results[name] = float('inf')
            
            # Calculate crossover points
            if baseline in size_results and size_results[baseline] != float('inf'):
                baseline_time = size_results[baseline]
                
                for name, ffi_time in size_results.items():
                    if name == baseline or ffi_time == float('inf'):
                        continue
                    
                    overhead_ratio = ffi_time / baseline_time
                    overhead_percentage = ((ffi_time - baseline_time) / baseline_time) * 100
                    is_crossover = overhead_percentage <= self.overhead_threshold
                    
                    crossover_point = CrossoverPoint(
                        problem_size=size,
                        ffi_method=name,
                        baseline_method=baseline,
                        ffi_time_ns=ffi_time,
                        baseline_time_ns=baseline_time,
                        overhead_ratio=overhead_ratio,
                        overhead_percentage=overhead_percentage,
                        is_crossover=is_crossover
                    )
                    
                    crossover_points.append(crossover_point)
                    
                    print(f"    {name}: {format_nanoseconds(ffi_time)} ({overhead_percentage:+.1f}% vs {baseline})")
        
        crossover_size = self._find_crossover_size(crossover_points)
        fastest_method = self._determine_fastest_method(crossover_points)
        
        return CrossoverAnalysis(
            analysis_name="vector_operations",
            algorithm_complexity="O(n)",
            problem_sizes=sizes,
            crossover_points=crossover_points,
            threshold_percentage=self.overhead_threshold,
            fastest_method=fastest_method,
            crossover_size=crossover_size
        )
    
    def analyze_iterative_algorithm_crossover(self,
                                            implementations: Dict[str, Callable],
                                            sizes: Optional[List[int]] = None,
                                            baseline: str = 'python') -> CrossoverAnalysis:
        """
        Analyze crossover point for iterative algorithms (O(n²) complexity).
        
        Args:
            implementations: Dict mapping method names to iterative algorithm functions  
            sizes: List of problem sizes to test
            baseline: Name of baseline implementation
        """
        print("\n🔄 Analyzing iterative algorithm crossover (O(n²))...")
        
        if sizes is None:
            sizes = [10, 25, 50, 100, 200, 500]
        
        crossover_points = []
        
        # Add Python baseline if not provided
        if baseline not in implementations:
            implementations[baseline] = self._create_python_bubble_sort
        
        for size in sizes:
            print(f"  📊 Testing problem size {size}...")
            
            size_results = {}
            
            # Test each implementation
            for name, func in implementations.items():
                try:
                    # Create test function for this size
                    def test_func():
                        return func(size)
                    
                    # Measure performance
                    result = self.timer.measure_with_warmup(test_func)
                    size_results[name] = result['wall_time']['median_ns']
                    
                except Exception as e:
                    print(f"    ❌ {name} failed for size {size}: {e}")
                    size_results[name] = float('inf')
            
            # Calculate crossover points
            if baseline in size_results and size_results[baseline] != float('inf'):
                baseline_time = size_results[baseline]
                
                for name, ffi_time in size_results.items():
                    if name == baseline or ffi_time == float('inf'):
                        continue
                    
                    overhead_ratio = ffi_time / baseline_time
                    overhead_percentage = ((ffi_time - baseline_time) / baseline_time) * 100
                    is_crossover = overhead_percentage <= self.overhead_threshold
                    
                    crossover_point = CrossoverPoint(
                        problem_size=size,
                        ffi_method=name,
                        baseline_method=baseline,
                        ffi_time_ns=ffi_time,
                        baseline_time_ns=baseline_time,
                        overhead_ratio=overhead_ratio,
                        overhead_percentage=overhead_percentage,
                        is_crossover=is_crossover
                    )
                    
                    crossover_points.append(crossover_point)
                    
                    print(f"    {name}: {format_nanoseconds(ffi_time)} ({overhead_percentage:+.1f}% vs {baseline})")
        
        crossover_size = self._find_crossover_size(crossover_points)
        fastest_method = self._determine_fastest_method(crossover_points)
        
        return CrossoverAnalysis(
            analysis_name="iterative_algorithm",
            algorithm_complexity="O(n²)",
            problem_sizes=sizes,
            crossover_points=crossover_points,
            threshold_percentage=self.overhead_threshold,
            fastest_method=fastest_method,
            crossover_size=crossover_size
        )
    
    def plot_crossover_analysis(self, analysis: CrossoverAnalysis, save_path: Optional[str] = None):
        """
        Plot crossover analysis results.
        
        Args:
            analysis: CrossoverAnalysis to plot
            save_path: Optional path to save the plot
        """
        try:
            plt.figure(figsize=(12, 8))
            
            # Group crossover points by FFI method
            methods = {}
            for point in analysis.crossover_points:
                if point.ffi_method not in methods:
                    methods[point.ffi_method] = {'sizes': [], 'overhead': []}
                methods[point.ffi_method]['sizes'].append(point.problem_size)
                methods[point.ffi_method]['overhead'].append(point.overhead_percentage)
            
            # Plot each method
            for method, data in methods.items():
                plt.plot(data['sizes'], data['overhead'], 'o-', label=method, linewidth=2, markersize=8)
            
            # Add threshold line
            plt.axhline(y=self.overhead_threshold, color='red', linestyle='--', 
                       label=f'Threshold ({self.overhead_threshold}%)', linewidth=2)
            
            # Mark crossover point if found
            if analysis.crossover_size:
                plt.axvline(x=analysis.crossover_size, color='green', linestyle=':', 
                           label=f'Crossover Size ({analysis.crossover_size})', linewidth=2)
            
            plt.xlabel('Problem Size')
            plt.ylabel('FFI Overhead (%)')
            plt.title(f'FFI Overhead Crossover Analysis: {analysis.analysis_name.replace("_", " ").title()}\n'
                     f'Algorithm Complexity: {analysis.algorithm_complexity}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.xscale('log')
            
            # Annotate with fastest method
            plt.text(0.02, 0.98, f'Fastest overall: {analysis.fastest_method}', 
                    transform=plt.gca().transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"📊 Plot saved: {save_path}")
            else:
                plt.show()
        
        except ImportError:
            print("⚠️  matplotlib not available, skipping plot generation")
    
    def generate_crossover_report(self, analyses: List[CrossoverAnalysis]) -> str:
        """Generate comprehensive crossover analysis report."""
        report = []
        report.append("# FFI Crossover Point Analysis Report")
        report.append("=" * 50)
        report.append("")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Overhead threshold: {self.overhead_threshold}%")
        report.append("")
        
        for analysis in analyses:
            report.append(f"## {analysis.analysis_name.replace('_', ' ').title()}")
            report.append(f"**Algorithm Complexity**: {analysis.algorithm_complexity}")
            report.append(f"**Problem Sizes Tested**: {analysis.problem_sizes}")
            report.append(f"**Fastest Method**: {analysis.fastest_method}")
            
            if analysis.crossover_size:
                report.append(f"**Crossover Size**: {analysis.crossover_size}")
            else:
                report.append("**Crossover Size**: Not found within tested range")
            
            report.append("")
            report.append("### Detailed Results")
            
            # Group by problem size
            size_groups = {}
            for point in analysis.crossover_points:
                if point.problem_size not in size_groups:
                    size_groups[point.problem_size] = []
                size_groups[point.problem_size].append(point)
            
            for size in sorted(size_groups.keys()):
                report.append(f"#### Size {size}")
                
                for point in size_groups[size]:
                    status = "✅ Below threshold" if point.is_crossover else "❌ Above threshold"
                    report.append(f"- **{point.ffi_method}**: {point.overhead_percentage:+.1f}% overhead, "
                                f"{point.overhead_ratio:.2f}x slower {status}")
                
                report.append("")
            
            report.append("---")
            report.append("")
        
        return "\n".join(report)
    
    def _find_crossover_size(self, crossover_points: List[CrossoverPoint]) -> Optional[int]:
        """Find the first problem size where overhead drops below threshold."""
        # Group by FFI method
        methods = {}
        for point in crossover_points:
            if point.ffi_method not in methods:
                methods[point.ffi_method] = []
            methods[point.ffi_method].append(point)
        
        # Find earliest crossover for any method
        min_crossover_size = None
        
        for method, points in methods.items():
            points.sort(key=lambda p: p.problem_size)
            
            for point in points:
                if point.is_crossover:
                    if min_crossover_size is None or point.problem_size < min_crossover_size:
                        min_crossover_size = point.problem_size
                    break
        
        return min_crossover_size
    
    def _numpy_matmul_benchmark(self, size: int) -> float:
        """Numpy matrix multiplication benchmark (baseline)."""
        a = np.random.random((size, size)).astype(np.float64)
        b = np.random.random((size, size)).astype(np.float64)
        
        # Perform matrix multiplication
        c = np.dot(a, b)
        
        # Return a simple checksum to ensure computation happened
        return float(np.sum(c))
    
    def create_ctypes_matmul_benchmark(self) -> Callable[[int], float]:
        """Create ctypes matrix multiplication benchmark function."""
        try:
            from benchmarks.ctypes_bench import CtypesBenchmark
            bench = CtypesBenchmark()
            
            def ctypes_matmul(size: int) -> float:
                # Create test matrices
                a = np.random.random((size, size)).astype(np.float64)
                b = np.random.random((size, size)).astype(np.float64)
                c = np.zeros((size, size), dtype=np.float64)
                
                # Convert to ctypes arrays
                a_ctypes = (ctypes.c_double * (size * size))(*a.flatten())
                b_ctypes = (ctypes.c_double * (size * size))(*b.flatten())
                c_ctypes = (ctypes.c_double * (size * size))(*c.flatten())
                
                # Call C matrix multiplication via ctypes
                bench.lib.matrix_multiply_naive(a_ctypes, b_ctypes, c_ctypes, size, size, size)
                
                # Convert back and return checksum
                result = np.array(c_ctypes).reshape((size, size))
                return float(np.sum(result))
            
            return ctypes_matmul
            
        except ImportError:
            return lambda size: float('inf')
    
    def create_cffi_matmul_benchmark(self) -> Callable[[int], float]:
        """Create cffi matrix multiplication benchmark function."""
        try:
            from benchmarks.cffi_bench import CFfiBenchmark
            bench = CFfiBenchmark()
            
            def cffi_matmul(size: int) -> float:
                # Create test matrices
                a = np.random.random((size, size)).astype(np.float64)
                b = np.random.random((size, size)).astype(np.float64)
                c = np.zeros((size, size), dtype=np.float64)
                
                # Use cffi for matrix multiplication
                if hasattr(bench, 'api') and bench.api:
                    # Use API mode
                    a_ptr = bench.api.ffi.cast("double*", a.ctypes.data)
                    b_ptr = bench.api.ffi.cast("double*", b.ctypes.data)
                    c_ptr = bench.api.ffi.cast("double*", c.ctypes.data)
                    bench.api.lib.matrix_multiply_naive(a_ptr, b_ptr, c_ptr, size, size, size)
                else:
                    # Use ABI mode
                    a_ptr = bench.abi.ffi.cast("double*", a.ctypes.data)
                    b_ptr = bench.abi.ffi.cast("double*", b.ctypes.data)
                    c_ptr = bench.abi.ffi.cast("double*", c.ctypes.data)
                    bench.abi.lib.matrix_multiply_naive(a_ptr, b_ptr, c_ptr, size, size, size)
                
                return float(np.sum(c))
            
            return cffi_matmul
            
        except ImportError:
            return lambda size: float('inf')
    
    def create_pybind11_matmul_benchmark(self) -> Callable[[int], float]:
        """Create pybind11 matrix multiplication benchmark function."""
        try:
            import benchlib_pybind11 as pybind11_lib
            
            def pybind11_matmul(size: int) -> float:
                # Create test matrices
                a = np.random.random((size, size)).astype(np.float64)
                b = np.random.random((size, size)).astype(np.float64)
                c = np.zeros((size, size), dtype=np.float64)
                
                # Call matrix multiplication via pybind11
                pybind11_lib.matrix_multiply_naive(a, b, c, size, size, size)
                
                return float(np.sum(c))
            
            return pybind11_matmul
            
        except ImportError:
            return lambda size: float('inf')
    
    def _determine_fastest_method(self, crossover_points: List[CrossoverPoint]) -> str:
        """Determine the fastest method overall."""
        if not crossover_points:
            return "unknown"
        
        # Count wins for each method
        method_wins = {}
        
        # Group by problem size
        size_groups = {}
        for point in crossover_points:
            if point.problem_size not in size_groups:
                size_groups[point.problem_size] = []
            size_groups[point.problem_size].append(point)
        
        # For each size, find the fastest method
        for size, points in size_groups.items():
            if not points:
                continue
            
            fastest_point = min(points, key=lambda p: p.ffi_time_ns)
            fastest_method = fastest_point.ffi_method
            
            if fastest_method not in method_wins:
                method_wins[fastest_method] = 0
            method_wins[fastest_method] += 1
        
        # Return method with most wins
        if method_wins:
            return max(method_wins.items(), key=lambda x: x[1])[0]
        else:
            return "unknown"
    
    def _create_numpy_matmul(self, size: int) -> np.ndarray:
        """Create numpy matrix multiplication baseline."""
        a = np.random.random((size, size)).astype(np.float64)
        b = np.random.random((size, size)).astype(np.float64)
        return np.dot(a, b)
    
    def _create_numpy_vector_add(self, size: int) -> np.ndarray:
        """Create numpy vector addition baseline."""
        a = np.random.random(size).astype(np.float64)
        b = np.random.random(size).astype(np.float64)
        return a + b
    
    def _create_python_bubble_sort(self, size: int) -> List[int]:
        """Create Python bubble sort baseline."""
        arr = list(range(size, 0, -1))  # Worst case: reverse sorted
        
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        
        return arr


def create_crossover_analyzer(overhead_threshold: float = 10.0) -> CrossoverAnalyzer:
    """Factory function to create crossover analyzer."""
    return CrossoverAnalyzer(overhead_threshold)


if __name__ == "__main__":
    # Example usage
    analyzer = create_crossover_analyzer()
    
    # Test matrix multiplication crossover
    def ctypes_matmul(size):
        # Simplified - in real implementation would call C library
        return analyzer._create_numpy_matmul(size)
    
    def cffi_matmul(size):
        # Simplified - in real implementation would call C library via cffi
        return analyzer._create_numpy_matmul(size)
    
    implementations = {
        'ctypes': ctypes_matmul,
        'cffi': cffi_matmul
    }
    
    print("🚀 Running crossover analysis example...")
    
    # Analyze matrix multiplication
    matrix_analysis = analyzer.analyze_matrix_multiplication_crossover(
        implementations, sizes=[8, 16, 32, 64]
    )
    
    print(f"\n📊 Matrix multiplication analysis complete:")
    print(f"  Crossover size: {matrix_analysis.crossover_size}")
    print(f"  Fastest method: {matrix_analysis.fastest_method}")
    
    # Generate report
    report = analyzer.generate_crossover_report([matrix_analysis])
    print(f"\n📝 Analysis report:\n{report}")
    
    print("\n🎉 Crossover analysis example completed!")