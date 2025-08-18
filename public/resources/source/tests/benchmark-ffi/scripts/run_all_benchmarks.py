#!/usr/bin/env python3
"""
Master benchmark runner - Clean implementation without LD_LIBRARY_PATH hacks

Enhanced with Python matrix support for GIL/No-GIL comparisons across versions.
"""

import os
import sys
from pathlib import Path

# Add the benchmark-ffi root to Python path
benchmark_root = Path(__file__).parent.parent
sys.path.insert(0, str(benchmark_root))

# Setup virtual environment integration
try:
    from framework.venv_integration import auto_integrate_venv, get_current_build
    
    # Automatically integrate with appropriate venv (quietly for this simple script)
    if not auto_integrate_venv(quiet=True):
        print("⚠️  Virtual environment integration failed - using available packages")
        print("   For optimal results, run: python scripts/setup_isolated_venvs.py")
        print()

except ImportError:
    print("⚠️  Venv integration not available - using system packages")

# Import clean implementations
from implementations import get_available_implementations
from framework.timer import BenchmarkTimer, print_benchmark_results

def detect_python_build_info():
    """Detect information about current Python build."""
    import sysconfig
    
    info = {
        "version": sys.version_info[:3],
        "version_string": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "executable": sys.executable,
        "gil_enabled": True,  # Default assumption
        "build_info": {}
    }
    
    # Check for GIL status (Python 3.13+)
    if hasattr(sys, '_is_gil_enabled'):
        info["gil_enabled"] = sys._is_gil_enabled()
    else:
        # Fallback: check build configuration
        try:
            config_args = sysconfig.get_config_var('CONFIG_ARGS')
            if config_args and '--disable-gil' in config_args:
                info["gil_enabled"] = False
        except:
            pass
    
    # Additional build information
    try:
        info["build_info"] = {
            "compiler": sysconfig.get_config_var('CC'),
            "config_args": sysconfig.get_config_var('CONFIG_ARGS'),
            "prefix": sys.prefix
        }
    except:
        pass
    
    return info

def main():
    # Detect current Python build
    python_info = detect_python_build_info()
    gil_status = "No-GIL" if not python_info["gil_enabled"] else "GIL"
    
    print("🚀 FFI Benchmark Framework - Clean Architecture")
    print("=" * 60)
    print(f"🐍 Python: {python_info['version_string']} ({gil_status})")
    print(f"📍 Executable: {python_info['executable']}")
    
    # Show venv integration status
    try:
        current_build = get_current_build()
        if current_build:
            if ".isolated_venvs" in str(sys.executable):
                print(f"📦 Venv: Isolated environment ({current_build})")
            else:
                print(f"📦 Venv: System/Legacy environment")
        else:
            print(f"📦 Venv: System packages")
    except:
        print(f"📦 Venv: System packages")
    
    # Load all available implementations
    implementations = get_available_implementations()
    
    if not implementations:
        print("❌ No FFI implementations available!")
        return 1
    
    print(f"\n📊 Testing {len(implementations)} FFI methods:")
    for name in implementations:
        print(f"  ✅ {name}")
    
    print("\n🧪 Running basic function call benchmark...")
    
    # Create timer
    timer = BenchmarkTimer(target_relative_error=0.02, max_time_seconds=30)
    
    results = {}
    
    for name, impl in implementations.items():
        print(f"\n📈 Benchmarking {name}...")
        
        # Get the return_int method
        if hasattr(impl, 'return_int'):
            func = impl.return_int
        elif hasattr(impl, 'lib') and hasattr(impl.lib, 'return_int'):
            func = impl.lib.return_int
        else:
            print(f"⚠️ {name}: return_int method not found")
            continue
        
        try:
            # Run benchmark
            result = timer.auto_tune_iterations(func)
            results[name] = result
            
            median_ns = result['wall_time']['median_ns']
            samples = result['wall_time']['samples']
            print(f"  📊 {name}: {median_ns:.1f} ns (n={samples})")
            
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")
    
    # Print final comparison
    if len(results) > 1:
        print("\n🏁 Performance Comparison:")
        sorted_results = sorted(results.items(), key=lambda x: x[1]['wall_time']['median_ns'])
        
        fastest_time = sorted_results[0][1]['wall_time']['median_ns']
        
        for name, result in sorted_results:
            median_ns = result['wall_time']['median_ns']
            speedup = median_ns / fastest_time
            print(f"  {name:>8}: {median_ns:>7.1f} ns ({speedup:.2f}x)")
    
    print(f"\n✅ Benchmark complete!")
    print(f"💡 For matrix analysis across Python builds, use: python scripts/run_matrix_benchmarks.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())