"""
Dispatch Pattern Benchmarks

This module implements comprehensive dispatch pattern benchmarks following
docs/benchmark-ffi/dispatch-patterns.md to test hypothesis H9-H11:

H9: Dictionary lookup outperforms if/elif chains for large function sets
H10: Cache warming significantly improves dynamic dispatch performance  
H11: Function call locality affects dispatch pattern efficiency
"""

import os
import random
import time
import ctypes
from pathlib import Path
from typing import Dict, List, Callable, Any, Tuple
from enum import IntEnum
from functools import singledispatch
from dataclasses import dataclass

# Find the benchmark library
_lib_path = None
for potential_path in [
    Path(__file__).parent / "benchlib.so",
    Path(__file__).parent / "benchlib.dylib", 
    Path(__file__).parent / "benchlib.dll",
    Path(__file__).parent.parent / "benchlib.so",
    Path(__file__).parent.parent / "benchlib.dylib",
    Path(__file__).parent.parent / "benchlib.dll",
    Path(__file__).parent.parent / "lib" / "benchlib.so",
    Path(__file__).parent.parent / "lib" / "benchlib.dylib",
    Path(__file__).parent.parent / "lib" / "benchlib.dll",
]:
    if potential_path.exists():
        _lib_path = str(potential_path)
        break

if not _lib_path:
    raise RuntimeError("Could not find benchlib shared library")


