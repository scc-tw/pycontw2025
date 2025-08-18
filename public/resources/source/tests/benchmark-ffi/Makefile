# Master Makefile for FFI Benchmark Framework
# Eliminates LD_LIBRARY_PATH workarounds through proper RPATH management

.PHONY: all clean install test setup-env validate-setup
.DEFAULT_GOAL := all

# Build configuration
CC = gcc

# Profile mode selection (default: fast)
PROFILE ?= fast

# Base flags for all builds
BASE_CFLAGS = -O3 -march=native -mtune=native -fvisibility=hidden -fPIC -Wall -Wextra

# Profile-specific flags
ifeq ($(PROFILE),fast)
    # Maximum performance mode: no frame pointers, minimal debug info
    CFLAGS = $(BASE_CFLAGS) -g1
    PROFILE_DESC = "fast (max performance, LBR profiling)"
else ifeq ($(PROFILE),instrumented)
    # Instrumented mode: frame pointers for reliable profiling
    CFLAGS = $(BASE_CFLAGS) -g1 -fno-omit-frame-pointer
    PROFILE_DESC = "instrumented (with frame pointers)"
else
    $(error Invalid PROFILE mode. Use 'fast' or 'instrumented')
endif

LDFLAGS = -shared

# Rust build configuration functions
define get_rust_flags
$(if $(filter fast,$(1)),RUSTFLAGS="-C link-args=$(RPATH_FLAG)",RUSTFLAGS="-C link-args=$(RPATH_FLAG) -C force-frame-pointers=yes")
endef

define get_rust_build_cmd
$(if $(filter fast,$(1)),cargo build --release,cargo build --profile instrumented)
endef

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    LIB_EXT = .dylib
    LDFLAGS += -dynamiclib
    RPATH_FLAG = -Wl,-rpath,@loader_path
else
    LIB_EXT = .so
    RPATH_FLAG = -Wl,-rpath,$$ORIGIN
endif

# Paths
LIB_DIR = lib
BUILD_DIR = build
IMPL_DIR = implementations

TARGET = $(LIB_DIR)/benchlib$(LIB_EXT)

all: $(TARGET) install-libs

# Build the core shared library
$(TARGET): $(LIB_DIR)/benchlib.c
	@echo "🔨 Building core benchmark library with profile $(PROFILE)..."
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< -lm
	@echo "✅ Core library built: $@"

# Create proper library symlinks and install to implementations
install-libs: $(TARGET)
	@echo "🔗 Setting up library links..."
	@cd $(LIB_DIR) && ln -sf benchlib$(LIB_EXT) libbenchlib$(LIB_EXT)
	@mkdir -p $(IMPL_DIR)/ctypes_impl $(IMPL_DIR)/cffi_impl $(IMPL_DIR)/pybind11_impl $(IMPL_DIR)/pyo3_impl
	@cp $(TARGET) $(IMPL_DIR)/ctypes_impl/
	@cp $(TARGET) $(IMPL_DIR)/cffi_impl/
	@cp $(TARGET) $(IMPL_DIR)/pybind11_impl/
	@cp $(TARGET) $(IMPL_DIR)/pyo3_impl/
	@echo "✅ Libraries installed to all implementations"

# Build pybind11 extension with proper RPATH
build-pybind11: $(TARGET) install-libs
	@echo "🔨 Building pybind11 extension with profile $(PROFILE)..."
	@cd $(IMPL_DIR)/pybind11_impl && \
		CFLAGS="$(CFLAGS) $(RPATH_FLAG)" LDFLAGS="$(RPATH_FLAG)" PROFILE=$(PROFILE) python setup_pybind11.py build_ext --inplace
	@mkdir -p $(BUILD_DIR)/pybind11
	@find $(IMPL_DIR)/pybind11_impl -name "*.so" -exec cp {} $(BUILD_DIR)/pybind11/ \;
	@echo "✅ pybind11 extension built with RPATH and libraries installed"

