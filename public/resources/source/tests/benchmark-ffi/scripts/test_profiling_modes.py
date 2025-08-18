#!/usr/bin/env python3
"""
Test script to verify profiling mode functionality

This script tests that both build profiles work correctly and can be profiled
with their respective recommended profiling methods.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add the benchmark framework to Python path
benchmark_root = Path(__file__).parent.parent
sys.path.insert(0, str(benchmark_root))

def run_command(cmd, cwd=None, capture_output=True):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=capture_output, 
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def test_build_profile(profile):
    """Test building with a specific profile"""
    print(f"\n🔨 Testing {profile} profile build...")
    
    # Clean and build
    success, stdout, stderr = run_command(f"make clean", benchmark_root)
    if not success:
        print(f"❌ Clean failed: {stderr}")
        return False
    
    success, stdout, stderr = run_command(f"make PROFILE={profile} build-all", benchmark_root)
    if not success:
        print(f"❌ Build failed for {profile}: {stderr}")
        return False
    
    print(f"✅ {profile} profile built successfully")
    return True

def test_ctypes_functionality():
    """Test that ctypes implementation works"""
    print("\n🧪 Testing ctypes functionality...")
    
    ctypes_dir = benchmark_root / "implementations" / "ctypes_impl"
    success, stdout, stderr = run_command(
        "python -c \"import ctypes_bench; print('ctypes test:', ctypes_bench.test_basic_functionality())\"", 
        ctypes_dir
    )
    
    if success and "ctypes test: True" in stdout:
        print("✅ ctypes functionality verified")
        return True
    else:
        print(f"❌ ctypes test failed: {stderr}")
        return False

def test_profiling_setup(profile):
    """Test that profiling can be set up for the given profile"""
    print(f"\n📊 Testing profiling setup for {profile} profile...")
    
    # Check if perf is available
    success, _, _ = run_command("which perf")
    if not success:
        print("⚠️  perf not found, skipping profiling test")
        return True
    
    # Test basic perf record (dry run)
    if profile == "fast":
        cmd = "perf list | grep lbr"
        success, stdout, stderr = run_command(cmd)
        if success and "lbr" in stdout.lower():
            print("✅ Intel LBR available for fast mode profiling")
            return True
        else:
            print("⚠️  LBR not available, would fall back to DWARF")
            return True
    else:  # instrumented
        # Test frame pointer profiling capability
        cmd = "perf list | grep cycles"
        success, stdout, stderr = run_command(cmd)
        if success:
            print("✅ Frame pointer profiling available for instrumented mode")
            return True
        else:
            print("❌ Basic perf events not available")
            return False

def check_frame_pointers(binary_path):
    """Check if frame pointers are present in binary"""
    success, stdout, stderr = run_command(f"objdump -d {binary_path} | grep -c 'push.*%rbp' || true")
    if success:
        count = int(stdout.strip() or "0")
        return count > 0
    return False

def main():
    """Main test function"""
    print("🧪 FFI Profiling Mode Test Suite")
    print("=" * 40)
    
    os.chdir(benchmark_root)
    
    # Test both profiles
    profiles = ["fast", "instrumented"]
    results = {}
    
    for profile in profiles:
        print(f"\n{'='*50}")
        print(f"Testing {profile.upper()} profile")
        print(f"{'='*50}")
        
        # Test build
        build_success = test_build_profile(profile)
        
        # Test functionality
        func_success = False
        if build_success:
            func_success = test_ctypes_functionality()
        
        # Test profiling setup
        prof_success = False
        if build_success:
            prof_success = test_profiling_setup(profile)
        
        # Check frame pointers for instrumented build
        fp_check = None
        if profile == "instrumented" and build_success:
            lib_path = benchmark_root / "lib" / "benchlib.so"
            if lib_path.exists():
                fp_present = check_frame_pointers(lib_path)
                fp_check = fp_present
                if fp_present:
                    print("✅ Frame pointers detected in instrumented build")
                else:
                    print("⚠️  Frame pointers not clearly detected (may be optimized)")
        
        results[profile] = {
            "build": build_success,
            "functionality": func_success,
            "profiling": prof_success,
            "frame_pointers": fp_check
        }
    
    # Summary report
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    all_passed = True
    for profile, tests in results.items():
        print(f"\n{profile.upper()} Profile:")
        for test_name, passed in tests.items():
            if passed is None:
                continue
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test_name:15}: {status}")
            if not passed:
                all_passed = False
    
    if all_passed:
        print(f"\n🎉 All tests passed! Profiling modes are ready.")
        print(f"\nNext steps:")
        print(f"  1. Build with: make PROFILE=fast build-all")
        print(f"  2. Profile with: perf record --call-graph lbr -F 99 -g -- python benchmark.py")
        print(f"  3. See docs/PROFILING_GUIDE.md for detailed usage")
        return 0
    else:
        print(f"\n❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())