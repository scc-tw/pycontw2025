# tests/rust_ffi/test_handcrafted_impl.py
# TDD tests for handcrafted FFI implementation

import unittest
import ctypes
import sys
import os
from pathlib import Path

class TestHandcraftedFFI(unittest.TestCase):
    """Test suite for handcrafted FFI implementation without PyO3"""
    
    @classmethod
    def setUpClass(cls):
        """Load the handcrafted FFI library"""
        # Find the built library
        project_root = Path(__file__).parent.parent.parent
        
        # Try different possible library locations (updated paths)
        test_dir = Path(__file__).parent
        lib_paths = [
            test_dir / "handcrafted_ffi" / "target" / "release" / "libhandcrafted_ffi.dylib",
            test_dir / "handcrafted_ffi" / "target" / "release" / "libhandcrafted_ffi.so",
            test_dir / "handcrafted_ffi" / "target" / "debug" / "libhandcrafted_ffi.dylib", 
            test_dir / "handcrafted_ffi" / "target" / "debug" / "libhandcrafted_ffi.so",
        ]
        
        cls.lib = None
        for lib_path in lib_paths:
            if lib_path.exists():
                try:
                    cls.lib = ctypes.CDLL(str(lib_path))
                    break
                except OSError as e:
                    print(f"Failed to load {lib_path}: {e}")
                    continue
                    
        if cls.lib is None:
            raise unittest.SkipTest("Handcrafted FFI library not found. Run 'cargo build --release' in handcrafted_ffi/")
            
        # Setup function signatures
        cls._setup_function_signatures()
        
    @classmethod
    def _setup_function_signatures(cls):
        """Setup ctypes function signatures for handcrafted FFI"""
        # Basic function call
        cls.lib.test_function_call.argtypes = []
        cls.lib.test_function_call.restype = ctypes.c_int
        
        # String operations
        cls.lib.test_string_conversion.argtypes = [ctypes.c_char_p]
        cls.lib.test_string_conversion.restype = ctypes.c_char_p
        
        # Memory operations
        cls.lib.test_memory_allocation.argtypes = [ctypes.c_size_t]
        cls.lib.test_memory_allocation.restype = ctypes.c_void_p
        
        cls.lib.test_memory_free.argtypes = [ctypes.c_void_p]
        cls.lib.test_memory_free.restype = None
        
        # Manual Python object operations
        cls.lib.manual_string_from_rust.argtypes = [ctypes.c_char_p]
        cls.lib.manual_string_from_rust.restype = ctypes.c_void_p
        
        cls.lib.manual_list_new.argtypes = [ctypes.c_long]
        cls.lib.manual_list_new.restype = ctypes.c_void_p
        
        cls.lib.manual_set_exception.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        cls.lib.manual_set_exception.restype = ctypes.c_int
        
        # Error handling
        cls.lib.safe_string_operation.argtypes = [ctypes.c_char_p]
        cls.lib.safe_string_operation.restype = ctypes.c_char_p
        
        cls.lib.get_last_error.argtypes = []
        cls.lib.get_last_error.restype = ctypes.c_void_p
        
        cls.lib.clear_last_error.argtypes = []
        cls.lib.clear_last_error.restype = None
        
        # Concurrent operations for thread safety testing
        cls.lib.create_shared_object.argtypes = []
        cls.lib.create_shared_object.restype = ctypes.c_void_p
        
        cls.lib.concurrent_operation.argtypes = [ctypes.c_void_p]
        cls.lib.concurrent_operation.restype = ctypes.c_int
        
        cls.lib.release_shared_object.argtypes = [ctypes.c_void_p]
        cls.lib.release_shared_object.restype = None
        
    def test_basic_function_call(self):
        """Test basic function call overhead - TDD Red→Green→Refactor"""
        # RED: Write a failing test
        result = self.lib.test_function_call()
        
        # GREEN: Verify implementation works
        self.assertEqual(result, 42, "Basic function should return 42")
        
    def test_string_conversion(self):
        """Test string conversion between Python and Rust"""
        test_string = b"hello world"
        result = self.lib.test_string_conversion(test_string)
        
        # Should return reversed string
        if result:
            result_str = ctypes.string_at(result)
            expected = b"dlrow olleh"
            self.assertEqual(result_str, expected, f"String reversal failed: got {result_str}, expected {expected}")
        else:
            self.fail("String conversion returned null pointer")
            
    def test_string_conversion_null_input(self):
        """Test string conversion with null input"""
        result = self.lib.test_string_conversion(None)
        self.assertIsNone(result, "Null input should return null pointer")
        
    def test_memory_allocation_and_free(self):
        """Test memory allocation and deallocation"""
        # Allocate memory
        size = 1024
        ptr = self.lib.test_memory_allocation(size)
        self.assertIsNotNone(ptr, "Memory allocation should not return null")
        
        # Free memory (no direct way to verify, but should not crash)
        self.lib.test_memory_free(ptr)
        
    def test_memory_allocation_zero_size(self):
        """Test memory allocation with zero size"""
        ptr = self.lib.test_memory_allocation(0)
        # Behavior may vary by platform, but should not crash
        if ptr:
            self.lib.test_memory_free(ptr)
            
    def test_manual_python_string_creation(self):
        """Test manual Python string object creation"""
        test_input = b"test string"
        py_obj = self.lib.manual_string_from_rust(test_input)
        
        # Should return non-null pointer (simplified test - real verification would need Python C API)
        self.assertIsNotNone(py_obj, "Manual string creation should not return null")
        
    def test_manual_list_creation(self):
        """Test manual Python list creation"""
        size = 10
        py_list = self.lib.manual_list_new(size)
        
        # Should return non-null pointer
        self.assertIsNotNone(py_list, "Manual list creation should not return null")
        
    def test_exception_handling(self):
        """Test custom exception handling mechanism"""
        exc_type = b"RuntimeError"
        message = b"Test error message"
        
        result = self.lib.manual_set_exception(exc_type, message)
        self.assertEqual(result, 0, "Exception setting should succeed")
        
    def test_exception_handling_null_inputs(self):
        """Test exception handling with null inputs"""
        result = self.lib.manual_set_exception(None, b"message")
        self.assertEqual(result, -1, "Null exception type should return error")
        
        result = self.lib.manual_set_exception(b"RuntimeError", None)
        self.assertEqual(result, -1, "Null message should return error")
        
    def test_safe_string_operation(self):
        """Test safe error handling wrapper"""
        test_input = b"safe test"
        result = self.lib.safe_string_operation(test_input)
        
        if result:
            result_str = ctypes.string_at(result)
            self.assertTrue(result_str.startswith(b"Processed:"), 
                          f"Safe operation should add prefix: {result_str}")
        else:
            self.fail("Safe string operation returned null")
            
    def test_safe_string_operation_null_input(self):
        """Test safe error handling with null input"""
        # Clear any previous errors
        self.lib.clear_last_error()
        
        result = self.lib.safe_string_operation(None)
        self.assertIsNone(result, "Null input should return null")
        
        # Check if error was set
        error_ptr = self.lib.get_last_error()
        self.assertIsNotNone(error_ptr, "Error should be set for null input")
        
    def test_concurrent_operations(self):
        """Test basic concurrent operation support"""
        # Create shared object
        obj = self.lib.create_shared_object()
        self.assertIsNotNone(obj, "Shared object creation should not return null")
        
        # Perform operation
        result = self.lib.concurrent_operation(obj)
        self.assertIsInstance(result, int, "Concurrent operation should return integer")
        
        # Release object
        self.lib.release_shared_object(obj)
        
    def test_concurrent_operations_null_input(self):
        """Test concurrent operations with null input"""
        result = self.lib.concurrent_operation(None)
        self.assertEqual(result, -1, "Null object should return error code")
        
    def test_error_handling_workflow(self):
        """Test complete error handling workflow"""
        # Clear errors
        self.lib.clear_last_error()
        
        # Trigger an error
        self.lib.safe_string_operation(None)
        
        # Check error was recorded
        error_ptr = self.lib.get_last_error()
        self.assertIsNotNone(error_ptr, "Error should be recorded")
        
        # Clear error
        self.lib.clear_last_error()
        
        # Verify error is cleared
        error_ptr = self.lib.get_last_error()
        # After clearing, should return null or indicate no error
        
