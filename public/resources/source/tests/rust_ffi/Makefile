# Makefile for running FFI tests with different Python builds
# Tests PyO3 bugs that appear with GIL vs no-GIL configurations

.PHONY: help test test-gil test-nogil clean

help:
	@echo "Available targets:"
	@echo "  test       - Run tests with all available Python builds (GIL + no-GIL)"
	@echo "  test-quick - Run a quick test to check setup"
	@echo "  clean      - Clean build artifacts"
	@echo "  help       - Show this help"
	@echo ""
	@echo "This requires Python builds from the main Makefile:"
	@echo "  make python-gil    # Build GIL-enabled Python versions" 
	@echo "  make python-nogil  # Build no-GIL Python versions"

test:
	@echo "🧪 Running FFI tests with GIL and no-GIL Python builds..."
	python3 run_gil_tests.py

test-quick:
	@echo "🏃 Quick test with current Python..."
	python3 test_build_handcrafted_ffi.py
	python3 test_hypothesis_verification.py

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf handcrafted_ffi/target/
	rm -rf pyo3_investigation/target/
	rm -f gil_test_results.json
	find . -name "*.so" -delete
	find . -name "*.dylib" -delete
	find . -name "*.dll" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Individual Python version targets (if you want to test specific versions)
test-3.13-gil:
	@echo "Testing with Python 3.13 GIL..."
	../../cpython3.13.5-gil/bin/python3 test_hypothesis_verification.py

test-3.13-nogil:
	@echo "Testing with Python 3.13 no-GIL..."
	../../cpython3.13.5-nogil/bin/python3 test_hypothesis_verification.py

test-3.14-gil:
	@echo "Testing with Python 3.14 GIL..."
	../../cpython3.14.0rc1-gil/bin/python3 test_hypothesis_verification.py

test-3.14-nogil:
	@echo "Testing with Python 3.14 no-GIL..."
	../../cpython3.14.0rc1-nogil/bin/python3 test_hypothesis_verification.py