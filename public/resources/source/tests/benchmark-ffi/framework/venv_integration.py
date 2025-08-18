#!/usr/bin/env python3
"""
Virtual Environment Integration Module

Provides automatic detection and integration with isolated virtual environments
for benchmark scripts. Works seamlessly with both old and new venv approaches.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, List, Any
import sysconfig

class VenvIntegrator:
    """Handles virtual environment detection and integration."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the venv integrator."""
        if base_dir is None:
            # Detect base directory from current file location
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        self.isolated_venvs_dir = self.base_dir / ".isolated_venvs"
        self.venv_results_file = self.base_dir / "venv_setup_results.json"
        self.legacy_venv = self.base_dir / ".matrix_venv"
        
        # Cache for loaded venv info
        self._venv_info_cache = None
        self._current_build_cache = None
        
    def detect_python_build(self) -> Optional[str]:
        """Detect which Python build is currently running."""
        if self._current_build_cache is not None:
            return self._current_build_cache
        
        # Get current Python executable path
        current_exe = Path(sys.executable).resolve()
        
        # Check if we're already in an isolated venv
        if ".isolated_venvs" in str(current_exe):
            # Extract build name from venv path
            parts = current_exe.parts
            for i, part in enumerate(parts):
                if part == ".isolated_venvs" and i + 1 < len(parts):
                    venv_name = parts[i + 1]
                    if venv_name.startswith("venv_"):
                        build_name = venv_name[5:]  # Remove "venv_" prefix
                        self._current_build_cache = build_name
                        return build_name
        
        # Try to match against known Python builds
        possible_builds = [
            "3.13.5-gil", "3.13.5-nogil",
            "3.14.0rc1-gil", "3.14.0rc1-nogil"
        ]
        
        # Check executable path patterns
        exe_str = str(current_exe)
        for build in possible_builds:
            build_pattern = build.replace(".", "").replace("-", "")
            if build_pattern in exe_str or build in exe_str:
                self._current_build_cache = build
                return build
        
        # Check Python version and GIL status
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        gil_enabled = getattr(sys, '_is_gil_enabled', lambda: True)()
        
        if version.startswith("3.13.5"):
            self._current_build_cache = "3.13.5-gil" if gil_enabled else "3.13.5-nogil"
        elif version.startswith("3.14.0"):
            self._current_build_cache = "3.14.0rc1-gil" if gil_enabled else "3.14.0rc1-nogil"
        else:
            # Unknown build, use generic name
            gil_suffix = "gil" if gil_enabled else "nogil"
            self._current_build_cache = f"{version}-{gil_suffix}"
        
        return self._current_build_cache
    
    def load_venv_info(self) -> Dict[str, Any]:
        """Load virtual environment setup information."""
        if self._venv_info_cache is not None:
            return self._venv_info_cache
        
        if not self.venv_results_file.exists():
            self._venv_info_cache = {}
            return self._venv_info_cache
        
        try:
            with open(self.venv_results_file) as f:
                self._venv_info_cache = json.load(f)
            return self._venv_info_cache
        except Exception:
            self._venv_info_cache = {}
            return self._venv_info_cache
    
    def get_venv_site_packages(self, build_name: str) -> Optional[Path]:
        """Get site-packages directory for a specific build."""
        venv_info = self.load_venv_info()
        
        if build_name not in venv_info or venv_info[build_name]["status"] != "success":
            return None
        
        venv_path = Path(venv_info[build_name]["venv_path"])
        
        if not venv_path.exists():
            return None
        
        # Find site-packages directory
        python_exe = venv_path / "bin" / "python"
        
        if python_exe.exists():
            try:
                # Get site-packages path using the venv's Python
                import subprocess
                result = subprocess.run(
                    [str(python_exe), "-c", "import site; print(site.getsitepackages()[0])"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0:
                    site_packages = Path(result.stdout.strip())
                    if site_packages.exists():
                        return site_packages
            except Exception:
                pass
        
        # Fallback: construct path manually
        possible_paths = [
            venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
            venv_path / "lib64" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def integrate_venv(self, force_build: Optional[str] = None) -> bool:
        """
        Integrate with the appropriate virtual environment.
        
        Args:
            force_build: Force use of specific build (for testing)
        
        Returns:
            True if integration successful, False otherwise
        """
        build_name = force_build or self.detect_python_build()
        
        if not build_name:
            print("⚠️  Could not detect Python build - using system packages")
            return self._fallback_integration()
        
        # Check if we're already in the right venv
        if ".isolated_venvs" in str(sys.executable) and f"venv_{build_name}" in str(sys.executable):
            print(f"✅ Already running in isolated venv for {build_name}")
            return True
        
        # Try to integrate with isolated venv
        site_packages = self.get_venv_site_packages(build_name)
        
        if site_packages:
            # Add to Python path if not already present
            site_packages_str = str(site_packages)
            if site_packages_str not in sys.path:
                sys.path.insert(0, site_packages_str)
                print(f"✅ Integrated with isolated venv: {build_name}")
                print(f"   📁 Site-packages: {site_packages}")
                return True
            else:
                print(f"✅ Already integrated with venv: {build_name}")
                return True
        
        print(f"⚠️  Could not find isolated venv for {build_name}")
        return self._fallback_integration()
    
    def _fallback_integration(self) -> bool:
        """Fallback to legacy shared venv or system packages."""
        # Try legacy shared venv
        if self.legacy_venv.exists():
            legacy_site_packages = self._find_site_packages(self.legacy_venv)
            if legacy_site_packages:
                site_packages_str = str(legacy_site_packages)
                if site_packages_str not in sys.path:
                    sys.path.insert(0, site_packages_str)
                    print("⚠️  Using legacy shared venv")
                    print(f"   📁 Site-packages: {legacy_site_packages}")
                return True
        
        print("⚠️  Using system packages (not recommended for benchmarking)")
        return False
    
    def _find_site_packages(self, venv_path: Path) -> Optional[Path]:
        """Find site-packages directory in a venv."""
        possible_paths = [
            venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
            venv_path / "lib64" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def get_available_builds(self) -> List[str]:
        """Get list of available Python builds with isolated venvs."""
        venv_info = self.load_venv_info()
        
        available = []
        for build_name, info in venv_info.items():
            if info.get("status") == "success":
                available.append(build_name)
        
        return available
    
    def get_python_executable(self, build_name: str) -> Optional[Path]:
        """Get Python executable for a specific build."""
        venv_info = self.load_venv_info()
        
        if build_name not in venv_info or venv_info[build_name]["status"] != "success":
            return None
        
        venv_path = Path(venv_info[build_name]["venv_path"])
        python_exe = venv_path / "bin" / "python"
        
        if python_exe.exists():
            return python_exe
        
        return None
    
    def create_execution_environment(self, build_name: str) -> Dict[str, str]:
        """Create environment variables for isolated execution."""
        env = os.environ.copy()
        
        # Clear Python-related paths for isolation
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONUSERBASE", None)
        
        # Disable user site packages
        env["PYTHONNOUSERSITE"] = "1"
        
        # Set build information
        env["FFI_BENCHMARK_BUILD"] = build_name
        env["FFI_BENCHMARK_VENV_INTEGRATED"] = "true"
        
        return env
    
    def print_integration_status(self):
        """Print current integration status."""
        build_name = self.detect_python_build()
        available_builds = self.get_available_builds()
        
        print("🔧 VIRTUAL ENVIRONMENT INTEGRATION STATUS")
        print("=" * 50)
        print(f"Current Python build: {build_name or 'Unknown'}")
        print(f"Python executable: {sys.executable}")
        print(f"Available isolated venvs: {len(available_builds)}")
        
        for build in available_builds:
            if build == build_name:
                print(f"   ✅ {build} (current)")
            else:
                print(f"   📦 {build}")
        
        # Check current integration
        if ".isolated_venvs" in str(sys.executable):
            print("Status: ✅ Running in isolated virtual environment")
        elif str(self.legacy_venv) in str(sys.path):
            print("Status: ⚠️  Using legacy shared virtual environment")
        else:
            print("Status: ❌ Using system packages")
        print()


# Global integrator instance
_integrator = None

def get_venv_integrator() -> VenvIntegrator:
    """Get global venv integrator instance."""
    global _integrator
    if _integrator is None:
        _integrator = VenvIntegrator()
    return _integrator

def auto_integrate_venv(force_build: Optional[str] = None, quiet: bool = False) -> bool:
    """
    Automatically integrate with appropriate virtual environment.
    
    This should be called at the top of benchmark scripts.
    """
    integrator = get_venv_integrator()
    
    if not quiet:
        integrator.print_integration_status()
    
    return integrator.integrate_venv(force_build)

def get_current_build() -> Optional[str]:
    """Get current Python build name."""
    integrator = get_venv_integrator()
    return integrator.detect_python_build()

def get_available_builds() -> List[str]:
    """Get list of available Python builds."""
    integrator = get_venv_integrator()
    return integrator.get_available_builds()

def get_python_executable(build_name: str) -> Optional[Path]:
    """Get Python executable for specific build."""
    integrator = get_venv_integrator()
    return integrator.get_python_executable(build_name)

def create_isolated_environment(build_name: str) -> Dict[str, str]:
    """Create environment for isolated execution."""
    integrator = get_venv_integrator()
    return integrator.create_execution_environment(build_name)


if __name__ == "__main__":
    # Test the integrator
    integrator = VenvIntegrator()
    integrator.print_integration_status()
    
    print("🧪 Testing integration...")
    success = integrator.integrate_venv()
    
    if success:
        print("✅ Integration test successful")
        
        # Test importing a package that should be in the venv
        try:
            import numpy
            print(f"   NumPy version: {numpy.__version__}")
            print(f"   NumPy location: {numpy.__file__}")
        except ImportError:
            print("   ⚠️  NumPy not available")
    else:
        print("❌ Integration test failed")