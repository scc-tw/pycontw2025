#!/usr/bin/env python3
"""
Test: True Parallelism Verification and Scaling Analysis
Tests CPU utilization and scaling behavior under GIL vs no-GIL Python builds.
"""

import unittest
import subprocess
import time
import threading
import multiprocessing
import ctypes
import json
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class ScalingResult:
    """Results from a scaling test."""
    thread_count: int
    execution_time: float
    throughput: float
    speedup: float
    efficiency: float
    
    def to_dict(self):
        return {
            "thread_count": self.thread_count,
            "execution_time": self.execution_time,
            "throughput": self.throughput,
            "speedup": self.speedup,
            "efficiency": self.efficiency
        }


class TestTrueParallelism(unittest.TestCase):
    """Test suite for verifying true parallelism in free-threaded Python."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.base_dir = Path(__file__).parent.parent.parent
        cls.test_dir = Path(__file__).parent
        
        # Python builds
        cls.python_builds = {
            "3.13.5-gil": cls.base_dir / "cpython3.13.5-gil" / "bin" / "python3",
            "3.13.5-nogil": cls.base_dir / "cpython3.13.5-nogil" / "bin" / "python3",
            "3.14.0rc1-gil": cls.base_dir / "cpython3.14.0rc1-gil" / "bin" / "python3",
            "3.14.0rc1-nogil": cls.base_dir / "cpython3.14.0rc1-nogil" / "bin" / "python3",
        }
        
        # Load the thread test library
        cls.lib_path = cls.test_dir / "libthreadtest.so"
        if cls.lib_path.exists():
            cls.lib = ctypes.CDLL(str(cls.lib_path))
            cls._setup_library_functions()
        else:
            cls.lib = None
        
        # CPU count for scaling tests
        cls.cpu_count = multiprocessing.cpu_count()
        cls.thread_counts = [1, 2, 4, 8, min(16, cls.cpu_count)]
    
    @classmethod
    def _setup_library_functions(cls):
        """Set up ctypes function signatures."""
        if cls.lib:
            cls.lib.unsafe_increment.argtypes = [ctypes.c_int]
            cls.lib.unsafe_increment.restype = ctypes.c_long
            
            cls.lib.safe_increment.argtypes = [ctypes.c_int]
            cls.lib.safe_increment.restype = ctypes.c_long
            
            cls.lib.atomic_increment.argtypes = [ctypes.c_int]
            cls.lib.atomic_increment.restype = ctypes.c_long
            
            cls.lib.reset_counters.argtypes = []
            cls.lib.reset_counters.restype = None
    
    def test_cpu_bound_python_scaling(self):
        """Test CPU-bound pure Python workload scaling."""
        
        def cpu_bound_work(iterations=1000000):
            """CPU-intensive Python computation."""
            result = 0
            for i in range(iterations):
                result += i * i
            return result
        
        results = {}
        
        for build_name, python_path in self.python_builds.items():
            if not python_path.exists():
                continue
            
            build_results = []
            
            for thread_count in self.thread_counts:
                # Test code to run in subprocess
                test_code = f"""
import threading
import time

def cpu_bound_work(iterations=1000000):
    result = 0
    for i in range(iterations):
        result += i * i
    return result

def run_threaded(num_threads):
    start = time.perf_counter()
    
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=cpu_bound_work)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    elapsed = time.perf_counter() - start
    return elapsed

# Warm up
cpu_bound_work(100000)

# Measure
elapsed = run_threaded({thread_count})
print(f"TIME: {{elapsed}}")
"""
                
                # Run test
                result = subprocess.run(
                    [str(python_path), "-c", test_code],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if "TIME:" in output:
                        time_str = output.split("TIME:")[1].strip()
                        elapsed = float(time_str)
                        
                        # Calculate metrics
                        baseline = build_results[0].execution_time if build_results else elapsed
                        speedup = baseline / elapsed if elapsed > 0 else 1.0
                        efficiency = speedup / thread_count
                        throughput = thread_count / elapsed if elapsed > 0 else 0
                        
                        scaling_result = ScalingResult(
                            thread_count=thread_count,
                            execution_time=elapsed,
                            throughput=throughput,
                            speedup=speedup,
                            efficiency=efficiency
                        )
                        
                        build_results.append(scaling_result)
            
            results[build_name] = build_results
        
        # Verify scaling differences
        self._verify_scaling_behavior(results)
    
    def test_ffi_scaling_with_library(self):
        """Test FFI call scaling with the thread test library."""
        if not self.lib:
            self.skipTest("Thread test library not available")
        
        results = {}
        iterations = 100000
        
        for build_name, python_path in self.python_builds.items():
            if not python_path.exists():
                continue
            
            build_results = []
            
            for thread_count in self.thread_counts:
                # Test code for FFI scaling
                test_code = f"""
