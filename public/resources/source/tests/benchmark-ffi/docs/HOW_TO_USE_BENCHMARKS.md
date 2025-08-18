# 🚀 FFI Benchmarks - Complete User Guide

## Overview

This benchmarking suite provides comprehensive performance analysis of **4 Foreign Function Interface (FFI) methods** for Python:

- **ctypes** - Python's built-in FFI
- **cffi** - C Foreign Function Interface (ABI + API modes)  
- **pybind11** - C++ binding library
- **PyO3** - Rust binding library

## ✅ Current Status: ALL 4 FFI METHODS WORKING

```
🏆 Performance Ranking (Basic Calls):
1. PyO3:     ~37 ns  (3x faster than ctypes)
2. pybind11: ~53 ns  (2x faster than ctypes)
3. cffi:     ~94 ns  (1.1x faster than ctypes)
4. ctypes:   ~104 ns (baseline)

🏆 Performance Ranking (Array Operations):
1. PyO3:     ~5 μs   (18x faster than ctypes!)
2. pybind11: ~15 μs  (6x faster than ctypes)
3. cffi:     ~32 μs  (3x faster than ctypes)
4. ctypes:   ~94 μs  (baseline)
```

## 🔧 Prerequisites & Setup

### 1. Build the Core Library
```bash
# From project root
cd tests/benchmark-ffi
make
```

### 2. Install Python Dependencies
```bash
pip install numpy scipy psutil cffi
```

### 3. One-Time PyO3 Setup
```bash
cd tests/benchmark-ffi/benchmarks

# Create symbolic link for Rust linker
ln -sf "$(pwd)/../benchlib.so" ../libbenchlib.so

# Build PyO3 module
cargo build --release
cp target/release/deps/libbenchlib_pyo3.so benchlib_pyo3.so
```

### 4. Optional: pybind11 Setup
```bash
# If pybind11 benchmarks aren't working
python setup_pybind11.py build_ext --inplace
```

## 🎯 How to Use the Benchmarks

### Quick Performance Comparison (Recommended)
```bash
cd tests/benchmark-ffi/benchmarks
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python demo_all_ffi.py
```

**Expected Output:**
```
🚀 All FFI Methods Performance Comparison
✅ ctypes loaded
✅ cffi loaded  
✅ pybind11 loaded
✅ PyO3 loaded

📊 Successfully loaded 4 FFI implementations

All FFI Methods Performance Comparison
======================================
Rank   Implementation       Median Time     95% CI                    Relative  
1      pyo3                 36.5 ns         [36.4 ns, 36.5 ns]        2.83x     
2      pybind11             53.2 ns         [53.1 ns, 53.2 ns]        1.94x     
3      cffi                 93.9 ns         [93.8 ns, 94.0 ns]        1.10x     
4      ctypes               103.4 ns        [103.3 ns, 103.5 ns]      1.00x     
```

### Validate Implementation Correctness
```bash
# Test ctypes + cffi consistency
cd tests/benchmark-ffi
python validation.py

# Test PyO3 functionality (comprehensive)
cd benchmarks  
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python test_pyo3_fix.py
```

### Individual FFI Method Testing
```bash
cd tests/benchmark-ffi/benchmarks

# Test ctypes
python -c "from ctypes_bench import create_ctypes_benchmark; b = create_ctypes_benchmark(); print('return_int:', b.return_int())"

# Test cffi
python -c "from cffi_bench import create_cffi_benchmark; b = create_cffi_benchmark(); print('return_int:', b.return_int())"

# Test pybind11
python -c "from pybind11_bench import Pybind11Benchmark; b = Pybind11Benchmark(); print('return_int:', b.lib.return_int())"

# Test PyO3 (needs library path)
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python -c "from pyo3_bench import PyO3Benchmark; b = PyO3Benchmark(); print('return_int:', b.lib.py_return_int())"
```

### Advanced Performance Analysis
```bash
# Full benchmark suite with environment validation
cd tests/benchmark-ffi
LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH python run_phase1_demo.py
```

## 📊 Understanding the Results

### Performance Metrics
- **Median Time**: Middle value of timing measurements (more robust than average)
- **95% CI**: 95% confidence interval showing measurement precision
- **Relative**: Performance compared to baseline (ctypes)
- **Speedup**: How many times faster than the slowest method

### What Each Test Measures
1. **Basic Function Calls**: Simple C function invocation overhead
2. **Array Operations**: NumPy array processing (1000 elements)
3. **Integer Operations**: 32-bit and 64-bit integer arithmetic
4. **String Operations**: Text processing and encoding
5. **Structure Operations**: Complex data type handling
6. **Callback Operations**: Python→C→Python function calls

