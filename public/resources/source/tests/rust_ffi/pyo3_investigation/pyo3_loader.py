#!/usr/bin/env python3
# pyo3_loader.py - Simple loader for PyO3 investigation module

import ctypes
import sys
import os
from pathlib import Path

def load_pyo3_module():
    """Load the PyO3 investigation module manually with platform auto-detection"""
    import platform
    import shutil
    
    # Auto-detect platform extension
    system = platform.system().lower()
    if system == "darwin":  # macOS
        lib_extensions = [".dylib"]
        python_ext = ".so"  # Python expects .so even on macOS
    elif system == "linux":
        lib_extensions = [".so"]
        python_ext = ".so"
    elif system == "windows":
        lib_extensions = [".dll"]
        python_ext = ".pyd"
    else:
        lib_extensions = [".dylib", ".so", ".dll"]
        python_ext = ".so"
    
    # Find the built library with platform detection
    base_dir = Path(__file__).parent
    search_paths = [
        base_dir / "target" / "release",
        base_dir / "target" / "debug",
    ]
    
    lib_path = None
    for search_dir in search_paths:
        if not search_dir.exists():
            continue
        for ext in lib_extensions:
            candidate = search_dir / f"libpyo3_investigation{ext}"
            if candidate.exists():
                lib_path = candidate
                break
        if lib_path:
            break
    
    if not lib_path:
        searched = [f"{search_dir}/libpyo3_investigation{ext}" for search_dir in search_paths for ext in lib_extensions]
        raise ImportError(f"PyO3 investigation library not found. Searched: {searched}")
    
    # Create a Python importable file with correct extension
    import_name = f"pyo3_investigation{python_ext}"
    import_path = base_dir / import_name
    
    # Copy the library to the import path
    shutil.copy2(str(lib_path), str(import_path))
    
    # Add current directory to path
    sys.path.insert(0, str(base_dir))
    
    try:
        # Import the module (remove extension for import)
        module_name = import_name.split('.')[0]
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, import_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        # Clean up
        if import_path.exists():
            import_path.unlink()
        raise ImportError(f"Failed to import PyO3 module: {e}")

if __name__ == "__main__":
    # Test the loader
    try:
        module = load_pyo3_module()
        print(f"Successfully loaded PyO3 module: {module}")
        print(f"Available attributes: {[attr for attr in dir(module) if not attr.startswith('_')]}")
        
        # Test basic functionality
        if hasattr(module, 'pyo3_function_call_test'):
            result = module.pyo3_function_call_test()
            print(f"Basic function test: {result}")
        else:
            print("pyo3_function_call_test not available")
            
    except Exception as e:
        print(f"Failed to load PyO3 module: {e}")