import ctypes
import threading
import time
from pathlib import Path

# Load library
lib_path = Path("{self.lib_path}")
lib = ctypes.CDLL(str(lib_path))
lib.atomic_increment.argtypes = [ctypes.c_int]
lib.atomic_increment.restype = ctypes.c_long
lib.reset_counters.argtypes = []
lib.reset_counters.restype = None

def ffi_work():
    lib.atomic_increment({iterations})

# Reset and warm up
lib.reset_counters()
ffi_work()
lib.reset_counters()

# Measure
start = time.perf_counter()

threads = []
for _ in range({thread_count}):
    t = threading.Thread(target=ffi_work)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

elapsed = time.perf_counter() - start
print(f"TIME: {{elapsed}}")
"""
                
                result = subprocess.run(
                    [str(python_path), "-c", test_code],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if "TIME:" in output:
                        time_str = output.split("TIME:")[1].strip()
                        elapsed = float(time_str)
                        
                        # Calculate metrics
                        baseline = build_results[0].execution_time if build_results else elapsed
                        speedup = baseline / elapsed if elapsed > 0 else 1.0
                        efficiency = speedup / thread_count
                        throughput = thread_count / elapsed if elapsed > 0 else 0
                        
                        scaling_result = ScalingResult(
                            thread_count=thread_count,
                            execution_time=elapsed,
                            throughput=throughput,
                            speedup=speedup,
                            efficiency=efficiency
                        )
                        
                        build_results.append(scaling_result)
            
            results[build_name] = build_results
        
        self._verify_ffi_scaling(results)
    
    def test_memory_bandwidth_scaling(self):
        """Test memory bandwidth utilization under concurrent access."""
        
        def memory_intensive_work(size_mb=10):
            """Memory bandwidth intensive work."""
            size = size_mb * 1024 * 1024 // 8  # Convert to number of floats
            data = list(range(size))
            result = 0
            
            # Multiple passes over large array
            for _ in range(10):
                result += sum(data)
                data = [x * 1.1 for x in data]
            
            return result
        
        results = {}
        
        for build_name, python_path in self.python_builds.items():
            if not python_path.exists():
                continue
            
            build_results = []
            
            for thread_count in [1, 2, 4]:  # Limited thread counts for memory tests
                test_code = f"""
import threading
import time

def memory_intensive_work(size_mb=10):
    size = size_mb * 1024 * 1024 // 8
    data = list(range(size))
    result = 0
    
    for _ in range(10):
        result += sum(data)
        data = [x * 1.1 for x in data]
    
    return result

def run_threaded(num_threads):
    start = time.perf_counter()
    
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=memory_intensive_work)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    elapsed = time.perf_counter() - start
    return elapsed

# Warm up
memory_intensive_work(1)

# Measure
elapsed = run_threaded({thread_count})
print(f"TIME: {{elapsed}}")
print(f"THREADS: {thread_count}")
"""
                
                result = subprocess.run(
                    [str(python_path), "-c", test_code],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if "TIME:" in output:
                        for line in output.split('\n'):
                            if "TIME:" in line:
                                time_str = line.split("TIME:")[1].strip()
                                elapsed = float(time_str)
                                
                                baseline = build_results[0].execution_time if build_results else elapsed
                                speedup = baseline / elapsed if elapsed > 0 else 1.0
                                efficiency = speedup / thread_count
                                throughput = thread_count / elapsed if elapsed > 0 else 0
                                
                                scaling_result = ScalingResult(
                                    thread_count=thread_count,
                                    execution_time=elapsed,
                                    throughput=throughput,
                                    speedup=speedup,
                                    efficiency=efficiency
                                )
                                
                                build_results.append(scaling_result)
                                break
            
            results[build_name] = build_results
        
        # Memory bandwidth should show saturation effects
        self._verify_memory_scaling(results)
    
    def test_context_switching_overhead(self):
        """Test context switching overhead during FFI transitions."""
        if not self.lib:
            self.skipTest("Thread test library not available")
        
        # Test with high frequency of FFI calls
        small_iterations = 10  # Small work per call
        num_calls = 10000  # Many calls
        
        results = {}
        
        for build_name, python_path in self.python_builds.items():
            if not python_path.exists():
                continue
            
            test_code = f"""
import ctypes
import threading
import time
from pathlib import Path

lib_path = Path("{self.lib_path}")
lib = ctypes.CDLL(str(lib_path))
lib.safe_increment.argtypes = [ctypes.c_int]
lib.safe_increment.restype = ctypes.c_long
lib.reset_counters.argtypes = []

