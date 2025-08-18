# Environment Recovery Script Guide

## Overview

The `recover_environment.py` script provides automated environment configuration and recovery for rigorous performance benchmarking. It addresses all validation requirements from `validate_environment.py` with safe backup/restore functionality.

## Features

- ✅ **Automatic Backup**: Creates complete system state backup before changes
- ✅ **Safe Recovery**: Restore original settings with one command  
- ✅ **Comprehensive Setup**: Configures all benchmarking requirements
- ✅ **Dry Run Mode**: Preview changes without applying them
- ✅ **Integration Ready**: Works with existing validation and benchmark workflows

## Quick Start

### 1. Preview Changes (Recommended First Step)
```bash
python3 scripts/recover_environment.py --dry-run
```

### 2. Apply All Optimizations  
```bash
python3 scripts/recover_environment.py --apply
```

### 3. Restore Original Settings
```bash
python3 scripts/recover_environment.py --restore
```

## Usage Examples

### Interactive Setup (Recommended)
```bash
# Preview what will be changed
python3 scripts/recover_environment.py --dry-run

# Apply with confirmation prompt
python3 scripts/recover_environment.py --apply

# Verify environment is optimized
python3 scripts/validate_environment.py
```

### Automated Setup (CI/Testing)
```bash
# Apply without prompts
python3 scripts/recover_environment.py --apply --force

# Skip package installation (if tools already available)
python3 scripts/recover_environment.py --apply --skip-tools --force
```

### Recovery Operations
```bash
# Restore from backup
python3 scripts/recover_environment.py --restore

# Force restore without confirmation
python3 scripts/recover_environment.py --restore --force
```

## What Gets Configured

### CPU Performance Settings
- **CPU Governor**: Set to `performance` mode for consistent frequency
- **SMT/Hyper-Threading**: Disabled to eliminate thread interference
- **Turbo Boost**: Disabled (Intel/AMD) for frequency consistency
- **CPU Isolation**: Guidance for manual setup (requires reboot)

### Memory Optimization
- **ASLR**: Temporarily disabled for consistent memory layout
- **Huge Pages**: Allocated (128 pages) for better memory performance

### System Configuration  
- **Performance Counters**: Enabled hardware counter access for `perf`
- **Disk Schedulers**: Optimized for storage devices (`noop`/`none`)
- **Required Tools**: Installs `linux-tools-generic`, `numactl`, `cpufrequtils`

### Validation Integration
- **Environment Checks**: Addresses all `validate_environment.py` requirements
- **Backup Safety**: Complete state backup in `results/environment_backup.json`

## Integration Workflow

### Complete Benchmarking Setup
```bash
# 1. Check current environment
python3 scripts/validate_environment.py

# 2. If validation fails, apply recovery
python3 scripts/recover_environment.py --apply

# 3. Verify optimizations applied  
python3 scripts/validate_environment.py

# 4. Run benchmarks
benchmark-runner python scripts/run_all_benchmarks.py

# 5. Restore environment when done
python3 scripts/recover_environment.py --restore
```

### Automated Testing Integration
```bash
#!/bin/bash
# Automated benchmark testing with environment recovery

set -e

echo "🔧 Setting up benchmarking environment..."
python3 scripts/recover_environment.py --apply --force --skip-tools

echo "🔬 Validating environment..."
python3 scripts/validate_environment.py

echo "🚀 Running benchmarks..."
benchmark-runner python scripts/run_all_benchmarks.py

echo "🔄 Restoring environment..."
python3 scripts/recover_environment.py --restore --force

echo "✅ Benchmark cycle complete!"
```

## Command Line Options

### Actions
- `--apply` - Apply all performance optimizations (default)
- `--restore` - Restore original settings from backup
- `--dry-run` - Show what would be changed without applying

### Modifiers  
- `--force` - Skip safety confirmation prompts
- `--skip-tools` - Skip package installation (for testing/restricted environments)

### Examples
```bash
# Safe interactive setup
python3 scripts/recover_environment.py

# Force apply without prompts or package installation
python3 scripts/recover_environment.py --apply --force --skip-tools

# Preview all changes
python3 scripts/recover_environment.py --dry-run

# Restore with confirmation
python3 scripts/recover_environment.py --restore
```

