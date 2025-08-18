#!/usr/bin/env python3
"""
Arena Manager - Core management functionality for Python environments and utilities.

This module provides the base functionality for managing Python environments,
executing commands, and handling common operations across all arena tools.
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union

class ArenaManager:
    """Core manager for Arena extension operations."""
    
    def __init__(self, base_dir: Union[str, Path]):
        self.base_dir = Path(base_dir)
        # Look for both benchmark-ffi style venvs and direct Python installs
        self.venv_base = self.base_dir.parent.parent / "benchmark-ffi" / ".isolated_venvs"
        self.arena_dir = self.base_dir  # Current directory contains the Rust project
        
        # Python builds to target - check both venv and direct installs
        self.python_builds = [
            "3.13.5-gil",
            "3.13.5-nogil", 
            "3.14.0rc1-gil",
            "3.14.0rc1-nogil",
        ]
        
        # Root directory for direct Python installs
        self.python_installs = self.base_dir.parent.parent.parent
        
    def log(self, message: str, level: str = "INFO", timestamp: bool = True):
        """Log messages with optional timestamp."""
        if timestamp:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{ts}] [{level}] {message}"
        else:
            log_entry = f"[{level}] {message}"
        print(log_entry)
        return log_entry
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None,
                   env: Optional[Dict] = None, check: bool = True, 
                   capture_output: bool = True, verbose: bool = False) -> subprocess.CompletedProcess:
        """Run command with proper error handling."""
        if verbose:
            self.log(f"Running: {' '.join(cmd)}")
            if cwd:
                self.log(f"  in directory: {cwd}")
        
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=cwd,
            env=env or os.environ.copy(),
            check=False
        )
        
        if result.returncode != 0:
            if verbose:
                self.log(f"Command output: {result.stdout}", "DEBUG")
                self.log(f"Command stderr: {result.stderr}", "ERROR")
            if check:
                raise RuntimeError(f"Command failed: {' '.join(cmd)}")
            
        return result
    
    def get_python_executable(self, build_name: str) -> Optional[Path]:
        """Get Python executable for a specific build (try venv first, then direct install)."""
        # Try venv first
        if self.venv_base.exists():
            venv_path = self.venv_base / f"venv_{build_name}"
            python_path = venv_path / "bin" / "python"
            if python_path.exists():
                return python_path
        
        # Try direct install
        if "nogil" in build_name:
            # For nogil builds, try the 't' suffix version first
            version = build_name.split('-')[0]  # e.g., "3.13.5" from "3.13.5-nogil"
            major_minor = '.'.join(version.split('.')[:2])  # e.g., "3.13"
            direct_path = self.python_installs / f"cpython{build_name}" / "bin" / f"python{major_minor}t"
            if direct_path.exists():
                return direct_path
            # Fallback to regular python executable
            direct_path = self.python_installs / f"cpython{build_name}" / "bin" / f"python{major_minor}"
            if direct_path.exists():
                return direct_path
        else:
            # For GIL builds
            version = build_name.split('-')[0]
            major_minor = '.'.join(version.split('.')[:2])
            direct_path = self.python_installs / f"cpython{build_name}" / "bin" / f"python{major_minor}"
            if direct_path.exists():
                return direct_path
        
        return None
    
    def get_venv_path(self, build_name: str) -> Optional[Path]:
        """Get virtual environment path for a specific build."""
        if self.venv_base.exists():
            venv_path = self.venv_base / f"venv_{build_name}"
            if venv_path.exists():
                return venv_path
        return None
    
    def setup_environment(self, build_name: str, base_env: Optional[Dict] = None) -> Dict[str, str]:
        """Set up environment variables for a specific Python build."""
        env = dict(base_env or os.environ.copy())
        
        # Set virtual environment if using venv
        venv_path = self.get_venv_path(build_name)
        if venv_path:
            env["VIRTUAL_ENV"] = str(venv_path)
            env["PATH"] = f"{venv_path / 'bin'}:{env.get('PATH', '')}"
        
        return env
    
    def validate_build_name(self, build_name: str) -> bool:
        """Validate that a build name is supported."""
        return build_name in self.python_builds
    
    def get_available_builds(self) -> List[str]:
        """Get list of available Python builds with their status."""
        available = []
        for build_name in self.python_builds:
            python_path = self.get_python_executable(build_name)
            if python_path:
                available.append(build_name)
        return available
    
    def check_python_availability(self) -> Dict[str, bool]:
        """Check which Python builds are available."""
        status = {}
        for build_name in self.python_builds:
            python_path = self.get_python_executable(build_name)
            status[build_name] = python_path is not None
        return status
    
    def get_module_info(self, build_name: str, module_name: str = "glibc_arena_poc") -> Optional[Dict]:
        """Get information about an installed module in a specific Python build."""
        python_path = self.get_python_executable(build_name)
        if not python_path:
            return None
        
        try:
            env = self.setup_environment(build_name)
            result = self.run_command(
                [str(python_path), "-c", 
                 f"import {module_name}; import os; "
                 f"print(os.path.dirname({module_name}.__file__)); "
                 f"print({module_name}.__version__ if hasattr({module_name}, '__version__') else 'unknown')"],
                env=env,
                check=False,
                verbose=False
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                return {
                    "installed": True,
                    "path": lines[0] if lines else None,
                    "version": lines[1] if len(lines) > 1 else "unknown"
                }
        except Exception:
            pass
        
        return {"installed": False, "path": None, "version": None}
    
    def install_package_if_needed(self, python_path: Path, package_name: str, 
                                 check_import: Optional[str] = None) -> bool:
        """Install a package in the Python environment if not available."""
        check_name = check_import or package_name
        
        try:
            # Check if package is available
            result = self.run_command(
                [str(python_path), "-c", f"import {check_name}"],
                check=False,
                verbose=False
            )
            if result.returncode == 0:
                return True
            
            # Install package
            self.log(f"Installing {package_name} for {python_path}")
            result = self.run_command(
                [str(python_path), "-m", "pip", "install", package_name],
                check=True,
                verbose=True
            )
            return True
        except Exception as e:
            self.log(f"Failed to install {package_name}: {e}", "ERROR")
            return False
