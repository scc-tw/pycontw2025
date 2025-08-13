#!/usr/bin/env python3
"""
CPU Performance Benchmark Test
PyCon TW 2025 Demo
"""

import time
import numpy as np
from typing import List, Dict, Any


def matrix_multiplication_benchmark(size: int = 1000) -> Dict[str, Any]:
    """Benchmark matrix multiplication performance."""
    matrix_a = np.random.rand(size, size)
    matrix_b = np.random.rand(size, size)
    
    start_time = time.perf_counter()
    result = np.matmul(matrix_a, matrix_b)
    end_time = time.perf_counter()
    
    return {
        "operation": "matrix_multiplication",
        "size": size,
        "execution_time": end_time - start_time,
        "memory_usage_mb": (matrix_a.nbytes + matrix_b.nbytes + result.nbytes) / (1024 * 1024)
    }


def fibonacci_recursive(n: int) -> int:
    """Calculate Fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def recursive_benchmark(n: int = 30) -> Dict[str, Any]:
    """Benchmark recursive function performance."""
    start_time = time.perf_counter()
    result = fibonacci_recursive(n)
    end_time = time.perf_counter()
    
    return {
        "operation": "fibonacci_recursive",
        "n": n,
        "result": result,
        "execution_time": end_time - start_time
    }


def list_comprehension_benchmark(size: int = 1000000) -> Dict[str, Any]:
    """Benchmark list comprehension vs loop performance."""
    # List comprehension
    start_comp = time.perf_counter()
    comp_result = [i ** 2 for i in range(size)]
    end_comp = time.perf_counter()
    
    # Traditional loop
    start_loop = time.perf_counter()
    loop_result = []
    for i in range(size):
        loop_result.append(i ** 2)
    end_loop = time.perf_counter()
    
    return {
        "operation": "list_operations",
        "size": size,
        "comprehension_time": end_comp - start_comp,
        "loop_time": end_loop - start_loop,
        "speedup": (end_loop - start_loop) / (end_comp - start_comp)
    }


def run_all_benchmarks() -> List[Dict[str, Any]]:
    """Run all benchmark tests."""
    results = []
    
    print("Running CPU Performance Benchmarks...")
    
    # Matrix multiplication
    print("1. Matrix Multiplication...")
    results.append(matrix_multiplication_benchmark(500))
    results.append(matrix_multiplication_benchmark(1000))
    
    # Recursive operations
    print("2. Recursive Operations...")
    results.append(recursive_benchmark(25))
    results.append(recursive_benchmark(30))
    
    # List operations
    print("3. List Operations...")
    results.append(list_comprehension_benchmark(100000))
    results.append(list_comprehension_benchmark(1000000))
    
    return results


if __name__ == "__main__":
    import json
    
    results = run_all_benchmarks()
    
    print("\n" + "=" * 50)
    print("Benchmark Results:")
    print("=" * 50)
    
    for result in results:
        print(json.dumps(result, indent=2))
    
    # Save results to file
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to benchmark_results.json")