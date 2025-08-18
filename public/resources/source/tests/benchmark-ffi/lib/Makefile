# Makefile for building benchmark shared library
# Uses identical flags as specified in the benchmark design

CC = gcc
CFLAGS = -O3 -march=native -mtune=native -fno-omit-frame-pointer -g -fvisibility=hidden -fPIC -Wall -Wextra
LDFLAGS = -shared

# Library name (platform-specific)
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    LIB_EXT = .dylib
    LDFLAGS += -dynamiclib
else
    LIB_EXT = .so
endif

TARGET = benchlib$(LIB_EXT)

# Build targets
.PHONY: all clean install test

all: $(TARGET)

$(TARGET): benchlib.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< -lm

install: $(TARGET)
	@echo "Installing $(TARGET) to benchmark directories..."
	@mkdir -p benchmarks/ctypes
	@mkdir -p benchmarks/cffi
	@mkdir -p benchmarks/pybind11
	@mkdir -p benchmarks/pyo3
	cp $(TARGET) benchmarks/ctypes/
	cp $(TARGET) benchmarks/cffi/
	cp $(TARGET) benchmarks/pybind11/
	cp $(TARGET) benchmarks/pyo3/
	@echo "Installation complete!"

test: $(TARGET)
	@echo "Testing library loading..."
	python3 -c "import ctypes; lib = ctypes.CDLL('./$(TARGET)'); print('Library version:', lib.get_library_version.restype or lib.get_library_version())"

clean:
	rm -f $(TARGET)
	rm -f benchmarks/*/$(TARGET)
	@echo "Cleaned!"

# Debug build
debug: CFLAGS += -DDEBUG -O0
debug: $(TARGET)

# Platform-specific adjustments
ifeq ($(UNAME_S),Linux)
    # Linux-specific flags
    CFLAGS += -D_GNU_SOURCE
endif

ifeq ($(UNAME_S),Darwin)
    # macOS-specific flags
    CFLAGS += -mmacosx-version-min=10.15
endif

# Show configuration
info:
	@echo "Build configuration:"
	@echo "  CC      = $(CC)"
	@echo "  CFLAGS  = $(CFLAGS)"
	@echo "  LDFLAGS = $(LDFLAGS)"
	@echo "  TARGET  = $(TARGET)"
	@echo "  UNAME_S = $(UNAME_S)"