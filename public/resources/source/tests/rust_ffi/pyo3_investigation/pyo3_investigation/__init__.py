# pyo3_investigation/__init__.py
# Python package initialization for PyO3 investigation module

# Try to import the Rust extension
try:
    from .pyo3_investigation import *
except ImportError:
    # Fallback: try to import from built library
    import ctypes
    import sys
    import os
    from pathlib import Path
    
    # Find the built library
    lib_dir = Path(__file__).parent.parent / "target" / "release"
    lib_paths = [
        lib_dir / "libpyo3_investigation.dylib",
        lib_dir / "libpyo3_investigation.so",
    ]
    
    for lib_path in lib_paths:
        if lib_path.exists():
            # Load as ctypes library for basic functionality
            _lib = ctypes.CDLL(str(lib_path))
            break
    else:
        raise ImportError("PyO3 investigation module not built properly")

__version__ = "0.1.0"