def high_frequency_ffi():
    for _ in range({num_calls}):
        lib.safe_increment({small_iterations})

lib.reset_counters()

# Single thread baseline
start = time.perf_counter()
high_frequency_ffi()
single_time = time.perf_counter() - start

lib.reset_counters()

# Multi-thread with high contention
start = time.perf_counter()
threads = []
for _ in range(4):
    t = threading.Thread(target=high_frequency_ffi)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
multi_time = time.perf_counter() - start

overhead = (multi_time - single_time * 4) / (single_time * 4) * 100
print(f"SINGLE: {{single_time}}")
print(f"MULTI: {{multi_time}}")
print(f"OVERHEAD: {{overhead}}%")
"""
            
            result = subprocess.run(
                [str(python_path), "-c", test_code],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                metrics = {}
                for line in output.split('\n'):
                    if "SINGLE:" in line:
                        metrics['single'] = float(line.split(":")[1].strip())
                    elif "MULTI:" in line:
                        metrics['multi'] = float(line.split(":")[1].strip())
                    elif "OVERHEAD:" in line:
                        metrics['overhead'] = float(line.split(":")[1].strip().rstrip('%'))
                
                results[build_name] = metrics
        
        # Verify context switching patterns
        self._verify_context_switching(results)
    
    def _verify_scaling_behavior(self, results: Dict[str, List[ScalingResult]]):
        """Verify that no-GIL builds show better scaling than GIL builds."""
        for build_name, build_results in results.items():
            if not build_results:
                continue
            
            print(f"\nScaling results for {build_name}:")
            for result in build_results:
                print(f"  Threads: {result.thread_count}, "
                      f"Time: {result.execution_time:.3f}s, "
                      f"Speedup: {result.speedup:.2f}x, "
                      f"Efficiency: {result.efficiency:.2%}")
            
            # Check scaling efficiency
            if "nogil" in build_name and len(build_results) > 1:
                # No-GIL should show better scaling
                best_efficiency = max(r.efficiency for r in build_results[1:])
                self.assertGreater(
                    best_efficiency, 0.5,
                    f"No-GIL build {build_name} should show >50% efficiency"
                )
            elif "gil" in build_name and "-gil" in build_name:
                # GIL builds should show limited scaling
                if len(build_results) > 2:
                    # Efficiency should drop significantly with more threads
                    late_efficiency = build_results[-1].efficiency
                    self.assertLess(
                        late_efficiency, 0.5,
                        f"GIL build {build_name} should show limited scaling"
                    )
    
    def _verify_ffi_scaling(self, results: Dict[str, List[ScalingResult]]):
        """Verify FFI scaling patterns."""
        for build_name, build_results in results.items():
            if not build_results:
                continue
            
            print(f"\nFFI scaling results for {build_name}:")
            for result in build_results:
                print(f"  Threads: {result.thread_count}, "
                      f"Speedup: {result.speedup:.2f}x, "
                      f"Efficiency: {result.efficiency:.2%}")
            
            # FFI calls should scale better with no-GIL
            if "nogil" in build_name and len(build_results) > 2:
                # Should maintain reasonable efficiency
                mid_efficiency = build_results[2].efficiency  # 4 threads
                self.assertGreater(
                    mid_efficiency, 0.4,
                    f"No-GIL FFI should maintain >40% efficiency at 4 threads"
                )
    
    def _verify_memory_scaling(self, results: Dict[str, List[ScalingResult]]):
        """Verify memory bandwidth scaling patterns."""
        for build_name, build_results in results.items():
            if not build_results or len(build_results) < 2:
                continue
            
            print(f"\nMemory scaling results for {build_name}:")
            for result in build_results:
                print(f"  Threads: {result.thread_count}, "
                      f"Speedup: {result.speedup:.2f}x")
            
            # Memory bandwidth should saturate
            if len(build_results) >= 3:
                # Speedup should plateau
                speedup_2 = build_results[1].speedup  # 2 threads
                speedup_4 = build_results[2].speedup  # 4 threads
                
                # Diminishing returns expected
                speedup_increase = speedup_4 - speedup_2
                self.assertLess(
                    speedup_increase, speedup_2 - 1.0,
                    "Memory bandwidth should show saturation"
                )
    
    def _verify_context_switching(self, results: Dict[str, Dict]):
        """Verify context switching overhead patterns."""
        print("\nContext switching overhead:")
        for build_name, metrics in results.items():
            if metrics:
                print(f"  {build_name}: {metrics.get('overhead', 'N/A')}% overhead")
                
                # No-GIL should have less overhead
                if "nogil" in build_name and 'overhead' in metrics:
                    self.assertLess(
                        metrics['overhead'], 100,
                        f"No-GIL should have <100% context switch overhead"
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)