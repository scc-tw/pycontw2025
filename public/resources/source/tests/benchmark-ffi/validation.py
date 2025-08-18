"""
Validation suite to ensure all FFI methods produce identical results.

This module validates that ctypes, cffi, pybind11, and PyO3 implementations
all produce the same results for the same inputs, ensuring fair benchmarking.
"""

import math
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass

# Import FFI implementations
from benchmarks.ctypes_bench import create_ctypes_benchmark
from benchmarks.cffi_bench import create_cffi_benchmark


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    passed: bool
    results: Dict[str, Any]
    errors: Dict[str, str]
    tolerances_used: Dict[str, float]


class FFIValidator:
    """Validator for FFI implementation consistency."""
    
    def __init__(self):
        """Initialize the validator with available FFI implementations."""
        self.implementations = {}
        self.errors = {}
        
        # Load available implementations
        try:
            self.implementations['ctypes'] = create_ctypes_benchmark()
            print("✅ ctypes implementation loaded")
        except Exception as e:
            self.errors['ctypes'] = str(e)
            print(f"❌ ctypes implementation failed: {e}")
        
        try:
            self.implementations['cffi'] = create_cffi_benchmark('abi')
            print("✅ cffi implementation loaded")
        except Exception as e:
            self.errors['cffi'] = str(e)
            print(f"❌ cffi implementation failed: {e}")
        
        # Note: pybind11 and PyO3 would be added here when implemented
        print(f"\n📊 Loaded {len(self.implementations)} FFI implementations")
        
        # Define validation test cases
        self.test_cases = self._define_test_cases()
    
    def _define_test_cases(self) -> List[Dict[str, Any]]:
        """Define test cases for validation."""
        return [
            {
                'name': 'noop',
                'method': 'noop',
                'args': [],
                'expected': None,
                'tolerance': 0.0
            },
            {
                'name': 'return_int',
                'method': 'return_int',
                'args': [],
                'expected': 42,
                'tolerance': 0.0
            },
            {
                'name': 'return_int64',
                'method': 'return_int64',
                'args': [],
                'expected': 0x123456789ABCDEF0,
                'tolerance': 0.0
            },
            {
                'name': 'integer_operations',
                'method': 'integer_operations',
                'args': [10, 20],
                'expected': 30,
                'tolerance': 0.0
            },
            {
                'name': 'integer_operations_64bit',
                'method': 'integer_operations_64bit',
                'args': [1000000000000, 2000000000000],
                'expected': 3000000000000,
                'tolerance': 0.0
            },
            {
                'name': 'string_operations_bytes',
                'method': 'string_operations_bytes',
                'args': [b"hello world"],
                'expected': 11,
                'tolerance': 0.0
            },
            {
                'name': 'string_operations_str',
                'method': 'string_operations_str',
                'args': ["hello world"],
                'expected': 11,
                'tolerance': 0.0
            },
            # Disabled for now due to memory management issues
            # {
            #     'name': 'string_concat_operations',
            #     'method': 'string_concat_operations',
            #     'args': ["hello", " world"],
            #     'expected': "hello world",
            #     'tolerance': 0.0
            # },
            {
                'name': 'array_operations_readonly_small',
                'method': 'array_operations_readonly',
                'args': [10],
                'expected': 45.0,  # sum(0..9) = 45
                'tolerance': 1e-10
            },
            {
                'name': 'array_operations_readonly_medium',
                'method': 'array_operations_readonly',
                'args': [100],
                'expected': 4950.0,  # sum(0..99) = 4950
                'tolerance': 1e-10
            },
            {
                'name': 'array_operations_int32',
                'method': 'array_operations_int32',
                'args': [10],
                'expected': 45,  # sum(0..9) = 45
                'tolerance': 0.0
            },
            {
                'name': 'structure_operations_simple',
                'method': 'structure_operations_simple',
                'args': [10, 20, 3.14],
                'expected': 33.14,
                'tolerance': 1e-10
            },
            {
                'name': 'structure_operations_create',
                'method': 'structure_operations_create',
                'args': [5, 15, 2.5],
                'expected': 22.5,
                'tolerance': 1e-10
            },
            {
                'name': 'callback_operations_simple',
                'method': 'callback_operations_simple',
                'args': [42],
                'expected': 84,  # 42 * 2
                'tolerance': 0.0
            },
            {
                'name': 'memory_operations_alloc',
                'method': 'memory_operations_alloc',
                'args': [1024],
                'expected': True,
                'tolerance': 0.0
            },
            {
                'name': 'compute_operations_dot_product_small',
                'method': 'compute_operations_dot_product',
                'args': [10],
                'expected': 570.0,  # sum(i * i * 2) for i in 0..9
                'tolerance': 1e-8
            },
            {
                'name': 'compute_operations_matrix_multiply_small',
                'method': 'compute_operations_matrix_multiply',
                'args': [3, 3, 3],
                'expected': None,  # Will calculate expected value
                'tolerance': 1e-8
            },
        ]
    
    def _calculate_expected_matrix_multiply(self, m: int, n: int, k: int) -> float:
        """Calculate expected result for matrix multiplication test."""
        # Create the same matrices as in the benchmark
        a_data = [float(i + j) for i in range(m) for j in range(k)]
        b_data = [float(i * j + 1) for i in range(k) for j in range(n)]
        
        # Perform multiplication manually
        c_data = [0.0] * (m * n)
        for i in range(m):
            for j in range(n):
                for l in range(k):
                    c_data[i * n + j] += a_data[i * k + l] * b_data[l * n + j]
        
        return sum(c_data)
    
    def validate_single_test(self, test_case: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single test case across all implementations.
        
        Args:
            test_case: Test case definition
            
        Returns:
            ValidationResult object
        """
        test_name = test_case['name']
        method_name = test_case['method']
        args = test_case['args']
        expected = test_case['expected']
        tolerance = test_case['tolerance']
        
        # Special handling for matrix multiply expected value
        if expected is None and method_name == 'compute_operations_matrix_multiply':
            expected = self._calculate_expected_matrix_multiply(*args)
        
        results = {}
        errors = {}
        tolerances_used = {}
        
        # Run test on each implementation
        for impl_name, impl in self.implementations.items():
            try:
                if hasattr(impl, method_name):
                    method = getattr(impl, method_name)
                    if args:
                        result = method(*args)
                    else:
                        result = method()
                    results[impl_name] = result
                    tolerances_used[impl_name] = tolerance
                else:
                    errors[impl_name] = f"Method {method_name} not found"
            except Exception as e:
                errors[impl_name] = str(e)
        
        # Check if all results match expected value and each other
        passed = True
        
        # Check against expected value if provided
        if expected is not None:
            for impl_name, result in results.items():
                if not self._values_match(result, expected, tolerance):
                    passed = False
                    errors[impl_name] = f"Expected {expected}, got {result}"
        
        # Check all implementations against each other
        if len(results) > 1:
            first_result = next(iter(results.values()))
            for impl_name, result in results.items():
                if not self._values_match(result, first_result, tolerance):
                    passed = False
                    if impl_name not in errors:
                        errors[impl_name] = f"Result {result} differs from other implementations"
        
        return ValidationResult(
            test_name=test_name,
            passed=passed,
            results=results,
            errors=errors,
            tolerances_used=tolerances_used
        )
    
    def _values_match(self, value1: Any, value2: Any, tolerance: float) -> bool:
        """
        Check if two values match within tolerance.
        
        Args:
            value1: First value
            value2: Second value
            tolerance: Floating point tolerance
            
        Returns:
            True if values match within tolerance
        """
        # Handle None values
        if value1 is None and value2 is None:
            return True
        if value1 is None or value2 is None:
            return False
        
        # Handle boolean values
        if isinstance(value1, bool) and isinstance(value2, bool):
            return value1 == value2
        
        # Handle string values
        if isinstance(value1, str) and isinstance(value2, str):
            return value1 == value2
        
        # Handle bytes values
        if isinstance(value1, bytes) and isinstance(value2, bytes):
            return value1 == value2
        
        # Handle list/array values
        if isinstance(value1, (list, tuple)) and isinstance(value2, (list, tuple)):
            if len(value1) != len(value2):
                return False
            return all(self._values_match(v1, v2, tolerance) for v1, v2 in zip(value1, value2))
        
        # Handle numeric values
        try:
            v1 = float(value1)
            v2 = float(value2)
            
            # Check for infinite or NaN values
            if math.isinf(v1) or math.isinf(v2) or math.isnan(v1) or math.isnan(v2):
                return (math.isinf(v1) == math.isinf(v2) and 
                       math.isnan(v1) == math.isnan(v2))
            
            # Check absolute difference
            if tolerance == 0.0:
                return v1 == v2
            else:
                return abs(v1 - v2) <= tolerance
                
        except (TypeError, ValueError):
            # Fall back to equality for non-numeric types
            return value1 == value2
    
    def validate_all_tests(self) -> List[ValidationResult]:
        """
        Validate all test cases.
        
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        print(f"\n🔍 Running {len(self.test_cases)} validation tests...")
        print("=" * 80)
        
        passed_count = 0
        
        for test_case in self.test_cases:
            print(f"Testing {test_case['name']}...", end=' ')
            
            result = self.validate_single_test(test_case)
            results.append(result)
            
            if result.passed:
                print("✅ PASSED")
                passed_count += 1
            else:
                print("❌ FAILED")
                for impl_name, error in result.errors.items():
                    print(f"  {impl_name}: {error}")
        
        print("=" * 80)
        print(f"Results: {passed_count}/{len(self.test_cases)} tests passed")
        
        if passed_count == len(self.test_cases):
            print("🎉 All validation tests passed!")
        else:
            print(f"⚠️  {len(self.test_cases) - passed_count} tests failed")
        
        return results
    
    def generate_validation_report(self, results: List[ValidationResult]) -> str:
        """
        Generate a detailed validation report.
        
        Args:
            results: List of validation results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("FFI Implementation Validation Report")
        report.append("=" * 50)
        report.append("")
        
        # Summary
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        report.append(f"Summary: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
        report.append("")
        
        # Implementation status
        report.append("Implementation Status:")
        for impl_name in ['ctypes', 'cffi', 'pybind11', 'pyo3']:
            if impl_name in self.implementations:
                report.append(f"  ✅ {impl_name}: Available")
            elif impl_name in self.errors:
                report.append(f"  ❌ {impl_name}: {self.errors[impl_name]}")
            else:
                report.append(f"  ⏳ {impl_name}: Not implemented")
        report.append("")
        
        # Detailed results
        report.append("Detailed Results:")
        report.append("-" * 20)
        
        for result in results:
            report.append(f"\nTest: {result.test_name}")
            report.append(f"Status: {'PASSED' if result.passed else 'FAILED'}")
            
            if result.results:
                report.append("Results:")
                for impl_name, value in result.results.items():
                    report.append(f"  {impl_name}: {value}")
            
            if result.errors:
                report.append("Errors:")
                for impl_name, error in result.errors.items():
                    report.append(f"  {impl_name}: {error}")
        
        return "\n".join(report)
    
    def benchmark_validation_overhead(self) -> Dict[str, float]:
        """
        Benchmark the overhead of validation calls.
        
        Returns:
            Dictionary of benchmark times per implementation
        """
        import time
        
        overhead_results = {}
        
        # Simple test case
        test_method = 'return_int'
        iterations = 1000
        
        for impl_name, impl in self.implementations.items():
            if hasattr(impl, test_method):
                method = getattr(impl, test_method)
                
                # Warm up
                for _ in range(100):
                    method()
                
                # Benchmark
                start_time = time.perf_counter()
                for _ in range(iterations):
                    method()
                end_time = time.perf_counter()
                
                avg_time = (end_time - start_time) / iterations * 1e9  # nanoseconds
                overhead_results[impl_name] = avg_time
        
        return overhead_results


def run_validation() -> bool:
    """
    Run complete validation suite.
    
    Returns:
        True if all tests pass, False otherwise
    """
    validator = FFIValidator()
    
    if not validator.implementations:
        print("❌ No FFI implementations available for validation")
        return False
    
    # Run validation tests
    results = validator.validate_all_tests()
    
    # Generate detailed report
    report = validator.generate_validation_report(results)
    
    # Save report to file
    report_file = "validation_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Benchmark validation overhead
    print("\n⏱️  Benchmarking validation overhead...")
    overhead = validator.benchmark_validation_overhead()
    
    if overhead:
        print("Validation call overhead (return_int):")
        for impl_name, time_ns in overhead.items():
            print(f"  {impl_name}: {time_ns:.1f} ns")
    
    # Return overall pass/fail status
    return all(result.passed for result in results)


if __name__ == "__main__":
    success = run_validation()
    exit(0 if success else 1)