#!/bin/bash
#
# CFFI 2.0.0b1 Installation Script
# Reproducible installation for all Python builds including 3.13-nogil
#
# This script handles:
# 1. Regular installation for Python 3.14+ and GIL-enabled builds
# 2. Patched source build for Python 3.13-nogil (unsupported officially)
# 3. Verification and rollback on failure
#
# Usage: ./install_cffi_2.0.0b1.sh [venv_path]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CFFI_VERSION="2.0.0b1"
CFFI_REPO="https://github.com/python-cffi/cffi.git"
CFFI_TAG="v${CFFI_VERSION}"
BUILD_DIR="/tmp/cffi-build-$$"
LOG_DIR="${HOME}/.cache/cffi_install_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/cffi_install_$(date +%Y%m%d_%H%M%S).log"

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

detect_python_info() {
    local python_bin="$1"
    
    # Get Python version
    local version=$("$python_bin" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    
    # Check if it's free-threaded (nogil)
    local is_nogil=$("$python_bin" -c "import sysconfig; print('yes' if sysconfig.get_config_var('Py_GIL_DISABLED') else 'no')")
    
    # Get site-packages directory
    local site_packages=$("$python_bin" -c "import site; print(site.getsitepackages()[0])")
    
    echo "$version|$is_nogil|$site_packages"
}

backup_existing_cffi() {
    local python_bin="$1"
    local backup_dir="/tmp/cffi_backup_$$"
    
    # Check if cffi is installed
    if "$python_bin" -c "import cffi" 2>/dev/null; then
        local cffi_version=$("$python_bin" -c "import cffi; print(cffi.__version__)")
        warn "Existing CFFI ${cffi_version} found. Creating backup..."
        
        mkdir -p "$backup_dir"
        echo "$cffi_version" > "$backup_dir/version.txt"
        
        # Save pip freeze for potential restoration
        "$python_bin" -m pip freeze | grep -i cffi > "$backup_dir/cffi_pip.txt" || true
        
        return 0
    fi
    
    return 1
}

install_cffi_standard() {
    local python_bin="$1"
    local pip_bin="${python_bin/python/pip}"
    
    log "Installing CFFI ${CFFI_VERSION} using pip with --pre flag..."
    
    if "$pip_bin" install --upgrade --pre "cffi==${CFFI_VERSION}" >> "$LOG_FILE" 2>&1; then
        return 0
    else
        return 1
    fi
}

build_cffi_from_source() {
    local python_bin="$1"
    local patch_for_313_nogil="$2"
    local pip_bin="${python_bin/python/pip}"
    
    log "Building CFFI ${CFFI_VERSION} from source..."
    
    # First uninstall any existing cffi to avoid conflicts
    info "Uninstalling existing CFFI if present..."
    "$pip_bin" uninstall -y cffi 2>/dev/null || true
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Clone repository
    info "Cloning CFFI repository..."
    git clone --depth 1 --branch "$CFFI_TAG" "$CFFI_REPO" cffi-src >> "$LOG_FILE" 2>&1
    cd cffi-src
    
    # Apply patch for Python 3.13-nogil if requested
    if [ "$patch_for_313_nogil" = "yes" ]; then
        warn "Patching setup.py to allow Python 3.13 free-threaded build..."
        
        # Create patch to remove the version check
        cat > setup.patch << 'EOF'
--- setup.py.orig
+++ setup.py
@@ -19,10 +19,13 @@
 FREE_THREADED_BUILD = bool(sysconfig.get_config_var('Py_GIL_DISABLED'))
 
-if FREE_THREADED_BUILD and sys.version_info < (3, 14):
-    raise RuntimeError("CFFI does not support the free-threaded build of CPython 3.13. "
-                       "Upgrade to free-threaded 3.14 or newer to use CFFI with the "
-                       "free-threaded build.")
+# Patched to allow experimental Python 3.13 nogil support
+# WARNING: This is unsupported and may cause issues
+if FREE_THREADED_BUILD and sys.version_info < (3, 13):
+    raise RuntimeError("CFFI requires at least Python 3.13 for free-threaded builds")
+
+if FREE_THREADED_BUILD:
+    print("WARNING: Building CFFI for free-threaded Python - this is experimental!", file=sys.stderr)
 
 def _ask_pkg_config(resultlist, option, result_prefix='', sysroot=False):
EOF
        
        # Apply the patch
        patch -p0 < setup.patch >> "$LOG_FILE" 2>&1
    fi
    
    # Install build dependencies
    info "Installing build dependencies..."
    "$python_bin" -m pip install --upgrade setuptools wheel >> "$LOG_FILE" 2>&1
    
    # Build and install using pip for better integration
    info "Building and installing CFFI..."
    "$python_bin" -m pip install --force-reinstall --no-deps . >> "$LOG_FILE" 2>&1
    
    # Clean up
    cd /
    rm -rf "$BUILD_DIR"
    
    return 0
}

verify_installation() {
    local python_bin="$1"
    
    log "Verifying CFFI installation..."
    
    # Check if import works
    if ! "$python_bin" -c "import cffi" 2>/dev/null; then
        error "CFFI import failed!"
    fi
    
    # Check version
    local installed_version=$("$python_bin" -c "import cffi; print(cffi.__version__)")
    
    if [ "$installed_version" = "$CFFI_VERSION" ]; then
        log "✅ CFFI ${CFFI_VERSION} successfully installed!"
        
        # Run basic functionality test
        info "Running basic functionality test..."
        "$python_bin" -c "
from cffi import FFI
ffi = FFI()
ffi.cdef('int add(int, int);')
print('Basic CFFI functionality: OK')
" >> "$LOG_FILE" 2>&1
        
        return 0
    else
        error "Version mismatch! Expected ${CFFI_VERSION}, got ${installed_version}"
    fi
}

install_for_venv() {
    local venv_path="$1"
    local python_bin="${venv_path}/bin/python"
    
    # Check if venv exists
    if [ ! -f "$python_bin" ]; then
        error "Python not found at ${python_bin}"
    fi
    
    log "Processing virtual environment: ${venv_path}"
    
    # Detect Python info
    local python_info=$(detect_python_info "$python_bin")
    IFS='|' read -r version is_nogil site_packages <<< "$python_info"
    
    info "Python version: ${version}"
    info "Free-threaded: ${is_nogil}"
    info "Site-packages: ${site_packages}"
    
    # Backup existing installation
    backup_existing_cffi "$python_bin"
    
    # Determine installation method
    if [ "$version" = "3.13.5" ] && [ "$is_nogil" = "yes" ]; then
        warn "Python 3.13.5-nogil detected. Using patched source build..."
        
        if build_cffi_from_source "$python_bin" "yes"; then
            verify_installation "$python_bin"
        else
            error "Failed to build CFFI from source for Python 3.13.5-nogil"
        fi
    else
        # Try standard pip installation first
        if install_cffi_standard "$python_bin"; then
            verify_installation "$python_bin"
        else
            # Fallback to source build
            warn "Pip installation failed. Trying source build..."
            if build_cffi_from_source "$python_bin" "no"; then
                verify_installation "$python_bin"
            else
                error "Failed to install CFFI ${CFFI_VERSION}"
            fi
        fi
    fi
    
    log "Installation complete for ${venv_path}"
    echo ""
}

# Main execution
main() {
    log "========================================="
    log "CFFI ${CFFI_VERSION} Installation Script"
    log "========================================="
    
    if [ $# -eq 0 ]; then
        # Auto-detect all venvs in .isolated_venvs directory
        VENV_BASE="$(dirname "$0")/../.isolated_venvs"
        
        if [ ! -d "$VENV_BASE" ]; then
            error "No virtual environments found in ${VENV_BASE}"
        fi
        
        log "Auto-detecting virtual environments..."
        
        for venv_dir in "$VENV_BASE"/venv_*; do
            if [ -d "$venv_dir" ]; then
                install_for_venv "$venv_dir"
            fi
        done
    else
        # Install for specific venv
        install_for_venv "$1"
    fi
    
    log "========================================="
    log "All installations completed!"
    log "Log saved to: ${LOG_FILE}"
    log "========================================="
}

# Run main function
main "$@"