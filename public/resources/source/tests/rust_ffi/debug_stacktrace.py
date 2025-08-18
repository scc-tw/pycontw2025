#!/usr/bin/env python3
"""
Cross-language stacktrace capture for Python-Rust FFI debugging
Captures both Python and Rust stack traces when crashes occur
"""

import os
import sys
import signal
import traceback
import faulthandler
import subprocess
import tempfile
from pathlib import Path
import ctypes
from ctypes import c_void_p, c_char_p, POINTER

class CrossLanguageDebugger:
    """Capture stacktraces across Python-Rust FFI boundary"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        self.debug_enabled = True
        
        # Enable Python fault handler
        faulthandler.enable()
        
        # Register signal handlers for crashes
        signal.signal(signal.SIGSEGV, self._crash_handler)
        signal.signal(signal.SIGABRT, self._crash_handler)
        
    def _crash_handler(self, signum, frame):
        """Handle crashes and capture stacktraces"""
        print(f"\n💥 CRASH DETECTED: Signal {signum}")
        print("="*80)
        
        # Python stacktrace
        print("🐍 PYTHON STACKTRACE:")
        traceback.print_stack(frame)
        
        # Fault handler traceback
        print("\n🔍 FAULT HANDLER TRACEBACK:")
        faulthandler.dump_traceback()
        
        # Try to get native stacktrace
        print("\n🦀 ATTEMPTING NATIVE STACKTRACE:")
        self._capture_native_stacktrace()
        
        sys.exit(1)
    
    def _capture_native_stacktrace(self):
        """Capture native stacktrace using gdb/lldb"""
        pid = os.getpid()
        
        # Try gdb first (Linux/macOS with gdb installed)
        gdb_cmd = [
            "gdb", "-batch", "-ex", "thread apply all bt", 
            "-p", str(pid)
        ]
        
        try:
            result = subprocess.run(gdb_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("GDB STACKTRACE:")
                print(result.stdout)
                return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try lldb (macOS default)
        lldb_cmd = [
            "lldb", "-p", str(pid), "-o", "thread backtrace all", "-o", "quit"
        ]
        
        try:
            result = subprocess.run(lldb_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("LLDB STACKTRACE:")
                print(result.stdout)
                return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("❌ No native debugger available (install gdb or lldb)")
    
    def enable_rust_backtrace(self):
        """Enable Rust backtrace environment variables"""
        os.environ["RUST_BACKTRACE"] = "full"
        os.environ["RUST_LIB_BACKTRACE"] = "1"
        print("🦀 Rust backtrace enabled")
    
    def run_with_debugging(self, test_function, *args, **kwargs):
        """Run a test function with comprehensive debugging"""
        print(f"🔬 Running {test_function.__name__} with debugging...")
        
        try:
            # Enable all debugging features
            self.enable_rust_backtrace()
            
            # Run the actual test
            return test_function(*args, **kwargs)
            
        except Exception as e:
            print(f"\n💥 PYTHON EXCEPTION: {type(e).__name__}: {e}")
            print("\n🐍 PYTHON TRACEBACK:")
            traceback.print_exc()
            
            # Try to capture additional context
            self._capture_python_context()
            raise
    
    def _capture_python_context(self):
        """Capture additional Python execution context"""
        print(f"\n📊 PYTHON CONTEXT:")
        print(f"  Python version: {sys.version}")
        print(f"  Platform: {sys.platform}")
        print(f"  GIL enabled: {getattr(sys, '_is_gil_enabled', lambda: 'unknown')()}")
        print(f"  Reference count tracking: {hasattr(sys, 'getrefcount')}")
        
        # Memory info if available
        try:
            import psutil
            process = psutil.Process()
            print(f"  Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        except ImportError:
            pass

def debug_performance_comparison():
    """Debug why handcrafted FFI is slower than PyO3"""
    import platform
    import time
    
    debugger = CrossLanguageDebugger()
    
    def _get_library_path():
        test_dir = Path(__file__).parent
        base_path = test_dir / "handcrafted_ffi" / "target" / "release"
        
        system = platform.system().lower()
        if system == "darwin":
            return base_path / "libhandcrafted_ffi.dylib"
        elif system == "linux":
            return base_path / "libhandcrafted_ffi.so"
        elif system == "windows":
            return base_path / "handcrafted_ffi.dll"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    
    def test_handcrafted_performance():
        print("\n🔧 HANDCRAFTED FFI PERFORMANCE ANALYSIS")
        
        # Load library
        lib_path = _get_library_path()
        print(f"Loading library: {lib_path}")
        
        start_load = time.perf_counter_ns()
        lib = ctypes.CDLL(str(lib_path))
        load_time = time.perf_counter_ns() - start_load
        print(f"Library load time: {load_time / 1000:.1f}µs")
        
        # Setup function
        lib.test_function_call.argtypes = []
        lib.test_function_call.restype = ctypes.c_int
        
        # Warmup
        for _ in range(1000):
            lib.test_function_call()
        
        # Benchmark with detailed timing
        iterations = 100000
        times = []
        
        for i in range(iterations):
            start = time.perf_counter_ns()
            result = lib.test_function_call()
            end = time.perf_counter_ns()
            times.append(end - start)
            
            if i < 10:  # First 10 calls
                print(f"  Call {i}: {end - start}ns")
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"Handcrafted FFI stats:")
        print(f"  Average: {avg_time:.2f}ns")
        print(f"  Min: {min_time}ns")
        print(f"  Max: {max_time}ns")
        print(f"  Std dev: {(sum((t - avg_time)**2 for t in times) / len(times))**0.5:.2f}ns")
        
        return avg_time
    
    def test_pyo3_performance():
        print("\n⚡ PyO3 PERFORMANCE ANALYSIS")
        
        try:
            sys.path.insert(0, str(Path(__file__).parent / "pyo3_investigation"))
            from pyo3_loader import load_pyo3_module
            pyo3_module = load_pyo3_module()
            
            # Warmup
            for _ in range(1000):
                pyo3_module.pyo3_function_call_test()
            
            # Benchmark with detailed timing
            iterations = 100000
            times = []
            
            for i in range(iterations):
                start = time.perf_counter_ns()
                result = pyo3_module.pyo3_function_call_test()
                end = time.perf_counter_ns()
                times.append(end - start)
                
                if i < 10:  # First 10 calls
                    print(f"  Call {i}: {end - start}ns")
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"PyO3 stats:")
            print(f"  Average: {avg_time:.2f}ns")
            print(f"  Min: {min_time}ns") 
            print(f"  Max: {max_time}ns")
            print(f"  Std dev: {(sum((t - avg_time)**2 for t in times) / len(times))**0.5:.2f}ns")
            
            return avg_time
            
        except ImportError as e:
            print(f"❌ PyO3 module not available: {e}")
            return None
    
    # Run performance analysis with debugging
    handcrafted_time = debugger.run_with_debugging(test_handcrafted_performance)
    pyo3_time = debugger.run_with_debugging(test_pyo3_performance)
    
    if pyo3_time:
        overhead = ((handcrafted_time - pyo3_time) / pyo3_time) * 100
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"  Handcrafted FFI: {handcrafted_time:.2f}ns")
        print(f"  PyO3: {pyo3_time:.2f}ns")
        print(f"  Overhead: {overhead:.1f}%")
        
        if handcrafted_time > pyo3_time:
            print(f"\n🐌 HANDCRAFTED IS SLOWER because:")
            print(f"  - ctypes dynamic dispatch overhead")
            print(f"  - Python-C type conversion overhead")
            print(f"  - No compiler optimizations for call path")
            print(f"  - Dynamic symbol resolution")

def debug_segfault_with_gdb():
    """Run test under GDB to catch segfaults"""
    import subprocess
    import tempfile
    
    # Create GDB script
    gdb_script = """
set environment RUST_BACKTRACE=full
set environment RUST_LIB_BACKTRACE=1
handle SIGSEGV stop print
handle SIGABRT stop print
run
thread apply all bt
info registers
quit
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gdb', delete=False) as f:
        f.write(gdb_script)
        gdb_script_path = f.name
    
    try:
        print("🔍 Running test under GDB to catch segfaults...")
        
        # Run the failing test under GDB
        cmd = [
            "gdb", 
            "-batch",
            "-x", gdb_script_path,
            "--args",
            sys.executable, "test_hypothesis_verification.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print("GDB OUTPUT:")
        print(result.stdout)
        if result.stderr:
            print("GDB STDERR:")
            print(result.stderr)
            
    finally:
        os.unlink(gdb_script_path)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "performance":
            debug_performance_comparison()
        elif sys.argv[1] == "segfault":
            debug_segfault_with_gdb()
        else:
            print("Usage: python3 debug_stacktrace.py [performance|segfault]")
    else:
        print("Cross-language debugger ready. Use:")
        print("  python3 debug_stacktrace.py performance  # Analyze performance")
        print("  python3 debug_stacktrace.py segfault     # Debug crashes with GDB")