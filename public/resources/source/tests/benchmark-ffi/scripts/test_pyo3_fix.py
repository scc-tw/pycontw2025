#!/usr/bin/env python3
"""Test script to validate PyO3 fixes"""

import os
import sys
import numpy as np

# Set the library path for the benchlib shared library
lib_dir = os.path.join(os.path.dirname(__file__), '..')
current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
if current_ld_path:
    os.environ['LD_LIBRARY_PATH'] = f"{lib_dir}:{current_ld_path}"
else:
    os.environ['LD_LIBRARY_PATH'] = lib_dir

try:
    import benchlib_pyo3
    _HAS_PYO3_LIB = True
except ImportError as e:
    _HAS_PYO3_LIB = False
    print(f"❌ Failed to import PyO3 module: {e}")
    sys.exit(1)

def test_basic_functions():
    """Test basic PyO3 function calls"""
    print("Testing basic functions...")
    
    # Test simple calls
    benchlib_pyo3.py_noop()
    assert benchlib_pyo3.py_return_int() == 42
    assert benchlib_pyo3.py_add_int32(10, 20) == 30
    assert abs(benchlib_pyo3.py_add_double(1.5, 2.5) - 4.0) < 1e-10
    
    # Test logical operations
    assert benchlib_pyo3.py_logical_and(True, True) == True
    assert benchlib_pyo3.py_logical_or(False, True) == True
    assert benchlib_pyo3.py_logical_not(True) == False
    
    print("✅ Basic functions work")

def test_integer_operations():
    """Test integer operations"""
    print("Testing integer operations...")
    
    assert benchlib_pyo3.py_add_int64(1000000000000, 2000000000000) == 3000000000000
    assert benchlib_pyo3.py_add_uint64(18446744073709551615, 1) == 0  # Overflow test
    
    print("✅ Integer operations work")

def test_floating_point_operations():
    """Test floating point operations"""
    print("Testing floating point operations...")
    
    assert abs(benchlib_pyo3.py_add_float(1.5, 2.5) - 4.0) < 1e-6
    assert abs(benchlib_pyo3.py_multiply_double(3.14, 2.0) - 6.28) < 1e-10
    
    print("✅ Floating point operations work")

def test_available_functions():
    """Test what functions are available"""
    print("Testing available functions...")
    
    functions = [name for name in dir(benchlib_pyo3) if not name.startswith('_')]
    print(f"Available functions: {functions}")
    
    # Basic functions that should be available
    expected_basic = ['py_noop', 'py_return_int', 'py_add_int32', 'py_add_double']
    missing = [f for f in expected_basic if f not in functions]
    
    if missing:
        print(f"⚠️ Missing basic functions: {missing}")
    else:
        print("✅ All basic functions available")
    
    return functions

if __name__ == "__main__":
    print("🧪 Testing PyO3 fixes...")
    print(f"Library path: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
    
    if not _HAS_PYO3_LIB:
        print("❌ PyO3 module not available")
        sys.exit(1)
    
    print("✅ PyO3 module imported successfully")
    
    try:
        test_basic_functions()
        test_integer_operations() 
        test_floating_point_operations()
        functions = test_available_functions()
        
        print(f"\n🎉 All tests passed!")
        print(f"📊 Total functions available: {len(functions)}")
        print("✅ PyO3 implementation is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)