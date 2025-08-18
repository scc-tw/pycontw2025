#!/usr/bin/env python3
"""
Professional isolated virtual environment management for FFI benchmarking.

This script replaces the shared venv approach with isolated environments
for each Python build, ensuring:
- Complete isolation between test environments
- Reproducible dependency versions
- Latest package versions for each environment
- Proper cleanup and verification procedures
"""

import os
import sys
import subprocess
import json
import shutil
import yaml
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib

class VenvManager:
    """Manages isolated virtual environments for benchmark testing."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.venv_base = self.base_dir / ".isolated_venvs"
        self.requirements_dir = self.base_dir / "requirements"
        self.log_file = self.base_dir / "venv_setup.log"
        self.config_file = self.base_dir / "scripts" / "venv_config.yaml"
        
        # Load configuration from YAML if it exists
        self.config = self._load_config()
        
        # Python builds to manage
        self.python_builds = {
            "3.13.5-gil": self.base_dir.parent.parent / "cpython3.13.5-gil" / "bin" / "python3.13",
            "3.13.5-nogil": self.base_dir.parent.parent / "cpython3.13.5-nogil" / "bin" / "python3.13",
            "3.14.0rc1-gil": self.base_dir.parent.parent / "cpython3.14.0rc1-gil" / "bin" / "python3.14",
            "3.14.0rc1-nogil": self.base_dir.parent.parent / "cpython3.14.0rc1-nogil" / "bin" / "python3.14",
        }
        
        # Dependencies from config or defaults
        if self.config and 'dependencies' in self.config:
            deps = self.config['dependencies']
            self.core_dependencies = deps.get('core', []) + deps.get('ffi', [])
            self.prerelease_dependencies = deps.get('prerelease', [])
            self.rust_dependencies = deps.get('rust', ["maturin", "setuptools-rust"])
            self.dev_dependencies = deps.get('development', [])
            self.profiling_dependencies = deps.get('profiling', [])
        else:
            # Fallback to hardcoded defaults
            self.core_dependencies = [
                "numpy",
                "scipy", 
                "matplotlib",
                "psutil",
                "pybind11",
                "viztracer",
                "memory-profiler",
                "py-spy",
            ]
            self.prerelease_dependencies = []
            self.rust_dependencies = [
                "maturin",
                "setuptools-rust",
            ]
            self.dev_dependencies = [
                "pytest",
                "pytest-benchmark",
                "black",
                "ruff",
                "mypy",
            ]
            self.profiling_dependencies = []
        
    def setup_directories(self):
        """Create necessary directory structure."""
        self.venv_base.mkdir(exist_ok=True)
        self.requirements_dir.mkdir(exist_ok=True)
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, cmd: List[str], env: Optional[Dict] = None, 
                   check: bool = True) -> subprocess.CompletedProcess:
        """Run command with proper error handling."""
        self.log(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env or os.environ.copy(),
            check=False
        )
        
        if result.returncode != 0 and check:
            self.log(f"Command failed: {result.stderr}", "ERROR")
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")
            
        return result
    
    def create_venv(self, python_path: Path, venv_name: str) -> Path:
        """Create an isolated virtual environment."""
        venv_path = self.venv_base / venv_name
        
        # Remove existing venv if present
        if venv_path.exists():
            self.log(f"Removing existing venv: {venv_path}")
            shutil.rmtree(venv_path)
        
        # Create new venv
        self.log(f"Creating venv: {venv_path}")
        self.run_command([str(python_path), "-m", "venv", str(venv_path)])
        
        return venv_path
    
    def get_pip_path(self, venv_path: Path) -> Path:
        """Get pip executable path for a venv."""
        return venv_path / "bin" / "pip"
    
    def get_python_path(self, venv_path: Path) -> Path:
        """Get python executable path for a venv."""
        return venv_path / "bin" / "python"
    
    def upgrade_pip(self, venv_path: Path):
        """Upgrade pip, setuptools, and wheel in venv."""
        pip_path = self.get_pip_path(venv_path)
        
        self.log(f"Upgrading pip in {venv_path.name}")
        self.run_command([
            str(pip_path), "install", "--upgrade", 
            "pip", "setuptools", "wheel"
        ])
    
    def _load_config(self) -> Optional[Dict]:
        """Load configuration from YAML file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_file}: {e}")
        return None
    
    def install_dependencies(self, venv_path: Path, deps: List[str], use_pre: bool = False):
        """Install dependencies in venv."""
        pip_path = self.get_pip_path(venv_path)
        
        for dep in deps:
            self.log(f"Installing {dep} in {venv_path.name}")
            # Build command with --upgrade and optionally --pre
            cmd = [str(pip_path), "install", "--upgrade"]
            if use_pre:
                cmd.append("--pre")
            cmd.append(dep)
            
            result = self.run_command(cmd, check=False)
            
            if result.returncode != 0:
                self.log(f"Warning: Failed to install {dep}: {result.stderr}", "WARN")
    
    def install_prerelease_dependencies(self, venv_path: Path, deps: List[str]):
        """Install pre-release dependencies with --pre flag."""
        self.install_dependencies(venv_path, deps, use_pre=True)
    
    def install_cffi_2_0_0b1(self, venv_path: Path, build_name: str) -> bool:
        """Install CFFI 2.0.0b1 with special handling for Python 3.13-nogil only."""
        python_path = self.get_python_path(venv_path)
        pip_path = self.get_pip_path(venv_path)
        
        # Only Python 3.13.5-nogil needs the workaround
        if build_name != "3.13.5-nogil":
            # Standard installation for all other builds (GIL-enabled and 3.14)
            self.log(f"Installing CFFI 2.0.0b1 using pip for {build_name}")
            result = self.run_command([
                str(pip_path), "install", "--upgrade", "--pre", "cffi==2.0.0b1"
            ], check=False)
            return result.returncode == 0
        
        # Special handling for Python 3.13-nogil - build from source with patch
        self.log(f"Building CFFI 2.0.0b1 from source for {build_name} (patched for nogil)")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Clone the repository
            self.log("Cloning CFFI repository...")
            result = self.run_command([
                "git", "clone", "--depth", "1", "--branch", "v2.0.0b1",
                "https://github.com/python-cffi/cffi.git",
                str(tmpdir_path / "cffi")
            ], check=False)
            
            if result.returncode != 0:
                self.log("Failed to clone CFFI repository", "ERROR")
                return False
            
            cffi_dir = tmpdir_path / "cffi"
            
            # Patch setup.py to allow Python 3.13 nogil
            setup_py = cffi_dir / "setup.py"
            content = setup_py.read_text()
            
            # Replace the version check
            original_check = """if FREE_THREADED_BUILD and sys.version_info < (3, 14):
    raise RuntimeError("CFFI does not support the free-threaded build of CPython 3.13. "
                       "Upgrade to free-threaded 3.14 or newer to use CFFI with the "
                       "free-threaded build.")"""
            
            patched_check = """# Patched to allow experimental Python 3.13 nogil support
if FREE_THREADED_BUILD and sys.version_info < (3, 13):
    raise RuntimeError("CFFI requires at least Python 3.13 for free-threaded builds")

if FREE_THREADED_BUILD:
    print("WARNING: Building CFFI for free-threaded Python - this is experimental!", file=sys.stderr)"""
            
            content = content.replace(original_check, patched_check)
            setup_py.write_text(content)
            
            # Uninstall existing cffi if present
            self.log("Uninstalling existing CFFI...")
            self.run_command([str(pip_path), "uninstall", "-y", "cffi"], check=False)
            
            # Install build dependencies
            self.log("Installing build dependencies...")
            self.run_command([
                str(pip_path), "install", "--upgrade", "setuptools", "wheel"
            ])
            
            # Build and install
            self.log("Building and installing CFFI...")
            result = self.run_command([
                str(pip_path), "install", "--force-reinstall", "--no-deps", str(cffi_dir)
            ], check=False)
            
            if result.returncode != 0:
                self.log(f"Failed to install CFFI 2.0.0b1: {result.stderr}", "ERROR")
                return False
            
            # Verify installation
            result = self.run_command([
                str(python_path), "-c", 
                "import cffi; print(f'CFFI {cffi.__version__} installed successfully')"
            ], check=False)
            
            if result.returncode == 0:
                self.log(f"✅ CFFI 2.0.0b1 installed successfully for {build_name}")
                return True
            else:
                self.log(f"Failed to verify CFFI installation: {result.stderr}", "ERROR")
                return False
    
    def generate_requirements(self, venv_path: Path, build_name: str):
        """Generate requirements.txt for a venv."""
        pip_path = self.get_pip_path(venv_path)
        
        self.log(f"Generating requirements for {build_name}")
        result = self.run_command([str(pip_path), "freeze"])
        
        req_file = self.requirements_dir / f"requirements_{build_name}.txt"
        
        with open(req_file, "w") as f:
            f.write(f"# Generated on {datetime.now().isoformat()}\n")
            f.write(f"# Python build: {build_name}\n\n")
            f.write(result.stdout)
        
        # Also create a hash for verification
        content_hash = hashlib.sha256(result.stdout.encode()).hexdigest()[:8]
        
        hash_file = self.requirements_dir / f"requirements_{build_name}.hash"
        with open(hash_file, "w") as f:
            f.write(content_hash)
        
        return req_file, content_hash
    
    def verify_installation(self, venv_path: Path, build_name: str) -> Dict:
        """Verify installed packages and versions."""
        python_path = self.get_python_path(venv_path)
        
        verification = {
            "build": build_name,
            "timestamp": datetime.now().isoformat(),
            "packages": {},
            "import_tests": {}
        }
        
        # Check core packages
        for pkg in ["numpy", "scipy", "cffi", "pybind11"]:
            try:
                result = self.run_command([
                    str(python_path), "-c",
                    f"import {pkg}; print({pkg}.__version__)"
                ])
                verification["packages"][pkg] = result.stdout.strip()
                verification["import_tests"][pkg] = "success"
            except Exception as e:
                verification["import_tests"][pkg] = f"failed: {str(e)}"
        
        return verification
    
    def setup_all_venvs(self):
        """Set up isolated venvs for all Python builds."""
        self.setup_directories()
        
        self.log("=" * 60)
        self.log("Starting isolated virtual environment setup")
        self.log("=" * 60)
        
        results = {}
        
        for build_name, python_path in self.python_builds.items():
            self.log(f"\nProcessing {build_name}...")
            
            if not python_path.exists():
                self.log(f"Python not found: {python_path}", "WARN")
                results[build_name] = {"status": "skipped", "reason": "Python not found"}
                continue
            
            try:
                # Create venv
                venv_path = self.create_venv(python_path, f"venv_{build_name}")
                
                # Upgrade pip
                self.upgrade_pip(venv_path)
                
                # Install regular dependencies
                all_deps = self.core_dependencies + self.rust_dependencies + self.dev_dependencies + self.profiling_dependencies
                self.install_dependencies(venv_path, all_deps)
                
                # Install pre-release dependencies if any
                if self.prerelease_dependencies:
                    self.log(f"Installing pre-release packages for {build_name}...")
                    self.install_prerelease_dependencies(venv_path, self.prerelease_dependencies)
                
                # Install CFFI 2.0.0b1 (special handling for nogil builds)
                self.log(f"Installing CFFI 2.0.0b1 for {build_name}...")
                cffi_success = self.install_cffi_2_0_0b1(venv_path, build_name)
                if not cffi_success:
                    self.log(f"Warning: Failed to install CFFI 2.0.0b1 for {build_name}", "WARN")
                
                # Generate requirements
                req_file, req_hash = self.generate_requirements(venv_path, build_name)
                
                # Verify installation
                verification = self.verify_installation(venv_path, build_name)
                
                results[build_name] = {
                    "status": "success",
                    "venv_path": str(venv_path),
                    "requirements_file": str(req_file),
                    "requirements_hash": req_hash,
                    "verification": verification
                }
                
                self.log(f"✅ Successfully set up {build_name}")
                
            except Exception as e:
                self.log(f"Failed to set up {build_name}: {str(e)}", "ERROR")
                results[build_name] = {"status": "failed", "error": str(e)}
        
        # Save results
        results_file = self.base_dir / "venv_setup_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        self.log(f"\n📊 Results saved to: {results_file}")
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: Dict):
        """Print setup summary."""
        self.log("\n" + "=" * 60)
        self.log("SETUP SUMMARY")
        self.log("=" * 60)
        
        successful = sum(1 for r in results.values() if r["status"] == "success")
        failed = sum(1 for r in results.values() if r["status"] == "failed")
        skipped = sum(1 for r in results.values() if r["status"] == "skipped")
        
        self.log(f"Total builds: {len(results)}")
        self.log(f"Successful: {successful}")
        self.log(f"Failed: {failed}")
        self.log(f"Skipped: {skipped}")
        
        if successful > 0:
            self.log("\n✅ Successfully configured builds:")
            for build, result in results.items():
                if result["status"] == "success":
                    # Handle different result formats
                    if "venv_path" in result:
                        self.log(f"   • {build}: {result['venv_path']}")
                    elif "message" in result:
                        self.log(f"   • {build}: {result['message']}")
                    else:
                        self.log(f"   • {build}: Success")
        
        if failed > 0:
            self.log("\n❌ Failed builds:")
            for build, result in results.items():
                if result["status"] == "failed":
                    # Handle different result formats
                    if "error" in result:
                        self.log(f"   • {build}: {result['error']}")
                    elif "message" in result:
                        self.log(f"   • {build}: {result['message']}")
                    else:
                        self.log(f"   • {build}: Failed")
    
    def cleanup_old_venvs(self):
        """Remove all virtual environments."""
        if self.venv_base.exists():
            self.log("Cleaning up all virtual environments...")
            shutil.rmtree(self.venv_base)
            self.log("✅ Cleanup complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage isolated virtual environments for FFI benchmarking"
    )
    parser.add_argument(
        "--cleanup", 
        action="store_true",
        help="Remove all existing virtual environments"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Base directory for benchmark project"
    )
    parser.add_argument(
        "--cffi-only",
        action="store_true",
        help="Only install/update CFFI 2.0.0b1 in existing venvs"
    )
    
    args = parser.parse_args()
    
    manager = VenvManager(args.base_dir)
    
    if args.cleanup:
        manager.cleanup_old_venvs()
    elif args.cffi_only:
        # Only update CFFI in existing venvs
        manager.setup_directories()
        results = {}
        
        for build_name in manager.python_builds.keys():
            venv_path = manager.venv_base / f"venv_{build_name}"
            
            if not venv_path.exists():
                manager.log(f"Venv not found: {venv_path}", "WARN")
                results[build_name] = {"status": "skipped", "reason": "Venv not found"}
                continue
            
            manager.log(f"Updating CFFI 2.0.0b1 in {build_name}...")
            success = manager.install_cffi_2_0_0b1(venv_path, build_name)
            
            if success:
                results[build_name] = {"status": "success", "message": "CFFI 2.0.0b1 installed"}
            else:
                results[build_name] = {"status": "failed", "message": "CFFI installation failed"}
        
        manager.print_summary(results)
        
        if any(r["status"] == "failed" for r in results.values()):
            sys.exit(1)
    else:
        results = manager.setup_all_venvs()
        
        # Exit with error if any setup failed
        if any(r["status"] == "failed" for r in results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()