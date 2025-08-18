"""
Python Version Matrix Management for FFI Benchmarks

Detects and orchestrates benchmarks across multiple Python builds:
- Python 3.13.5 & 3.14.0rc1
- GIL enabled & disabled variants
- Clean subprocess execution with environment isolation
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PythonBuild:
    """Represents a specific Python build configuration."""
    version: str
    gil_enabled: bool
    executable_path: Path
    build_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def variant_name(self) -> str:
        """Get human-readable variant name."""
        gil_status = "gil" if self.gil_enabled else "nogil"
        return f"{self.version}-{gil_status}"
    
    @property
    def is_valid(self) -> bool:
        """Check if this Python build is available and executable."""
        return self.executable_path.exists() and os.access(self.executable_path, os.X_OK)


class PythonMatrixDetector:
    """Detects available Python builds for matrix benchmarking."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize detector with base directory to search."""
        self.base_dir = base_dir or Path.cwd()
        self.detected_builds: List[PythonBuild] = []
        
    def detect_python_builds(self) -> List[PythonBuild]:
        """Detect all available Python builds following the expected pattern."""
        builds = []
        
        # Expected build directories based on your pattern
        expected_patterns = [
            ("3.13.5", True, "cpython3.13.5-gil/bin/python3"),
            ("3.13.5", False, "cpython3.13.5-nogil/bin/python3"), 
            ("3.14.0rc1", True, "cpython3.14.0rc1-gil/bin/python3"),
            ("3.14.0rc1", False, "cpython3.14.0rc1-nogil/bin/python3"),
        ]
        
        print("🔍 Detecting Python builds...")
        
        for version, gil_enabled, rel_path in expected_patterns:
            # Try multiple base directories
            potential_paths = [
                self.base_dir / rel_path,
                self.base_dir.parent / rel_path,
                self.base_dir.parent.parent / rel_path,
                Path.cwd() / rel_path,
                Path.cwd().parent / rel_path,
            ]
            
            for path in potential_paths:
                if path.exists() and os.access(path, os.X_OK):
                    # Verify this is actually the right Python build
                    build_info = self._get_python_build_info(path)
                    if build_info:
                        build = PythonBuild(
                            version=version,
                            gil_enabled=gil_enabled,
                            executable_path=path.resolve(),
                            build_info=build_info
                        )
                        builds.append(build)
                        print(f"  ✅ Found: {build.variant_name} at {path}")
                        break
            else:
                print(f"  ❌ Missing: {version}-{'gil' if gil_enabled else 'nogil'}")
        
        self.detected_builds = builds
        return builds
    
    def _get_python_build_info(self, python_path: Path) -> Optional[Dict[str, Any]]:
        """Get detailed information about a Python build."""
        try:
            # Run a small Python script to get build information
            info_script = '''
import sys
import platform
import sysconfig
import json

info = {
    "version": sys.version,
    "version_info": list(sys.version_info),
    "platform": platform.platform(),
    "executable": sys.executable,
    "prefix": sys.prefix,
    "gil_enabled": getattr(sys, "_is_gil_enabled", lambda: True)(),
    "config_args": sysconfig.get_config_var("CONFIG_ARGS"),
    "compiler": sysconfig.get_config_var("CC"),
}

print(json.dumps(info))
'''
            
            result = subprocess.run(
                [str(python_path), "-c", info_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout.strip())
                
        except Exception as e:
            print(f"  ⚠️ Failed to get info for {python_path}: {e}")
        
        return None
    
    def validate_matrix_completeness(self) -> Tuple[bool, List[str]]:
        """Validate that we have a complete 2×2 matrix."""
        required_variants = [
            ("3.13.5", True),
            ("3.13.5", False),
            ("3.14.0rc1", True), 
            ("3.14.0rc1", False),
        ]
        
        found_variants = {(b.version, b.gil_enabled) for b in self.detected_builds}
        missing_variants = []
        
        for version, gil_enabled in required_variants:
            if (version, gil_enabled) not in found_variants:
                gil_status = "gil" if gil_enabled else "nogil"
                missing_variants.append(f"{version}-{gil_status}")
        
        is_complete = len(missing_variants) == 0
        return is_complete, missing_variants
    
    def get_matrix_summary(self) -> Dict[str, Any]:
        """Get summary of detected Python matrix."""
        is_complete, missing = self.validate_matrix_completeness()
        
        return {
            "total_builds": len(self.detected_builds),
            "matrix_complete": is_complete,
            "missing_variants": missing,
            "detected_variants": [b.variant_name for b in self.detected_builds],
            "builds": [
                {
                    "variant": b.variant_name,
                    "version": b.version,
                    "gil_enabled": b.gil_enabled,
                    "path": str(b.executable_path),
                    "valid": b.is_valid
                }
                for b in self.detected_builds
            ]
        }


class PythonMatrixExecutor:
    """Executes benchmarks across multiple Python builds."""
    
    def __init__(self, builds: List[PythonBuild]):
        """Initialize with detected Python builds."""
        self.builds = builds
        self.results = {}
        
    def run_benchmark_matrix(self, benchmark_script: str, 
                           script_args: List[str] = None,
                           timeout: int = 300) -> Dict[str, Any]:
        """Run benchmark script across all Python builds."""
        print(f"\n🚀 Running benchmark matrix across {len(self.builds)} Python builds")
        print("=" * 70)
        
        matrix_results = {
            "timestamp": datetime.now().isoformat(),
            "methodology": "python_version_matrix_ffi_benchmarks",
            "benchmark_script": benchmark_script,
            "script_args": script_args or [],
            "matrix_config": {
                "python_versions": list(set(b.version for b in self.builds)),
                "gil_variants": ["gil", "nogil"],
                "total_builds": len(self.builds)
            },
            "results": {},
            "execution_summary": {}
        }
        
        successful_runs = 0
        failed_runs = 0
        
        for build in self.builds:
            print(f"\n📊 Running benchmark on {build.variant_name}")
            print(f"   Path: {build.executable_path}")
            
            try:
                # Execute benchmark in subprocess
                result = self._execute_benchmark(build, benchmark_script, script_args, timeout)
                
                if result["success"]:
                    print(f"   ✅ Success: {result.get('summary', 'Completed')}")
                    successful_runs += 1
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                    failed_runs += 1
                
                # Store result with nested structure
                version_key = build.version
                gil_key = "gil" if build.gil_enabled else "nogil"
                
                if version_key not in matrix_results["results"]:
                    matrix_results["results"][version_key] = {}
                
                matrix_results["results"][version_key][gil_key] = {
                    "python_executable": str(build.executable_path),
                    "build_info": build.build_info,
                    "benchmark_result": result
                }
                
            except Exception as e:
                print(f"   💥 Exception: {e}")
                failed_runs += 1
        
        # Add execution summary
        matrix_results["execution_summary"] = {
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": f"{successful_runs}/{len(self.builds)}",
            "completion_percentage": (successful_runs / len(self.builds)) * 100
        }
        
        print(f"\n📊 Matrix Execution Summary:")
        print(f"   ✅ Successful: {successful_runs}/{len(self.builds)}")
        print(f"   ❌ Failed: {failed_runs}/{len(self.builds)}")
        print(f"   📈 Success Rate: {successful_runs/len(self.builds)*100:.1f}%")
        
        return matrix_results
    
    def _execute_benchmark(self, build: PythonBuild, script: str, 
                          args: List[str], timeout: int) -> Dict[str, Any]:
        """Execute benchmark script with specific Python build."""
        script_path = Path(script)
        if not script_path.is_absolute():
            # Assume script is relative to benchmark-ffi directory
            script_path = Path(__file__).parent.parent / script
        
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
                "stdout": "",
                "stderr": ""
            }
        
        # Build command
        cmd = [str(build.executable_path), str(script_path)]
        if args:
            cmd.extend(args)
        
        try:
            # Set environment to ensure clean execution
            env = os.environ.copy()
            
            # Add benchmark framework to Python path
            framework_path = str(script_path.parent)
            
            # Add shared virtual environment site-packages for dependencies
            venv_dir = Path(__file__).parent.parent / ".matrix_venv"
            if venv_dir.exists():
                # Get site-packages path from the shared venv
                try:
                    import subprocess as sp
                    result = sp.run([
                        str(venv_dir / "bin" / "python"), 
                        "-c", "import site; print(site.getsitepackages()[0])"
                    ], capture_output=True, text=True)
                    if result.returncode == 0:
                        venv_site_packages = result.stdout.strip()
                        env["PYTHONPATH"] = f"{framework_path}:{venv_site_packages}"
                    else:
                        env["PYTHONPATH"] = framework_path
                except Exception:
                    env["PYTHONPATH"] = framework_path
            else:
                env["PYTHONPATH"] = framework_path
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=script_path.parent,
                env=env
            )
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "summary": self._extract_benchmark_summary(result.stdout) if success else None,
                "error": result.stderr if not success else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Benchmark timeout after {timeout} seconds",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "stdout": "",
                "stderr": ""
            }
    
    def _extract_benchmark_summary(self, stdout: str) -> Optional[str]:
        """Extract a brief summary from benchmark output."""
        lines = stdout.strip().split('\n')
        
        # Look for summary patterns
        for line in reversed(lines[-10:]):  # Check last 10 lines
            line = line.strip()
            if any(keyword in line.lower() for keyword in 
                   ['benchmark complete', 'performance comparison', 'results:', 'success']):
                return line
        
        # Fallback: return last non-empty line
        for line in reversed(lines):
            if line.strip():
                return line.strip()
        
        return "Completed successfully"


