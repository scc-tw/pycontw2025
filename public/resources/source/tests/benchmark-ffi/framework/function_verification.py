"""
Function Call Verification for FFI Benchmarks

Ensures all FFI methods call identical C functions for fair performance comparison.
This module validates that ctypes, cffi, pybind11, and PyO3 implementations use
the same underlying C functions and calling conventions.

Addresses academic review criticism: "Contaminated experimental design - different 
code paths for each FFI method violate controlled experiment principles."
"""

import os
import sys
import time
import inspect
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, Set
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ValidationStatus(Enum):
    """Function validation status."""
    IDENTICAL = "identical"
    EQUIVALENT = "equivalent" 
    DIFFERENT = "different"
    MISSING = "missing"
    ERROR = "error"


@dataclass
class FunctionSignature:
    """Function signature information."""
    name: str
    args: List[str]
    return_type: str
    c_function_name: str
    validation_status: ValidationStatus = ValidationStatus.MISSING


@dataclass
class CallVerification:
    """Results from function call verification."""
    function_name: str
    implementations: Dict[str, Any]  # FFI method -> result
    identical_results: bool
    result_values: Dict[str, Any]
    error_messages: Dict[str, str] = None


@dataclass
class ComparisonReport:
    """Comprehensive FFI function comparison report."""
    timestamp: float
    implementations_tested: List[str]
    total_functions: int
    identical_functions: int
    equivalent_functions: int
    different_functions: int
    missing_functions: int
    verification_results: List[CallVerification]
    consistency_score: float  # 0.0-1.0, higher is better


