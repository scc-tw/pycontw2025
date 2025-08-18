# Python Matrix FFI Benchmarks - PyCon 2025

Complete benchmarking across Python version matrix with GIL/no-GIL analysis.

## Overview

This framework enables comprehensive FFI performance analysis across:
- **Python Versions**: 3.13.5 & 3.14.0rc1
- **GIL Variants**: GIL enabled & disabled
- **FFI Methods**: ctypes, cffi, pybind11, PyO3

**Target Matrix**: 2×2×4 = 16 configuration combinations

## Required Python Builds

The framework expects these Python builds to be available:

```bash
# Required build structure:
./cpython3.13.5-gil/bin/python3     # Python 3.13.5 with GIL
./cpython3.13.5-nogil/bin/python3   # Python 3.13.5 without GIL  
./cpython3.14.0rc1-gil/bin/python3  # Python 3.14.0rc1 with GIL
./cpython3.14.0rc1-nogil/bin/python3 # Python 3.14.0rc1 without GIL
```

**Build Instructions** (if needed):
```bash
# Python 3.13.5 with --disable-gil
cd cpython3.13.5
./configure --disable-gil --prefix=$(pwd)/../cpython3.13.5-nogil
make -j$(nproc) && make install

# Python 3.13.5 with GIL (standard)
./configure --prefix=$(pwd)/../cpython3.13.5-gil
make -j$(nproc) && make install
```

## Quick Start

### 1. Detect Available Builds
```bash
# Test Python matrix detection
python framework/python_matrix.py

# Expected output:
# 🔍 Detecting Python builds...
#   ✅ Found: 3.13.5-gil at ./cpython3.13.5-gil/bin/python3
#   ✅ Found: 3.13.5-nogil at ./cpython3.13.5-nogil/bin/python3
#   ...
```

### 2. Run Matrix Benchmarks
```bash
# Run comprehensive matrix benchmarks
python scripts/run_matrix_benchmarks.py

# This executes:
# - Detects all available Python builds
# - Runs FFI benchmarks on each build
# - Analyzes GIL impact, version differences, FFI rankings
# - Saves structured results to results/matrix_benchmark_results_*.json
```

### 3. Search and Analyze Results
```bash
# List available results
python scripts/search_matrix_results.py --list

# Generate comprehensive report
python scripts/search_matrix_results.py --report

# Search for GIL impact on specific FFI method
python scripts/search_matrix_results.py --gil-impact --ffi-method pyo3

# Export data to CSV
python scripts/search_matrix_results.py --csv matrix_results.csv
```

## Result Structure

### JSON Output Format
```json
{
  "timestamp": "2025-01-08T12:34:56Z",
  "methodology": "python_version_matrix_ffi_benchmarks",
  "matrix_config": {
    "python_versions": ["3.13.5", "3.14.0rc1"],
    "gil_variants": ["gil", "nogil"],
    "total_builds": 4
  },
  "results": {
    "3.13.5": {
      "gil": {
        "python_executable": "./cpython3.13.5-gil/bin/python3",
        "build_info": {...},
        "benchmark_result": {
          "success": true,
          "stdout": "...",
          "summary": "Benchmark complete"
        }
      },
      "nogil": {...}
    },
    "3.14.0rc1": {...}
  },
  "performance_matrix": {
    "3.13.5": {
      "gil": {
        "ffi_results": {
          "ctypes": {"median_ns": 139.5, "speedup_factor": 1.57},
          "cffi": {"median_ns": 137.5, "speedup_factor": 1.55},
          "pybind11": {"median_ns": 110.5, "speedup_factor": 1.24},
          "pyo3": {"median_ns": 89.0, "speedup_factor": 1.00}
        }
      },
      "nogil": {...}
    }
  },
  "analysis": {
    "gil_impact": {
      "results": {
        "3.13.5": {
          "pyo3": {
            "gil_time_ns": 89.0,
            "nogil_time_ns": 82.5,
            "improvement_percent": 7.3,
            "nogil_speedup": 1.08,
            "interpretation": "Moderate improvement without GIL"
          }
        }
      }
    },
    "version_differences": {...},
    "ffi_method_rankings": {...}
  },
  "execution_summary": {
    "successful_runs": 4,
    "failed_runs": 0,
    "success_rate": "4/4",
    "completion_percentage": 100.0
  }
}
```

## Analysis Capabilities

### 1. GIL Impact Analysis
**Compares GIL vs no-GIL performance for each Python version and FFI method:**

```bash
# Search GIL impact for specific method
python scripts/search_matrix_results.py --gil-impact --ffi-method pyo3

# Example output:
# {
#   "results": {
#     "3.13.5": {
#       "pyo3": {
#         "improvement_percent": 7.3,
#         "interpretation": "Moderate improvement without GIL"
#       }
#     }
#   }
# }
```

**Interpretation Scale:**
- `> 10%`: Significant improvement without GIL
- `2-10%`: Moderate improvement without GIL  
- `-2 to 2%`: Negligible GIL impact
- `-10 to -2%`: Moderate regression without GIL
- `< -10%`: Significant regression without GIL