# Build PyO3 extension with proper linking
build-pyo3: $(TARGET) create-pkgconfig install-libs
	@echo "🔨 Building PyO3 extension with profile $(PROFILE)..."
	@cd $(IMPL_DIR)/pyo3_impl && \
		PKG_CONFIG_PATH=../../lib/pkg-config:$$PKG_CONFIG_PATH \
		$(call get_rust_flags,$(PROFILE)) \
		PROFILE=$(PROFILE) \
		$(call get_rust_build_cmd,$(PROFILE))
	@mkdir -p $(BUILD_DIR)/pyo3
	@find $(IMPL_DIR)/pyo3_impl/target/release -name "libbenchlib*.so" -exec cp {} $(BUILD_DIR)/pyo3/ \;
	@cp $(IMPL_DIR)/pyo3_impl/target/release/libbenchlib_pyo3.so $(IMPL_DIR)/pyo3_impl/benchlib_pyo3.so
	@echo "✅ PyO3 extension built with RPATH and installed"

# Create pkg-config file for standard Unix dependency management
create-pkgconfig: $(TARGET)
	@mkdir -p $(LIB_DIR)/pkg-config
	@echo "Creating pkg-config file..."
	@echo "Name: benchlib" > $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "Description: FFI benchmark shared library" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "Version: 1.0.0" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "prefix=$(shell pwd)/$(LIB_DIR)" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "libdir=\$${prefix}" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "includedir=\$${prefix}" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "Libs: -L\$${libdir} -lbenchlib" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "Cflags: -I\$${includedir}" >> $(LIB_DIR)/pkg-config/benchlib.pc
	@echo "✅ pkg-config file created"

# Environment validation
validate-setup:
	@echo "🔍 Validating environment setup..."
	@python framework/environment.py
	@echo "✅ Environment validation complete"

# Test all implementations
test: all
	@echo "🧪 Testing all FFI implementations..."
	@cd scripts && python demo_all_ffi.py
	@echo "✅ All tests passed"

# Development setup
setup-env:
	@echo "🔧 Setting up development environment..."
	@pip install -e framework/
	@echo "✅ Development environment ready"

# Clean all build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -f $(TARGET)
	@rm -f $(LIB_DIR)/libbenchlib$(LIB_EXT)
	@rm -rf $(BUILD_DIR)/*
	@rm -rf $(IMPL_DIR)/*/build
	@rm -rf $(IMPL_DIR)/pyo3_impl/target
	@rm -f $(IMPL_DIR)/*/benchlib$(LIB_EXT)
	@rm -f $(IMPL_DIR)/pybind11_impl/benchlib_pybind11*.so
	@rm -f $(IMPL_DIR)/pyo3_impl/libbenchlib_pyo3.so $(IMPL_DIR)/pyo3_impl/benchlib_pyo3.so
	@rm -rf $(LIB_DIR)/pkg-config
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean complete"

# Complete build including all extensions
build-all: all install-libs create-pkgconfig build-pybind11 build-pyo3
	@echo "🎉 Complete build finished - all FFI methods ready!"
	@echo "Testing all implementations..."
	@python -c "from implementations import get_available_implementations; impls = get_available_implementations(); print('Available:', list(impls.keys())); [print(f'{name}: {impl.return_int()}') for name, impl in impls.items()]"

# Quick info
info:
	@echo "FFI Benchmark Framework Build System"
	@echo "===================================="
	@echo "Core library: $(TARGET)"
	@echo "Build system: $(CC) with RPATH support"
	@echo "Platform: $(UNAME_S)"
	@echo "Current profile: $(PROFILE) mode"
	@echo ""
	@echo "Targets:"
	@echo "  all         - Build core library and install"
	@echo "  build-all   - Build everything including extensions" 
	@echo "  test        - Run all tests"
	@echo "  clean       - Clean all artifacts"
	@echo "  validate    - Validate environment"
	@echo ""
	@echo "Build Profiles (use PROFILE=mode):"
	@echo "  fast        - Maximum performance (default)"
	@echo "  instrumented- With frame pointers for profiling"
	@echo ""
	@echo "Profiling Commands:"
	@echo "  Fast mode:        perf record --call-graph lbr -F 99 -g -- [command]"
	@echo "  Instrumented:     perf record --call-graph fp -F 99 -g -- [command]"

# Help
help: info