#!/usr/bin/env python3
"""
Unified benchmark execution wrapper for running with all isolated venvs.

This script makes it easy to run any benchmark script across all available 
Python builds with their isolated virtual environments.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add benchmark framework to path
benchmark_root = Path(__file__).parent.parent
sys.path.insert(0, str(benchmark_root))

def load_venv_config() -> Dict[str, Any]:
    """Load virtual environment configuration."""
    results_file = benchmark_root / "venv_setup_results.json"
    
    if not results_file.exists():
        return {}
    
    try:
        with open(results_file) as f:
            return json.load(f)
    except Exception:
        return {}

def get_available_builds() -> List[str]:
    """Get list of available Python builds."""
    venv_config = load_venv_config()
    
    available = []
    for build_name, info in venv_config.items():
        if info.get("status") == "success":
            available.append(build_name)
    
    return available

def get_python_executable(build_name: str) -> Optional[Path]:
    """Get Python executable for a specific build."""
    venv_config = load_venv_config()
    
    if build_name not in venv_config or venv_config[build_name]["status"] != "success":
        return None
    
    venv_path = Path(venv_config[build_name]["venv_path"])
    python_exe = venv_path / "bin" / "python"
    
    return python_exe if python_exe.exists() else None

def create_execution_environment(build_name: str) -> Dict[str, str]:
    """Create isolated execution environment."""
    env = os.environ.copy()
    
    # Clear Python-related paths
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONUSERBASE", None)
    
    # Disable user site packages
    env["PYTHONNOUSERSITE"] = "1"
    
    # Set build information
    env["FFI_BENCHMARK_BUILD"] = build_name
    env["FFI_BENCHMARK_VENV_INTEGRATED"] = "true"
    
    return env

def run_script_with_build(script_path: Path, build_name: str, 
                         script_args: List[str] = None) -> Dict[str, Any]:
    """Run a script with a specific Python build."""
    python_exe = get_python_executable(build_name)
    
    if not python_exe:
        return {
            "status": "failed",
            "error": f"Python executable not found for {build_name}",
            "build": build_name
        }
    
    env = create_execution_environment(build_name)
    
    # Build command
    cmd = [str(python_exe), str(script_path)]
    if script_args:
        cmd.extend(script_args)
    
    try:
        print(f"📊 Running with {build_name}...")
        
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        end_time = datetime.now()
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "build": build_name,
            "python_exe": str(python_exe),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": (end_time - start_time).total_seconds(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "build": build_name,
            "error": "Script execution timeout (5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "build": build_name,
            "error": str(e)
        }

def run_matrix_benchmark(script_path: Path, script_args: List[str] = None,
                        builds: List[str] = None) -> Dict[str, Any]:
    """Run benchmark across all or specified builds."""
    
    if builds is None:
        builds = get_available_builds()
    
    if not builds:
        print("❌ No isolated virtual environments available!")
        print("   Run: python scripts/setup_isolated_venvs.py")
        return {"error": "no_venvs_available"}
    
    print(f"🚀 MATRIX BENCHMARK EXECUTION")
    print(f"Script: {script_path}")
    print(f"Builds: {', '.join(builds)}")
    if script_args:
        print(f"Args: {' '.join(script_args)}")
    print("=" * 60)
    
    matrix_results = {
        "timestamp": datetime.now().isoformat(),
        "script": str(script_path),
        "script_args": script_args or [],
        "total_builds": len(builds),
        "results": {}
    }
    
    # Execute on each build
    for build_name in builds:
        result = run_script_with_build(script_path, build_name, script_args)
        matrix_results["results"][build_name] = result
        
        # Print immediate feedback
        if result["status"] == "success":
            duration = result.get("duration_seconds", 0)
            print(f"   ✅ {build_name}: completed in {duration:.1f}s")
        elif result["status"] == "failed":
            print(f"   ❌ {build_name}: failed (exit code {result.get('returncode', 'unknown')})")
            if result.get("stderr"):
                # Show first error line
                error_line = result["stderr"].split('\n')[0]
                print(f"      Error: {error_line[:80]}...")
        elif result["status"] == "timeout":
            print(f"   ⏰ {build_name}: timeout")
        else:
            print(f"   ❌ {build_name}: {result.get('error', 'unknown error')}")
    
    # Summary
    successful = sum(1 for r in matrix_results["results"].values() 
                    if r["status"] == "success")
    failed = len(builds) - successful
    
    matrix_results["summary"] = {
        "successful": successful,
        "failed": failed,
        "success_rate": successful / len(builds) if builds else 0
    }
    
    print(f"\n📊 EXECUTION SUMMARY")
    print(f"   ✅ Successful: {successful}/{len(builds)}")
    print(f"   ❌ Failed: {failed}/{len(builds)}")
    print(f"   📈 Success rate: {successful/len(builds)*100:.1f}%")
    
    return matrix_results

def save_results(results: Dict[str, Any], output_file: Path):
    """Save results to file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved: {output_file}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")

def print_available_builds():
    """Print available builds."""
    builds = get_available_builds()
    
    if not builds:
        print("❌ No isolated virtual environments available")
        print("   Run: python scripts/setup_isolated_venvs.py")
        return
    
    print("📦 Available Python builds with isolated venvs:")
    for build in builds:
        python_exe = get_python_executable(build)
        print(f"   ✅ {build}: {python_exe}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run benchmarks across all isolated virtual environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run comprehensive benchmark on all builds
  python run_with_all_venvs.py ../benchmark-ffi-comprehensive/comprehensive_benchmark.py

  # Run simple benchmark on all builds  
  python run_with_all_venvs.py run_all_benchmarks.py
  
  # Run on specific builds only
  python run_with_all_venvs.py run_all_benchmarks.py --builds 3.13.5-gil 3.13.5-nogil
  
  # Pass arguments to the benchmark script
  python run_with_all_venvs.py ../benchmark-ffi-comprehensive/comprehensive_benchmark.py -- --enable-matrix --output results
  
  # List available builds
  python run_with_all_venvs.py --list-builds
"""
    )
    
    parser.add_argument(
        "script",
        nargs="?",
        help="Python script to run"
    )
    
    parser.add_argument(
        "--builds",
        nargs="+",
        help="Specific builds to use (default: all available)"
    )
    
    parser.add_argument(
        "--list-builds",
        action="store_true",
        help="List available builds and exit"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for results (default: matrix_results_<timestamp>.json)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed output"
    )
    
    # Parse known args to separate script args
    args, script_args = parser.parse_known_args()
    
    if args.list_builds:
        print_available_builds()
        return 0
    
    if not args.script:
        parser.print_help()
        return 1
    
    script_path = Path(args.script)
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return 1
    
    # Setup output file
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = benchmark_root / f"matrix_results_{timestamp}.json"
    
    # Run matrix benchmark
    try:
        results = run_matrix_benchmark(
            script_path=script_path,
            script_args=script_args,
            builds=args.builds
        )
        
        # Save results
        save_results(results, output_file)
        
        # Exit with appropriate code
        if results.get("summary", {}).get("successful", 0) > 0:
            return 0  # At least one success
        else:
            return 1  # All failed
            
    except KeyboardInterrupt:
        print("\n❌ Execution interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())