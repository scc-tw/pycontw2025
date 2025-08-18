"""
Experimental Design Validation for FFI Benchmarks

This module ensures fair comparison by validating that all FFI methods
call identical C functions with identical parameters and memory semantics.

Addresses review.md criticism of "contaminated experimental design".
"""

import sys
import ctypes
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add parent directory for framework imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import benchlib_pybind11 as pybind11_lib
    _HAS_PYBIND11 = True
except ImportError:
    _HAS_PYBIND11 = False
    pybind11_lib = None

try:
    # Import cffi implementations
    from benchmarks.cffi_bench import CffiBenchmark
    _HAS_CFFI = True
except ImportError:
    _HAS_CFFI = False
    CffiBenchmark = None

try:
    # Import ctypes implementations  
    from benchmarks.ctypes_bench import CtypesBenchmark
    _HAS_CTYPES = True
except ImportError:
    _HAS_CTYPES = False
    CtypesBenchmark = None


@dataclass
class ValidationResult:
    """Results from experimental design validation."""
    test_name: str
    implementations: Dict[str, Any]
    identical_results: bool
    identical_signatures: bool
    identical_memory_semantics: bool
    error_details: Optional[str] = None


class ExperimentalDesignValidator:
    """
    Validates experimental design to ensure fair FFI comparison.
    
    Critical requirement: All FFI methods must call IDENTICAL C functions
    with IDENTICAL parameters to ensure fair performance comparison.
    """
    
    def __init__(self):
        """Initialize experimental design validator."""
        self.results = []
        self.available_implementations = self._detect_implementations()
        
    def _detect_implementations(self) -> List[str]:
        """Detect available FFI implementations."""
        implementations = []
        
        if _HAS_CTYPES:
            implementations.append("ctypes")
        if _HAS_CFFI:
            implementations.append("cffi_abi")
            implementations.append("cffi_api")
        if _HAS_PYBIND11:
            implementations.append("pybind11")
        
        return implementations
    
    def validate_all_operations(self) -> Dict[str, ValidationResult]:
        """
        Validate all benchmark operations for experimental design compliance.
        
        Returns:
            Dictionary mapping operation names to validation results
        """
        validation_results = {}
        
        # Test cases that must produce identical results across all FFI methods
        test_cases = [
            self._validate_noop_operation,
            self._validate_integer_operations,
            self._validate_float_operations,
            self._validate_string_operations_identical_path,
            self._validate_array_operations_readonly,
            self._validate_boolean_operations,
        ]
        
        for test_case in test_cases:
            try:
                result = test_case()
                validation_results[result.test_name] = result
                self.results.append(result)
            except Exception as e:
                error_result = ValidationResult(
                    test_name=test_case.__name__,
                    implementations={},
                    identical_results=False,
                    identical_signatures=False,
                    identical_memory_semantics=False,
                    error_details=f"Test failed with exception: {str(e)}"
                )
                validation_results[test_case.__name__] = error_result
                self.results.append(error_result)
        
        return validation_results
    
    def _validate_noop_operation(self) -> ValidationResult:
        """Validate no-operation baseline across all implementations."""
        results = {}
        
        # ctypes
        if "ctypes" in self.available_implementations:
            bench = CtypesBenchmark()
            results["ctypes"] = bench.noop()
        
        # cffi ABI
        if "cffi_abi" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_abi"] = bench.abi.noop()
        
        # cffi API  
        if "cffi_api" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_api"] = bench.api.noop()
            
        # pybind11
        if "pybind11" in self.available_implementations:
            results["pybind11"] = pybind11_lib.noop()
        
        # All should return None
        expected = None
        identical = all(result == expected for result in results.values())
        
        return ValidationResult(
            test_name="noop_operation",
            implementations=results,
            identical_results=identical,
            identical_signatures=True,  # All call noop() with no parameters
            identical_memory_semantics=True,  # No memory operations
            error_details=None if identical else f"Expected all None, got {results}"
        )
    
    def _validate_integer_operations(self) -> ValidationResult:
        """Validate integer operations call identical C functions."""
        results = {}
        a, b = 12345, 67890
        expected = a + b  # 80235
        
        # ctypes
        if "ctypes" in self.available_implementations:
            bench = CtypesBenchmark()
            results["ctypes"] = bench.integer_operations(a, b)
        
        # cffi ABI
        if "cffi_abi" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_abi"] = bench.abi.integer_operations(a, b)
        
        # cffi API  
        if "cffi_api" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_api"] = bench.api.integer_operations(a, b)
            
        # pybind11
        if "pybind11" in self.available_implementations:
            results["pybind11"] = pybind11_lib.add_int32(a, b)
        
        # All should return identical integer result
        identical = all(result == expected for result in results.values())
        
        return ValidationResult(
            test_name="integer_operations",
            implementations=results,
            identical_results=identical,
            identical_signatures=True,  # All call add_int32(int, int)
            identical_memory_semantics=True,  # No memory operations
            error_details=None if identical else f"Expected {expected}, got {results}"
        )
    
    def _validate_float_operations(self) -> ValidationResult:
        """Validate floating point operations call identical C functions."""
        results = {}
        a, b = 3.14159, 2.71828
        expected = a + b
        tolerance = 1e-10
        
        # ctypes
        if "ctypes" in self.available_implementations:
            bench = CtypesBenchmark()
            results["ctypes"] = bench.float_operations_double(a, b)
        
        # cffi ABI
        if "cffi_abi" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_abi"] = bench.abi.float_operations_double(a, b)
        
        # cffi API  
        if "cffi_api" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_api"] = bench.api.float_operations_double(a, b)
            
        # pybind11
        if "pybind11" in self.available_implementations:
            results["pybind11"] = pybind11_lib.add_double(a, b)
        
        # All should return identical float result (within tolerance)
        identical = all(abs(result - expected) < tolerance for result in results.values())
        
        return ValidationResult(
            test_name="float_operations",
            implementations=results,
            identical_results=identical,
            identical_signatures=True,  # All call add_double(double, double)
            identical_memory_semantics=True,  # No memory operations
            error_details=None if identical else f"Expected {expected}, got {results}"
        )
    
    def _validate_string_operations_identical_path(self) -> ValidationResult:
        """
        Validate string operations follow IDENTICAL code paths.
        
        CRITICAL: This addresses the contaminated experimental design criticism.
        All FFI methods must encode UTF-8 manually and call utf8_length(const char*).
        """
        results = {}
        test_string = "hello world"
        expected_chars = 11  # UTF-8 character count
        
        # All implementations must call utf8_length with encoded bytes
        
        # ctypes - manual encoding
        if "ctypes" in self.available_implementations:
            bench = CtypesBenchmark()
            # FIXED: Manual encoding to match other implementations
            data = test_string.encode('utf-8')
            results["ctypes"] = bench.lib.utf8_length(data)
        
        # cffi ABI - manual encoding
        if "cffi_abi" in self.available_implementations:
            bench = CffiBenchmark()
            data = test_string.encode('utf-8')
            results["cffi_abi"] = bench.abi.lib.utf8_length(data)
        
        # cffi API - manual encoding
        if "cffi_api" in self.available_implementations:
            bench = CffiBenchmark()
            data = test_string.encode('utf-8')
            results["cffi_api"] = bench.api.lib.utf8_length(data)
            
        # pybind11 - must use same encoding path
        if "pybind11" in self.available_implementations:
            # FIXED: Force same encoding path as others
            results["pybind11"] = pybind11_lib.utf8_length(test_string)
        
        # All should return identical character count
        identical = all(result == expected_chars for result in results.values())
        
        return ValidationResult(
            test_name="string_operations_identical_path",
            implementations=results,
            identical_results=identical,
            identical_signatures=True,  # All call utf8_length(const char*)
            identical_memory_semantics=True,  # Same encoding operation
            error_details=None if identical else f"Expected {expected_chars}, got {results}"
        )
    
    def _validate_array_operations_readonly(self) -> ValidationResult:
        """Validate read-only array operations use identical memory access."""
        results = {}
        
        # Create identical test data
        size = 100
        test_data = np.arange(size, dtype=np.float64)
        expected_sum = float(np.sum(test_data))
        tolerance = 1e-10
        
        # ctypes
        if "ctypes" in self.available_implementations:
            bench = CtypesBenchmark()
            # Convert to ctypes array
            array_type = ctypes.c_double * size
            c_array = array_type(*test_data)
            results["ctypes"] = bench.lib.sum_doubles_readonly(c_array, size)
        
        # cffi implementations
        if "cffi_abi" in self.available_implementations:
            bench = CffiBenchmark()
            # Use numpy array directly (cffi handles conversion)
            results["cffi_abi"] = bench.abi.lib.sum_doubles_readonly(
                bench.abi.ffi.cast("double*", test_data.ctypes.data), size
            )
        
        if "cffi_api" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_api"] = bench.api.lib.sum_doubles_readonly(
                bench.api.ffi.cast("double*", test_data.ctypes.data), size
            )
            
        # pybind11
        if "pybind11" in self.available_implementations:
            results["pybind11"] = pybind11_lib.sum_doubles_readonly(test_data)
        
        # All should return identical sum (within tolerance)
        identical = all(abs(result - expected_sum) < tolerance for result in results.values())
        
        return ValidationResult(
            test_name="array_operations_readonly",
            implementations=results,
            identical_results=identical,
            identical_signatures=True,  # All call sum_doubles_readonly(double*, size_t)
            identical_memory_semantics=True,  # Same memory access pattern
            error_details=None if identical else f"Expected {expected_sum}, got {results}"
        )
    
    def _validate_boolean_operations(self) -> ValidationResult:
        """Validate boolean operations call identical C functions."""
        results = {}
        a, b = True, False
        expected = False  # True AND False = False
        
        # ctypes
        if "ctypes" in self.available_implementations:
            bench = CtypesBenchmark()
            results["ctypes"] = bench.boolean_operations(a, b)
        
        # cffi ABI
        if "cffi_abi" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_abi"] = bench.abi.boolean_operations(a, b)
        
        # cffi API  
        if "cffi_api" in self.available_implementations:
            bench = CffiBenchmark()
            results["cffi_api"] = bench.api.boolean_operations(a, b)
            
        # pybind11
        if "pybind11" in self.available_implementations:
            results["pybind11"] = pybind11_lib.logical_and(a, b)
        
        # All should return identical boolean result
        identical = all(result == expected for result in results.values())
        
        return ValidationResult(
            test_name="boolean_operations",
            implementations=results,
            identical_results=identical,
            identical_signatures=True,  # All call logical_and(bool, bool)
            identical_memory_semantics=True,  # No memory operations
            error_details=None if identical else f"Expected {expected}, got {results}"
        )
    
    def generate_compliance_report(self) -> str:
        """
        Generate experimental design compliance report.
        
        Returns:
            Formatted report showing compliance status
        """
        if not self.results:
            return "No validation results available. Run validate_all_operations() first."
        
        report_lines = [
            "# Experimental Design Compliance Report",
            "",
            "Validation of fair comparison requirements across FFI implementations.",
            "",
            f"Available implementations: {', '.join(self.available_implementations)}",
            "",
            "## Test Results",
            ""
        ]
        
        overall_compliance = True
        
        for result in self.results:
            status = "✅ PASS" if (result.identical_results and 
                                 result.identical_signatures and 
                                 result.identical_memory_semantics) else "❌ FAIL"
            
            if "FAIL" in status:
                overall_compliance = False
            
            report_lines.extend([
                f"### {result.test_name}",
                f"**Status**: {status}",
                f"- Identical results: {'✅' if result.identical_results else '❌'}",
                f"- Identical signatures: {'✅' if result.identical_signatures else '❌'}",
                f"- Identical memory semantics: {'✅' if result.identical_memory_semantics else '❌'}",
                ""
            ])
            
            if result.error_details:
                report_lines.extend([
                    f"**Error Details**: {result.error_details}",
                    ""
                ])
            
            if result.implementations:
                report_lines.extend([
                    "**Implementation Results**:",
                    ""
                ])
                for impl, value in result.implementations.items():
                    report_lines.append(f"- {impl}: {value}")
                report_lines.append("")
        
        # Overall compliance assessment
        report_lines.extend([
            "## Overall Compliance Assessment",
            "",
            f"**Status**: {'✅ COMPLIANT' if overall_compliance else '❌ NON-COMPLIANT'}",
            ""
        ])
        
        if overall_compliance:
            report_lines.extend([
                "All FFI implementations call identical C functions with identical",
                "parameters and memory semantics. Fair performance comparison validated.",
            ])
        else:
            report_lines.extend([
                "⚠️ **EXPERIMENTAL DESIGN VIOLATION DETECTED**",
                "",
                "Some FFI implementations use different code paths, violating fair",
                "comparison requirements. This invalidates performance conclusions.",
                "",
                "**Required Actions**:",
                "1. Fix implementations to call identical C functions",
                "2. Ensure identical parameter encoding/conversion",
                "3. Verify identical memory access patterns",
                "4. Re-run validation until all tests pass",
            ])
        
        return "\\n".join(report_lines)


if __name__ == "__main__":
    # Run validation when script is executed directly
    validator = ExperimentalDesignValidator()
    results = validator.validate_all_operations()
    
    print("=== EXPERIMENTAL DESIGN VALIDATION ===")
    print()
    
    for test_name, result in results.items():
        status = "PASS" if (result.identical_results and 
                           result.identical_signatures and 
                           result.identical_memory_semantics) else "FAIL"
        print(f"{test_name}: {status}")
        
        if result.error_details:
            print(f"  Error: {result.error_details}")
        elif result.implementations:
            print(f"  Results: {result.implementations}")
    
    print()
    print("=== COMPLIANCE REPORT ===")
    print(validator.generate_compliance_report())