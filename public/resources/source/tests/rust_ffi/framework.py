# rust_ffi/framework.py
# Core testing framework for PyO3 bug verification and performance analysis

import sys
import threading
import time
import ctypes
import subprocess
import tempfile
import concurrent.futures
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

@dataclass
class PyO3BugResult:
    """Results from PyO3 bug reproduction test"""
    bug_id: str
    reproduced: bool
    error_message: Optional[str]
    reproduction_count: int
    total_attempts: int
    timing_data: Dict[str, float]
    environment_info: Dict[str, Any]

class PyO3BugTester:
    """Framework for reproducing and analyzing PyO3 bugs"""
    
    def __init__(self, pyo3_version: str, python_executable: str):
        self.pyo3_version = pyo3_version
        self.python_executable = python_executable
        self.gil_disabled = self._check_gil_status()
        self.reproduction_attempts = 100  # Default attempts
        
    def _check_gil_status(self) -> bool:
        """Check if GIL is disabled in current Python build"""
        try:
            result = subprocess.run([
                self.python_executable, "-c", 
                "import sys; print(hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled())"
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip() == "True"
        except:
            return False
            
    def test_bug_4882_abi_cache_poisoning(self) -> PyO3BugResult:
        """Test ABI cache poisoning when toggling GIL vs free-threaded builds"""
        poisoning_detected = False
        errors = []
        timing_data = {}
        
        # This test requires building and testing with different Python configurations
        test_scenarios = [
            ("cpython3.13.5-gil", "Standard GIL build"),
            ("cpython3.13.5-nogil", "Free-threaded build"),
            ("cpython3.14.0rc1-gil", "Python 3.14 GIL build"),
            ("cpython3.14.0rc1-nogil", "Python 3.14 free-threaded build")
        ]
        
        for i, (python_build, description) in enumerate(test_scenarios):
            start_time = time.perf_counter()
            
            try:
                # Build PyO3 module with specific Python version
                build_result = subprocess.run([
                    "cargo", "build", "--release"
                ], env={
                    **os.environ,
                    "PYTHON_SYS_EXECUTABLE": f"./{python_build}/bin/python3"
                }, capture_output=True, text=True, cwd="pyo3_investigation")
                
                if build_result.returncode != 0:
                    errors.append(f"Build failed for {python_build}: {build_result.stderr}")
                    continue
                    
                # Test module import with different Python builds
                for j, (test_python, _) in enumerate(test_scenarios):
                    if i == j:
                        continue  # Skip same build
                        
                    import_result = subprocess.run([
                        f"./{test_python}/bin/python3", "-c",
                        "import pyo3_investigation; print('Import successful')"
                    ], capture_output=True, text=True)
                    
                    if import_result.returncode != 0:
                        error_msg = f"ABI mismatch: Built with {python_build}, imported with {test_python}"
                        errors.append(error_msg)
                        
                        # Check for specific ABI poisoning indicators
                        if "incompatible" in import_result.stderr.lower() or \
                           "symbol" in import_result.stderr.lower():
                            poisoning_detected = True
                            
            except Exception as e:
                errors.append(f"Test exception for {python_build}: {str(e)}")
                
            end_time = time.perf_counter()
            timing_data[f"scenario_{i}_{python_build}"] = end_time - start_time
            
        return PyO3BugResult(
            bug_id="4882",
            reproduced=poisoning_detected,
            error_message="; ".join(errors[:3]) if errors else None,
            reproduction_count=len([e for e in errors if "ABI mismatch" in e]),
            total_attempts=len(test_scenarios) * (len(test_scenarios) - 1),
            timing_data=timing_data,
            environment_info={
                "test_scenarios": len(test_scenarios),
                "build_system": "cargo/PyO3"
            }
        )
        
    def test_bug_4627_subclass_gc_flakiness(self) -> PyO3BugResult:
        """Test subclass creation/deletion cycles under concurrent load"""
        flakiness_detected = False
        errors = []
        timing_data = {}
        
        def subclass_stress_worker(worker_id: int) -> List[str]:
            """Create and destroy Python subclasses repeatedly"""
            local_errors = []
            
            try:
                import pyo3_investigation
                
                for i in range(500):
                    try:
                        # Create subclass instance
                        obj = pyo3_investigation.create_test_subclass(f"worker_{worker_id}_obj_{i}")
                        
                        # Force garbage collection
                        import gc
                        gc.collect()
                        
                        # Access object after GC
                        _ = obj.test_method()
                        
                        # Delete reference
                        del obj
                        
                    except Exception as e:
                        local_errors.append(f"Worker {worker_id}, iter {i}: {str(e)}")
                        
            except Exception as e:
                local_errors.append(f"Worker {worker_id} setup error: {str(e)}")
                
            return local_errors
            
        for attempt in range(50):  # Fewer attempts, longer stress test
            start_time = time.perf_counter()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(subclass_stress_worker, i)
                    for i in range(4)
                ]
                
                attempt_errors = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        worker_errors = future.result(timeout=10.0)
                        attempt_errors.extend(worker_errors)
                    except Exception as e:
                        attempt_errors.append(f"Worker exception: {str(e)}")
                        
            end_time = time.perf_counter()
            timing_data[f"attempt_{attempt}"] = end_time - start_time
            
            if attempt_errors:
                flakiness_detected = True
                errors.extend(attempt_errors)
                
        return PyO3BugResult(
            bug_id="4627",
            reproduced=flakiness_detected,
            error_message="; ".join(errors[:3]) if errors else None,
            reproduction_count=len(errors),
            total_attempts=50,
            timing_data=timing_data,
            environment_info={
                "worker_threads": 4,
                "objects_per_worker": 500,
                "gil_disabled": self.gil_disabled
            }
        )

class PerformanceComparison:
    """Compare PyO3 performance vs handcrafted FFI"""
    
    def __init__(self, handcrafted_lib_path: str):
        self.handcrafted_lib = ctypes.CDLL(handcrafted_lib_path)
        self._setup_handcrafted_functions()
        
    def _setup_handcrafted_functions(self):
        """Setup function signatures for handcrafted FFI"""
        # Basic function call
        self.handcrafted_lib.test_function_call.argtypes = []
        self.handcrafted_lib.test_function_call.restype = ctypes.c_int
        
        # String operations
        self.handcrafted_lib.test_string_conversion.argtypes = [ctypes.c_char_p]
        self.handcrafted_lib.test_string_conversion.restype = ctypes.c_char_p
        
        # Memory operations
        self.handcrafted_lib.test_memory_allocation.argtypes = [ctypes.c_size_t]
        self.handcrafted_lib.test_memory_allocation.restype = ctypes.c_void_p
        
        # Memory cleanup
        self.handcrafted_lib.test_memory_free.argtypes = [ctypes.c_void_p]
        self.handcrafted_lib.test_memory_free.restype = None
        
    def benchmark_function_call_overhead(self, iterations: int = 10000) -> Dict[str, float]:
        """Compare function call overhead between PyO3 and handcrafted FFI"""
        import pyo3_investigation
        
        # Warmup
        for _ in range(100):
            self.handcrafted_lib.test_function_call()
            pyo3_investigation.pyo3_function_call_test()
            
        # Benchmark handcrafted FFI
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            self.handcrafted_lib.test_function_call()
        handcrafted_time = time.perf_counter_ns() - start_time
        
        # Benchmark PyO3
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            pyo3_investigation.pyo3_function_call_test()
        pyo3_time = time.perf_counter_ns() - start_time
        
        return {
            "handcrafted_ns_per_call": handcrafted_time / iterations,
            "pyo3_ns_per_call": pyo3_time / iterations,
            "overhead_percent": ((pyo3_time - handcrafted_time) / handcrafted_time) * 100,
            "iterations": iterations
        }
        
    def benchmark_string_conversion(self, test_string: str, iterations: int = 1000) -> Dict[str, float]:
        """Compare string conversion performance"""
        import pyo3_investigation
        
        test_bytes = test_string.encode('utf-8')
        
        # Benchmark handcrafted string conversion
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            result = self.handcrafted_lib.test_string_conversion(test_bytes)
            # Convert back to Python string
            if result:
                _ = ctypes.string_at(result).decode('utf-8')
        handcrafted_time = time.perf_counter_ns() - start_time
        
        # Benchmark PyO3 string conversion
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            result = pyo3_investigation.pyo3_string_conversion_test(test_string)
        pyo3_time = time.perf_counter_ns() - start_time
        
        return {
            "handcrafted_ns_per_conversion": handcrafted_time / iterations,
            "pyo3_ns_per_conversion": pyo3_time / iterations,
            "string_length": len(test_string),
            "overhead_percent": ((pyo3_time - handcrafted_time) / handcrafted_time) * 100
        }
        
    def benchmark_memory_management(self, allocation_size: int, iterations: int = 1000) -> Dict[str, float]:
        """Compare memory allocation and reference counting patterns"""
        import pyo3_investigation
        import gc
        
        # Measure handcrafted memory management
        start_time = time.perf_counter_ns()
        ptrs = []
        for _ in range(iterations):
            ptr = self.handcrafted_lib.test_memory_allocation(allocation_size)
            ptrs.append(ptr)
        
        # Manual cleanup (simulating manual reference counting)
        for ptr in ptrs:
            self.handcrafted_lib.test_memory_free(ptr)
        handcrafted_time = time.perf_counter_ns() - start_time
        
        # Measure PyO3 memory management
        gc.collect()  # Clean slate
        start_time = time.perf_counter_ns()
        objects = []
        for _ in range(iterations):
            obj = pyo3_investigation.create_test_object(allocation_size)
            objects.append(obj)
            
        # Let PyO3 handle cleanup automatically
        del objects
        gc.collect()
        pyo3_time = time.perf_counter_ns() - start_time
        
        return {
            "handcrafted_ns_per_allocation": handcrafted_time / iterations,
            "pyo3_ns_per_allocation": pyo3_time / iterations,
            "allocation_size": allocation_size,
            "overhead_percent": ((pyo3_time - handcrafted_time) / handcrafted_time) * 100
        }

class ThreadSafetyAnalyzer:
    """Analyze thread safety issues in PyO3 vs handcrafted FFI"""
    
    def __init__(self, handcrafted_lib_path: str, test_duration: float = 10.0):
        self.handcrafted_lib = ctypes.CDLL(handcrafted_lib_path)
        self.test_duration = test_duration
        self.thread_count = 8
        self._setup_handcrafted_functions()
        
    def _setup_handcrafted_functions(self):
        """Setup function signatures for concurrent testing"""
        # Concurrent access functions
        self.handcrafted_lib.create_shared_object.argtypes = []
        self.handcrafted_lib.create_shared_object.restype = ctypes.c_void_p
        
        self.handcrafted_lib.concurrent_operation.argtypes = [ctypes.c_void_p]
        self.handcrafted_lib.concurrent_operation.restype = ctypes.c_int
        
        self.handcrafted_lib.release_shared_object.argtypes = [ctypes.c_void_p]
        self.handcrafted_lib.release_shared_object.restype = None
        
    def test_concurrent_access_patterns(self) -> Dict[str, Any]:
        """Test concurrent access to FFI functions"""
        import pyo3_investigation
        
        results = {
            "pyo3_errors": [],
            "handcrafted_errors": [],
            "race_conditions_detected": False,
            "deadlocks_detected": False
        }
        
        def pyo3_stress_worker():
            """Worker for PyO3 stress testing"""
            errors = []
            start_time = time.time()
            
            while time.time() - start_time < self.test_duration:
                try:
                    # Test concurrent PyO3 operations
                    obj = pyo3_investigation.create_test_subclass(f"stress_{threading.current_thread().ident}")
                    result = obj.test_method()
                    del obj
                except Exception as e:
                    errors.append(str(e))
                    
            return errors
            
        def handcrafted_stress_worker():
            """Worker for handcrafted FFI stress testing"""
            errors = []
            start_time = time.time()
            
            while time.time() - start_time < self.test_duration:
                try:
                    # Test concurrent handcrafted operations
                    obj_ptr = self.handcrafted_lib.create_shared_object()
                    result = self.handcrafted_lib.concurrent_operation(obj_ptr)
                    self.handcrafted_lib.release_shared_object(obj_ptr)
                except Exception as e:
                    errors.append(str(e))
                    
            return errors
            
        # Run concurrent tests
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # Test PyO3
            pyo3_futures = [
                executor.submit(pyo3_stress_worker)
                for _ in range(self.thread_count // 2)
            ]
            
            # Test handcrafted FFI
            handcrafted_futures = [
                executor.submit(handcrafted_stress_worker)
                for _ in range(self.thread_count // 2)
            ]
            
            # Collect results
            for future in concurrent.futures.as_completed(pyo3_futures):
                try:
                    errors = future.result(timeout=self.test_duration + 5)
                    results["pyo3_errors"].extend(errors)
                except concurrent.futures.TimeoutError:
                    results["deadlocks_detected"] = True
                    results["pyo3_errors"].append("Timeout - possible deadlock")
                    
            for future in concurrent.futures.as_completed(handcrafted_futures):
                try:
                    errors = future.result(timeout=self.test_duration + 5)
                    results["handcrafted_errors"].extend(errors)
                except concurrent.futures.TimeoutError:
                    results["deadlocks_detected"] = True
                    results["handcrafted_errors"].append("Timeout - possible deadlock")
                    
        # Analyze for race conditions
        race_indicators = ["race", "corrupt", "invalid", "segfault", "assertion"]
        for error in results["pyo3_errors"] + results["handcrafted_errors"]:
            if any(indicator in error.lower() for indicator in race_indicators):
                results["race_conditions_detected"] = True
                break
                
        return results