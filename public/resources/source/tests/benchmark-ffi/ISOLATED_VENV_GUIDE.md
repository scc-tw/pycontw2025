# Isolated Virtual Environment Guide for FFI Benchmarking

## Overview

This guide explains the professional isolated virtual environment strategy that replaces the problematic shared venv approach. Each Python build now gets its own completely isolated environment with the latest package versions.

## Why Isolated Environments?

The previous shared venv approach had several critical issues:

1. **Version Conflicts**: Different Python builds might require different package versions
2. **Contamination**: System packages could leak into test environments
3. **Non-reproducible**: Results varied based on system state
4. **Maintenance Issues**: Hard to track which packages belong to which Python version

## Architecture

```
benchmark-ffi/
├── .isolated_venvs/               # Isolated virtual environments
│   ├── venv_3.13.5-gil/          # Python 3.13.5 with GIL
│   ├── venv_3.13.5-nogil/        # Python 3.13.5 without GIL
│   ├── venv_3.14.0rc1-gil/       # Python 3.14.0rc1 with GIL
│   └── venv_3.14.0rc1-nogil/     # Python 3.14.0rc1 without GIL
├── requirements/                  # Locked dependency versions
│   ├── requirements_3.13.5-gil.txt
│   ├── requirements_3.13.5-gil.hash
│   └── ...
└── scripts/
    ├── setup_isolated_venvs.py    # Main setup script
    ├── run_with_venv.py          # Execution wrapper
    └── venv_config.yaml          # Configuration
```

## Setup Instructions

### 1. Initial Setup

First, ensure all Python builds are compiled:

```bash
# Build Python versions if not already done
cd /path/to/pycon2025-ffi-hidden-corner
make all  # Builds all Python versions
```

### 2. Create Isolated Environments

Run the setup script to create isolated venvs for each Python build:

```bash
cd tests/benchmark-ffi
python scripts/setup_isolated_venvs.py
```

This will:
- Create separate venv for each Python build
- Install latest versions of all dependencies
- Generate locked requirements files
- Verify all installations

### 3. Verify Setup

Check the setup results:

```bash
cat venv_setup_results.json
```

## Running Benchmarks

### Method 1: Using the Runner Script (Recommended)

```bash
# Run on all Python builds
python scripts/run_with_venv.py scripts/demo_all_ffi.py

# Run on specific build
python scripts/run_with_venv.py scripts/demo_all_ffi.py --build 3.13.5-nogil

# Verify packages before running
python scripts/run_with_venv.py scripts/demo_all_ffi.py --verify

# Pass arguments to benchmark script
python scripts/run_with_venv.py scripts/run_all_benchmarks.py -- --iterations 1000
```

### Method 2: Manual Activation

```bash
# Activate specific venv
source .isolated_venvs/venv_3.13.5-gil/bin/activate

# Run benchmark
python scripts/demo_all_ffi.py

# Deactivate when done
deactivate
```

### Method 3: Direct Execution

```bash
# Use Python from specific venv directly
.isolated_venvs/venv_3.13.5-gil/bin/python scripts/demo_all_ffi.py
```

## Maintenance

### Update All Environments

```bash
# Re-run setup to update all packages to latest versions
python scripts/setup_isolated_venvs.py
```

### Clean Up

```bash
# Remove all virtual environments
python scripts/setup_isolated_venvs.py --cleanup
```

### Check Package Versions

```bash
# List packages in specific environment
.isolated_venvs/venv_3.13.5-gil/bin/pip list
```

## Integration with Benchmarking Scripts

Update your benchmark scripts to use the runner:

```python
# In your benchmark script
import subprocess
import sys

# Run benchmark on all builds
subprocess.run([
    sys.executable, 
    "scripts/run_with_venv.py",
    "path/to/benchmark.py"
])
```

## Reproducibility

Each setup generates:
- `requirements_<build>.txt`: Exact package versions
- `requirements_<build>.hash`: Verification hash
- `venv_setup_results.json`: Complete setup metadata

To reproduce exact environment:

```bash
# Create venv
python3.13 -m venv test_env

# Install exact versions
pip install -r requirements/requirements_3.13.5-gil.txt
```

## Troubleshooting

### "Virtual environments not set up" Error
Run `python scripts/setup_isolated_venvs.py` first.

### Package Import Errors
1. Check venv is properly activated
2. Verify with: `python scripts/run_with_venv.py <script> --verify`
3. Re-run setup if needed

### Permission Errors
Ensure you have write permissions in the benchmark directory.

### Python Build Not Found
Check that Python builds exist at expected paths. Update paths in `setup_isolated_venvs.py` if needed.

## Best Practices

1. **Always use isolated venvs** for benchmarking
2. **Document package versions** used in results
3. **Update regularly** but record version changes
4. **Never mix system packages** with venv packages
5. **Use the runner script** for consistent execution

## Migration from Shared Venv

If you have existing scripts using the shared venv approach:

1. Remove old shared venv: `rm -rf .matrix_venv`
2. Update scripts to use `run_with_venv.py`
3. Remove any `sys.path` manipulations
4. Test thoroughly with isolated environments

This approach ensures complete isolation, reproducibility, and professional-grade benchmark environment management.