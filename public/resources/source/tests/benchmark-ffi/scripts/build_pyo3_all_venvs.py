#!/usr/bin/env python3
"""
Build PyO3 extension for all isolated virtual environments.

This script builds the PyO3 benchmark library for each Python build,
ensuring compatibility across GIL and no-GIL configurations.
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class PyO3Builder:
    """Manages PyO3 extension building across multiple environments."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.venv_base = self.base_dir / ".isolated_venvs"
        self.pyo3_dir = self.base_dir / "implementations" / "pyo3_impl"
        self.log_file = self.base_dir / "pyo3_build.log"
        
        # Python builds to target
        self.python_builds = [
            "3.13.5-gil",
            "3.13.5-nogil", 
            "3.14.0rc1-gil",
            "3.14.0rc1-nogil",
        ]
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None,
                   env: Optional[Dict] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run command with proper error handling."""
        self.log(f"Running: {' '.join(cmd)}")
        if cwd:
            self.log(f"  in directory: {cwd}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env or os.environ.copy(),
            check=False
        )
        
        if result.returncode != 0:
            self.log(f"Command output: {result.stdout}", "DEBUG")
            self.log(f"Command stderr: {result.stderr}", "ERROR")
            if check:
                raise RuntimeError(f"Command failed: {' '.join(cmd)}")
            
        return result
    
    def get_venv_python(self, build_name: str) -> Optional[Path]:
        """Get Python executable for a specific venv."""
        venv_path = self.venv_base / f"venv_{build_name}"
        python_path = venv_path / "bin" / "python"
        
        if python_path.exists():
            return python_path
        return None
    
    def get_venv_maturin(self, build_name: str) -> Optional[Path]:
        """Get maturin executable for a specific venv."""
        venv_path = self.venv_base / f"venv_{build_name}"
        maturin_path = venv_path / "bin" / "maturin"
        
        if maturin_path.exists():
            return maturin_path
        return None
    
    def clean_build_artifacts(self):
        """Clean previous build artifacts."""
        self.log("Cleaning build artifacts...")
        
        # Clean Rust target directory
        target_dir = self.pyo3_dir / "target"
        if target_dir.exists():
            shutil.rmtree(target_dir)
            self.log(f"  Removed: {target_dir}")
        
        # Clean Python build directories
        for dir_name in ["build", "dist", "*.egg-info", "__pycache__"]:
            for path in self.pyo3_dir.glob(dir_name):
                if path.is_dir():
                    shutil.rmtree(path)
                    self.log(f"  Removed: {path}")
        
        # Clean .so files but keep benchlib.so (the C library)
        for so_file in self.pyo3_dir.glob("*.so"):
            if so_file.name != "benchlib.so" and not so_file.is_symlink():
                so_file.unlink()
                self.log(f"  Removed: {so_file}")
    
    def build_for_venv(self, build_name: str, profile: str = "release") -> Dict:
        """Build PyO3 extension for a specific venv."""
        self.log(f"\n{'='*60}")
        self.log(f"Building PyO3 for {build_name} (profile: {profile})")
        self.log(f"{'='*60}")
        
        result = {
            "build": build_name,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get Python executable
        python_path = self.get_venv_python(build_name)
        if not python_path:
            self.log(f"❌ Python not found for {build_name}", "ERROR")
            result["status"] = "failed"
            result["error"] = "Python executable not found"
            return result
        
        # Get maturin executable
        maturin_path = self.get_venv_maturin(build_name)
        if not maturin_path:
            # Fallback to system maturin
            maturin_path = Path("/usr/bin/maturin")
            if not maturin_path.exists():
                self.log(f"❌ maturin not found for {build_name}", "ERROR")
                result["status"] = "failed"
                result["error"] = "maturin not found"
                return result
            self.log(f"Using system maturin: {maturin_path}")
        
        try:
            # Set environment
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = str(self.venv_base / f"venv_{build_name}")
            
            # Set Rust flags for instrumented profile
            if profile == "instrumented":
                env["RUSTFLAGS"] = "-C force-frame-pointers=yes"
            
            # Build the extension using maturin
            self.log(f"Building extension with maturin and {python_path}...")
            
            # Set the correct Python in the environment
            env["PATH"] = f"{python_path.parent}:{env['PATH']}"
            
            # Build and install into the venv using maturin develop
            # maturin develop automatically uses the active Python
            build_result = self.run_command(
                [str(python_path), "-m", "maturin", "develop", "--release"],
                cwd=self.pyo3_dir,
                env=env
            )
            
            # Find the generated .so file
            # Maturin installs directly into site-packages, so we need to find it there
            venv_path = self.venv_base / f"venv_{build_name}"
            site_packages = list(venv_path.glob("lib/python*/site-packages"))
            
            generated_so = None
            if site_packages:
                for sp in site_packages:
                    so_files = list(sp.glob("benchlib_pyo3*.so"))
                    if so_files:
                        generated_so = so_files[0]
                        break
            
            if generated_so:
                self.log(f"✅ Found installed module: {generated_so.name}")
                
                # Copy to pyo3_impl directory for consistency
                build_so_name = f"benchlib_pyo3_{build_name.replace('.', '_').replace('-', '_')}.so"
                build_so_path = self.pyo3_dir / build_so_name
                shutil.copy2(generated_so, build_so_path)
                self.log(f"✅ Created build-specific copy: {build_so_name}")
            else:
                self.log(f"⚠️ Module installed but .so file not found in expected location")
            
            # Test import
            self.log("Testing import...")
            test_result = self.run_command(
                [str(python_path), "-c", "import benchlib_pyo3; print('Import successful')"],
                cwd=self.pyo3_dir,
                env=env
            )
            
            result["status"] = "success"
            result["so_file"] = str(generated_so) if generated_so else "installed via maturin"
            result["import_test"] = "passed"
            
            self.log(f"✅ Successfully built PyO3 for {build_name}")
            
        except Exception as e:
            self.log(f"❌ Failed to build for {build_name}: {e}", "ERROR")
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def build_all(self, profile: str = "release") -> Dict:
        """Build PyO3 for all Python environments."""
        self.log("="*60)
        self.log("Starting PyO3 build for all environments")
        self.log("="*60)
        
        results = {}
        
        for build_name in self.python_builds:
            result = self.build_for_venv(build_name, profile)
            results[build_name] = result
        
        # Save results
        results_file = self.base_dir / "pyo3_build_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        self.log(f"\n📊 Results saved to: {results_file}")
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: Dict):
        """Print build summary."""
        self.log("\n" + "="*60)
        self.log("BUILD SUMMARY")
        self.log("="*60)
        
        successful = sum(1 for r in results.values() if r.get("status") == "success")
        failed = sum(1 for r in results.values() if r.get("status") == "failed")
        
        self.log(f"Total builds: {len(results)}")
        self.log(f"Successful: {successful}")
        self.log(f"Failed: {failed}")
        
        if successful > 0:
            self.log("\n✅ Successfully built for:")
            for build, result in results.items():
                if result.get("status") == "success":
                    self.log(f"   • {build}: {result.get('so_file', 'N/A')}")
        
        if failed > 0:
            self.log("\n❌ Failed builds:")
            for build, result in results.items():
                if result.get("status") == "failed":
                    self.log(f"   • {build}: {result.get('error', 'Unknown error')}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build PyO3 extension for all Python environments"
    )
    parser.add_argument(
        "--profile",
        choices=["release", "instrumented"],
        default="release",
        help="Build profile (release=optimized, instrumented=with frame pointers)"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Base directory for benchmark project"
    )
    parser.add_argument(
        "--build",
        help="Build for specific Python version only (e.g., 3.13.5-nogil)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    
    args = parser.parse_args()
    
    builder = PyO3Builder(args.base_dir)
    
    if args.clean:
        builder.clean_build_artifacts()
    
    if args.build:
        # Build for specific version
        if args.build not in builder.python_builds:
            print(f"❌ Unknown build: {args.build}")
            print(f"Available: {', '.join(builder.python_builds)}")
            sys.exit(1)
        
        result = builder.build_for_venv(args.build, args.profile)
        if result.get("status") != "success":
            sys.exit(1)
    else:
        # Build for all versions
        results = builder.build_all(args.profile)
        
        # Exit with error if any build failed
        if any(r.get("status") == "failed" for r in results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()