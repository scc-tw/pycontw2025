# FFI Performance Profiling Guide

This guide implements the recommendations from performance profiling experts to provide both maximum performance and detailed profiling capabilities for the FFI benchmark suite.

## Build Profiles

The benchmark system now supports two build profiles optimized for different use cases:

### Fast Profile (Default)
- **Purpose**: Maximum performance benchmarking
- **Optimization**: `-O3 -march=native -g1` (no frame pointers)
- **Rust**: `opt-level=3, debug=line-tables-only`
- **Profiling**: Use Intel LBR for minimal overhead

### Instrumented Profile
- **Purpose**: Detailed profiling and debugging
- **Optimization**: `-O3 -march=native -g1 -fno-omit-frame-pointer`
- **Rust**: Same + force frame pointers via `-C force-frame-pointers=yes`
- **Profiling**: Use frame pointer-based profiling

## Building with Profiles

### Build for Maximum Performance
```bash
# Default mode (fast)
make clean && make PROFILE=fast build-all

# Explicit fast mode
make clean && make PROFILE=fast build-all
```

### Build for Profiling
```bash
# Instrumented mode with frame pointers
make clean && make PROFILE=instrumented build-all
```

### Verify Build Configuration
```bash
make info
# Shows current profile and profiling commands
```

## Profiling Commands

### Fast Mode Profiling (Intel LBR)
Best for hot-path analysis with minimal overhead:

```bash
# Basic LBR profiling
perf record --call-graph lbr -F 99 -g -- taskset -c 2 python benchmark_script.py

# Analysis
perf report --stitch-lbr
```

**Advantages**:
- Lowest profiling overhead
- Hardware-assisted call stack capture
- Ideal for performance-critical measurements

**Limitations**:
- Limited stack depth (hardware dependent)
- Intel-specific feature

### Instrumented Mode Profiling (Frame Pointers)
Best for detailed, reliable stack traces:

```bash
# Frame pointer profiling
perf record --call-graph fp,128 -F 99 -g -- taskset -c 2 python benchmark_script.py

# Analysis
perf report
```

**Advantages**:
- Highly reliable stack traces
- Very low overhead (often lower than DWARF)
- Works across all platforms

**Limitations**:
- Slight performance impact from frame pointers
- Limited inline function visibility

### DWARF Profiling (Fallback)
When LBR and frame pointers are insufficient:

```bash
# DWARF unwinding (works with fast mode)
perf record --call-graph dwarf,16384 -F 99 -g -- taskset -c 2 python benchmark_script.py

# Analysis
perf report
```

**Advantages**:
- Works without frame pointers
- Rich inline function information

**Disadvantages**:
- Higher CPU overhead during profiling
- Larger recorded data files
- Can be sensitive to debug info quality

## Profiling Workflow Examples

### Profile ctypes Implementation
```bash
# Build in fast mode
make clean && make PROFILE=fast build-all

# Profile with LBR
cd implementations/ctypes_impl
perf record --call-graph lbr -F 99 -g -- taskset -c 2 python ctypes_bench.py --iterations 1000000

# Analyze results
perf report --stitch-lbr --stdio | head -50
```

### Profile PyO3 with Detailed Stacks
```bash
# Build in instrumented mode
make clean && make PROFILE=instrumented build-all

# Profile with frame pointers
cd implementations/pyo3_impl
perf record --call-graph fp,128 -F 99 -g -- taskset -c 2 python pyo3_bench.py --iterations 1000000

# Interactive analysis
perf report
```

### Comparative Profiling
```bash
# Build both modes for comparison
make clean && make PROFILE=fast build-all
cp -r implementations fast_build

make clean && make PROFILE=instrumented build-all
cp -r implementations instrumented_build

# Profile both and compare performance impact
# Fast mode
perf stat -e cycles,instructions -- taskset -c 2 python fast_build/ctypes_impl/ctypes_bench.py

# Instrumented mode  
perf stat -e cycles,instructions -- taskset -c 2 python instrumented_build/ctypes_impl/ctypes_bench.py
```

