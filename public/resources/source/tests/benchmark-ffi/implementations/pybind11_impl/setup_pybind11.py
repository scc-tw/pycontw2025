"""
Setup script for building pybind11 extension

This script builds the pybind11 extension module that wraps the benchlib
C library for performance comparison with ctypes and cffi.
"""

import os
import sys
from pathlib import Path
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup, Extension
import pybind11

def get_profile_flags():
    """Get compilation flags based on PROFILE environment variable"""
    profile = os.environ.get('PROFILE', 'fast')
    
    # Base flags for all builds
    base_flags = [
        "-O3", "-march=native", "-mtune=native", 
        "-Wall", "-Wextra", "-g1",
    ]
    
    if profile == 'fast':
        # Maximum performance: no frame pointers (default behavior)
        return base_flags
    elif profile == 'instrumented':
        # Instrumented: add frame pointers for reliable profiling
        return base_flags + ["-fno-omit-frame-pointer"]
    else:
        print(f"Warning: Unknown PROFILE '{profile}', using 'fast'")
        return base_flags

# Get the directory containing this script
script_dir = Path(__file__).parent
lib_dir = script_dir.parent.parent / "lib"  # lib directory contains benchlib.c

# Find the compiled benchlib shared library
benchlib_so = None
for lib_name in ['benchlib.so', 'benchlib.dylib', 'benchlib.dll']:
    lib_path = lib_dir / lib_name
    if lib_path.exists():
        benchlib_so = str(lib_path)
        break

if not benchlib_so:
    print("❌ Error: benchlib shared library not found!")
    print("   Please run 'make' in the parent directory first.")
    sys.exit(1)

print(f"✅ Found benchlib: {benchlib_so}")

# Define the pybind11 extension
ext_modules = [
    Pybind11Extension(
        "benchlib_pybind11",
        sources=[
            str(script_dir / "pybind11_wrapper.cpp"),
            str(lib_dir / "benchlib.c")  # Include source directly
        ],
        include_dirs=[
            pybind11.get_cmake_dir(),
            str(lib_dir),  # For benchlib.h if it exists
        ],
        libraries=["m"],  # Link math library
        define_macros=[
            ("VERSION_INFO", '"0.1.0"'),
        ],
        cxx_std=20,
        # Profile-aware optimization flags
        extra_compile_args=get_profile_flags(),
        language="c++"
    ),
]

setup(
    name="benchlib_pybind11",
    version="0.1.0",
    author="FFI Benchmark Suite",
    description="pybind11 bindings for FFI benchmark library",
    long_description="Provides pybind11 bindings for the FFI benchmark C library to enable performance comparison with ctypes and cffi implementations.",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        "pybind11>=2.6.0",
        "numpy"
    ],
)