### Performance Insights
- **PyO3 (Rust)**: Best for compute-intensive operations, excellent array performance
- **pybind11 (C++)**: Good balance of performance and ease of use
- **cffi**: Better than ctypes, especially for array operations
- **ctypes**: Most compatible but slowest performance

## 🗂️ Available Scripts & Tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `demo_all_ffi.py` | **Quick performance comparison** | `LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python demo_all_ffi.py` |
| `validation.py` | Correctness validation (ctypes + cffi) | `python validation.py` |
| `test_pyo3_fix.py` | PyO3 comprehensive testing | `LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python test_pyo3_fix.py` |
| `run_phase1_demo.py` | Full benchmark suite + environment | `LD_LIBRARY_PATH=.:$LD_LIBRARY_PATH python run_phase1_demo.py` |
| `ctypes_bench.py` | ctypes individual benchmarks | `python -m ctypes_bench` |
| `cffi_bench.py` | cffi individual benchmarks | `python -m cffi_bench` |
| `pybind11_bench.py` | pybind11 individual benchmarks | `python -m pybind11_bench` |
| `pyo3_bench.py` | PyO3 individual benchmarks | `LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python -m pyo3_bench` |

## ⚠️ Important Notes

### PyO3 Requirements
**Always set library path for PyO3:**
```bash
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python your_script.py
```

### Environment for Best Results
```bash
# Optional: Set performance governor for consistent results
sudo cpupower frequency-set -g performance

# Reduce background noise
sudo sysctl kernel.perf_event_paranoid=1
```

### Expected Function Counts
- **ctypes**: ~20 functions
- **cffi**: ~20 functions  
- **pybind11**: ~28 functions
- **PyO3**: ~55 functions (most comprehensive)

## 🐛 Troubleshooting

### "No module named 'benchlib_pyo3'"
```bash
cd tests/benchmark-ffi/benchmarks
cargo build --release
cp target/release/deps/libbenchlib_pyo3.so benchlib_pyo3.so
```

### "cannot find -lbenchlib"  
```bash
ln -sf "$(pwd)/../benchlib.so" ../libbenchlib.so
```

### "libbenchlib.so: cannot open shared object file"
```bash
export LD_LIBRARY_PATH="$(pwd)/..:$LD_LIBRARY_PATH"
```

### "pybind11 benchmark library not available"
```bash
python setup_pybind11.py build_ext --inplace
```

### "Unable to find benchlib shared library"
```bash
cd tests/benchmark-ffi
make clean && make
```

## 🎓 Academic/Research Usage

### For Conference Presentations
1. **Quick Demo**: Use `demo_all_ffi.py` (30-second results)
2. **Detailed Analysis**: Use `run_phase1_demo.py` (comprehensive)
3. **Validation**: Always run `validation.py` to prove correctness

### For Research Papers
- **Statistical Rigor**: Framework uses n≥30 samples, bootstrap CIs, Mann-Whitney U tests
- **Reproducibility**: All results include confidence intervals and environment info
- **Fair Comparison**: All methods call identical C functions

### Customizing Benchmarks
```python
from framework.timer import BenchmarkTimer
from ctypes_bench import create_ctypes_benchmark
from pyo3_bench import PyO3Benchmark

# Create custom benchmark
timer = BenchmarkTimer(target_relative_error=0.02, max_time_seconds=30)
ctypes_bench = create_ctypes_benchmark()
pyo3_bench = PyO3Benchmark()

# Compare custom operations
implementations = {
    'ctypes': lambda: your_ctypes_function(),
    'pyo3': lambda: your_pyo3_function(),
}

results = timer.compare_implementations(implementations)
```

## 🎉 Expected Results Summary

When everything is working correctly, you should see:

✅ **All 4 FFI methods load successfully**  
✅ **PyO3 shows best performance** (2-18x speedup)  
✅ **Validation tests pass** (identical results across methods)  
✅ **Comprehensive function coverage** (55 PyO3 functions total)  
✅ **Statistical confidence intervals** on all measurements  

**Happy benchmarking!** 🚀

---

## 📚 Additional Resources

- **Setup Details**: `PyO3_SETUP_INSTRUCTIONS.md`
- **PyO3 Issues**: `pyo3_compatibility_notes.md` 
- **Academic Review**: `../review.md`
- **Environment Setup**: `../ENVIRONMENT_SETUP.md`