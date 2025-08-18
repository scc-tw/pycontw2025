# Python versions to build
PYTHON_313_VERSION = 3.13.5
PYTHON_314_VERSION = 3.14.0rc1

# Build directories
BUILD_DIR = build
CACHE_DIR = $(BUILD_DIR)/cache
PYTHON_313_SRC = $(BUILD_DIR)/Python-$(PYTHON_313_VERSION)
PYTHON_314_SRC = $(BUILD_DIR)/Python-$(PYTHON_314_VERSION)
# No-GIL prefixes
PYTHON_313_NOGIL_PREFIX = $(CURDIR)/cpython3.13.5-nogil
PYTHON_314_NOGIL_PREFIX = $(CURDIR)/cpython3.14.0rc1-nogil
# With-GIL prefixes
PYTHON_313_GIL_PREFIX = $(CURDIR)/cpython3.13.5-gil
PYTHON_314_GIL_PREFIX = $(CURDIR)/cpython3.14.0rc1-gil

# Python source URLs
PYTHON_313_URL = https://www.python.org/ftp/python/$(PYTHON_313_VERSION)/Python-$(PYTHON_313_VERSION).tgz
PYTHON_314_URL = https://www.python.org/ftp/python/3.14.0/Python-$(PYTHON_314_VERSION).tgz

# Number of parallel jobs
JOBS ?= $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)

.PHONY: all clean distclean clean-pgo clean-pgo-313 clean-pgo-314 python-313-nogil python-314-nogil python-313-gil python-314-gil check check-313 check-314 check-313-gil check-313-nogil check-314-gil check-314-nogil

all: python-313-nogil python-314-nogil python-313-gil python-314-gil

# Create directories
$(BUILD_DIR) $(CACHE_DIR):
	mkdir -p $@

# Download Python 3.13
$(CACHE_DIR)/Python-$(PYTHON_313_VERSION).tgz: | $(CACHE_DIR)
	@echo "Downloading Python $(PYTHON_313_VERSION)..."
	curl -L -o $@ $(PYTHON_313_URL)

# Download Python 3.14
$(CACHE_DIR)/Python-$(PYTHON_314_VERSION).tgz: | $(CACHE_DIR)
	@echo "Downloading Python $(PYTHON_314_VERSION)..."
	curl -L -o $@ $(PYTHON_314_URL)

# Extract Python 3.13
$(PYTHON_313_SRC): $(CACHE_DIR)/Python-$(PYTHON_313_VERSION).tgz | $(BUILD_DIR)
	@echo "Extracting Python $(PYTHON_313_VERSION)..."
	tar -xzf $< -C $(BUILD_DIR)
	touch $@

# Extract Python 3.14
$(PYTHON_314_SRC): $(CACHE_DIR)/Python-$(PYTHON_314_VERSION).tgz | $(BUILD_DIR)
	@echo "Extracting Python $(PYTHON_314_VERSION)..."
	tar -xzf $< -C $(BUILD_DIR)
	touch $@

# Clean PGO (Profile Guided Optimization) data to avoid coverage-mismatch errors
clean-pgo-313:
	@echo "Cleaning PGO data for Python $(PYTHON_313_VERSION)..."
	@if [ -d "$(PYTHON_313_SRC)" ]; then \
		cd $(PYTHON_313_SRC) && \
		rm -f profile-run-stamp && \
		find . -name '*.gc??' -delete && \
		echo "✓ PGO data cleaned for Python $(PYTHON_313_VERSION)"; \
	else \
		echo "⚠ Python $(PYTHON_313_VERSION) source not found, skipping PGO cleanup"; \
	fi

clean-pgo-314:
	@echo "Cleaning PGO data for Python $(PYTHON_314_VERSION)..."
	@if [ -d "$(PYTHON_314_SRC)" ]; then \
		cd $(PYTHON_314_SRC) && \
		rm -f profile-run-stamp && \
		find . -name '*.gc??' -delete && \
		echo "✓ PGO data cleaned for Python $(PYTHON_314_VERSION)"; \
	else \
		echo "⚠ Python $(PYTHON_314_VERSION) source not found, skipping PGO cleanup"; \
	fi

# Clean PGO data for all Python versions
clean-pgo: clean-pgo-313 clean-pgo-314