### 2. Python Version Comparison
**Analyzes performance differences between Python 3.13.5 and 3.14.0rc1:**

```bash
# Compare versions for specific GIL variant
python scripts/search_matrix_results.py --version-diff --gil-variant nogil
```

### 3. FFI Method Rankings
**Ranks FFI methods by performance in each configuration:**

```bash
# Show rankings for specific configuration
python scripts/search_matrix_results.py --ffi-rankings --config "3.13.5-nogil"

# Example ranking:
# 1. pyo3: 82.5ns (1.00x relative, Excellent)
# 2. pybind11: 105.2ns (1.28x relative, Good)
# 3. cffi: 130.1ns (1.58x relative, Fair)
# 4. ctypes: 135.7ns (1.64x relative, Poor)
```

**Performance Ratings:**
- `≤ 1.1x`: Excellent
- `1.1-1.3x`: Good  
- `1.3-1.6x`: Fair
- `> 1.6x`: Poor

### 4. Raw Performance Data Access
**Direct access to timing measurements:**

```bash
# Get raw data for specific configuration
python scripts/search_matrix_results.py --python-version 3.13.5 --gil-variant nogil --ffi-method pyo3
```

## Data Export Options

### CSV Export
```bash
# Export all data to CSV
python scripts/search_matrix_results.py --csv results.csv

# CSV format:
# python_version,gil_variant,ffi_method,median_ns,speedup_factor
# 3.13.5,gil,ctypes,139.5,1.57
# 3.13.5,gil,cffi,137.5,1.55
# ...
```

### Comprehensive Report
```bash
# Generate detailed analysis report
python scripts/search_matrix_results.py --report

# Includes:
# - GIL impact analysis for all methods
# - FFI method rankings by configuration
# - Ranking consistency analysis
# - Performance interpretations
```

## Advanced Usage

### Custom Analysis Scripts
The structured JSON format enables custom analysis:

```python
import json

# Load results
with open("results/matrix_benchmark_results_20250108_123456.json") as f:
    data = json.load(f)

# Analyze GIL impact on PyO3 across versions
for version in data["analysis"]["gil_impact"]["results"]:
    pyo3_data = data["analysis"]["gil_impact"]["results"][version].get("pyo3", {})
    if pyo3_data:
        improvement = pyo3_data["improvement_percent"]
        print(f"Python {version}: PyO3 improves {improvement:.1f}% without GIL")
```

### Integration with Statistical Analysis
```bash
# Combine with existing statistical framework
python scripts/run_statistical_analysis.py --matrix-results results/matrix_benchmark_results_*.json
```

## Troubleshooting

### Missing Python Builds
```bash
# Check build detection
python framework/python_matrix.py

# Expected issues:
# ❌ Missing: 3.13.5-nogil
# Solution: Build Python 3.13.5 with --disable-gil

# ❌ Missing: 3.14.0rc1-gil  
# Solution: Build Python 3.14.0rc1 with standard configuration
```

### Build Path Issues
If builds are in different locations, the detector searches multiple paths:
- `./cpython*/bin/python3` (current directory)
- `../cpython*/bin/python3` (parent directory)  
- Current working directory variants

### Benchmark Execution Failures
```bash
# Check individual build execution
./cpython3.13.5-nogil/bin/python3 scripts/run_all_benchmarks.py

# Common issues:
# - Missing dependencies in specific Python build
# - Incompatible FFI libraries
# - Environment configuration differences
```

## Performance Expectations

### Typical GIL Impact Results
Based on FFI call overhead characteristics:

**Expected Improvements with --disable-gil:**
- **PyO3**: 5-15% (Rust's async-friendly design)
- **pybind11**: 3-10% (C++ template optimizations) 
- **cffi**: 1-5% (C library calls less affected)
- **ctypes**: 0-3% (Already has GIL releases)

**Note**: Results depend on specific operations and system configuration.

## Research Applications

This matrix framework enables research into:

### 1. GIL Impact Quantification
- Measure actual performance impact of GIL on FFI calls
- Compare theoretical vs. measured improvements
- Identify FFI methods that benefit most from --disable-gil

### 2. Python Version Evolution
- Track performance changes between Python versions
- Identify regressions or improvements in FFI subsystems
- Evaluate readiness of new Python releases

### 3. FFI Method Selection
- Data-driven FFI method selection based on use case
- Performance/complexity trade-off analysis
- Cross-configuration consistency evaluation

## Conference Presentation Integration

Results from this framework directly support PyCon 2025 presentation sections:

### Python 3.13 --disable-gil Analysis (6 min section)
- **Quantified GIL impact** across FFI methods
- **Real performance measurements** vs. theoretical expectations
- **Practical implications** for FFI-heavy applications

### Cross-language Integration (11 min section)  
- **Comprehensive FFI comparison** with statistical rigor
- **Performance hierarchy** validation with hardware metrics
- **Method selection guidance** based on empirical evidence

The structured output format ensures all claims in the presentation are backed by reproducible, searchable evidence.