## Performance Impact Analysis

### Expected Overhead

| Mode | Frame Pointers | Profiling Method | Overhead |
|------|---------------|------------------|----------|
| Fast | No | LBR | <1% |
| Fast | No | DWARF | 2-5% |
| Instrumented | Yes | Frame Pointers | 1-3% |
| Instrumented | Yes | LBR | <1% |

### Measurement Strategy

For rigorous performance comparison:

1. **Publish dual results**: Report both "maximum performance" (fast mode) and "instrumented" numbers
2. **Document overhead**: Show the performance delta between modes
3. **Profile selection**: Use LBR for headlines, frame pointers for detailed analysis
4. **Reproducibility**: Include exact build commands and profiling flags

## Advanced Profiling Features

### Hardware Counter Analysis
```bash
# Profile with additional hardware counters
perf record -e cycles,instructions,cache-misses,branch-misses \
  --call-graph lbr -F 99 -g -- taskset -c 2 python benchmark.py

# Multi-event analysis
perf report -e cycles --stdio
perf report -e cache-misses --stdio
```

### Memory Profiling Integration
```bash
# Combine with memory profiling
perf record --call-graph lbr -e cycles,page-faults -- \
  valgrind --tool=massif python benchmark.py
```

### Flame Graph Generation
```bash
# Generate flame graphs
perf record --call-graph lbr -F 99 -g -- python benchmark.py
perf script | stackcollapse-perf.pl | flamegraph.pl > profile.svg
```

## Build System Integration

### Makefile Targets
- `make info` - Show current profile and recommended profiling commands
- `make PROFILE=fast build-all` - Build for maximum performance
- `make PROFILE=instrumented build-all` - Build for profiling

### Environment Variables
- `PROFILE=fast|instrumented` - Select build profile
- Passed automatically to all sub-builds (pybind11, PyO3)

### Compiler Flag Details

#### C/C++ (ctypes, cffi, pybind11)
```bash
# Fast mode flags
-O3 -march=native -mtune=native -g1 -fvisibility=hidden -fPIC -Wall -Wextra

# Instrumented mode flags  
-O3 -march=native -mtune=native -g1 -fno-omit-frame-pointer -fvisibility=hidden -fPIC -Wall -Wextra
```

#### Rust (PyO3)
```toml
# Fast mode (Cargo.toml [profile.release])
opt-level = 3
debug = "line-tables-only"
codegen-units = 1

# Instrumented mode (Cargo.toml [profile.instrumented])
inherits = "release"
debug = "line-tables-only"
# Plus RUSTFLAGS="-C force-frame-pointers=yes"
```

## Troubleshooting

### Common Issues

1. **Missing debug symbols**: Ensure `-g1` is included and debug packages are installed
2. **Truncated stacks**: Increase DWARF stack dump size (`--call-graph dwarf,32768`)
3. **LBR not available**: Fallback to frame pointers or DWARF
4. **High profiling overhead**: Switch from DWARF to LBR or frame pointers

### Verification Commands
```bash
# Check frame pointer compilation
objdump -d lib/benchlib.so | grep -A5 -B5 "push.*%rbp"

# Verify debug info
readelf --debug-dump=info lib/benchlib.so | head -20

# Test LBR availability
perf list | grep lbr
```

## References

Implementation based on expert recommendations from:
- [LWN: Last Branch Records](https://lwn.net/Articles/680985/)
- [Red Hat: Frame Pointers Guide](https://developers.redhat.com/articles/2023/07/31/frame-pointers-untangling-unwinding)
- [Brendan Gregg's perf Examples](https://www.brendangregg.com/perf.html)
- [Richard WM Jones: Frame Pointers vs DWARF](https://rwmj.wordpress.com/2023/02/14/frame-pointers-vs-dwarf-my-verdict/)