# Detect OpenSSL location
ifeq ($(shell uname),Darwin)
    # macOS with Homebrew OpenSSL
    OPENSSL_PREFIX = $(shell brew --prefix openssl 2>/dev/null || echo /usr/local/opt/openssl)
    SSL_CONFIG = --with-openssl=$(OPENSSL_PREFIX)
else
    # Linux typically has OpenSSL in standard locations
    OPENSSL_PREFIX ?= $(shell pkg-config --variable=prefix openssl 2>/dev/null || echo /usr)
    SSL_CONFIG = --with-openssl=$(OPENSSL_PREFIX)
endif

# Build Python 3.13 with --disable-gil
python-313-nogil: check-ssl $(PYTHON_313_SRC) clean-pgo-313
	@echo "Building Python $(PYTHON_313_VERSION) with --disable-gil..."
	cd $(PYTHON_313_SRC) && \
	./configure --disable-gil --prefix=$(PYTHON_313_NOGIL_PREFIX) --enable-optimizations $(SSL_CONFIG) && \
	make -j$(JOBS) && \
	make install
	@echo "Python 3.13 (no-GIL) installed at: $(PYTHON_313_NOGIL_PREFIX)"

# Build Python 3.14 with --disable-gil
python-314-nogil: check-ssl $(PYTHON_314_SRC) clean-pgo-314
	@echo "Building Python $(PYTHON_314_VERSION) with --disable-gil..."
	cd $(PYTHON_314_SRC) && \
	./configure --disable-gil --prefix=$(PYTHON_314_NOGIL_PREFIX) --enable-optimizations $(SSL_CONFIG) && \
	make -j$(JOBS) && \
	make install
	@echo "Python 3.14 (no-GIL) installed at: $(PYTHON_314_NOGIL_PREFIX)"

# Build Python 3.13 with GIL enabled
python-313-gil: check-ssl $(PYTHON_313_SRC) clean-pgo-313
	@echo "Building Python $(PYTHON_313_VERSION) with GIL enabled..."
	cd $(PYTHON_313_SRC) && \
	./configure --prefix=$(PYTHON_313_GIL_PREFIX) --enable-optimizations $(SSL_CONFIG) && \
	make -j$(JOBS) && \
	make install
	@echo "Python 3.13 (with GIL) installed at: $(PYTHON_313_GIL_PREFIX)"

# Build Python 3.14 with GIL enabled
python-314-gil: check-ssl $(PYTHON_314_SRC) clean-pgo-314
	@echo "Building Python $(PYTHON_314_VERSION) with GIL enabled..."
	cd $(PYTHON_314_SRC) && \
	./configure --prefix=$(PYTHON_314_GIL_PREFIX) --enable-optimizations $(SSL_CONFIG) && \
	make -j$(JOBS) && \
	make install
	@echo "Python 3.14 (with GIL) installed at: $(PYTHON_314_GIL_PREFIX)"

