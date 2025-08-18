#!/usr/bin/env python3
"""
Demo script showing all 4 FFI methods working together - Clean Architecture
"""

import sys
from pathlib import Path

# Add the benchmark-ffi root to Python path
benchmark_root = Path(__file__).parent.parent
sys.path.insert(0, str(benchmark_root))

# Import clean implementations (no more LD_LIBRARY_PATH hacks!)
from framework.timer import BenchmarkTimer, print_benchmark_results
from implementations import get_available_implementations

def main():
    print("🚀 All FFI Methods Performance Comparison - Clean Architecture")
    print("=" * 70)
    
    # Load all available implementations using clean registry
    impl_objects = get_available_implementations()
    
    if not impl_objects:
        print("❌ No FFI implementations available!")
        return 1
    
    # Prepare callable functions for benchmarking
    implementations = {}
    
    for name, impl in impl_objects.items():
        try:
            # Standardized interface for return_int function
            if hasattr(impl, 'return_int'):
                implementations[name] = lambda i=impl: i.return_int()
            elif hasattr(impl, 'lib'):
                if hasattr(impl.lib, 'return_int'):
                    implementations[name] = lambda i=impl: i.lib.return_int()
                elif hasattr(impl.lib, 'py_return_int'):  # PyO3 naming
                    implementations[name] = lambda i=impl: i.lib.py_return_int()
                else:
                    print(f"⚠️ {name}: No return_int method found")
            else:
                print(f"⚠️ {name}: Incompatible interface")
                
        except Exception as e:
            print(f"❌ {name} setup failed: {e}")
    
    print(f"\n📊 Successfully prepared {len(implementations)} FFI implementations for benchmarking")
    
    if len(implementations) >= 2:
        # Run performance comparison
        print("\n🏃 Running performance comparison (return_int)...")
        timer = BenchmarkTimer(target_relative_error=0.03, max_time_seconds=15)
        
        results = timer.compare_implementations(implementations, baseline_name='ctypes')
        print_benchmark_results(results, "All FFI Methods Performance Comparison")
        
        # Array operations comparison
        if len(implementations) >= 3:
            print("\n🔢 Array Operations Comparison...")
            array_implementations = {}
            
            if 'ctypes' in implementations:
                array_implementations['ctypes'] = lambda: ctypes_bench.array_operations_readonly(1000)
            if 'cffi' in implementations:
                array_implementations['cffi'] = lambda: cffi_bench.array_operations_readonly(1000)
            if 'pybind11' in implementations:
                # Check if pybind11 has the right method
                try:
                    test_result = pybind11_bench.benchmark_array_operations(1000)
                    array_implementations['pybind11'] = lambda: pybind11_bench.benchmark_array_operations(1000)
                except:
                    print("⚠️ pybind11 array operations not available")
            if 'pyo3' in implementations:
                # Test PyO3 array operations
                try:
                    import numpy as np
                    test_array = np.array([1.0, 2.0, 3.0], dtype=np.float64)
                    result = pyo3_bench.lib.py_sum_doubles_readonly(test_array)
                    array_implementations['pyo3'] = lambda: pyo3_bench.lib.py_sum_doubles_readonly(np.random.random(1000).astype(np.float64))
                except Exception as e:
                    print(f"⚠️ PyO3 array operations not available: {e}")
            
            if len(array_implementations) >= 2:
                array_results = timer.compare_implementations(array_implementations, baseline_name='ctypes')
                print_benchmark_results(array_results, "Array Operations Performance Comparison")
    
    else:
        print("❌ Need at least 2 implementations for comparison")
    
    print("\n🎉 Demo completed!")

if __name__ == "__main__":
    main()