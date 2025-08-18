#!/usr/bin/env python3
"""
Analyze first-time vs subsequent call overhead for handcrafted FFI vs PyO3
Tests the hypothesis that handcrafted FFI slowness is due to dynamic loading overhead
"""

import time
import ctypes
import platform
import sys
from pathlib import Path
import statistics

class FirstCallAnalyzer:
    """Analyze first-time call overhead vs subsequent calls"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        
    def _get_library_path(self):
        """Get platform-specific library path"""
        base_path = self.test_dir / "handcrafted_ffi" / "target" / "release"
        
        system = platform.system().lower()
        if system == "darwin":
            return base_path / "libhandcrafted_ffi.dylib"
        elif system == "linux":
            return base_path / "libhandcrafted_ffi.so"
        elif system == "windows":
            return base_path / "handcrafted_ffi.dll"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    
    def analyze_handcrafted_ffi_loading(self):
        """Analyze handcrafted FFI loading and first calls"""
        print("🔧 HANDCRAFTED FFI FIRST-CALL ANALYSIS")
        print("="*60)
        
        lib_path = self._get_library_path()
        
        # 1. Measure library loading time
        print("1. Library Loading Time:")
        start_load = time.perf_counter_ns()
        lib = ctypes.CDLL(str(lib_path))
        load_time = time.perf_counter_ns() - start_load
        print(f"   Library load: {load_time / 1000:.1f}µs")
        
        # 2. Setup function signature (also has overhead)
        print("\n2. Function Setup Time:")
        start_setup = time.perf_counter_ns()
        lib.test_function_call.argtypes = []
        lib.test_function_call.restype = ctypes.c_int
        setup_time = time.perf_counter_ns() - start_setup
        print(f"   Function setup: {setup_time / 1000:.1f}µs")
        
        # 3. Measure first 10 calls individually
        print("\n3. First 10 Function Calls:")
        print("   Call# │    Time (ns) │   Time (µs) │ Notes")
        print("   ──────┼──────────────┼─────────────┼─────────────────")
        
        call_times = []
        for i in range(10):
            start_call = time.perf_counter_ns()
            result = lib.test_function_call()
            end_call = time.perf_counter_ns()
            call_time = end_call - start_call
            call_times.append(call_time)
            
            note = ""
            if i == 0:
                note = "First call (lazy binding)"
            elif i == 1:
                note = "Second call"
            elif i == 9:
                note = "Warmed up"
            
            print(f"   {i+1:5d} │ {call_time:12d} │ {call_time/1000:11.2f} │ {note}")
        
        # 4. Statistics analysis
        print(f"\n4. Call Time Statistics:")
        first_call = call_times[0]
        subsequent_calls = call_times[1:]
        avg_subsequent = statistics.mean(subsequent_calls)
        
        print(f"   First call:        {first_call:8d}ns ({first_call/1000:6.2f}µs)")
        print(f"   Subsequent avg:    {avg_subsequent:8.1f}ns ({avg_subsequent/1000:6.2f}µs)")
        print(f"   First call overhead: {((first_call - avg_subsequent) / avg_subsequent) * 100:5.1f}%")
        
        # 5. Test if first-call penalty persists after reload
        print(f"\n5. Library Reload Test:")
        del lib  # Try to unload (may not work on all platforms)
        
        # Reload and test first call again
        start_reload = time.perf_counter_ns()
        lib2 = ctypes.CDLL(str(lib_path))
        reload_time = time.perf_counter_ns() - start_reload
        print(f"   Reload time: {reload_time / 1000:.1f}µs")
        
        lib2.test_function_call.argtypes = []
        lib2.test_function_call.restype = ctypes.c_int
        
        start_first_again = time.perf_counter_ns()
        result = lib2.test_function_call()
        first_again_time = time.perf_counter_ns() - start_first_again
        print(f"   First call after reload: {first_again_time}ns ({first_again_time/1000:.2f}µs)")
        
        return {
            "load_time": load_time,
            "setup_time": setup_time,
            "first_call": first_call,
            "subsequent_avg": avg_subsequent,
            "call_times": call_times,
            "reload_time": reload_time,
            "first_again": first_again_time
        }
    
    def analyze_pyo3_loading(self):
        """Analyze PyO3 module loading and first calls"""
        print("\n⚡ PyO3 FIRST-CALL ANALYSIS")
        print("="*60)
        
        try:
            # 1. Measure module import time
            print("1. Module Import Time:")
            pyo3_dir = self.test_dir / "pyo3_investigation"
            sys.path.insert(0, str(pyo3_dir))
            
            start_import = time.perf_counter_ns()
            from pyo3_loader import load_pyo3_module
            pyo3_module = load_pyo3_module()
            import_time = time.perf_counter_ns() - start_import
            print(f"   Module import: {import_time / 1000:.1f}µs")
            
            # 2. Measure first 10 calls individually
            print("\n2. First 10 Function Calls:")
            print("   Call# │    Time (ns) │   Time (µs) │ Notes")
            print("   ──────┼──────────────┼─────────────┼─────────────────")
            
            call_times = []
            for i in range(10):
                start_call = time.perf_counter_ns()
                result = pyo3_module.pyo3_function_call_test()
                end_call = time.perf_counter_ns()
                call_time = end_call - start_call
                call_times.append(call_time)
                
                note = ""
                if i == 0:
                    note = "First call"
                elif i == 1:
                    note = "Second call"
                elif i == 9:
                    note = "Warmed up"
                
                print(f"   {i+1:5d} │ {call_time:12d} │ {call_time/1000:11.2f} │ {note}")
            
            # 3. Statistics analysis
            print(f"\n3. Call Time Statistics:")
            first_call = call_times[0]
            subsequent_calls = call_times[1:]
            avg_subsequent = statistics.mean(subsequent_calls)
            
            print(f"   First call:        {first_call:8d}ns ({first_call/1000:6.2f}µs)")
            print(f"   Subsequent avg:    {avg_subsequent:8.1f}ns ({avg_subsequent/1000:6.2f}µs)")
            if first_call > avg_subsequent:
                print(f"   First call overhead: {((first_call - avg_subsequent) / avg_subsequent) * 100:5.1f}%")
            else:
                print(f"   First call faster by: {((avg_subsequent - first_call) / avg_subsequent) * 100:5.1f}%")
            
            return {
                "import_time": import_time,
                "first_call": first_call,
                "subsequent_avg": avg_subsequent,
                "call_times": call_times
            }
            
        except ImportError as e:
            print(f"❌ PyO3 module not available: {e}")
            return None
    
    def compare_loading_overhead(self, handcrafted_data, pyo3_data):
        """Compare loading overhead between handcrafted FFI and PyO3"""
        print("\n📊 LOADING OVERHEAD COMPARISON")
        print("="*60)
        
        print("┌─────────────────────────┬─────────────────┬─────────────────┬─────────────────┐")
        print("│ Metric                  │ Handcrafted FFI │ PyO3            │ Difference      │")
        print("├─────────────────────────┼─────────────────┼─────────────────┼─────────────────┤")
        
        # Loading/Import time
        hc_load = handcrafted_data["load_time"] / 1000  # µs
        py_import = pyo3_data["import_time"] / 1000 if pyo3_data else 0
        
        print(f"│ Loading/Import Time     │ {hc_load:13.1f}µs │ {py_import:13.1f}µs │ {hc_load - py_import:+13.1f}µs │")
        
        # First call time
        hc_first = handcrafted_data["first_call"]
        py_first = pyo3_data["first_call"] if pyo3_data else 0
        
        print(f"│ First Call Time         │ {hc_first:13d}ns │ {py_first:13d}ns │ {hc_first - py_first:+13d}ns │")
        
        # Subsequent call average
        hc_sub = handcrafted_data["subsequent_avg"]
        py_sub = pyo3_data["subsequent_avg"] if pyo3_data else 0
        
        print(f"│ Subsequent Call Avg     │ {hc_sub:13.1f}ns │ {py_sub:13.1f}ns │ {hc_sub - py_sub:+13.1f}ns │")
        
        print("└─────────────────────────┴─────────────────┴─────────────────┴─────────────────┘")
        
        print(f"\n🔍 ANALYSIS:")
        if pyo3_data:
            # Check if loading time explains the difference
            total_hc_overhead = hc_load * 1000 + hc_first  # Convert to ns
            setup_overhead = handcrafted_data["setup_time"]
            
            print(f"   • Handcrafted FFI total first-time cost: {total_hc_overhead/1000:.1f}µs")
            print(f"     - Library loading: {hc_load:.1f}µs")
            print(f"     - Function setup: {setup_overhead/1000:.1f}µs") 
            print(f"     - First call: {hc_first/1000:.2f}µs")
            
            print(f"   • PyO3 total first-time cost: {py_import/1000:.1f}µs")
            print(f"     - Module import: {py_import:.1f}µs")
            print(f"     - First call: {py_first/1000:.2f}µs")
            
            # Steady-state comparison
            steady_overhead = ((hc_sub - py_sub) / py_sub) * 100
            print(f"   • Steady-state overhead: {steady_overhead:+.1f}% (handcrafted vs PyO3)")
            
            # Is first call the main culprit?
            if hc_first > hc_sub * 2:
                print(f"   • ⚠️  First call penalty significant: {((hc_first - hc_sub) / hc_sub) * 100:.1f}%")
            
            if hc_load > py_import:
                print(f"   • ⚠️  Loading overhead significant: {hc_load - py_import:.1f}µs difference")
        
    def create_detailed_table(self, handcrafted_data, pyo3_data):
        """Create detailed call-by-call comparison table"""
        print(f"\n📋 DETAILED CALL-BY-CALL COMPARISON")
        print("="*80)
        
        print("┌───────┬────────────────┬────────────────┬─────────────────┬─────────────────┐")
        print("│ Call# │ Handcrafted    │ PyO3           │ HC Overhead     │ Notes           │")
        print("│       │ Time (ns)      │ Time (ns)      │ vs PyO3         │                 │")
        print("├───────┼────────────────┼────────────────┼─────────────────┼─────────────────┤")
        
        hc_times = handcrafted_data["call_times"]
        py_times = pyo3_data["call_times"] if pyo3_data else [0] * 10
        
        for i in range(10):
            hc_time = hc_times[i]
            py_time = py_times[i] if i < len(py_times) else 0
            
            if py_time > 0:
                overhead = ((hc_time - py_time) / py_time) * 100
            else:
                overhead = 0
            
            note = ""
            if i == 0:
                note = "First (lazy bind)"
            elif i == 1:
                note = "Second"
            elif 2 <= i <= 4:
                note = "Warming up"
            elif i >= 5:
                note = "Steady state"
            
            print(f"│ {i+1:5d} │ {hc_time:14d} │ {py_time:14d} │ {overhead:+13.1f}% │ {note:15s} │")
        
        print("└───────┴────────────────┴────────────────┴─────────────────┴─────────────────┘")

def main():
    """Main analysis function"""
    analyzer = FirstCallAnalyzer()
    
    print("🔬 FIRST-CALL OVERHEAD ANALYSIS")
    print("Investigating whether handcrafted FFI slowness is due to dynamic loading")
    print("="*80)
    
    # Analyze handcrafted FFI
    handcrafted_data = analyzer.analyze_handcrafted_ffi_loading()
    
    # Analyze PyO3
    pyo3_data = analyzer.analyze_pyo3_loading()
    
    if pyo3_data:
        # Compare loading overhead
        analyzer.compare_loading_overhead(handcrafted_data, pyo3_data)
        
        # Create detailed table
        analyzer.create_detailed_table(handcrafted_data, pyo3_data)
    
    # Summary and conclusions
    print(f"\n🎯 CONCLUSIONS:")
    first_call_penalty = ((handcrafted_data["first_call"] - handcrafted_data["subsequent_avg"]) / 
                         handcrafted_data["subsequent_avg"]) * 100
    
    print(f"   1. First-call penalty for handcrafted FFI: {first_call_penalty:.1f}%")
    print(f"   2. Library loading overhead: {handcrafted_data['load_time']/1000:.1f}µs")
    print(f"   3. Function setup overhead: {handcrafted_data['setup_time']/1000:.1f}µs")
    
    if pyo3_data:
        steady_diff = handcrafted_data["subsequent_avg"] - pyo3_data["subsequent_avg"]
        print(f"   4. Steady-state difference: {steady_diff:.1f}ns per call")
        
        if first_call_penalty > 50:
            print(f"   ⚠️  First-call penalty is significant but doesn't explain steady-state overhead")
        else:
            print(f"   ✅ First-call penalty is minimal; steady-state difference is the main factor")

if __name__ == "__main__":
    main()