## Safety Features

### Automatic Backup
- **Complete State**: All modified settings backed up before changes
- **Backup Location**: `results/environment_backup.json`  
- **Metadata**: Includes timestamp, hostname, kernel version
- **Validation**: Backup integrity checked before restore

### Safe Restoration
- **Atomic Operations**: All-or-nothing restore approach
- **Error Handling**: Graceful failure with detailed error messages  
- **Manual Fallback**: Clear guidance for manual recovery if needed

### Rollback Protection
```bash
# Always create backup before applying
python3 scripts/recover_environment.py --apply

# Restore if something goes wrong  
python3 scripts/recover_environment.py --restore

# Validate environment after any changes
python3 scripts/validate_environment.py
```

## Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Ensure script is executable
chmod +x scripts/recover_environment.py

# Run with sudo for system modifications
sudo python3 scripts/recover_environment.py --apply
```

#### Backup Not Found
```bash
# Check backup location
ls -la results/environment_backup.json

# If missing, apply will create new backup
python3 scripts/recover_environment.py --apply
```

#### Partial Restoration
```bash
# Check which settings were restored
python3 scripts/recover_environment.py --restore

# Manually verify critical settings
python3 scripts/validate_environment.py

# Re-apply if needed
python3 scripts/recover_environment.py --apply
```

### Manual Recovery (If Script Fails)

#### CPU Governor
```bash
# Check current governor
cpupower frequency-info -p

# Set to performance
sudo cpupower frequency-set -g performance
```

#### SMT/Hyper-Threading
```bash
# Check status
cat /sys/devices/system/cpu/smt/control

# Disable SMT
echo off | sudo tee /sys/devices/system/cpu/smt/control
```

#### ASLR
```bash
# Check ASLR status
cat /proc/sys/kernel/randomize_va_space

# Disable ASLR
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
```

#### Performance Counters
```bash
# Enable hardware counters
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid

# Test access
perf stat -e cycles true
```

## Advanced Usage

### Custom Backup Location
```bash
# Modify backup_file path in script
self.backup_file = Path("/custom/path/environment_backup.json")
```

### Selective Restoration
```python
# Restore only specific settings
backup = recovery.load_backup()
# ... customize restoration logic
```

### Integration with Other Tools
```bash
# Use with numactl for NUMA binding
numactl --physcpubind=0-7 --membind=0 python3 scripts/run_benchmarks.py

# Combine with CPU isolation
# (requires manual kernel parameter setup)
```

## File Structure

```
scripts/
├── recover_environment.py      # Main recovery script
├── validate_environment.py     # Environment validation  
├── RECOVERY_GUIDE.md          # This guide
└── ...

results/
├── environment_backup.json    # System settings backup
├── environment_validation.json # Validation results
└── ...
```

## Best Practices

### Before Benchmarking
1. Always run `--dry-run` first to understand changes
2. Create backup with `--apply` (automatic)
3. Validate environment with `validate_environment.py`
4. Document any manual CPU isolation setup

### During Benchmarking  
1. Monitor system temperature and load
2. Use real-time monitoring for quality gates
3. Verify consistent performance across runs

### After Benchmarking
1. Always restore original settings with `--restore`
2. Verify restoration with `validate_environment.py`
3. Clean up temporary files and results as needed

### Production Systems
- **Never** run on production systems without testing
- Always use `--dry-run` first on new hardware
- Keep manual recovery procedures documented
- Test backup/restore cycle before relying on it

## Integration with Existing Workflow

This recovery script is designed to work seamlessly with:

- ✅ `validate_environment.py` - Addresses all validation requirements
- ✅ `benchmark-runner` wrapper - Environment setup before benchmarking  
- ✅ Real-time monitoring - Safe configuration for quality gates
- ✅ Evidence generation - Ensures consistent environment for results
- ✅ Hardware counter analysis - Proper `perf` access configuration

## Security Considerations

- **Temporary Changes**: All optimizations can be reversed
- **Backup Integrity**: Settings backed up before any modifications
- **Sudo Access**: Required for system-level performance tuning
- **Audit Trail**: All changes logged and documented in backup

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Verify backup exists and is valid
3. Run validation script to identify specific issues
4. Use manual recovery procedures as fallback