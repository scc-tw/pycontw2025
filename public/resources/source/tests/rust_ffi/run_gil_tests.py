#!/usr/bin/env python3
"""
Test runner for GIL vs no-GIL Python versions
Tests PyO3 bugs that only appear with different GIL configurations
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

class GILTestRunner:
    """Run tests with both GIL and no-GIL Python versions"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.test_dir = Path(__file__).parent
        
        # Python executable paths (from Makefile builds)
        self.python_configs = {
            "cpython3.13.5-gil": self.project_root / "cpython3.13.5-gil" / "bin" / "python3",
            "cpython3.13.5-nogil": self.project_root / "cpython3.13.5-nogil" / "bin" / "python3",
            "cpython3.14.0rc1-gil": self.project_root / "cpython3.14.0rc1-gil" / "bin" / "python3",
            "cpython3.14.0rc1-nogil": self.project_root / "cpython3.14.0rc1-nogil" / "bin" / "python3",
        }
        
        # Test files to run
        self.test_files = [
            "test_build_handcrafted_ffi.py",
            "test_hypothesis_verification.py",
        ]
        
        self.results = {}
    
    def check_python_builds(self):
        """Check which Python builds are available"""
        available = {}
        for name, path in self.python_configs.items():
            if path.exists():
                try:
                    # Test if Python works and get version info
                    result = subprocess.run([
                        str(path), "-c", 
                        "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); "
                        "print(hasattr(sys, '_is_gil_enabled')); "
                        "print(sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else 'unknown')"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        version = lines[0]
                        has_gil_api = lines[1] == 'True'
                        gil_enabled = lines[2]
                        
                        available[name] = {
                            "path": str(path),
                            "version": version,
                            "has_gil_api": has_gil_api,
                            "gil_enabled": gil_enabled,
                            "working": True
                        }
                    else:
                        available[name] = {"path": str(path), "working": False, "error": result.stderr}
                except Exception as e:
                    available[name] = {"path": str(path), "working": False, "error": str(e)}
            else:
                available[name] = {"path": str(path), "working": False, "error": "File not found"}
        
        return available
    
    def build_rust_modules(self, python_exe):
        """Build Rust modules for specific Python version"""
        print(f"Building Rust modules for {python_exe}...")
        
        # Build handcrafted FFI
        handcrafted_dir = self.test_dir / "handcrafted_ffi"
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=handcrafted_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"WARNING: Handcrafted FFI build failed: {result.stderr}")
            return False
        
        # Build PyO3 module
        pyo3_dir = self.test_dir / "pyo3_investigation"
        
        # Set Python interpreter for maturin
        env = os.environ.copy()
        env["PYTHON_SYS_EXECUTABLE"] = str(python_exe)
        
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=pyo3_dir,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"WARNING: PyO3 build failed: {result.stderr}")
            return False
        
        return True
    
    def run_test_with_python(self, python_name, python_path, test_file):
        """Run a specific test with a specific Python version"""
        print(f"\n{'='*60}")
        print(f"Running {test_file} with {python_name}")
        print(f"Python: {python_path}")
        print(f"{'='*60}")
        
        # Build modules for this Python version
        if not self.build_rust_modules(python_path):
            return {
                "status": "build_failed",
                "error": "Failed to build Rust modules"
            }
        
        # Run the test
        test_path = self.test_dir / test_file
        
        try:
            result = subprocess.run(
                [str(python_path), str(test_path)],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "status": "completed",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "Test timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def run_all_tests(self):
        """Run all tests with all available Python versions"""
        print("Checking available Python builds...")
        available_pythons = self.check_python_builds()
        
        print("\nAvailable Python builds:")
        for name, info in available_pythons.items():
            if info["working"]:
                gil_status = info.get("gil_enabled", "unknown")
                print(f"  ✅ {name}: v{info['version']} (GIL: {gil_status})")
            else:
                print(f"  ❌ {name}: {info['error']}")
        
        working_pythons = {k: v for k, v in available_pythons.items() if v["working"]}
        
        if not working_pythons:
            print("\n❌ No working Python builds found!")
            print("Please run 'make' to build Python versions, or check paths in run_gil_tests.py")
            return
        
        # Run tests
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "python_builds": available_pythons,
            "test_results": {}
        }
        
        for test_file in self.test_files:
            print(f"\n{'*'*80}")
            print(f"TESTING: {test_file}")
            print(f"{'*'*80}")
            
            self.results["test_results"][test_file] = {}
            
            for python_name, python_info in working_pythons.items():
                python_path = Path(python_info["path"])
                
                result = self.run_test_with_python(python_name, python_path, test_file)
                self.results["test_results"][test_file][python_name] = result
                
                # Print summary
                if result["status"] == "completed":
                    status = "✅ PASS" if result["success"] else "❌ FAIL"
                    print(f"{status} {python_name}")
                    if not result["success"]:
                        print(f"  Error: {result['stderr'][:200]}...")
                else:
                    print(f"❌ ERROR {python_name}: {result.get('error', 'Unknown error')}")
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save test results to JSON file"""
        results_file = self.test_dir / "gil_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Results saved to: {results_file}")
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        
        for test_file, python_results in self.results["test_results"].items():
            print(f"\n📄 {test_file}:")
            
            for python_name, result in python_results.items():
                if result["status"] == "completed":
                    status = "✅ PASS" if result["success"] else "❌ FAIL"
                else:
                    status = f"❌ {result['status'].upper()}"
                
                gil_info = self.results["python_builds"][python_name]
                gil_status = gil_info.get("gil_enabled", "unknown") if gil_info["working"] else "N/A"
                
                print(f"  {status} {python_name} (GIL: {gil_status})")
        
        # Look for ABI compatibility issues
        print(f"\n🔍 ABI COMPATIBILITY ANALYSIS:")
        self.analyze_abi_issues()
    
    def analyze_abi_issues(self):
        """Analyze results for ABI compatibility issues"""
        gil_results = {}
        nogil_results = {}
        
        for test_file, python_results in self.results["test_results"].items():
            for python_name, result in python_results.items():
                python_info = self.results["python_builds"][python_name]
                if not python_info["working"]:
                    continue
                
                gil_enabled = python_info.get("gil_enabled")
                
                if gil_enabled == "True":
                    gil_results[python_name] = result
                elif gil_enabled == "False":
                    nogil_results[python_name] = result
        
        print(f"  GIL enabled configs: {len(gil_results)} tested")
        print(f"  GIL disabled configs: {len(nogil_results)} tested")
        
        # Check for patterns
        if nogil_results:
            nogil_failures = [name for name, result in nogil_results.items() 
                            if result["status"] != "completed" or not result["success"]]
            if nogil_failures:
                print(f"  ⚠️  No-GIL failures detected: {nogil_failures}")
                print("     This may indicate PyO3 race conditions (Bug #4627)")
            else:
                print("  ✅ No obvious no-GIL specific failures detected")
        else:
            print("  ℹ️  No no-GIL configurations tested")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 run_gil_tests.py")
        print("\nThis script tests PyO3 FFI implementations with both GIL and no-GIL Python builds.")
        print("It looks for Python executables built by Makefile:")
        print("  - cpython3.13.5-gil/bin/python3")
        print("  - cpython3.13.5-nogil/bin/python3") 
        print("  - cpython3.14.0rc1-gil/bin/python3")
        print("  - cpython3.14.0rc1-nogil/bin/python3")
        print("\nResults are saved to gil_test_results.json")
        return
    
    runner = GILTestRunner()
    runner.run_all_tests()

if __name__ == "__main__":
    main()