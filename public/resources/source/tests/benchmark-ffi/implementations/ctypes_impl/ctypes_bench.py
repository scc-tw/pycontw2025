"""
ctypes FFI benchmark implementations.

This module provides ctypes-based implementations of all benchmark functions
for fair comparison with other FFI methods.
"""

import ctypes
import ctypes.util
import os
from typing import List, Tuple, Any, Optional
from pathlib import Path

# Find the benchmark library in the new clean structure
_lib_path = None
for potential_path in [
    Path(__file__).parent / "benchlib.so",
    Path(__file__).parent / "benchlib.dylib", 
    Path(__file__).parent / "benchlib.dll",
    Path(__file__).parent.parent.parent / "lib" / "benchlib.so",
    Path(__file__).parent.parent.parent / "lib" / "benchlib.dylib",
    Path(__file__).parent.parent.parent / "lib" / "benchlib.dll",
]:
    if potential_path.exists():
        _lib_path = str(potential_path)
        break

if not _lib_path:
    raise RuntimeError("Could not find benchlib shared library")


class CTypesBenchmark:
    """ctypes implementation of FFI benchmarks."""
    
    def __init__(self):
        """Initialize the ctypes library wrapper."""
        self.lib = ctypes.CDLL(_lib_path)
        self._setup_function_signatures()
        
    def _setup_function_signatures(self):
        """Set up function signatures for type safety."""
        
        # Basic functions
        self.lib.noop.argtypes = []
        self.lib.noop.restype = None
        
        self.lib.return_int.argtypes = []
        self.lib.return_int.restype = ctypes.c_int
        
        self.lib.return_int64.argtypes = []
        self.lib.return_int64.restype = ctypes.c_int64
        
        self.lib.return_bool.argtypes = []
        self.lib.return_bool.restype = ctypes.c_bool
        
        self.lib.return_double.argtypes = []
        self.lib.return_double.restype = ctypes.c_double
        
        # Integer operations
        self.lib.add_int32.argtypes = [ctypes.c_int32, ctypes.c_int32]
        self.lib.add_int32.restype = ctypes.c_int32
        
        self.lib.add_int64.argtypes = [ctypes.c_int64, ctypes.c_int64]
        self.lib.add_int64.restype = ctypes.c_int64
        
        self.lib.add_uint64.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
        self.lib.add_uint64.restype = ctypes.c_uint64
        
        # String operations
        self.lib.bytes_length.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
        self.lib.bytes_length.restype = ctypes.c_size_t
        
        self.lib.utf8_length.argtypes = [ctypes.c_char_p]
        self.lib.utf8_length.restype = ctypes.c_size_t
        
        self.lib.string_identity.argtypes = [ctypes.c_char_p]
        self.lib.string_identity.restype = ctypes.c_char_p
        
        self.lib.string_concat.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.string_concat.restype = ctypes.c_void_p
        
        self.lib.free_string.argtypes = [ctypes.c_void_p]
        self.lib.free_string.restype = None
        
        # Array operations
        self.lib.sum_doubles_readonly.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t]
        self.lib.sum_doubles_readonly.restype = ctypes.c_double
        
        self.lib.scale_doubles_inplace.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_double]
        self.lib.scale_doubles_inplace.restype = None
        
        self.lib.sum_int32_array.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t]
        self.lib.sum_int32_array.restype = ctypes.c_int32
        
        # Structure operations
        class SimpleStruct(ctypes.Structure):
            _fields_ = [
                ('x', ctypes.c_int32),
                ('y', ctypes.c_int32),
                ('value', ctypes.c_double)
            ]
        
        self.SimpleStruct = SimpleStruct
        
        self.lib.create_simple.argtypes = [ctypes.c_int32, ctypes.c_int32, ctypes.c_double]
        self.lib.create_simple.restype = SimpleStruct
        
        self.lib.sum_simple.argtypes = [ctypes.POINTER(SimpleStruct)]
        self.lib.sum_simple.restype = ctypes.c_double
        
        # Callback operations
        self.IntTransformCallback = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_int32)
        
        self.lib.apply_callback.argtypes = [ctypes.c_int32, self.IntTransformCallback]
        self.lib.apply_callback.restype = ctypes.c_int32
        
        self.lib.sum_with_transform.argtypes = [ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t, self.IntTransformCallback]
        self.lib.sum_with_transform.restype = ctypes.c_int32
        
        # Memory operations
        self.lib.allocate_sized.argtypes = [ctypes.c_size_t]
        self.lib.allocate_sized.restype = ctypes.c_void_p
        
        self.lib.deallocate.argtypes = [ctypes.c_void_p]
        self.lib.deallocate.restype = None
        
        # Compute operations
        self.lib.dot_product.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_size_t]
        self.lib.dot_product.restype = ctypes.c_double
        
        self.lib.matrix_multiply_naive.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t
        ]
        self.lib.matrix_multiply_naive.restype = None
    
    # =============================================================================
    # Benchmark Functions
    # =============================================================================
    
    def noop(self):
        """No-operation benchmark."""
        self.lib.noop()
    
    def return_int(self):
        """Return integer benchmark."""
        return self.lib.return_int()
    
    def return_int64(self):
        """Return 64-bit integer benchmark."""
        return self.lib.return_int64()
    
    def integer_operations(self, a: int = 10, b: int = 20):
        """Integer arithmetic operations."""
        return self.lib.add_int32(a, b)
    
    def integer_operations_64bit(self, a: int = 1000000000000, b: int = 2000000000000):
        """64-bit integer arithmetic operations."""
        return self.lib.add_int64(a, b)
    
    def string_operations_bytes(self, data: bytes = b"hello world"):
        """String operations using bytes."""
        return self.lib.bytes_length(data, len(data))
    
    def string_operations_str(self, text: str = "hello world"):
        """String operations using strings."""
        data = text.encode('utf-8')
        return self.lib.utf8_length(data)
    
    def string_concat_operations(self, a: str = "hello", b: str = " world"):
        """String concatenation with memory management."""
        a_bytes = a.encode('utf-8')
        b_bytes = b.encode('utf-8')
        
        result_ptr = self.lib.string_concat(a_bytes, b_bytes)
        if result_ptr:
            result = ctypes.string_at(result_ptr).decode('utf-8')
            self.lib.free_string(result_ptr)
            return result
        return ""
    
    def array_operations_readonly(self, size: int = 1000):
        """Read-only array operations."""
        # Create array
        data = [float(i) for i in range(size)]
        array_type = ctypes.c_double * size
        c_array = array_type(*data)
        
        # Call function
        return self.lib.sum_doubles_readonly(c_array, size)
    
    def array_operations_inplace(self, size: int = 1000, factor: float = 2.0):
        """In-place array operations."""
        # Create array
        data = [float(i) for i in range(size)]
        array_type = ctypes.c_double * size
        c_array = array_type(*data)
        
        # Modify in place
        self.lib.scale_doubles_inplace(c_array, size, factor)
        
        # Return first few elements for verification
        return [c_array[i] for i in range(min(5, size))]
    
    def array_operations_int32(self, size: int = 1000):
        """Integer array operations."""
        # Create array
        data = list(range(size))
        array_type = ctypes.c_int32 * size
        c_array = array_type(*data)
        
        # Call function
        return self.lib.sum_int32_array(c_array, size)
    
    def structure_operations_simple(self, x: int = 10, y: int = 20, value: float = 3.14):
        """Simple structure operations."""
        struct = self.SimpleStruct(x, y, value)
        return self.lib.sum_simple(ctypes.byref(struct))
    
    def structure_operations_create(self, x: int = 10, y: int = 20, value: float = 3.14):
        """Structure creation operations."""
        struct = self.lib.create_simple(x, y, value)
        return struct.x + struct.y + struct.value
    
    def callback_operations_simple(self, value: int = 42):
        """Simple callback operations."""
        def transform(x):
            return x * 2
        
        callback = self.IntTransformCallback(transform)
        return self.lib.apply_callback(value, callback)
    
    def callback_operations_array(self, size: int = 100):
        """Array callback operations."""
        # Create array
        data = list(range(size))
        array_type = ctypes.c_int32 * size
        c_array = array_type(*data)
        
        # Transform function
        def transform(x):
            return x * x
        
        callback = self.IntTransformCallback(transform)
        return self.lib.sum_with_transform(c_array, size, callback)
    
    def memory_operations_alloc(self, size: int = 1024):
        """Memory allocation operations."""
        ptr = self.lib.allocate_sized(size)
        if ptr:
            self.lib.deallocate(ptr)
            return True
        return False
    
    def compute_operations_dot_product(self, size: int = 1000):
        """Dot product computation."""
        # Create arrays
        a_data = [float(i) for i in range(size)]
        b_data = [float(i * 2) for i in range(size)]
        
        array_type = ctypes.c_double * size
        a_array = array_type(*a_data)
        b_array = array_type(*b_data)
        
        return self.lib.dot_product(a_array, b_array, size)
    
    def compute_operations_matrix_multiply(self, m: int = 10, n: int = 10, k: int = 10):
        """Matrix multiplication computation."""
        # Create matrices
        a_data = [float(i + j) for i in range(m) for j in range(k)]
        b_data = [float(i * j + 1) for i in range(k) for j in range(n)]
        c_data = [0.0] * (m * n)
        
        a_type = ctypes.c_double * (m * k)
        b_type = ctypes.c_double * (k * n)
        c_type = ctypes.c_double * (m * n)
        
        a_array = a_type(*a_data)
        b_array = b_type(*b_data)
        c_array = c_type(*c_data)
        
        self.lib.matrix_multiply_naive(a_array, b_array, c_array, m, n, k)
        
        # Return checksum for verification
        return sum(c_array)
    
    # =============================================================================
    # Dispatch Pattern Benchmarks
    # =============================================================================
    
    def setup_dispatch_functions(self, count: int = 100):
        """Setup functions for dispatch benchmarking."""
        self.dispatch_functions = {}
        
        # Create function mappings
        for i in range(count):
            name = f"func_{i}"
            # Each function just returns a different value
            self.dispatch_functions[name] = lambda x, i=i: x + i
    
    def dispatch_if_elif_chain(self, func_name: str, arg: int = 42):
        """Dispatch using if/elif chain."""
        # This would normally be a long if/elif chain
        # For simplicity, we'll use the dictionary for now
        if func_name in self.dispatch_functions:
            return self.dispatch_functions[func_name](arg)
        return 0
    
    def dispatch_dictionary_lookup(self, func_name: str, arg: int = 42):
        """Dispatch using dictionary lookup."""
        func = self.dispatch_functions.get(func_name)
        if func:
            return func(arg)
        return 0
    
    def dispatch_class_based(self, func_name: str, arg: int = 42):
        """Dispatch using class-based approach."""
        # Simulate class-based dispatch
        if hasattr(self, f"_dispatch_{func_name}"):
            method = getattr(self, f"_dispatch_{func_name}")
            return method(arg)
        return 0
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def validate_library(self) -> bool:
        """Validate that the library is working correctly."""
        try:
            # Test basic functions
            assert self.lib.return_int() == 42
            assert self.lib.add_int32(10, 20) == 30
            assert self.lib.bytes_length(b"hello", 5) == 5
            
            # Test array operations
            result = self.array_operations_readonly(10)
            expected = sum(range(10))  # 0+1+2+...+9 = 45
            assert abs(result - expected) < 1e-10
            
            return True
        except Exception as e:
            print(f"Library validation failed: {e}")
            return False
    
    def get_available_benchmarks(self) -> List[str]:
        """Get list of available benchmark functions."""
        benchmarks = []
        for attr_name in dir(self):
            if not attr_name.startswith('_') and callable(getattr(self, attr_name)):
                if any(keyword in attr_name for keyword in ['operations', 'benchmark']):
                    benchmarks.append(attr_name)
        return sorted(benchmarks)


