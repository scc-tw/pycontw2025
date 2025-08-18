#!/bin/bash
# Setup a shared virtual environment for all matrix benchmarks
# Uses the self-compiled Python to ensure compatibility

set -e

BENCHMARK_DIR="/home/scc/git/pycon2025-ffi-hidden-corner/tests/benchmark-ffi"
VENV_DIR="$BENCHMARK_DIR/.matrix_venv"

# Use the GIL-enabled 3.13.5 as the base Python for the shared venv
BASE_PYTHON="/home/scc/git/pycon2025-ffi-hidden-corner/cpython3.13.5-gil/bin/python3.13"

echo "🔧 Setting up shared virtual environment for matrix benchmarks"
echo "============================================================="
echo "Base Python: $BASE_PYTHON"
echo "Virtual env: $VENV_DIR"
echo ""

# Check if base Python exists
if [ ! -f "$BASE_PYTHON" ]; then
    echo "❌ Error: Base Python not found at $BASE_PYTHON"
    echo "Please ensure Python 3.13.5 with GIL is built first."
    exit 1
fi

# Remove existing venv if it exists
if [ -d "$VENV_DIR" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
fi

# Create new virtual environment
echo "📦 Creating virtual environment..."
"$BASE_PYTHON" -m venv "$VENV_DIR"

# Activate venv and install dependencies
echo "📊 Installing dependencies..."
source "$VENV_DIR/bin/activate"

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install required packages
echo "   • Installing numpy..."
pip install numpy

echo "   • Installing scipy..."
pip install scipy

# Verify installations
echo ""
echo "✅ Verifying installations:"
python -c "import numpy; print(f'   • NumPy {numpy.__version__}')"
python -c "import scipy; print(f'   • SciPy {scipy.__version__}')"

# Deactivate venv
deactivate

# Get site-packages path for the venv
SITE_PACKAGES=$("$VENV_DIR/bin/python" -c "import site; print(site.getsitepackages()[0])")

echo ""
echo "✅ Shared virtual environment created successfully!"
echo "📁 Site-packages location: $SITE_PACKAGES"
echo ""
echo "This path will be used by all Python builds in matrix benchmarking."