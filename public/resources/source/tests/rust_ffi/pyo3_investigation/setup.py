#!/usr/bin/env python3
# setup.py for PyO3 investigation module

from setuptools import setup
from pyo3_setuptools_rust import Pyo3RustExtension, build_rust

# Try pyo3-setuptools-rust first, fallback to setuptools-rust
try:
    from setuptools_rust import RustExtension
    rust_extension_class = RustExtension
except ImportError:
    # Fallback for manual build
    rust_extension_class = None

def build_native():
    """Build the Rust extension using cargo directly"""
    import subprocess
    import sys
    import os
    
    # Build using cargo
    result = subprocess.run([
        "cargo", "build", "--release"
    ], cwd=os.path.dirname(__file__))
    
    if result.returncode != 0:
        sys.exit("Failed to build Rust extension")

if rust_extension_class:
    rust_extensions = [
        RustExtension(
            "pyo3_investigation.pyo3_investigation",
            path="Cargo.toml",
            binding="pyo3",
            debug=False,
        )
    ]
else:
    rust_extensions = []
    # Build manually
    build_native()

setup(
    name="pyo3_investigation",
    version="0.1.0",
    description="PyO3 bug investigation and reproduction",
    author="PyCon Taiwan 2025",
    packages=["pyo3_investigation"],
    rust_extensions=rust_extensions,
    zip_safe=False,
    python_requires=">=3.8",
)