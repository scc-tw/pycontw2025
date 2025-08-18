# Environment Setup for FFI Benchmarks

This document provides the prerequisites and setup instructions for running FFI benchmarks. 

## System Requirements

### Required Software

The following software must be installed on your system before running benchmarks:

#### Core Development Tools
- **GCC** or **Clang** compiler with C99 and C++11 support
- **Make** build system
- **Python 3.13.5+** (must be built from source with specific flags)
- **Git** for version control

#### Python Packages
```bash
pip install numpy scipy psutil viztracer cffi pybind11
```

#### Rust Toolchain (for PyO3)
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install maturin
```

#### Performance Analysis Tools (Linux)
- **perf** - Linux profiling tool
  ```bash
  # Ubuntu/Debian
  sudo apt-get install linux-tools-common linux-tools-generic linux-tools-`uname -r`
  
  # Fedora/RHEL
  sudo dnf install perf
  ```

- **Brendan Gregg's FlameGraph tools**
  ```bash
  git clone https://github.com/brendangregg/FlameGraph
  export PATH=$PATH:$PWD/FlameGraph
  ```

- **valgrind** - Memory profiling (optional)
  ```bash
  sudo apt-get install valgrind  # Ubuntu/Debian
  sudo dnf install valgrind       # Fedora/RHEL
  ```

#### System Utilities
- **cpupower** - CPU frequency scaling control
  ```bash
  sudo apt-get install linux-cpupower  # Ubuntu/Debian
  sudo dnf install kernel-tools        # Fedora/RHEL
  ```

- **numactl** - NUMA memory policy control
  ```bash
  sudo apt-get install numactl  # Ubuntu/Debian
  sudo dnf install numactl       # Fedora/RHEL
  ```

### macOS Specific Tools
- **Instruments** (comes with Xcode)
- **leaks** command-line tool (pre-installed)
- **dtrace** (pre-installed, requires SIP modification for full access)

### Windows Specific Tools (if applicable)
- **Visual Studio Build Tools** or **MinGW-w64**
- **Windows Performance Toolkit** (part of Windows SDK)
- **Dependencies Walker** or **Dependencies GUI** for DLL analysis

## Pre-Benchmark System Configuration

### Linux System Preparation

Before running benchmarks, execute these commands with appropriate privileges:

```bash
# 1. Disable CPU frequency scaling (requires root)
sudo cpupower frequency-set -g performance

# 2. Disable Turbo Boost (Intel)
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# 3. Disable SMT/Hyper-Threading (optional but recommended)
echo off | sudo tee /sys/devices/system/cpu/smt/control

# 4. Configure huge pages
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# 5. Allow unprivileged access to performance counters
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid

# 6. Disable ASLR temporarily (for consistent results)
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
```

### CPU Isolation (Advanced)

For the most consistent results, isolate CPUs at boot time:

1. Edit `/etc/default/grub` and add to `GRUB_CMDLINE_LINUX`:
   ```
   isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7
   ```

2. Update grub and reboot:
   ```bash
   sudo update-grub  # Ubuntu/Debian
   sudo grub2-mkconfig -o /boot/grub2/grub.cfg  # Fedora/RHEL
   sudo reboot
   ```

3. Run benchmarks on isolated CPUs:
   ```bash
   taskset -c 2 python benchmark.py
   ```

## Building Python Versions

The project requires multiple Python builds. Use the provided Makefile:

```bash
# Build all required Python versions
make all

# Verify installations
make test
```

This will create:
- `./cpython3.13.5-gil/` - Python 3.13.5 with GIL
- `./cpython3.13.5-nogil/` - Python 3.13.5 without GIL
- `./cpython3.14.0rc1-gil/` - Python 3.14.0rc1 with GIL
- `./cpython3.14.0rc1-nogil/` - Python 3.14.0rc1 without GIL

## Verification Checklist

Before running benchmarks, verify:

- [ ] All required software is installed
- [ ] Python builds completed successfully (`make test`)
- [ ] Performance governor is set to "performance"
- [ ] CPU frequency scaling is disabled
- [ ] Turbo Boost is disabled (if desired)
- [ ] Performance counters are accessible (`perf stat sleep 1`)
- [ ] System is idle (minimal background processes)
- [ ] Sufficient free memory available
- [ ] No thermal throttling is occurring

## Troubleshooting

### Permission Errors with perf
If you get "Permission denied" errors:
```bash
# Option 1: Run with sudo
sudo perf record -g python benchmark.py

# Option 2: Add user to performance group
sudo groupadd perf_users
sudo usermod -a -G perf_users $USER
# Log out and back in
```

### CPU Frequency Scaling Issues
Check current CPU frequency:
```bash
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
lscpu | grep MHz
```

### Python Build Failures
Common issues:
- Missing development headers: Install `python3-dev` or `python3-devel`
- Missing SSL: Install `libssl-dev` or `openssl-devel`
- Missing FFI: Install `libffi-dev` or `libffi-devel`

### macOS SIP (System Integrity Protection)
For full dtrace access on macOS:
1. Boot into Recovery Mode (Cmd+R during startup)
2. Open Terminal and run: `csrutil enable --without dtrace`
3. Reboot

## References

- [Brendan Gregg's Systems Performance](http://www.brendangregg.com/systems-performance-2nd-edition-book.html)
- [Linux perf Examples](http://www.brendangregg.com/perf.html)
- [CPU Isolation Guide](https://www.kernel.org/doc/html/latest/admin-guide/kernel-per-CPU-kthreads.html)