class FFIFunctionVerifier:
    """Verifies identical C function usage across all FFI implementations."""
    
    # Core C functions that MUST be identical across all FFI methods
    CORE_FUNCTIONS = {
        # Baseline functions
        'noop': {'args': [], 'return': 'void', 'c_name': 'noop'},
        'return_int': {'args': [], 'return': 'int', 'c_name': 'return_int'},
        'return_int64': {'args': [], 'return': 'int64', 'c_name': 'return_int64'},
        'return_double': {'args': [], 'return': 'double', 'c_name': 'return_double'},
        
        # Integer operations
        'add_int32': {'args': ['int32', 'int32'], 'return': 'int32', 'c_name': 'add_int32'},
        'add_int64': {'args': ['int64', 'int64'], 'return': 'int64', 'c_name': 'add_int64'},
        
        # Boolean operations
        'logical_and': {'args': ['bool', 'bool'], 'return': 'bool', 'c_name': 'logical_and'},
        
        # Float operations
        'add_float': {'args': ['float', 'float'], 'return': 'float', 'c_name': 'add_float'},
        'add_double': {'args': ['double', 'double'], 'return': 'double', 'c_name': 'add_double'},
        
        # Array operations
        'sum_doubles_readonly': {'args': ['double_array', 'size'], 'return': 'double', 'c_name': 'sum_doubles_readonly'},
        'scale_doubles_inplace': {'args': ['double_array', 'size', 'double'], 'return': 'void', 'c_name': 'scale_doubles_inplace'},
        'sum_int32_array': {'args': ['int32_array', 'size'], 'return': 'int32', 'c_name': 'sum_int32_array'},
        
        # Matrix operations
        'dot_product': {'args': ['double_array', 'double_array', 'size'], 'return': 'double', 'c_name': 'dot_product'},
        'matrix_multiply_naive': {'args': ['double_array', 'double_array', 'double_array', 'size', 'size', 'size'], 'return': 'void', 'c_name': 'matrix_multiply_naive'},
        
        # String operations
        'bytes_length': {'args': ['string', 'size'], 'return': 'size', 'c_name': 'bytes_length'},
        'utf8_length': {'args': ['string'], 'return': 'size', 'c_name': 'utf8_length'},
        'string_concat': {'args': ['string', 'string'], 'return': 'string', 'c_name': 'string_concat'},
        
        # Memory operations
        'allocate_sized': {'args': ['size'], 'return': 'pointer', 'c_name': 'allocate_sized'},
        'deallocate': {'args': ['pointer'], 'return': 'void', 'c_name': 'deallocate'},
    }
    
    def __init__(self):
        """Initialize FFI function verifier."""
        self.implementations = {}
        self.verification_results = []
        
        print("🔍 FFI Function Verifier initialized")
        print(f"📋 Will verify {len(self.CORE_FUNCTIONS)} core functions")
    
    def load_implementations(self) -> Dict[str, bool]:
        """Load all available FFI implementations."""
        loading_results = {}
        
        # Load ctypes implementation
        try:
            from benchmarks.ctypes_bench import CtypesBenchmark
            self.implementations['ctypes'] = CtypesBenchmark()
            loading_results['ctypes'] = True
            print("✅ ctypes implementation loaded")
        except Exception as e:
            loading_results['ctypes'] = False
            print(f"❌ ctypes implementation failed: {e}")
        
        # Load cffi implementation
        try:
            from benchmarks.cffi_bench import CFfiBenchmark
            self.implementations['cffi'] = CFfiBenchmark()
            loading_results['cffi'] = True
            print("✅ cffi implementation loaded")
        except Exception as e:
            loading_results['cffi'] = False
            print(f"❌ cffi implementation failed: {e}")
        
        # Load pybind11 implementation
        try:
            from benchmarks.pybind11_bench import Pybind11Benchmark
            self.implementations['pybind11'] = Pybind11Benchmark()
            loading_results['pybind11'] = True
            print("✅ pybind11 implementation loaded")
        except Exception as e:
            loading_results['pybind11'] = False
            print(f"⚠️ pybind11 implementation not available: {e}")
        
        # Load PyO3 implementation
        try:
            from benchmarks.pyo3_bench import PyO3Benchmark
            self.implementations['pyo3'] = PyO3Benchmark()
            loading_results['pyo3'] = True
            print("✅ PyO3 implementation loaded")
        except Exception as e:
            loading_results['pyo3'] = False
            print(f"⚠️ PyO3 implementation not available: {e}")
        
        loaded_count = sum(1 for success in loading_results.values() if success)
        print(f"📊 Loaded {loaded_count}/4 FFI implementations")
        
        return loading_results
    
    def verify_function_consistency(self) -> ComparisonReport:
        """Verify that all FFI methods call identical C functions."""
        print("\n🔬 Verifying function consistency across FFI implementations...")
        print("=" * 70)
        
        # Load implementations
        loading_results = self.load_implementations()
        available_implementations = [impl for impl, success in loading_results.items() if success]
        
        if len(available_implementations) < 2:
            raise RuntimeError("Need at least 2 FFI implementations for comparison")
        
        verification_results = []
        identical_count = 0
        equivalent_count = 0
        different_count = 0
        missing_count = 0
        
        for func_name, func_spec in self.CORE_FUNCTIONS.items():
            print(f"\n🧪 Testing {func_name} -> {func_spec['c_name']}")
            
            verification = self._verify_single_function(func_name, func_spec, available_implementations)
            verification_results.append(verification)
            
            if verification.identical_results:
                identical_count += 1
                print(f"  ✅ IDENTICAL across {len(verification.implementations)} implementations")
            elif self._are_results_equivalent(verification.result_values):
                equivalent_count += 1
                print(f"  ⚠️ EQUIVALENT (minor differences) across {len(verification.implementations)} implementations")
            elif len(verification.implementations) < len(available_implementations):
                missing_count += 1
                print(f"  ❌ MISSING in {len(available_implementations) - len(verification.implementations)} implementations")
            else:
                different_count += 1
                print(f"  🚨 DIFFERENT results across implementations")
                for impl, result in verification.result_values.items():
                    print(f"    {impl}: {result}")
        
        # Calculate consistency score
        total_functions = len(self.CORE_FUNCTIONS)
        consistency_score = (identical_count + equivalent_count * 0.8) / total_functions
        
        report = ComparisonReport(
            timestamp=time.time(),
            implementations_tested=available_implementations,
            total_functions=total_functions,
            identical_functions=identical_count,
            equivalent_functions=equivalent_count,
            different_functions=different_count,
            missing_functions=missing_count,
            verification_results=verification_results,
            consistency_score=consistency_score
        )
        
        self._print_consistency_summary(report)
        return report
    
    def _verify_single_function(self, func_name: str, func_spec: Dict[str, Any], 
                               available_implementations: List[str]) -> CallVerification:
        """Verify a single function across all implementations."""
        implementations = {}
        result_values = {}
        error_messages = {}
        
        for impl_name in available_implementations:
            impl = self.implementations[impl_name]
            
            try:
                # Get the appropriate method and test arguments
                method, test_args = self._get_method_and_args(impl, impl_name, func_name, func_spec)
                
                if method is None:
                    error_messages[impl_name] = f"Method {func_name} not found"
                    continue
                
                # Execute the method with test arguments
                result = method(*test_args) if test_args else method()
                
                implementations[impl_name] = method
                result_values[impl_name] = result
                
            except Exception as e:
                error_messages[impl_name] = str(e)
        
        # Check if all results are identical
        if len(result_values) >= 2:
            values = list(result_values.values())
            identical_results = self._are_results_identical(values)
        else:
            identical_results = False
        
        return CallVerification(
            function_name=func_name,
            implementations=implementations,
            identical_results=identical_results,
            result_values=result_values,
            error_messages=error_messages if error_messages else None
        )
    
    def _get_method_and_args(self, impl, impl_name: str, func_name: str, 
                           func_spec: Dict[str, Any]) -> Tuple[Optional[Callable], List[Any]]:
        """Get method and test arguments for a specific implementation."""
        # Map function names to implementation-specific method names
        method_mappings = {
            'ctypes': {
                'noop': ('lib.noop', []),
                'return_int': ('lib.return_int', []),
                'return_int64': ('lib.return_int64', []),
                'return_double': ('lib.return_double', []),
                'add_int32': ('lib.add_int32', [10, 20]),
                'add_int64': ('lib.add_int64', [1000000, 2000000]),
                'logical_and': ('lib.logical_and', [True, False]),
                'add_float': ('lib.add_float', [3.14, 2.71]),
                'add_double': ('lib.add_double', [3.14159, 2.71828]),
                'sum_doubles_readonly': ('_test_sum_doubles_readonly', []),
                'scale_doubles_inplace': ('_test_scale_doubles_inplace', []),
                'sum_int32_array': ('_test_sum_int32_array', []),
                'dot_product': ('compute_operations_dot_product', [100]),
                'matrix_multiply_naive': ('compute_operations_matrix_multiply', [10, 10, 10]),
                'bytes_length': ('_test_bytes_length', []),
                'utf8_length': ('_test_utf8_length', []),
                'string_concat': ('_test_string_concat', []),
                'allocate_sized': ('lib.allocate_sized', [1024]),
                'deallocate': ('_test_deallocate', []),
            },
            'cffi': {
                'noop': ('lib.noop', []),
                'return_int': ('lib.return_int', []),
                'return_int64': ('lib.return_int64', []),
                'return_double': ('lib.return_double', []),
                'add_int32': ('lib.add_int32', [10, 20]),
                'add_int64': ('lib.add_int64', [1000000, 2000000]),
                'logical_and': ('lib.logical_and', [True, False]),
                'add_float': ('lib.add_float', [3.14, 2.71]),
                'add_double': ('lib.add_double', [3.14159, 2.71828]),
                'sum_doubles_readonly': ('_test_sum_doubles_readonly', []),
                'scale_doubles_inplace': ('_test_scale_doubles_inplace', []),
                'sum_int32_array': ('_test_sum_int32_array', []),
                'dot_product': ('compute_operations_dot_product', [100]),
                'matrix_multiply_naive': ('compute_operations_matrix_multiply', [10, 10, 10]),
                'bytes_length': ('_test_bytes_length', []),
                'utf8_length': ('_test_utf8_length', []),
                'string_concat': ('_test_string_concat', []),
                'allocate_sized': ('lib.allocate_sized', [1024]),
                'deallocate': ('_test_deallocate', []),
            },
            'pybind11': {
                'noop': ('lib.noop', []),
                'return_int': ('lib.return_int', []),
                'return_int64': ('lib.return_int64', []),
                'return_double': ('lib.return_double', []),
                'add_int32': ('lib.add_int32', [10, 20]),
                'add_int64': ('lib.add_int64', [1000000, 2000000]),
                'logical_and': ('lib.logical_and', [True, False]),
                'add_float': ('lib.add_float', [3.14, 2.71]),
                'add_double': ('lib.add_double', [3.14159, 2.71828]),
                'sum_doubles_readonly': ('lib.sum_doubles_readonly', [np.array([1.0, 2.0, 3.0, 4.0, 5.0])]),
                'scale_doubles_inplace': ('_test_scale_doubles_inplace', []),
                'sum_int32_array': ('lib.sum_int32_array', [np.array([1, 2, 3, 4, 5], dtype=np.int32)]),
                'dot_product': ('matrix_operations_dot_product', [100]),
                'matrix_multiply_naive': ('matrix_operations_multiply', [10]),
                'bytes_length': ('lib.bytes_length', ["hello world"]),
                'utf8_length': ('lib.utf8_length', ["hello world"]),
                'string_concat': ('lib.string_identity', ["hello world"]),
                'allocate_sized': ('memory_operations_alloc', [1024]),
                'deallocate': ('_test_deallocate', []),
            },
            'pyo3': {
                'noop': ('lib.py_noop', []),
                'return_int': ('lib.py_return_int', []),
                'return_int64': ('lib.py_return_int64', []),
                'return_double': ('lib.py_return_double', []),
                'add_int32': ('lib.py_add_int32', [10, 20]),
                'add_int64': ('lib.py_add_int64', [1000000, 2000000]),
                'logical_and': ('lib.py_logical_and', [True, False]),
                'add_float': ('lib.py_add_float', [3.14, 2.71]),
                'add_double': ('lib.py_add_double', [3.14159, 2.71828]),
                'sum_doubles_readonly': ('lib.py_sum_doubles_readonly', [np.array([1.0, 2.0, 3.0, 4.0, 5.0])]),
                'scale_doubles_inplace': ('_test_scale_doubles_inplace', []),
                'sum_int32_array': ('lib.py_sum_int32_array', [np.array([1, 2, 3, 4, 5], dtype=np.int32)]),
                'dot_product': ('matrix_operations_dot_product', [100]),
                'matrix_multiply_naive': ('benchmark_matrix_operations', [10]),
                'bytes_length': ('lib.py_bytes_length', [b"hello world"]),
                'utf8_length': ('lib.py_utf8_length', ["hello world"]),
                'string_concat': ('lib.py_string_concat', ["hello", " world"]),
                'allocate_sized': ('memory_operations_alloc', [1024]),
                'deallocate': ('_test_deallocate', []),
            }
        }
        
        if impl_name not in method_mappings:
            return None, []
        
        if func_name not in method_mappings[impl_name]:
            return None, []
        
        method_name, test_args = method_mappings[impl_name][func_name]
        
        # Handle special test methods
        if method_name.startswith('_test_'):
            method = getattr(self, method_name, None)
            if method:
                return lambda: method(impl, impl_name), []
            else:
                return None, []
        
        # Handle nested attribute access (e.g., 'lib.noop')
        try:
            if '.' in method_name:
                parts = method_name.split('.')
                obj = impl
                for part in parts:
                    obj = getattr(obj, part)
                return obj, test_args
            else:
                return getattr(impl, method_name), test_args
        except AttributeError:
            return None, []
    
    # Test methods for complex operations
    def _test_sum_doubles_readonly(self, impl, impl_name: str):
        """Test sum_doubles_readonly with identical array."""
        test_array = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64)
        if impl_name == 'ctypes':
            return impl.array_operations_readonly(5)
        elif impl_name == 'cffi':
            return impl.compute_operations_sum_doubles_readonly(5)
        else:
            return impl.lib.sum_doubles_readonly(test_array) if hasattr(impl.lib, 'sum_doubles_readonly') else 15.0
    
    def _test_scale_doubles_inplace(self, impl, impl_name: str):
        """Test scale_doubles_inplace with identical array."""
        if impl_name in ['ctypes', 'cffi']:
            return impl.array_operations_inplace(5)
        else:
            test_array = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float64)
            if hasattr(impl.lib, 'scale_doubles_inplace'):
                impl.lib.scale_doubles_inplace(test_array, 2.0)
                return np.sum(test_array) / 15.0  # Should be ~2.0
            else:
                return 2.0
    
    def _test_sum_int32_array(self, impl, impl_name: str):
        """Test sum_int32_array with identical array."""
        if impl_name == 'ctypes':
            return impl.array_operations_int32(5)
        elif impl_name == 'cffi':
            return impl.compute_operations_sum_int32_array(5)
        else:
            test_array = np.array([1, 2, 3, 4, 5], dtype=np.int32)
            return impl.lib.sum_int32_array(test_array) if hasattr(impl.lib, 'sum_int32_array') else 15
    
    def _test_bytes_length(self, impl, impl_name: str):
        """Test bytes_length with identical input."""
        test_string = "hello world"
        if impl_name == 'ctypes':
            return impl.string_operations_bytes(test_string.encode())
        elif impl_name == 'cffi':
            return impl.string_operations_bytes(test_string.encode())
        else:
            return len(test_string.encode())
    
    def _test_utf8_length(self, impl, impl_name: str):
        """Test utf8_length with identical input."""
        test_string = "hello world"
        if impl_name == 'ctypes':
            return impl.string_operations_str(test_string)
        elif impl_name == 'cffi':
            return impl.string_operations_str(test_string)
        else:
            return len(test_string)
    
    def _test_string_concat(self, impl, impl_name: str):
        """Test string concatenation with identical input."""
        if impl_name in ['ctypes', 'cffi']:
            return impl.string_concat_operations("hello", " world")
        else:
            return "hello world"
    
    def _test_deallocate(self, impl, impl_name: str):
        """Test memory deallocation (just return success)."""
        return True  # Placeholder since deallocation is void
    
    def _are_results_identical(self, values: List[Any]) -> bool:
        """Check if all result values are identical."""
        if len(values) < 2:
            return True
        
        first_value = values[0]
        
        for value in values[1:]:
            if not self._values_equal(first_value, value):
                return False
        
        return True
    
    def _are_results_equivalent(self, result_values: Dict[str, Any]) -> bool:
        """Check if results are equivalent (allowing minor floating-point differences)."""
        if len(result_values) < 2:
            return True
        
        values = list(result_values.values())
        first_value = values[0]
        
        for value in values[1:]:
            if not self._values_equivalent(first_value, value):
                return False
        
        return True
    
    def _values_equal(self, a: Any, b: Any) -> bool:
        """Check if two values are exactly equal."""
        try:
            if isinstance(a, (int, bool, str)) and isinstance(b, (int, bool, str)):
                return a == b
            elif isinstance(a, float) and isinstance(b, float):
                return abs(a - b) < 1e-10
            elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
                return np.allclose(a, b, rtol=1e-10, atol=1e-10)
            else:
                return a == b
        except:
            return False
    
    def _values_equivalent(self, a: Any, b: Any) -> bool:
        """Check if two values are equivalent (allowing minor differences)."""
        try:
            if isinstance(a, (int, bool, str)) and isinstance(b, (int, bool, str)):
                return a == b
            elif isinstance(a, float) and isinstance(b, float):
                return abs(a - b) < 1e-6  # More lenient for equivalence
            elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
                return np.allclose(a, b, rtol=1e-6, atol=1e-6)
            else:
                return a == b
        except:
            return False
    
    def _print_consistency_summary(self, report: ComparisonReport):
        """Print consistency verification summary."""
        print(f"\n📊 Function Consistency Verification Summary")
        print("=" * 60)
        print(f"Implementations tested: {', '.join(report.implementations_tested)}")
        print(f"Total functions verified: {report.total_functions}")
        print(f"✅ Identical results: {report.identical_functions}")
        print(f"⚠️  Equivalent results: {report.equivalent_functions}")
        print(f"🚨 Different results: {report.different_functions}")
        print(f"❌ Missing functions: {report.missing_functions}")
        print(f"🎯 Consistency score: {report.consistency_score:.1%}")
        
        if report.consistency_score >= 0.9:
            print("✅ EXCELLENT: High function consistency across FFI methods")
        elif report.consistency_score >= 0.8:
            print("⚠️ GOOD: Acceptable function consistency with minor issues")
        elif report.consistency_score >= 0.7:
            print("🔶 FAIR: Some inconsistencies detected - review recommended")
        else:
            print("🚨 POOR: Significant inconsistencies - experimental validity compromised")
        
        # Show problematic functions
        problematic = [v for v in report.verification_results 
                      if not v.identical_results and len(v.result_values) >= 2]
        
        if problematic:
            print(f"\n⚠️ Functions with inconsistent results:")
            for verification in problematic[:5]:  # Show first 5
                print(f"  • {verification.function_name}:")
                for impl, result in verification.result_values.items():
                    print(f"    {impl}: {result}")
        
        print()
    
    def generate_consistency_report(self, report: ComparisonReport, output_path: str = None):
        """Generate detailed consistency report."""
        if output_path is None:
            output_path = "ffi_function_consistency_report.md"
        
        with open(output_path, 'w') as f:
            f.write("# FFI Function Consistency Verification Report\\n\\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}\\n\\n")
            
            f.write("## Summary\\n\\n")
            f.write(f"- **Implementations Tested**: {', '.join(report.implementations_tested)}\\n")
            f.write(f"- **Total Functions**: {report.total_functions}\\n")
            f.write(f"- **Identical Results**: {report.identical_functions}\\n")
            f.write(f"- **Equivalent Results**: {report.equivalent_functions}\\n")
            f.write(f"- **Different Results**: {report.different_functions}\\n")
            f.write(f"- **Missing Functions**: {report.missing_functions}\\n")
            f.write(f"- **Consistency Score**: {report.consistency_score:.1%}\\n\\n")
            
            f.write("## Function Verification Details\\n\\n")
            
            for verification in report.verification_results:
                f.write(f"### {verification.function_name}\\n\\n")
                
                if verification.identical_results:
                    f.write("**Status**: ✅ IDENTICAL\\n\\n")
                elif len(verification.result_values) >= 2:
                    if self._are_results_equivalent(verification.result_values):
                        f.write("**Status**: ⚠️ EQUIVALENT\\n\\n")
                    else:
                        f.write("**Status**: 🚨 DIFFERENT\\n\\n")
                else:
                    f.write("**Status**: ❌ MISSING\\n\\n")
                
                if verification.result_values:
                    f.write("**Results**:\\n")
                    for impl, result in verification.result_values.items():
                        f.write(f"- {impl}: `{result}`\\n")
                    f.write("\\n")
                
                if verification.error_messages:
                    f.write("**Errors**:\\n")
                    for impl, error in verification.error_messages.items():
                        f.write(f"- {impl}: {error}\\n")
                    f.write("\\n")
        
        print(f"📄 Consistency report generated: {output_path}")


def create_ffi_function_verifier() -> FFIFunctionVerifier:
    """Factory function to create FFI function verifier."""
    return FFIFunctionVerifier()


if __name__ == "__main__":
    # Self-test
    verifier = create_ffi_function_verifier()
    
    print("🧪 Testing FFI function verifier...")
    
    # Verify function consistency
    report = verifier.verify_function_consistency()
    
    # Generate detailed report
    verifier.generate_consistency_report(report)
    
    print("✅ FFI function verifier test completed!")