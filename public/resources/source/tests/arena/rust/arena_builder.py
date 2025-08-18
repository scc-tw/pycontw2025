#!/usr/bin/env python3
"""
Arena Builder - Build management functionality for Arena extensions.

This module handles building, cleaning, and managing Rust extensions
across multiple Python environments using maturin.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from arena_manager import ArenaManager

class ArenaBuilder(ArenaManager):
    """Manages Arena PyO3 extension building across multiple environments."""
    
    def __init__(self, base_dir: Path):
        super().__init__(base_dir)
        self.log_file = self.base_dir / "arena_build.log"
        self.results_file = self.base_dir / "arena_build_results.json"
        self._building = False
        
    def log(self, message: str, level: str = "INFO", timestamp: bool = True):
        """Log messages with timestamp and file logging during builds."""
        log_entry = super().log(message, level, timestamp)
        
        # Only write to log file if it's a build operation
        if self._building:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
    
    def clean_build_artifacts(self):
        """Clean previous build artifacts."""
        self.log("Cleaning build artifacts...")
        
        # Clean Rust target directory
        target_dir = self.arena_dir / "target"
        if target_dir.exists():
            shutil.rmtree(target_dir)
            self.log(f"  Removed: {target_dir}")
        
        # Clean Python build directories
        for dir_name in ["build", "dist", "*.egg-info", "__pycache__"]:
            for path in self.arena_dir.glob(dir_name):
                if path.is_dir():
                    shutil.rmtree(path)
                    self.log(f"  Removed: {path}")
        
        # Clean .so files
        for so_file in self.arena_dir.glob("*.so"):
            if not so_file.is_symlink():
                so_file.unlink()
                self.log(f"  Removed: {so_file}")
                
        # Clean log and results files
        if self.log_file.exists():
            self.log_file.unlink()
            print(f"Removed: {self.log_file}")
        if self.results_file.exists():
            self.results_file.unlink()
            print(f"Removed: {self.results_file}")
    
    def build_for_python(self, build_name: str, profile: str = "release") -> Dict:
        """Build Arena extension for a specific Python environment."""
        self.log(f"\n{'='*60}")
        self.log(f"Building Arena for {build_name} (profile: {profile})")
        self.log(f"{'='*60}")
        
        result = {
            "build": build_name,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get Python executable
        python_path = self.get_python_executable(build_name)
        if not python_path:
            self.log(f"❌ Python not found for {build_name}", "ERROR")
            result["status"] = "failed"
            result["error"] = "Python executable not found"
            return result
        
        self.log(f"Found Python: {python_path}")
        
        # Ensure maturin is available
        if not self.install_package_if_needed(python_path, "maturin"):
            self.log(f"❌ maturin not available for {build_name}", "ERROR")
            result["status"] = "failed"
            result["error"] = "maturin not available"
            return result
        
        try:
            # Set environment
            env = self.setup_environment(build_name)
            
            # Set Rust flags for instrumented profile
            if profile == "instrumented":
                env["RUSTFLAGS"] = "-C force-frame-pointers=yes"
            
            # Build the extension using maturin
            self.log(f"Building extension with maturin and {python_path}...")
            
            # Use maturin develop to build and install directly
            build_result = self.run_command(
                [str(python_path), "-m", "maturin", "develop", "--release"],
                cwd=self.arena_dir,
                env=env,
                verbose=True
            )
            
            # Find the installed module location
            module_name = "glibc_arena_poc"  # From Cargo.toml
            
            # Try to find the installed .so file
            try:
                import_result = self.run_command(
                    [str(python_path), "-c", 
                     f"import {module_name}; import os; print(os.path.dirname({module_name}.__file__))"],
                    cwd=self.arena_dir,
                    env=env,
                    verbose=False
                )
                
                if import_result.returncode == 0:
                    install_dir = import_result.stdout.strip()
                    self.log(f"✅ Module installed at: {install_dir}")
                    
                    # Copy to arena directory for consistency
                    installed_files = list(Path(install_dir).glob(f"{module_name}*.so"))
                    if installed_files:
                        build_so_name = f"{module_name}_{build_name.replace('.', '_').replace('-', '_')}.so"
                        build_so_path = self.arena_dir / build_so_name
                        shutil.copy2(installed_files[0], build_so_path)
                        self.log(f"✅ Created build-specific copy: {build_so_name}")
                        result["so_file"] = str(build_so_path)
                    else:
                        result["so_file"] = f"installed in {install_dir}"
                
            except Exception as e:
                self.log(f"⚠️ Could not locate installed module: {e}")
                result["so_file"] = "installed via maturin"
            
            # Test import and basic functionality
            self.log("Testing import and basic functionality...")
            test_result = self.run_command(
                [str(python_path), "-c", 
                 f"import {module_name}; "
                 f"print(f'RSS: {{glibc_arena_poc.get_rss_mib():.1f}} MiB'); "
                 f"config = {module_name}.get_config(); "
                 f"print(f'Alloc size: {{config[\"alloc_size_mib\"]:.2f}} MiB'); "
                 f"print('Import and basic functionality test successful')"],
                cwd=self.arena_dir,
                env=env,
                verbose=False
            )
            
            result["status"] = "success"
            result["import_test"] = "passed"
            result["functionality_test"] = "passed"
            
            self.log(f"✅ Successfully built Arena for {build_name}")
            
        except Exception as e:
            self.log(f"❌ Failed to build for {build_name}: {e}", "ERROR")
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def build_all(self, profile: str = "release", specific_build: Optional[str] = None) -> Dict:
        """Build Arena for all or specific Python environments."""
        self._building = True
        
        self.log("="*60)
        if specific_build:
            self.log(f"Starting Arena build for {specific_build}")
        else:
            self.log("Starting Arena build for all environments")
        self.log("="*60)
        
        results = {}
        builds_to_process = [specific_build] if specific_build else self.python_builds
        
        for build_name in builds_to_process:
            if not self.validate_build_name(build_name):
                print(f"❌ Unknown build: {build_name}")
                print(f"Available: {', '.join(self.python_builds)}")
                continue
                
            result = self.build_for_python(build_name, profile)
            results[build_name] = result
        
        # Save results
        with open(self.results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        self.log(f"\n📊 Results saved to: {self.results_file}")
        
        # Print summary
        self.print_build_summary(results)
        
        self._building = False
        return results
    
    def print_build_summary(self, results: Dict):
        """Print build summary."""
        self.log("\n" + "="*60)
        self.log("ARENA BUILD SUMMARY")
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
                    so_info = result.get('so_file', 'N/A')
                    self.log(f"   • {build}: {so_info}")
        
        if failed > 0:
            self.log("\n❌ Failed builds:")
            for build, result in results.items():
                if result.get("status") == "failed":
                    self.log(f"   • {build}: {result.get('error', 'Unknown error')}")
    
    def get_build_results(self) -> Optional[Dict]:
        """Load and return build results."""
        if not self.results_file.exists():
            return None
        
        try:
            with open(self.results_file) as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Failed to load build results: {e}", "ERROR")
            return None
    
    def get_build_status(self) -> Dict[str, str]:
        """Get build status for all Python environments."""
        results = self.get_build_results()
        if not results:
            return {build: "not_built" for build in self.python_builds}
        
        status = {}
        for build in self.python_builds:
            if build in results:
                status[build] = results[build].get("status", "unknown")
            else:
                status[build] = "not_built"
        
        return status