class DispatchPatterns:
    """Comprehensive dispatch pattern implementations for benchmarking."""
    
    def __init__(self, num_functions: int = 100):
        """Initialize dispatch patterns with specified number of functions."""
        self.num_functions = num_functions
        self.lib = ctypes.CDLL(_lib_path)
        
        # Setup C library dispatch baseline
        self.lib.dispatch_c_baseline.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        self.lib.dispatch_c_baseline.restype = ctypes.c_int
        
        # Initialize all dispatch patterns
        self._setup_global_if_elif()
        self._setup_dict_lookup()
        self._setup_class_getattr()
        self._setup_class_precached()
        self._setup_enum_table()
        
        # Generate access patterns for testing
        self.access_patterns = self._generate_access_patterns()
    
    def _setup_global_if_elif(self):
        """Setup global variables with if/elif chain dispatch."""
        # Create global function references
        self.global_funcs = {}
        for i in range(self.num_functions):
            func_name = f"dispatch_test_{i}"
            func = getattr(self.lib, func_name)
            func.argtypes = [ctypes.c_int, ctypes.c_int]
            func.restype = ctypes.c_int
            self.global_funcs[i] = func
    
    def dispatch_global_if_elif(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """Global variables + if/elif chain dispatch (worst case for large N)."""
        # Generate if/elif chain dynamically for first 100 functions
        if func_id == 0: return self.global_funcs[0](a, b)
        elif func_id == 1: return self.global_funcs[1](a, b)
        elif func_id == 2: return self.global_funcs[2](a, b)
        elif func_id == 3: return self.global_funcs[3](a, b)
        elif func_id == 4: return self.global_funcs[4](a, b)
        elif func_id == 5: return self.global_funcs[5](a, b)
        elif func_id == 6: return self.global_funcs[6](a, b)
        elif func_id == 7: return self.global_funcs[7](a, b)
        elif func_id == 8: return self.global_funcs[8](a, b)
        elif func_id == 9: return self.global_funcs[9](a, b)
        elif func_id == 10: return self.global_funcs[10](a, b)
        elif func_id == 11: return self.global_funcs[11](a, b)
        elif func_id == 12: return self.global_funcs[12](a, b)
        elif func_id == 13: return self.global_funcs[13](a, b)
        elif func_id == 14: return self.global_funcs[14](a, b)
        elif func_id == 15: return self.global_funcs[15](a, b)
        elif func_id == 16: return self.global_funcs[16](a, b)
        elif func_id == 17: return self.global_funcs[17](a, b)
        elif func_id == 18: return self.global_funcs[18](a, b)
        elif func_id == 19: return self.global_funcs[19](a, b)
        elif func_id == 20: return self.global_funcs[20](a, b)
        elif func_id == 21: return self.global_funcs[21](a, b)
        elif func_id == 22: return self.global_funcs[22](a, b)
        elif func_id == 23: return self.global_funcs[23](a, b)
        elif func_id == 24: return self.global_funcs[24](a, b)
        elif func_id == 25: return self.global_funcs[25](a, b)
        elif func_id == 26: return self.global_funcs[26](a, b)
        elif func_id == 27: return self.global_funcs[27](a, b)
        elif func_id == 28: return self.global_funcs[28](a, b)
        elif func_id == 29: return self.global_funcs[29](a, b)
        elif func_id == 30: return self.global_funcs[30](a, b)
        elif func_id == 31: return self.global_funcs[31](a, b)
        elif func_id == 32: return self.global_funcs[32](a, b)
        elif func_id == 33: return self.global_funcs[33](a, b)
        elif func_id == 34: return self.global_funcs[34](a, b)
        elif func_id == 35: return self.global_funcs[35](a, b)
        elif func_id == 36: return self.global_funcs[36](a, b)
        elif func_id == 37: return self.global_funcs[37](a, b)
        elif func_id == 38: return self.global_funcs[38](a, b)
        elif func_id == 39: return self.global_funcs[39](a, b)
        elif func_id == 40: return self.global_funcs[40](a, b)
        elif func_id == 41: return self.global_funcs[41](a, b)
        elif func_id == 42: return self.global_funcs[42](a, b)
        elif func_id == 43: return self.global_funcs[43](a, b)
        elif func_id == 44: return self.global_funcs[44](a, b)
        elif func_id == 45: return self.global_funcs[45](a, b)
        elif func_id == 46: return self.global_funcs[46](a, b)
        elif func_id == 47: return self.global_funcs[47](a, b)
        elif func_id == 48: return self.global_funcs[48](a, b)
        elif func_id == 49: return self.global_funcs[49](a, b)
        elif func_id == 50: return self.global_funcs[50](a, b)
        elif func_id == 51: return self.global_funcs[51](a, b)
        elif func_id == 52: return self.global_funcs[52](a, b)
        elif func_id == 53: return self.global_funcs[53](a, b)
        elif func_id == 54: return self.global_funcs[54](a, b)
        elif func_id == 55: return self.global_funcs[55](a, b)
        elif func_id == 56: return self.global_funcs[56](a, b)
        elif func_id == 57: return self.global_funcs[57](a, b)
        elif func_id == 58: return self.global_funcs[58](a, b)
        elif func_id == 59: return self.global_funcs[59](a, b)
        elif func_id == 60: return self.global_funcs[60](a, b)
        elif func_id == 61: return self.global_funcs[61](a, b)
        elif func_id == 62: return self.global_funcs[62](a, b)
        elif func_id == 63: return self.global_funcs[63](a, b)
        elif func_id == 64: return self.global_funcs[64](a, b)
        elif func_id == 65: return self.global_funcs[65](a, b)
        elif func_id == 66: return self.global_funcs[66](a, b)
        elif func_id == 67: return self.global_funcs[67](a, b)
        elif func_id == 68: return self.global_funcs[68](a, b)
        elif func_id == 69: return self.global_funcs[69](a, b)
        elif func_id == 70: return self.global_funcs[70](a, b)
        elif func_id == 71: return self.global_funcs[71](a, b)
        elif func_id == 72: return self.global_funcs[72](a, b)
        elif func_id == 73: return self.global_funcs[73](a, b)
        elif func_id == 74: return self.global_funcs[74](a, b)
        elif func_id == 75: return self.global_funcs[75](a, b)
        elif func_id == 76: return self.global_funcs[76](a, b)
        elif func_id == 77: return self.global_funcs[77](a, b)
        elif func_id == 78: return self.global_funcs[78](a, b)
        elif func_id == 79: return self.global_funcs[79](a, b)
        elif func_id == 80: return self.global_funcs[80](a, b)
        elif func_id == 81: return self.global_funcs[81](a, b)
        elif func_id == 82: return self.global_funcs[82](a, b)
        elif func_id == 83: return self.global_funcs[83](a, b)
        elif func_id == 84: return self.global_funcs[84](a, b)
        elif func_id == 85: return self.global_funcs[85](a, b)
        elif func_id == 86: return self.global_funcs[86](a, b)
        elif func_id == 87: return self.global_funcs[87](a, b)
        elif func_id == 88: return self.global_funcs[88](a, b)
        elif func_id == 89: return self.global_funcs[89](a, b)
        elif func_id == 90: return self.global_funcs[90](a, b)
        elif func_id == 91: return self.global_funcs[91](a, b)
        elif func_id == 92: return self.global_funcs[92](a, b)
        elif func_id == 93: return self.global_funcs[93](a, b)
        elif func_id == 94: return self.global_funcs[94](a, b)
        elif func_id == 95: return self.global_funcs[95](a, b)
        elif func_id == 96: return self.global_funcs[96](a, b)
        elif func_id == 97: return self.global_funcs[97](a, b)
        elif func_id == 98: return self.global_funcs[98](a, b)
        elif func_id == 99: return self.global_funcs[99](a, b)
        else:
            raise ValueError(f"Unknown function ID: {func_id}")
    
    def _setup_dict_lookup(self):
        """Setup dictionary-based dispatch patterns."""
        # Pre-built function dictionary
        self.dispatch_dict = {}
        for i in range(self.num_functions):
            func_name = f"dispatch_test_{i}"
            func = getattr(self.lib, func_name)
            func.argtypes = [ctypes.c_int, ctypes.c_int]
            func.restype = ctypes.c_int
            self.dispatch_dict[i] = func
    
    def dispatch_dict_lookup(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """Dictionary lookup dispatch (O(1) hash table access)."""
        func = self.dispatch_dict[func_id]
        return func(a, b)
    
    def dispatch_dict_get(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """Dictionary .get() dispatch (with None check overhead)."""
        func = self.dispatch_dict.get(func_id)
        if func is None:
            raise ValueError(f"Unknown function ID: {func_id}")
        return func(a, b)
    
    def _setup_class_getattr(self):
        """Setup class-based dispatch with __getattr__ and caching."""
        class DispatchLibrary:
            def __init__(self, lib):
                self._lib = lib
                self._cache = {}
            
            def __getattr__(self, name):
                if name in self._cache:
                    return self._cache[name]
                
                if name.startswith('dispatch_test_'):
                    try:
                        func = getattr(self._lib, name)
                        func.argtypes = [ctypes.c_int, ctypes.c_int]
                        func.restype = ctypes.c_int
                        self._cache[name] = func
                        return func
                    except AttributeError:
                        pass
                
                raise AttributeError(f"No function named {name}")
        
        self.dispatch_lib = DispatchLibrary(self.lib)
    
    def dispatch_class_getattr(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """Class __getattr__ dispatch with caching."""
        func_name = f"dispatch_test_{func_id}"
        func = getattr(self.dispatch_lib, func_name)
        return func(a, b)
    
    def _setup_class_precached(self):
        """Setup class with pre-cached methods."""
        class DispatchLibraryPreCached:
            def __init__(self, lib, num_functions):
                # Pre-cache all functions as attributes
                for i in range(num_functions):
                    func_name = f"dispatch_test_{i}"
                    func = getattr(lib, func_name)
                    func.argtypes = [ctypes.c_int, ctypes.c_int]
                    func.restype = ctypes.c_int
                    setattr(self, f"func_{i}", func)
        
        self.dispatch_precached = DispatchLibraryPreCached(self.lib, self.num_functions)
    
    def dispatch_class_precached(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """Pre-cached class attributes dispatch."""
        func = getattr(self.dispatch_precached, f"func_{func_id}")
        return func(a, b)
    
    def _setup_enum_table(self):
        """Setup enum-based table dispatch."""
        # Create function table array
        self.enum_dispatch_table = []
        for i in range(self.num_functions):
            func_name = f"dispatch_test_{i}"
            func = getattr(self.lib, func_name)
            func.argtypes = [ctypes.c_int, ctypes.c_int]
            func.restype = ctypes.c_int
            self.enum_dispatch_table.append(func)
    
    def dispatch_enum_table(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """Enum table dispatch (integer array indexing)."""
        return self.enum_dispatch_table[func_id](a, b)
    
    def dispatch_c_baseline(self, func_id: int, a: int = 1, b: int = 2) -> int:
        """C-side dispatch baseline for comparison."""
        return self.lib.dispatch_c_baseline(func_id, a, b)
    
    def _generate_access_patterns(self) -> Dict[str, List[int]]:
        """Generate realistic access patterns for testing."""
        random.seed(42)  # Reproducible patterns
        
        patterns = {}
        
        # Sequential access
        patterns['sequential'] = list(range(self.num_functions))
        
        # Random access
        patterns['random'] = [random.randint(0, self.num_functions-1) for _ in range(1000)]
        
        # Hotspot 80/20 - 80% of calls to 20% of functions
        hotspot_funcs = random.sample(range(self.num_functions), self.num_functions // 5)
        patterns['hotspot_80_20'] = []
        for _ in range(1000):
            if random.random() < 0.8:
                patterns['hotspot_80_20'].append(random.choice(hotspot_funcs))
            else:
                patterns['hotspot_80_20'].append(random.randint(0, self.num_functions-1))
        
        # Worst case - always hit last function in if/elif chain
        patterns['worst_case_linear'] = [self.num_functions-1] * 1000
        
        # Clustered access - calls clustered around subsets
        patterns['clustered'] = []
        cluster_size = 10
        for _ in range(1000):
            cluster_start = random.randint(0, self.num_functions - cluster_size)
            patterns['clustered'].append(random.randint(cluster_start, cluster_start + cluster_size - 1))
        
        # First function only (best case for if/elif)
        patterns['best_case_linear'] = [0] * 1000
        
        return patterns
    
    def get_available_patterns(self) -> List[str]:
        """Get list of available dispatch patterns."""
        return [
            'c_baseline',
            'enum_table', 
            'class_precached',
            'dict_lookup',
            'dict_get',
            'class_getattr',
            'global_if_elif'
        ]
    
    def get_dispatch_function(self, pattern_name: str) -> Callable:
        """Get dispatch function by pattern name."""
        dispatch_map = {
            'c_baseline': self.dispatch_c_baseline,
            'enum_table': self.dispatch_enum_table,
            'class_precached': self.dispatch_class_precached,
            'dict_lookup': self.dispatch_dict_lookup,
            'dict_get': self.dispatch_dict_get,
            'class_getattr': self.dispatch_class_getattr,
            'global_if_elif': self.dispatch_global_if_elif,
        }
        
        if pattern_name not in dispatch_map:
            raise ValueError(f"Unknown dispatch pattern: {pattern_name}")
        
        return dispatch_map[pattern_name]


class DispatchBenchmark:
    """Comprehensive dispatch pattern benchmark suite."""
    
    def __init__(self, num_functions: int = 100):
        """Initialize dispatch benchmark with specified number of functions."""
        self.num_functions = num_functions
        self.patterns = DispatchPatterns(num_functions)
    
    def benchmark_single_pattern(self, pattern_name: str, access_pattern: List[int], 
                                iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark a single dispatch pattern with given access pattern."""
        dispatch_func = self.patterns.get_dispatch_function(pattern_name)
        
        # Warmup phase (H10: cache warming)
        warmup_size = min(100, len(access_pattern))
        for func_id in access_pattern[:warmup_size]:
            dispatch_func(func_id, 1, 2)
        
        # Measurement phase
        total_calls = 0
        start_time = time.perf_counter_ns()
        
        for _ in range(iterations):
            for func_id in access_pattern:
                result = dispatch_func(func_id, 1, 2)
                total_calls += 1
                # Verify correctness
                expected = 1 + 2 + func_id  # From C function: a + b + func_id
                assert result == expected, f"Expected {expected}, got {result} for func {func_id}"
        
        end_time = time.perf_counter_ns()
        
        total_time_ns = end_time - start_time
        ns_per_call = total_time_ns / total_calls
        
        return {
            'pattern': pattern_name,
            'access_pattern': f"{len(access_pattern)} calls",
            'total_calls': total_calls,
            'total_time_ns': total_time_ns,
            'ns_per_call': ns_per_call,
            'calls_per_second': 1e9 / ns_per_call if ns_per_call > 0 else 0
        }
    
    def benchmark_all_patterns(self, access_pattern_name: str = 'random', 
                              iterations: int = 100) -> Dict[str, Dict[str, Any]]:
        """Benchmark all dispatch patterns with specified access pattern."""
        if access_pattern_name not in self.patterns.access_patterns:
            raise ValueError(f"Unknown access pattern: {access_pattern_name}")
        
        access_pattern = self.patterns.access_patterns[access_pattern_name]
        results = {}
        
        # Benchmark each pattern
        for pattern_name in self.patterns.get_available_patterns():
            print(f"Benchmarking {pattern_name} with {access_pattern_name} access...")
            try:
                result = self.benchmark_single_pattern(pattern_name, access_pattern, iterations)
                results[pattern_name] = result
            except Exception as e:
                print(f"Error benchmarking {pattern_name}: {e}")
                results[pattern_name] = {'error': str(e)}
        
        return results
    
    def compare_patterns(self, results: Dict[str, Dict[str, Any]], 
                        baseline: str = 'c_baseline') -> List[Dict[str, Any]]:
        """Compare patterns and rank by performance."""
        if baseline not in results or 'error' in results[baseline]:
            baseline = 'enum_table'  # Fallback baseline
        
        baseline_time = results[baseline]['ns_per_call']
        
        comparison = []
        for pattern_name, result in results.items():
            if 'error' in result:
                continue
            
            relative_performance = result['ns_per_call'] / baseline_time
            
            comparison.append({
                'pattern': pattern_name,
                'ns_per_call': result['ns_per_call'],
                'relative_performance': relative_performance,
                'calls_per_second': result['calls_per_second'],
                'slower_than_baseline': f"{relative_performance:.2f}x"
            })
        
        # Sort by performance (fastest first)
        comparison.sort(key=lambda x: x['ns_per_call'])
        
        return comparison
    
    def test_hypothesis_h9(self) -> Dict[str, Any]:
        """Test H9: Dictionary lookup outperforms if/elif chains for large function sets."""
        print("\n🧪 Testing Hypothesis H9: Dictionary vs if/elif performance")
        
        # Test with different function set sizes
        results = {}
        
        for num_funcs in [10, 25, 50, 100]:
            print(f"Testing with {num_funcs} functions...")
            
            # Create smaller patterns instance
            patterns = DispatchPatterns(num_funcs)
            
            # Test with worst-case access (last function in if/elif chain)
            worst_case_pattern = [num_funcs - 1] * 100
            
            # Measure dict lookup
            dict_func = patterns.get_dispatch_function('dict_lookup')
            start = time.perf_counter_ns()
            for func_id in worst_case_pattern:
                dict_func(func_id, 1, 2)
            dict_time = time.perf_counter_ns() - start
            
            # Measure if/elif (simplified version for smaller sets)
            if_elif_func = patterns.get_dispatch_function('global_if_elif')
            start = time.perf_counter_ns()
            for func_id in worst_case_pattern:
                if_elif_func(func_id, 1, 2)
            if_elif_time = time.perf_counter_ns() - start
            
            results[num_funcs] = {
                'dict_ns_per_call': dict_time / len(worst_case_pattern),
                'if_elif_ns_per_call': if_elif_time / len(worst_case_pattern),
                'dict_advantage': if_elif_time / dict_time
            }
        
        return results
    
    def test_hypothesis_h10(self) -> Dict[str, Any]:
        """Test H10: Cache warming significantly improves dynamic dispatch performance."""
        print("\n🧪 Testing Hypothesis H10: Cache warming effects")
        
        # Test class_getattr pattern (has caching)
        dispatch_func = self.patterns.get_dispatch_function('class_getattr')
        
        # Cold start - first call to each function
        cold_times = []
        for func_id in range(min(20, self.num_functions)):
            start = time.perf_counter_ns()
            dispatch_func(func_id, 1, 2)
            end = time.perf_counter_ns()
            cold_times.append(end - start)
        
        # Warm calls - repeat the same functions
        warm_times = []
        for func_id in range(min(20, self.num_functions)):
            start = time.perf_counter_ns()
            dispatch_func(func_id, 1, 2)
            end = time.perf_counter_ns()
            warm_times.append(end - start)
        
        return {
            'cold_median_ns': sorted(cold_times)[len(cold_times)//2],
            'warm_median_ns': sorted(warm_times)[len(warm_times)//2],
            'cache_speedup': sorted(cold_times)[len(cold_times)//2] / sorted(warm_times)[len(warm_times)//2]
        }
    
    def test_hypothesis_h11(self) -> Dict[str, Any]:
        """Test H11: Function call locality affects dispatch pattern efficiency."""
        print("\n🧪 Testing Hypothesis H11: Locality effects on dispatch")
        
        results = {}
        
        # Test different access patterns
        for pattern_name, access_pattern in self.patterns.access_patterns.items():
            print(f"Testing {pattern_name} access pattern...")
            
            # Use dict_lookup as it should show locality effects
            dispatch_func = self.patterns.get_dispatch_function('dict_lookup')
            
            # Measure performance
            start = time.perf_counter_ns()
            for func_id in access_pattern[:500]:  # Limit for speed
                dispatch_func(func_id, 1, 2)
            end = time.perf_counter_ns()
            
            ns_per_call = (end - start) / 500
            results[pattern_name] = {
                'ns_per_call': ns_per_call,
                'calls_per_second': 1e9 / ns_per_call
            }
        
        return results


def create_dispatch_benchmark(num_functions: int = 100) -> DispatchBenchmark:
    """Factory function to create dispatch benchmark instance."""
    return DispatchBenchmark(num_functions)


if __name__ == "__main__":
    # Self-test and demonstration
    print("🚀 Dispatch Pattern Benchmark Suite")
    print("=" * 50)
    
    # Create benchmark
    benchmark = create_dispatch_benchmark(100)
    
    # Test basic functionality
    print("\n1️⃣ Testing dispatch patterns...")
    for pattern_name in benchmark.patterns.get_available_patterns():
        try:
            dispatch_func = benchmark.patterns.get_dispatch_function(pattern_name)
            result = dispatch_func(5, 10, 20)  # Should return 10 + 20 + 5 = 35
            print(f"✅ {pattern_name}: {result}")
            assert result == 35, f"Expected 35, got {result}"
        except Exception as e:
            print(f"❌ {pattern_name}: {e}")
    
    # Run quick benchmark comparison
    print("\n2️⃣ Quick performance comparison...")
    results = benchmark.benchmark_all_patterns('random', iterations=10)
    comparison = benchmark.compare_patterns(results)
    
    print("\nPerformance Ranking:")
    print("-" * 60)
    for i, result in enumerate(comparison, 1):
        print(f"{i:2d}. {result['pattern']:20s} "
              f"{result['ns_per_call']:8.1f} ns/call "
              f"({result['slower_than_baseline']})")
    
    # Test hypotheses
    print("\n3️⃣ Hypothesis Testing...")
    
    # H9: Dictionary vs if/elif scaling
    h9_results = benchmark.test_hypothesis_h9()
    print(f"\nH9 Results (Dictionary advantage by function count):")
    for num_funcs, result in h9_results.items():
        print(f"  {num_funcs:3d} functions: {result['dict_advantage']:.2f}x faster")
    
    # H10: Cache warming
    h10_results = benchmark.test_hypothesis_h10()
    print(f"\nH10 Results (Cache warming effects):")
    print(f"  Cold calls: {h10_results['cold_median_ns']:.1f} ns")
    print(f"  Warm calls: {h10_results['warm_median_ns']:.1f} ns")
    print(f"  Speedup: {h10_results['cache_speedup']:.2f}x")
    
    # H11: Locality effects
    h11_results = benchmark.test_hypothesis_h11()
    print(f"\nH11 Results (Access pattern locality effects):")
    for pattern, result in h11_results.items():
        print(f"  {pattern:15s}: {result['ns_per_call']:8.1f} ns/call")
    
    print("\n🎉 Dispatch pattern benchmarks completed!")