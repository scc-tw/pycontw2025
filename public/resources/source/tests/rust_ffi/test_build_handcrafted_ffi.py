# tests/rust_ffi/test_build_handcrafted_ffi.py
# TDD Phase 3: Start with ONE failing test

import unittest
import ctypes
import platform
from pathlib import Path

class TestBuildHandcraftedFFI(unittest.TestCase):
    """TDD: Test basic handcrafted FFI library builds and loads"""
    
    @classmethod
    def _get_library_path(cls):
        """Get platform-specific library path"""
        test_dir = Path(__file__).parent
        base_path = test_dir / "handcrafted_ffi" / "target" / "release"
        
        system = platform.system().lower()
        if system == "darwin":  # macOS
            return base_path / "libhandcrafted_ffi.dylib"
        elif system == "linux":
            return base_path / "libhandcrafted_ffi.so"
        elif system == "windows":
            return base_path / "handcrafted_ffi.dll"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    
    def test_build_handcrafted_ffi_library(self):
        """GREEN: Test that handcrafted FFI library builds and exports basic function"""
        # Find the library
        lib_path = self._get_library_path()
        
        # Library should exist
        self.assertTrue(lib_path.exists(), f"Library not found at {lib_path}")
        
        # Should load successfully
        lib = ctypes.CDLL(str(lib_path))
        
        # Should export test_function_call
        self.assertTrue(hasattr(lib, 'test_function_call'), "Library should export test_function_call")
        
        # Function should return 42
        lib.test_function_call.argtypes = []
        lib.test_function_call.restype = ctypes.c_int
        
        result = lib.test_function_call()
        self.assertEqual(result, 42, "test_function_call should return 42")

    def test_manual_python_object_creation(self):
        """RED: Test manual Python object creation without PyO3"""
        # Find the library
        lib_path = self._get_library_path()
        lib = ctypes.CDLL(str(lib_path))
        
        # Should export manual_create_python_string
        self.assertTrue(hasattr(lib, 'manual_create_python_string'), 
                       "Library should export manual_create_python_string")
        
        # For now just test that function exists and can be called safely
        # Full Python object creation requires proper Python interpreter setup
        lib.manual_create_python_string.argtypes = [ctypes.c_char_p]
        lib.manual_create_python_string.restype = ctypes.c_void_p
        
        # Test with null input (should return null safely) 
        result = lib.manual_create_python_string(None)
        self.assertIsNone(result, "Null input should return null pointer")

    def test_reference_counting_correctness(self):
        """RED: Test manual reference counting without PyO3"""
        # Find the library
        lib_path = self._get_library_path()
        lib = ctypes.CDLL(str(lib_path))
        
        # Should export manual_incref and manual_decref functions
        self.assertTrue(hasattr(lib, 'manual_incref'), 
                       "Library should export manual_incref")
        self.assertTrue(hasattr(lib, 'manual_decref'), 
                       "Library should export manual_decref")
        
        # Test basic reference counting operations
        lib.manual_incref.argtypes = [ctypes.py_object]
        lib.manual_incref.restype = None
        
        lib.manual_decref.argtypes = [ctypes.py_object]  
        lib.manual_decref.restype = None
        
        # Test with a Python object
        test_obj = "test reference counting"
        
        # Should be able to incref/decref without crashing
        lib.manual_incref(test_obj)
        lib.manual_decref(test_obj)

    def test_error_propagation_patterns(self):
        """RED: Test error propagation across FFI boundary without PyO3"""
        # Find the library
        lib_path = self._get_library_path()
        lib = ctypes.CDLL(str(lib_path))
        
        # Should export manual_set_python_exception
        self.assertTrue(hasattr(lib, 'manual_set_python_exception'), 
                       "Library should export manual_set_python_exception")
        
        # Test setting Python exception from Rust
        lib.manual_set_python_exception.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        lib.manual_set_python_exception.restype = ctypes.c_int
        
        # Test with null inputs (should return error safely)
        result = lib.manual_set_python_exception(None, b"test message")
        self.assertEqual(result, -1, "Null exception type should return error")
        
        result = lib.manual_set_python_exception(b"ValueError", None)
        self.assertEqual(result, -1, "Null message should return error")

if __name__ == '__main__':
    unittest.main(verbosity=2)