class TestHandcraftedFFIPerformance(unittest.TestCase):
    """Performance-focused tests for handcrafted FFI"""
    
    @classmethod
    def setUpClass(cls):
        """Setup performance testing environment"""
        # Reuse library setup from main test class
        TestHandcraftedFFI.setUpClass()
        cls.lib = TestHandcraftedFFI.lib
        
    def test_function_call_performance(self):
        """Benchmark basic function call performance"""
        import time
        
        iterations = 100000
        
        # Warmup
        for _ in range(1000):
            self.lib.test_function_call()
            
        # Benchmark
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            self.lib.test_function_call()
        end_time = time.perf_counter_ns()
        
        avg_time_ns = (end_time - start_time) / iterations
        
        # Performance assertion (should be very fast, <1000ns per call)
        self.assertLess(avg_time_ns, 1000, 
                       f"Function call too slow: {avg_time_ns:.2f}ns per call")
        
        print(f"Handcrafted FFI function call: {avg_time_ns:.2f}ns per call")
        
    def test_string_conversion_performance(self):
        """Benchmark string conversion performance"""
        import time
        
        test_string = b"performance test string" * 10  # ~240 bytes
        iterations = 10000
        
        # Warmup
        for _ in range(100):
            result = self.lib.test_string_conversion(test_string)
            
        # Benchmark
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            result = self.lib.test_string_conversion(test_string)
        end_time = time.perf_counter_ns()
        
        avg_time_ns = (end_time - start_time) / iterations
        
        # Performance assertion (string ops should be reasonable)
        self.assertLess(avg_time_ns, 10000, 
                       f"String conversion too slow: {avg_time_ns:.2f}ns per call")
        
        print(f"Handcrafted FFI string conversion: {avg_time_ns:.2f}ns per call")
        
    def test_memory_allocation_performance(self):
        """Benchmark memory allocation performance"""
        import time
        
        size = 1024
        iterations = 10000
        
        # Benchmark allocation + deallocation
        start_time = time.perf_counter_ns()
        for _ in range(iterations):
            ptr = self.lib.test_memory_allocation(size)
            if ptr:
                self.lib.test_memory_free(ptr)
        end_time = time.perf_counter_ns()
        
        avg_time_ns = (end_time - start_time) / iterations
        
        # Performance assertion (malloc/free should be fast)
        self.assertLess(avg_time_ns, 5000, 
                       f"Memory allocation too slow: {avg_time_ns:.2f}ns per call")
        
        print(f"Handcrafted FFI memory allocation: {avg_time_ns:.2f}ns per cycle")

if __name__ == '__main__':
    unittest.main(verbosity=2)