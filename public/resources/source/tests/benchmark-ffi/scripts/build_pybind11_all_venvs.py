#!/usr/bin/env python3
"""
Build pybind11 extension for all isolated virtual environments.

This script builds the pybind11 benchmark library for each Python build,
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

class Pybind11Builder:
    """Manages pybind11 extension building across multiple environments."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.venv_base = self.base_dir / ".isolated_venvs"
        self.pybind11_dir = self.base_dir / "implementations" / "pybind11_impl"
        self.lib_dir = self.base_dir / "lib"
        self.log_file = self.base_dir / "pybind11_build.log"
        
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
    
    def ensure_benchlib(self) -> bool:
        """Ensure benchlib.so is built."""
        benchlib_so = self.lib_dir / "benchlib.so"
        
        if benchlib_so.exists():
            self.log(f"✅ benchlib.so already exists: {benchlib_so}")
            return True
        
        self.log("Building benchlib.so...")
        
        # Check if Makefile exists
        makefile = self.lib_dir / "Makefile"
        if not makefile.exists():
            self.log(f"❌ Makefile not found at {makefile}", "ERROR")
            return False
        
        # Run make in lib directory
        try:
            self.run_command(["make", "clean"], cwd=self.lib_dir, check=False)
            self.run_command(["make"], cwd=self.lib_dir)
            
            if benchlib_so.exists():
                self.log(f"✅ Successfully built benchlib.so")
                return True
            else:
                self.log(f"❌ benchlib.so not created after make", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Failed to build benchlib.so: {e}", "ERROR")
            return False
    
    def get_venv_python(self, build_name: str) -> Optional[Path]:
        """Get Python executable for a specific venv."""
        venv_path = self.venv_base / f"venv_{build_name}"
        python_path = venv_path / "bin" / "python"
        
        if python_path.exists():
            return python_path
        return None
    
    def clean_build_artifacts(self, keep_so_files=False):
        """Clean previous build artifacts."""
        self.log("Cleaning build artifacts...")
        
        # Clean build directories
        for dir_name in ["build", "dist", "*.egg-info", "__pycache__"]:
            for path in self.pybind11_dir.glob(dir_name):
                if path.is_dir():
                    shutil.rmtree(path)
                    self.log(f"  Removed: {path}")
        
        # Optionally clean .so files (don't clean them during multi-build)
        if not keep_so_files:
            for so_file in self.pybind11_dir.glob("*.so"):
                so_file.unlink()
                self.log(f"  Removed: {so_file}")
    
    def build_for_venv(self, build_name: str, profile: str = "fast") -> Dict:
        """Build pybind11 extension for a specific venv."""
        self.log(f"\n{'='*60}")
        self.log(f"Building pybind11 for {build_name} (profile: {profile})")
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
        
        try:
            # Clean previous artifacts but keep .so files
            self.clean_build_artifacts(keep_so_files=True)
            
            # Set environment for profile
            env = os.environ.copy()
            env["PROFILE"] = profile
            
            # Build the extension
            self.log(f"Building extension with {python_path}...")
            build_result = self.run_command(
                [str(python_path), "setup_pybind11.py", "build_ext", "--inplace"],
                cwd=self.pybind11_dir,
                env=env
            )
            
            # Find the generated .so file
            so_files = list(self.pybind11_dir.glob("*.so"))
            if not so_files:
                raise RuntimeError("No .so file generated")
            
            generated_so = so_files[0]
            self.log(f"✅ Generated: {generated_so.name}")
            
            # Create build-specific copy
            build_so_name = f"benchlib_pybind11_{build_name.replace('.', '_').replace('-', '_')}.so"
            build_so_path = self.pybind11_dir / build_so_name
            shutil.copy2(generated_so, build_so_path)
            self.log(f"✅ Created build-specific copy: {build_so_name}")
            
            # Test import
            self.log("Testing import...")
            test_result = self.run_command(
                [str(python_path), "-c", "import benchlib_pybind11; print('Import successful')"],
                cwd=self.pybind11_dir
            )
            
            result["status"] = "success"
            result["so_file"] = str(generated_so)
            result["build_so_file"] = str(build_so_path)
            result["import_test"] = "passed"
            
            self.log(f"✅ Successfully built pybind11 for {build_name}")
            
        except Exception as e:
            self.log(f"❌ Failed to build for {build_name}: {e}", "ERROR")
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def build_all(self, profile: str = "fast") -> Dict:
        """Build pybind11 for all Python environments."""
        self.log("="*60)
        self.log("Starting pybind11 build for all environments")
        self.log("="*60)
        
        # First ensure benchlib.so exists
        if not self.ensure_benchlib():
            self.log("❌ Cannot proceed without benchlib.so", "ERROR")
            return {"error": "benchlib.so build failed"}
        
        results = {}
        
        for build_name in self.python_builds:
            result = self.build_for_venv(build_name, profile)
            results[build_name] = result
        
        # Save results
        results_file = self.base_dir / "pybind11_build_results.json"
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
    
    def create_universal_link(self):
        """Create a universal benchlib.so link that works for the current Python."""
        self.log("\nCreating universal benchlib.so link...")
        
        # Find the most recent successful build
        so_files = list(self.pybind11_dir.glob("benchlib_pybind11*.so"))
        if not so_files:
            self.log("❌ No pybind11 .so files found", "ERROR")
            return False
        
        # Sort by modification time and get the most recent
        so_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        latest_so = so_files[0]
        
        # Create link
        universal_so = self.pybind11_dir / "benchlib.so"
        if universal_so.exists():
            universal_so.unlink()
        
        universal_so.symlink_to(latest_so.name)
        self.log(f"✅ Created universal link: benchlib.so -> {latest_so.name}")
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build pybind11 extension for all Python environments"
    )
    parser.add_argument(
        "--profile",
        choices=["fast", "instrumented"],
        default="fast",
        help="Build profile (fast=optimized, instrumented=with frame pointers)"
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
    
    args = parser.parse_args()
    
    builder = Pybind11Builder(args.base_dir)
    
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
        
        # Create universal link
        builder.create_universal_link()
        
        # Exit with error if any build failed
        if any(r.get("status") == "failed" for r in results.values()):
            sys.exit(1)


if __name__ == "__main__":
    main()