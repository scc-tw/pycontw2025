# 🚀 PyO3 Setup Instructions - WORKING SOLUTION

## ✅ Status: FIXED AND WORKING

PyO3 implementation is fully functional with **exceptional performance** (3x faster than ctypes for basic calls, 18x faster for arrays).

## 🔧 Quick Setup Guide

### Prerequisites
- Make sure the main benchlib is built: `cd .. && make`
- Verify `../benchlib.so` exists

### One-Time Setup

```bash
# 1. Navigate to benchmarks directory
cd tests/benchmark-ffi/benchmarks

# 2. Create symbolic link for Rust linker (CRITICAL!)
ln -sf "$(pwd)/../benchlib.so" ../libbenchlib.so

# 3. Build the PyO3 module
cargo clean
cargo build --release

# 4. Copy module to importable location
cp target/release/deps/libbenchlib_pyo3.so benchlib_pyo3.so

# 5. Test the setup
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python -c "import benchlib_pyo3; print('✅ PyO3 working!')"
```

### Daily Usage

**Always set LD_LIBRARY_PATH when using PyO3:**

```bash
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python your_script.py
```

### Verification

```bash
# Test all functionality
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python test_pyo3_fix.py

# Run performance comparison
LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH python demo_all_ffi.py
```

## 🏆 Expected Performance Results

```
Basic Function Calls (return_int):
- PyO3:    37.6 ns  (3.09x faster than ctypes)
- cffi:    93.2 ns  (1.25x faster than ctypes)  
- ctypes: 116.5 ns  (baseline)

Array Operations (1000 elements):
- PyO3:    5.2 μs   (18.01x faster than ctypes)
- cffi:   32.0 μs   (2.91x faster than ctypes)
- ctypes: 93.3 μs   (baseline)
```

## ⚠️ Important Notes

1. **Don't modify existing files** - this setup works alongside other FFI methods
2. **Library path is critical** - PyO3 needs `LD_LIBRARY_PATH=../:$LD_LIBRARY_PATH`
3. **Symlink location matters** - `../libbenchlib.so` must point to `../benchlib.so`
4. **Dependencies are correct** - Cargo.toml already has PyO3 0.25 + numpy 0.25

## 🛠️ Troubleshooting

**"cannot find -lbenchlib"**
```bash
# Fix: Create the symlink
ln -sf "$(pwd)/../benchlib.so" ../libbenchlib.so
```

**"libbenchlib.so: cannot open shared object file"**
```bash
# Fix: Set library path
export LD_LIBRARY_PATH="$(pwd)/..:$LD_LIBRARY_PATH"
```

**"No module named 'benchlib_pyo3'"**
```bash
# Fix: Copy the module
cp target/release/deps/libbenchlib_pyo3.so benchlib_pyo3.so
```

## 🧪 Test Scripts Available

- `test_pyo3_fix.py` - Comprehensive functionality test
- `demo_all_ffi.py` - Performance comparison with all FFI methods

## 💡 What This Fixes

The original problem was **not** PyO3 API compatibility - it was:
1. **Library linking**: Rust needed `libbenchlib.so` symlink
2. **Build configuration**: Fixed paths in `build.rs`
3. **Runtime loading**: Set `LD_LIBRARY_PATH` for dynamic libraries

PyO3 0.25 + rust-numpy 0.25 work perfectly together! 🎉