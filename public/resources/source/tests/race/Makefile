# Makefile for threadtest library with ThreadSanitizer support

CXX ?= g++
UNAME_S := $(shell uname -s)

# Defaults (Linux/others)
SHLIB_EXT = so
DYNLIBFLAG = -shared
NMFLAGS = -D
TSAN_CXX := $(CXX)
TSAN_STDLIB :=

# macOS (Darwin) specific settings
ifeq ($(UNAME_S),Darwin)
  CXX ?= clang++
  SHLIB_EXT = dylib
  DYNLIBFLAG = -dynamiclib
  NMFLAGS = -gU
  # Use clang++ for TSAN to ensure sanitizer runtime availability on macOS
  TSAN_CXX := clang++
  TSAN_STDLIB := -stdlib=libc++
endif

CXXFLAGS = -std=c++23 -Wall -Wextra -fPIC -pthread
LDFLAGS = $(DYNLIBFLAG)

# Library name
LIB_NAME = threadtest
LIB_SO = lib$(LIB_NAME).$(SHLIB_EXT)
LIB_TSAN_SO = lib$(LIB_NAME)_tsan.$(SHLIB_EXT)
LIB_DEBUG_SO = lib$(LIB_NAME)_debug.$(SHLIB_EXT)

# Source files
SOURCES = threadtest.cpp
OBJECTS = $(SOURCES:.cpp=.o)
OBJECTS_TSAN = $(SOURCES:.cpp=.tsan.o)
OBJECTS_DEBUG = $(SOURCES:.cpp=.debug.o)

# Default target
all: $(LIB_SO) $(LIB_TSAN_SO) $(LIB_DEBUG_SO)

# Regular build (optimized, no sanitizers)
$(LIB_SO): $(OBJECTS)
	$(CXX) $(LDFLAGS) -O2 -o $@ $^

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -O2 -c -o $@ $<

# ThreadSanitizer build
$(LIB_TSAN_SO): $(OBJECTS_TSAN)
	$(TSAN_CXX) $(TSAN_STDLIB) $(LDFLAGS) -fsanitize=thread -o $@ $^

%.tsan.o: %.cpp
	$(TSAN_CXX) $(TSAN_STDLIB) $(CXXFLAGS) -fsanitize=thread -O1 -g -c -o $@ $<

# Debug build with symbols
$(LIB_DEBUG_SO): $(OBJECTS_DEBUG)
	$(CXX) $(LDFLAGS) -O0 -g -o $@ $^

%.debug.o: %.cpp
	$(CXX) $(CXXFLAGS) -O0 -g -DDEBUG -c -o $@ $<

# Test target to verify builds
test: $(LIB_SO) $(LIB_TSAN_SO) $(LIB_DEBUG_SO)
	@echo "Testing regular library..."
	@nm $(NMFLAGS) $(LIB_SO) | grep -q unsafe_increment && echo "✓ Regular build successful"
	@echo "Testing TSAN library..."
	@nm $(NMFLAGS) $(LIB_TSAN_SO) | grep -q unsafe_increment && echo "✓ TSAN build successful"
	@echo "Testing debug library..."
	@nm $(NMFLAGS) $(LIB_DEBUG_SO) | grep -q unsafe_increment && echo "✓ Debug build successful"

# Clean target
clean:
	rm -f *.o *.$(SHLIB_EXT) *.tsan.o *.debug.o

# Install target (optional)
install: $(LIB_SO) $(LIB_TSAN_SO) $(LIB_DEBUG_SO)
	@echo "Libraries built:"
	@ls -lh *.$(SHLIB_EXT)

# Help target
help:
	@echo "Available targets:"
	@echo "  all             - Build all library versions (default)"
	@echo "  $(LIB_SO)       - Build regular optimized library"
	@echo "  $(LIB_TSAN_SO)  - Build library with ThreadSanitizer"
	@echo "  $(LIB_DEBUG_SO) - Build debug library with symbols"
	@echo "  test            - Test that libraries export expected symbols"
	@echo "  clean           - Remove all built files"
	@echo "  help            - Show this help message"

.PHONY: all clean test install help