# Arch Linux Benchmark Setup

This directory contains Arch Linux-specific setup scripts for configuring your system for academic-grade FFI performance benchmarking.

## Quick Start

```bash
# Make the setup script executable
chmod +x setup-benchmarking.sh

# Run the setup (requires sudo privileges)
./setup-benchmarking.sh

# Validate the environment
cd ../../..
python scripts/validate_environment.py
```

## What the Setup Script Does

### 📦 Package Installation
- **cpupower** - CPU frequency scaling control
- **linux-tools** - perf and kernel profiling tools  
- **numactl** - NUMA policy control
- **base-devel** - GCC, make, pkg-config for building
- **python-numpy, python-scipy** - Scientific computing libraries
- **python-matplotlib** - For generating crossover analysis graphs

### ⚡ CPU Performance Configuration
- Sets CPU governor to **performance** mode
- Disables SMT/Hyper-Threading for consistent performance
- Disables Intel Turbo Boost / AMD Boost for stability
- Locks CPU frequencies to maximum for consistency
- Creates systemd service for persistent settings

### 🧠 Memory Optimization
- Temporarily disables ASLR for consistent memory layout
- Configures huge pages (128 pages allocated)
- Optimizes memory allocation patterns

### 🔧 System Tuning
- Enables hardware performance counters for perf
- Optimizes disk scheduler (noop/none for minimal overhead)
- Suggests CPU isolation configuration for dedicated cores

### 🛠️ Tools Created
- **benchmark-runner** - Wrapper script with environment validation
- **monitor-system.sh** - Real-time system monitoring during benchmarks

## CPU Isolation (Optional but Recommended)

For maximum performance isolation, the script suggests configuring CPU isolation. This requires a reboot:

### GRUB Configuration
```bash
# Edit GRUB configuration
sudo vim /etc/default/grub

# Add to GRUB_CMDLINE_LINUX_DEFAULT (example for 8+ core system):
GRUB_CMDLINE_LINUX_DEFAULT="quiet isolcpus=managed,2-7 nohz_full=2-7 rcu_nocbs=2-7 irqaffinity=0-1"

# Update GRUB and reboot
sudo grub-mkconfig -o /boot/grub/grub.cfg
sudo reboot
```

### systemd-boot Configuration
```bash
# Edit your boot entry (usually in /boot/loader/entries/)
sudo vim /boot/loader/entries/arch.conf

# Add to the options line:
options ... isolcpus=managed,2-7 nohz_full=2-7 rcu_nocbs=2-7 irqaffinity=0-1

# Update systemd-boot
sudo bootctl update
sudo reboot
```

## Usage Examples

### Environment Validation
```bash
# Always validate before benchmarking
python scripts/validate_environment.py
```

### Running Benchmarks
```bash
# Use the wrapper for optimal settings
benchmark-runner python scripts/plt_aware_benchmark.py

# With NUMA binding (recommended for multi-socket systems)
numactl --physcpubind=0-7 --membind=0 -- python scripts/plt_aware_benchmark.py

# Generate all evidence
benchmark-runner python scripts/generate_all_evidence.py
```

### System Monitoring
```bash
# Monitor system metrics during benchmarks
./scripts/setup/arch/monitor-system.sh
```

## Verification Commands

### Check CPU Configuration
```bash
# CPU governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# SMT status
cat /sys/devices/system/cpu/smt/control

# CPU isolation (after reboot with isolation configured)
cat /proc/cmdline
cat /sys/devices/system/cpu/isolated
```

### Check Memory Configuration
```bash
# ASLR status
cat /proc/sys/kernel/randomize_va_space

# Huge pages
cat /proc/sys/vm/nr_hugepages
cat /proc/meminfo | grep Huge
```

### Check Performance Counters
```bash
# Perf permissions
cat /proc/sys/kernel/perf_event_paranoid

# Test perf functionality
perf stat -e cycles,instructions true
```

## Troubleshooting

### Permission Issues
```bash
# If perf doesn't work
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid

# If CPU governor can't be set
sudo pacman -S cpupower
sudo cpupower frequency-set -g performance
```

### CPU Frequency Issues
```bash
# Check available governors
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors

# Check current frequency
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq
```

### NUMA Configuration
```bash
# Check NUMA topology
numactl --hardware
lscpu -e=CPU,CORE,SOCKET,NODE,ONLINE

# Show current NUMA policy
numactl --show
```

## Advanced Configuration

### For Systems with > 8 Cores
Adjust CPU isolation ranges in the GRUB configuration. Example for 16-core system:
```
isolcpus=managed,4-15 nohz_full=4-15 rcu_nocbs=4-15 irqaffinity=0-3
```

### For Multi-Socket Systems
Use NUMA binding to keep benchmarks on a single socket:
```bash
# Find your NUMA topology first
numactl -H

# Run on socket 0 only
numactl --cpunodebind=0 --membind=0 -- python scripts/plt_aware_benchmark.py
```

### Reverting Changes
```bash
# Re-enable ASLR
echo 2 | sudo tee /proc/sys/kernel/randomize_va_space

# Restore conservative CPU governor
sudo cpupower frequency-set -g conservative

# Re-enable SMT (if available)
echo on | sudo tee /sys/devices/system/cpu/smt/control
```

## Integration with Validation Script

The setup script configures your system to pass all checks in `scripts/validate_environment.py`:

- ✅ CPU governor set to 'performance'
- ✅ SMT/Hyper-Threading disabled  
- ✅ ASLR disabled
- ✅ Hardware performance counters accessible
- ✅ Required tools installed (gcc, make, pkg-config, perf)
- ✅ System load and thermal state monitoring
- ✅ Memory pressure within acceptable limits

## Security Note

This setup temporarily reduces some security features (ASLR, perf restrictions) for benchmarking accuracy. After benchmarking:

1. Re-enable ASLR: `echo 2 | sudo tee /proc/sys/kernel/randomize_va_space`
2. Restore perf restrictions: `echo 2 | sudo tee /proc/sys/kernel/perf_event_paranoid`
3. Consider re-enabling CPU frequency scaling for power savings

## Log Files

Setup creates detailed logs at `/tmp/benchmark-setup-YYYYMMDD_HHMMSS.log` containing:
- All commands executed
- System configuration changes
- Error messages and warnings
- Verification results

Keep these logs for troubleshooting and to document your benchmark environment configuration.