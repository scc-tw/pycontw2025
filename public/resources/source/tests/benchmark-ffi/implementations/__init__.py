"""
FFI Implementation Registry

Clean import structure for all FFI methods with proper dependency resolution.
Eliminates LD_LIBRARY_PATH workarounds through organized module structure.
"""

import os
import sys
from pathlib import Path

# Add implementations to Python path
_impl_dir = Path(__file__).parent
sys.path.insert(0, str(_impl_dir))

# Import implementations with proper error handling
def load_implementation(impl_name: str):
    """Load FFI implementation with proper error handling"""
    try:
        if impl_name == 'ctypes':
            from ctypes_impl.ctypes_bench import create_ctypes_benchmark
            return create_ctypes_benchmark()
        elif impl_name == 'cffi':
            from cffi_impl.cffi_bench import create_cffi_benchmark
            return create_cffi_benchmark()
        elif impl_name == 'pybind11':
            from pybind11_impl.pybind11_bench import Pybind11Benchmark
            return Pybind11Benchmark()
        elif impl_name == 'pyo3':
            from pyo3_impl.pyo3_bench import PyO3Benchmark
            return PyO3Benchmark()
        else:
            raise ValueError(f"Unknown implementation: {impl_name}")
    except ImportError as e:
        print(f"⚠️ {impl_name} implementation not available: {e}")
        return None

# Registry of available implementations
AVAILABLE_IMPLEMENTATIONS = {}

def get_available_implementations():
    """Get all available FFI implementations"""
    if not AVAILABLE_IMPLEMENTATIONS:
        for impl in ['ctypes', 'cffi', 'pybind11', 'pyo3']:
            impl_obj = load_implementation(impl)
            if impl_obj:
                AVAILABLE_IMPLEMENTATIONS[impl] = impl_obj
                print(f"✅ {impl} implementation loaded")
            else:
                print(f"⚠️ {impl} implementation not available (skipping)")
    
    return AVAILABLE_IMPLEMENTATIONS

__all__ = ['load_implementation', 'get_available_implementations', 'AVAILABLE_IMPLEMENTATIONS']