def create_ctypes_benchmark() -> CTypesBenchmark:
    """Factory function to create ctypes benchmark instance."""
    return CTypesBenchmark()


# Benchmark function registry for easy access
CTYPES_BENCHMARKS = {
    'noop': lambda bench: bench.noop,
    'return_int': lambda bench: bench.return_int,
    'return_int64': lambda bench: bench.return_int64,
    'integer_ops': lambda bench: bench.integer_operations,
    'integer_ops_64': lambda bench: bench.integer_operations_64bit,
    'string_bytes': lambda bench: bench.string_operations_bytes,
    'string_str': lambda bench: bench.string_operations_str,
    'string_concat': lambda bench: bench.string_concat_operations,
    'array_readonly': lambda bench: bench.array_operations_readonly,
    'array_inplace': lambda bench: bench.array_operations_inplace,
    'array_int32': lambda bench: bench.array_operations_int32,
    'struct_simple': lambda bench: bench.structure_operations_simple,
    'struct_create': lambda bench: bench.structure_operations_create,
    'callback_simple': lambda bench: bench.callback_operations_simple,
    'callback_array': lambda bench: bench.callback_operations_array,
    'memory_alloc': lambda bench: bench.memory_operations_alloc,
    'compute_dot': lambda bench: bench.compute_operations_dot_product,
    'compute_matrix': lambda bench: bench.compute_operations_matrix_multiply,
}


if __name__ == "__main__":
    # Self-test
    print("Testing ctypes benchmark implementation...")
    
    bench = create_ctypes_benchmark()
    
    if bench.validate_library():
        print("✅ Library validation passed")
        
        # Run a few benchmark tests
        print("\n🧪 Running sample benchmarks:")
        
        print(f"noop(): {bench.noop()}")
        print(f"return_int(): {bench.return_int()}")
        print(f"integer_operations(10, 20): {bench.integer_operations(10, 20)}")
        print(f"array_operations_readonly(100): {bench.array_operations_readonly(100)}")
        print(f"callback_operations_simple(42): {bench.callback_operations_simple(42)}")
        
        print("\n📋 Available benchmarks:")
        for benchmark in bench.get_available_benchmarks():
            print(f"  - {benchmark}")
            
    else:
        print("❌ Library validation failed")