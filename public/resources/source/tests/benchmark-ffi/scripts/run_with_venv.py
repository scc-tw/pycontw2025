#!/usr/bin/env python3
"""
Execute benchmarks with proper virtual environment isolation.

This wrapper ensures benchmarks run in the correct isolated environment
with all dependencies at their latest versions.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict
import argparse

class VenvRunner:
    """Manages benchmark execution within isolated virtual environments."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.venv_base = self.base_dir / ".isolated_venvs"
        self.results_file = self.base_dir / "venv_setup_results.json"
        
        # Load venv configuration
        self.venv_config = self._load_venv_config()
        
    def _load_venv_config(self) -> Dict:
        """Load virtual environment configuration."""
        if not self.results_file.exists():
            raise RuntimeError(
                f"Virtual environments not set up. Run setup_isolated_venvs.py first.\n"
                f"Expected file: {self.results_file}"
            )
        
        with open(self.results_file) as f:
            return json.load(f)
    
    def get_python_executable(self, build_name: str) -> Path:
        """Get Python executable for a specific build."""
        if build_name not in self.venv_config:
            available = list(self.venv_config.keys())
            raise ValueError(
                f"Unknown build: {build_name}\n"
                f"Available builds: {', '.join(available)}"
            )
        
        build_info = self.venv_config[build_name]
        
        if build_info["status"] != "success":
            raise RuntimeError(
                f"Build {build_name} is not available: {build_info.get('reason', 'setup failed')}"
            )
        
        venv_path = Path(build_info["venv_path"])
        python_exe = venv_path / "bin" / "python"
        
        if not python_exe.exists():
            raise RuntimeError(f"Python executable not found: {python_exe}")
        
        return python_exe
    
    def prepare_environment(self, build_name: str) -> Dict[str, str]:
        """Prepare environment variables for isolated execution."""
        env = os.environ.copy()
        
        # Clear Python-related paths to ensure isolation
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONUSERBASE", None)
        
        # Disable user site packages
        env["PYTHONNOUSERSITE"] = "1"
        
        # Set consistent locale
        env["LC_ALL"] = "C.UTF-8"
        env["LANG"] = "C.UTF-8"
        
        # Add build information
        env["FFI_BENCHMARK_BUILD"] = build_name
        env["FFI_BENCHMARK_VENV"] = str(self.venv_base / f"venv_{build_name}")
        
        return env
    
    def run_benchmark(self, build_name: str, script_path: Path, 
                     args: List[str] = None) -> subprocess.CompletedProcess:
        """Run a benchmark script with the specified Python build."""
        python_exe = self.get_python_executable(build_name)
        env = self.prepare_environment(build_name)
        
        # Build command
        cmd = [str(python_exe), str(script_path)]
        if args:
            cmd.extend(args)
        
        print(f"🚀 Running benchmark with {build_name}")
        print(f"   Python: {python_exe}")
        print(f"   Script: {script_path}")
        if args:
            print(f"   Args: {' '.join(args)}")
        print()
        
        # Run the benchmark
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        return result
    
    def run_all_builds(self, script_path: Path, args: List[str] = None):
        """Run benchmark on all available Python builds."""
        results = {}
        
        for build_name, build_info in self.venv_config.items():
            if build_info["status"] != "success":
                print(f"⚠️  Skipping {build_name}: not available")
                continue
            
            print(f"\n{'=' * 60}")
            print(f"Running on {build_name}")
            print('=' * 60)
            
            try:
                result = self.run_benchmark(build_name, script_path, args)
                results[build_name] = {
                    "returncode": result.returncode,
                    "status": "success" if result.returncode == 0 else "failed"
                }
            except Exception as e:
                print(f"❌ Error running {build_name}: {e}")
                results[build_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Print summary
        print(f"\n{'=' * 60}")
        print("EXECUTION SUMMARY")
        print('=' * 60)
        
        for build, result in results.items():
            status = result["status"]
            icon = "✅" if status == "success" else "❌"
            print(f"{icon} {build}: {status}")
        
        return results
    
    def verify_venv_packages(self, build_name: str):
        """Verify packages are properly installed in venv."""
        python_exe = self.get_python_executable(build_name)
        
        print(f"🔍 Verifying packages for {build_name}")
        
        # Check key packages
        packages = ["numpy", "scipy", "cffi", "pybind11"]
        
        for pkg in packages:
            cmd = [str(python_exe), "-c", f"import {pkg}; print(f'{pkg} {{'.join(str({pkg}.__version__).split('.')[:2])}}'.)"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ {result.stdout.strip()}")
            else:
                print(f"   ❌ {pkg}: import failed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run benchmarks with isolated virtual environments"
    )
    
    parser.add_argument(
        "script",
        type=Path,
        help="Benchmark script to run"
    )
    
    parser.add_argument(
        "--build",
        choices=["3.13.5-gil", "3.13.5-nogil", "3.14.0rc1-gil", "3.14.0rc1-nogil", "all"],
        default="all",
        help="Python build to use (default: all)"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify package installations before running"
    )
    
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Base directory for benchmark project"
    )
    
    # Collect any additional arguments for the benchmark script
    parser.add_argument(
        "benchmark_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the benchmark script"
    )
    
    args = parser.parse_args()
    
    # Validate script exists
    if not args.script.exists():
        print(f"❌ Script not found: {args.script}")
        sys.exit(1)
    
    runner = VenvRunner(args.base_dir)
    
    if args.build == "all":
        # Verify first if requested
        if args.verify:
            for build in runner.venv_config.keys():
                if runner.venv_config[build]["status"] == "success":
                    runner.verify_venv_packages(build)
                    print()
        
        # Run on all builds
        results = runner.run_all_builds(args.script, args.benchmark_args)
        
        # Exit with error if any failed
        if any(r["status"] != "success" for r in results.values()):
            sys.exit(1)
    else:
        # Verify first if requested
        if args.verify:
            runner.verify_venv_packages(args.build)
            print()
        
        # Run on specific build
        result = runner.run_benchmark(args.build, args.script, args.benchmark_args)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()