# Test installations
test:
	@echo "Testing Python installations..."
	@echo "=== No-GIL versions ==="
	@if [ -x "$(PYTHON_313_NOGIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.13 (no-GIL):"; \
		$(PYTHON_313_NOGIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_313_NOGIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL disabled: {sys._is_gil_enabled() == False}')"; \
	fi
	@if [ -x "$(PYTHON_314_NOGIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.14 (no-GIL):"; \
		$(PYTHON_314_NOGIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_314_NOGIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL disabled: {sys._is_gil_enabled() == False}')"; \
	fi
	@echo "=== With-GIL versions ==="
	@if [ -x "$(PYTHON_313_GIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.13 (with GIL):"; \
		$(PYTHON_313_GIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_313_GIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL enabled: {sys._is_gil_enabled() == True}')"; \
	fi
	@if [ -x "$(PYTHON_314_GIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.14 (with GIL):"; \
		$(PYTHON_314_GIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_314_GIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL enabled: {sys._is_gil_enabled() == True}')"; \
	fi

# Clean build artifacts but keep downloads and installations
clean-build: clean-pgo
	rm -rf $(PYTHON_313_SRC) $(PYTHON_314_SRC)

# Clean everything except cached downloads
clean:
	rm -rf $(PYTHON_313_SRC) $(PYTHON_314_SRC)
	rm -rf $(PYTHON_313_NOGIL_PREFIX) $(PYTHON_314_NOGIL_PREFIX)
	rm -rf $(PYTHON_313_GIL_PREFIX) $(PYTHON_314_GIL_PREFIX)

# Clean everything including downloads
distclean: clean
	rm -rf $(BUILD_DIR)

# Check SSL configuration before building
check-ssl:
	@echo "Checking OpenSSL configuration..."
ifeq ($(shell uname),Darwin)
	@echo "Platform: macOS"
	@echo "OpenSSL location: $(OPENSSL_PREFIX)"
	@if [ -d "$(OPENSSL_PREFIX)" ]; then \
		echo "✓ OpenSSL found at $(OPENSSL_PREFIX)"; \
		ls -la $(OPENSSL_PREFIX)/lib/libssl.* 2>/dev/null | head -1; \
	else \
		echo "✗ OpenSSL not found! Install with: brew install openssl"; \
		exit 1; \
	fi
else
	@echo "Platform: Linux"
	@which openssl >/dev/null && echo "✓ OpenSSL found: $$(openssl version)" || echo "✗ OpenSSL not found"
endif

# Check Python 3.13 no-GIL installation
check-313-nogil:
	@echo "Checking Python 3.13 (no-GIL) installation..."
	@if [ -x "$(PYTHON_313_NOGIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.13 (no-GIL):"; \
		$(PYTHON_313_NOGIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_313_NOGIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL disabled: {sys._is_gil_enabled() == False}')"; \
		echo "✓ Python 3.13 (no-GIL) installation verified"; \
	else \
		echo "✗ Python 3.13 (no-GIL) not found at $(PYTHON_313_NOGIL_PREFIX)"; \
		exit 1; \
	fi

# Check Python 3.13 with-GIL installation
check-313-gil:
	@echo "Checking Python 3.13 (with GIL) installation..."
	@if [ -x "$(PYTHON_313_GIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.13 (with GIL):"; \
		$(PYTHON_313_GIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_313_GIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL enabled: {sys._is_gil_enabled() == True}')"; \
		echo "✓ Python 3.13 (with GIL) installation verified"; \
	else \
		echo "✗ Python 3.13 (with GIL) not found at $(PYTHON_313_GIL_PREFIX)"; \
		exit 1; \
	fi

# Check Python 3.14 no-GIL installation
check-314-nogil:
	@echo "Checking Python 3.14 (no-GIL) installation..."
	@if [ -x "$(PYTHON_314_NOGIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.14 (no-GIL):"; \
		$(PYTHON_314_NOGIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_314_NOGIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL disabled: {sys._is_gil_enabled() == False}')"; \
		echo "✓ Python 3.14 (no-GIL) installation verified"; \
	else \
		echo "✗ Python 3.14 (no-GIL) not found at $(PYTHON_314_NOGIL_PREFIX)"; \
		exit 1; \
	fi

# Check Python 3.14 with-GIL installation
check-314-gil:
	@echo "Checking Python 3.14 (with GIL) installation..."
	@if [ -x "$(PYTHON_314_GIL_PREFIX)/bin/python3" ]; then \
		echo "Python 3.14 (with GIL):"; \
		$(PYTHON_314_GIL_PREFIX)/bin/python3 --version; \
		$(PYTHON_314_GIL_PREFIX)/bin/python3 -c "import sys; print(f'GIL enabled: {sys._is_gil_enabled() == True}')"; \
		echo "✓ Python 3.14 (with GIL) installation verified"; \
	else \
		echo "✗ Python 3.14 (with GIL) not found at $(PYTHON_314_GIL_PREFIX)"; \
		exit 1; \
	fi

# Check all Python 3.13 installations (both GIL and no-GIL)
check-313: check-313-nogil check-313-gil
	@echo "✓ All Python 3.13 installations verified"

# Check all Python 3.14 installations (both GIL and no-GIL)
check-314: check-314-nogil check-314-gil
	@echo "✓ All Python 3.14 installations verified"

# Check all Python installations
check: check-313 check-314
	@echo "✓ All Python installations verified successfully"

# Shortcuts
313-nogil: python-313-nogil
314-nogil: python-314-nogil
313-gil: python-313-gil
314-gil: python-314-gil
313: python-313-nogil python-313-gil
314: python-314-nogil python-314-gil
