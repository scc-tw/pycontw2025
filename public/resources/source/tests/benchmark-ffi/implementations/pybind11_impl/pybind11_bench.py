"""
pybind11 FFI benchmark implementations aligned with ctypes baseline.

This module provides pybind11-based implementations of all benchmark functions
for fair comparison with other FFI methods. No numpy dependency - uses same
Python list approach as ctypes.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Any, Optional

# Import the compiled pybind11 module
try:
    import sys
    pybind11_dir = str(Path(__file__).parent)
    if pybind11_dir not in sys.path:
        sys.path.insert(0, pybind11_dir)
    
    import benchlib_pybind11 as pybind11_lib
except ImportError as e:
    raise RuntimeError(f"Could not load pybind11 library: {e}")


class Pybind11Benchmark:
    """pybind11 implementation of FFI benchmarks (aligned with ctypes)."""
    
    def __init__(self):
        """Initialize the pybind11 library wrapper."""
        self.lib = pybind11_lib
        
    # =============================================================================
    # Benchmark Functions (matching ctypes exactly)
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
        
        result = self.lib.string_concat(a_bytes, b_bytes)
        return result
    
    def array_operations_readonly(self, size: int = 1000):
        """Read-only array operations."""
        # Create array using Python list (same as ctypes)
        data = [float(i) for i in range(size)]
        
        # Call function - pybind11 can accept Python lists directly
        return self.lib.sum_doubles_readonly(data)
    
    def array_operations_inplace(self, size: int = 1000, factor: float = 2.0):
        """In-place array operations."""
        # Create array using Python list (same as ctypes)
        data = [float(i) for i in range(size)]
        
        # Modify in place - pybind11 will handle the conversion
        self.lib.scale_doubles_inplace(data, factor)
        
        # Return first few elements for verification
        return data[:min(5, size)]
    
    def array_operations_int32(self, size: int = 1000):
        """Integer array operations."""
        # Create array using Python list (same as ctypes)
        data = list(range(size))
        
        # Call function
        return self.lib.sum_int32_array(data)
    
    def structure_operations_simple(self, x: int = 10, y: int = 20, value: float = 3.14):
        """Simple structure operations."""
        struct = self.lib.create_simple(x, y, value)
        return self.lib.sum_simple(struct)
    
    def structure_operations_create(self, x: int = 10, y: int = 20, value: float = 3.14):
        """Structure creation operations."""
        struct = self.lib.create_simple(x, y, value)
        # Access struct fields (pybind11 exposes them as properties)
        return struct.x + struct.y + struct.value
    
    def callback_operations_simple(self, value: int = 42):
        """Simple callback operations."""
        def transform(x):
            return x * 2
        
        # pybind11 can accept Python functions as callbacks directly
        return self.lib.apply_callback(value, transform)
    
    def callback_operations_array(self, size: int = 100):
        """Array callback operations."""
        # Create array using Python list (same as ctypes)
        data = list(range(size))
        
        # Transform function
        def transform(x):
            return x * x
        
        return self.lib.sum_with_transform(data, transform)
    
    def memory_operations_alloc(self, size: int = 1024):
        """Memory allocation operations."""
        ptr = self.lib.allocate_sized(size)
        if ptr:
            self.lib.deallocate(ptr)
            return True
        return False
    
    def compute_operations_dot_product(self, size: int = 1000):
        """Dot product computation."""
        # Create arrays using Python lists (same as ctypes)
        a_data = [float(i) for i in range(size)]
        b_data = [float(i * 2) for i in range(size)]
        
        return self.lib.dot_product(a_data, b_data)
    
    def compute_operations_matrix_multiply(self, m: int = 10, n: int = 10, k: int = 10):
        """Matrix multiplication computation."""
        # Create matrices using Python lists (same as ctypes)
        a_data = [float(i + j) for i in range(m) for j in range(k)]
        b_data = [float(i * j + 1) for i in range(k) for j in range(n)]
        c_data = [0.0] * (m * n)
        
        self.lib.matrix_multiply_naive(a_data, b_data, c_data, m, n, k)
        
        # Return checksum for verification
        return sum(c_data)
    
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


def create_pybind11_benchmark() -> Pybind11Benchmark:
    """Factory function to create pybind11 benchmark instance."""
    return Pybind11Benchmark()


# Benchmark function registry for easy access (matching ctypes)
PYBIND11_BENCHMARKS = {
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
    print("Testing pybind11 benchmark implementation (aligned with ctypes)...")
    
    bench = create_pybind11_benchmark()
    
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