def create_python_matrix_detector(base_dir: Optional[Path] = None) -> PythonMatrixDetector:
    """Factory function to create Python matrix detector."""
    return PythonMatrixDetector(base_dir)


def create_python_matrix_executor(builds: List[PythonBuild]) -> PythonMatrixExecutor:
    """Factory function to create Python matrix executor."""
    return PythonMatrixExecutor(builds)


if __name__ == "__main__":
    # Self-test: detect available Python builds
    print("🧪 Python Matrix Detection Test")
    print("=" * 50)
    
    detector = create_python_matrix_detector()
    builds = detector.detect_python_builds()
    
    summary = detector.get_matrix_summary()
    print(f"\n📊 Matrix Summary:")
    print(f"   Total builds: {summary['total_builds']}")
    print(f"   Matrix complete: {summary['matrix_complete']}")
    
    if summary['missing_variants']:
        print(f"   Missing variants: {', '.join(summary['missing_variants'])}")
    
    print(f"\n📋 Detected builds:")
    for build_info in summary['builds']:
        status = "✅" if build_info['valid'] else "❌"
        print(f"   {status} {build_info['variant']} at {build_info['path']}")
    
    if builds:
        print(f"\n🎯 Ready for matrix benchmarking with {len(builds)} builds!")
    else:
        print(f"\n⚠️ No Python builds detected. Check build paths.")