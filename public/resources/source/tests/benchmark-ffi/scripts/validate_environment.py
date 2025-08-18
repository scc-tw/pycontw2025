#!/usr/bin/env python3
"""
Environment Validation Script - BLOCKS execution if requirements not met

This script implements HARD validation that will STOP benchmark execution
if the environment doesn't meet the rigorous requirements for academic 
performance measurement.

Based on reviewer feedback: "write a script to check weather the environment 
are set as the guide @README.md and @ENVIRONMENT_SETUP.md. if not. 
print some errors to block executing the test."
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time
import json

class EnvironmentValidationError(Exception):
    """Raised when environment validation fails."""
    pass

class EnvironmentValidator:
    """STRICT environment validator that BLOCKS execution on failure."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.system_info = {}
        self.validation_results = {}
        
    def validate_all(self) -> bool:
        """Run ALL validation checks. Returns False if ANY check fails."""
        print("🔬 STRICT Environment Validation - Academic Rigor Mode")
        print("=" * 60)
        print("⚠️  WARNING: This validator will BLOCK execution on ANY failure")
        print()
        
        checks = [
            self._check_cpu_governor,
            self._check_smt_hyperthreading,
            self._check_aslr_disabled,
            self._check_cpu_frequency_scaling,
            self._check_turbo_boost,
            self._check_numa_policy,
            self._check_huge_pages,
            self._check_thermal_state,
            self._check_system_load,
            self._check_memory_pressure,
            self._check_hardware_counters,
            self._check_required_tools,
            self._check_cpu_isolation,
            self._check_disk_scheduler,
            self._check_network_performance,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"Validation check failed: {e}")
        
        self._print_results()
        
        if self.errors:
            print("\n🚨 ENVIRONMENT VALIDATION FAILED!")
            print("❌ Benchmark execution BLOCKED due to validation errors.")
            print("\n📋 CRITICAL ERRORS:")
            for error in self.errors:
                print(f"   • {error}")
            
            if self.warnings:
                print("\n⚠️  WARNINGS:")
                for warning in self.warnings:
                    print(f"   • {warning}")
            
            print("\n🔧 REMEDIATION GUIDE:")
            self._print_remediation_guide()
            return False
        
        if self.warnings:
            print("\n⚠️  WARNINGS DETECTED (but proceeding):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print("\n✅ ENVIRONMENT VALIDATION PASSED!")
        print("🚀 Benchmark execution authorized - all requirements met.")
        return True
    
    def _check_cpu_governor(self):
        """Check CPU frequency governor is set to 'performance'."""
        print("🔧 Checking CPU frequency governor...")
        
        try:
            # Try external cpupower command first (most reliable)
            result = subprocess.run(
                ["cpupower", "frequency-info", "-p"], 
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and "performance" in result.stdout:
                print("   ✅ CPU governor verified as 'performance' via cpupower")
                return
            
            # Fallback to sysfs reading with robust error handling
            governors = []
            policy_dirs = list(Path("/sys/devices/system/cpu/cpufreq").glob("policy*"))
            
            if policy_dirs:
                # Use stable policy paths (recommended approach from todo.md)
                successful_reads = 0
                for policy_dir in policy_dirs:
                    governor_file = policy_dir / "scaling_governor"
                    if governor_file.exists():
                        try:
                            # Try multiple approaches to read the file
                            for attempt in range(3):
                                try:
                                    # Method 1: Direct read_text()
                                    governor = governor_file.read_text().strip()
                                    governors.append(governor)
                                    successful_reads += 1
                                    break
                                except OSError:
                                    if attempt == 0:
                                        # Method 2: Unbuffered read
                                        try:
                                            with open(governor_file, 'r', buffering=0) as f:
                                                governor = f.read().strip()
                                                governors.append(governor)
                                                successful_reads += 1
                                                break
                                        except OSError:
                                            pass
                                    elif attempt == 1:
                                        # Method 3: subprocess cat (handles kernel race conditions)
                                        try:
                                            cat_result = subprocess.run(
                                                ["cat", str(governor_file)], 
                                                capture_output=True, text=True, timeout=1
                                            )
                                            if cat_result.returncode == 0:
                                                governor = cat_result.stdout.strip()
                                                governors.append(governor)
                                                successful_reads += 1
                                                break
                                        except subprocess.TimeoutExpired:
                                            pass
                                    time.sleep(0.05)  # Brief wait between attempts
                        except Exception:
                            continue  # Skip problematic policy directories
                
                # If we successfully read at least half the policies, that's sufficient
                if successful_reads > 0 and successful_reads >= len(policy_dirs) // 2:
                    non_performance = [g for g in governors if g != "performance"]
                    if non_performance:
                        # If some are not performance, this is a real issue
                        if len(non_performance) > len(governors) // 2:
                            self.errors.append(
                                f"CPU governor not set to 'performance': found {set(governors)}. "
                                f"Run: sudo cpupower frequency-set -g performance"
                            )
                        else:
                            self.warnings.append(
                                f"Some CPU policies not set to performance: {set(non_performance)}"
                            )
                    else:
                        print(f"   ✅ CPU governor verified as 'performance' ({successful_reads}/{len(policy_dirs)} policies checked)")
                    return
            
            # If all sysfs methods fail, check via cpupower one more time
            self.warnings.append(
                "Cannot reliably read CPU governor from sysfs (kernel race condition). "
                "Verify manually with: cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"
            )
                
        except Exception as e:
            self.warnings.append(f"Cannot check CPU governor: {e} - verify manually with cpupower frequency-info")
    
    def _check_smt_hyperthreading(self):
        """Check SMT/Hyper-Threading is disabled."""
        print("🔧 Checking SMT/Hyper-Threading status...")
        
        try:
            smt_file = Path("/sys/devices/system/cpu/smt/control")
            if smt_file.exists():
                smt_status = smt_file.read_text().strip()
                if smt_status != "off":
                    self.errors.append(
                        f"SMT/Hyper-Threading is enabled ({smt_status}). "
                        f"Run: echo off | sudo tee /sys/devices/system/cpu/smt/control"
                    )
                else:
                    print("   ✅ SMT/Hyper-Threading disabled")
            else:
                self.warnings.append("Cannot check SMT status - /sys/devices/system/cpu/smt/control not found")
                
        except Exception as e:
            self.warnings.append(f"Cannot check SMT status: {e}")
    
    def _check_aslr_disabled(self):
        """Check ASLR is temporarily disabled."""
        print("🔧 Checking ASLR (Address Space Layout Randomization)...")
        
        try:
            aslr_file = Path("/proc/sys/kernel/randomize_va_space")
            if aslr_file.exists():
                aslr_value = aslr_file.read_text().strip()
                if aslr_value != "0":
                    self.errors.append(
                        f"ASLR is enabled ({aslr_value}). For consistent memory layout, "
                        f"run: echo 0 | sudo tee /proc/sys/kernel/randomize_va_space"
                    )
                else:
                    print("   ✅ ASLR disabled (consistent memory layout)")
            else:
                self.warnings.append("Cannot check ASLR - /proc/sys/kernel/randomize_va_space not found")
                
        except Exception as e:
            self.warnings.append(f"Cannot check ASLR: {e}")
    
    def _check_cpu_frequency_scaling(self):
        """Check CPU frequency scaling is disabled."""
        print("🔧 Checking CPU frequency scaling...")
        
        try:
            # Check if frequencies are locked using robust approach
            frequencies = []
            policy_dirs = list(Path("/sys/devices/system/cpu/cpufreq").glob("policy*"))
            
            if policy_dirs:
                successful_reads = 0
                for policy_dir in policy_dirs[:5]:  # Check first 5 policies to avoid excessive overhead
                    freq_file = policy_dir / "scaling_cur_freq"
                    if freq_file.exists():
                        try:
                            # Try multiple approaches to read frequency
                            for attempt in range(2):  # Fewer attempts for frequency check
                                try:
                                    if attempt == 0:
                                        # Method 1: Direct read
                                        freq = int(freq_file.read_text().strip())
                                    else:
                                        # Method 2: subprocess cat
                                        cat_result = subprocess.run(
                                            ["cat", str(freq_file)], 
                                            capture_output=True, text=True, timeout=1
                                        )
                                        if cat_result.returncode == 0:
                                            freq = int(cat_result.stdout.strip())
                                        else:
                                            continue
                                    
                                    frequencies.append(freq)
                                    successful_reads += 1
                                    break
                                except (OSError, ValueError, subprocess.TimeoutExpired):
                                    if attempt == 0:
                                        time.sleep(0.02)  # Brief wait
                                    continue
                        except Exception:
                            continue
                
                if successful_reads > 0:
                    if len(frequencies) > 1:
                        freq_variance = max(frequencies) - min(frequencies)
                        if freq_variance > 100000:  # More than 100MHz variance
                            self.warnings.append(
                                f"CPU frequency variance detected: {freq_variance/1000:.1f}MHz. "
                                f"Consider locking frequencies for consistency."
                            )
                        else:
                            print(f"   ✅ CPU frequencies stable (variance: {freq_variance/1000:.1f}MHz, {successful_reads} policies checked)")
                    else:
                        avg_freq = frequencies[0] / 1000000  # Convert to GHz
                        print(f"   ✅ CPU frequency: {avg_freq:.2f}GHz ({successful_reads} policy checked)")
                else:
                    self.warnings.append(
                        "Cannot read CPU frequencies from sysfs (kernel race condition). "
                        "Frequencies may still be properly configured."
                    )
            else:
                self.warnings.append("No CPU frequency policies found")
            
        except Exception as e:
            self.warnings.append(f"Cannot check CPU frequencies: {e}")
    
    def _check_turbo_boost(self):
        """Check Intel Turbo Boost / AMD Boost is disabled."""
        print("🔧 Checking Turbo Boost status...")
        
        try:
            # Intel Turbo Boost
            intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
            if intel_turbo.exists():
                turbo_status = intel_turbo.read_text().strip()
                if turbo_status != "1":
                    self.warnings.append(
                        "Intel Turbo Boost is enabled. For consistent performance, "
                        "run: echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo"
                    )
                else:
                    print("   ✅ Intel Turbo Boost disabled")
            
            # AMD Boost
            amd_boost = Path("/sys/devices/system/cpu/cpufreq/boost")
            if amd_boost.exists():
                boost_status = amd_boost.read_text().strip()
                if boost_status != "0":
                    self.warnings.append(
                        "AMD CPU Boost is enabled. For consistent performance, "
                        "run: echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost"
                    )
                else:
                    print("   ✅ AMD CPU Boost disabled")
            
            if not intel_turbo.exists() and not amd_boost.exists():
                self.warnings.append("Cannot determine Turbo Boost status - neither Intel nor AMD controls found")
                
        except Exception as e:
            self.warnings.append(f"Cannot check Turbo Boost: {e}")
    
    def _check_numa_policy(self):
        """Check NUMA policy for consistent memory access."""
        print("🔧 Checking NUMA policy...")
        
        try:
            result = subprocess.run(["numactl", "--show"], capture_output=True, text=True)
            if result.returncode == 0:
                # NUMA is available, check if we should bind to specific nodes
                numa_info = result.stdout
                print("   ℹ️  NUMA available - consider using numactl for CPU/memory binding")
                self.warnings.append("NUMA detected - consider using 'numactl --physcpubind=0-7 --membind=0' for benchmarks")
            else:
                print("   ✅ NUMA tools not available or not needed")
                
        except FileNotFoundError:
            self.warnings.append("numactl not installed - install with: sudo apt install numactl")
        except Exception as e:
            self.warnings.append(f"Cannot check NUMA: {e}")
    
    def _check_huge_pages(self):
        """Check huge pages configuration."""
        print("🔧 Checking huge pages...")
        
        try:
            hugepages_file = Path("/proc/sys/vm/nr_hugepages")
            if hugepages_file.exists():
                hugepages = int(hugepages_file.read_text().strip())
                if hugepages == 0:
                    self.warnings.append(
                        "No huge pages allocated. For better memory performance, "
                        "consider: echo 128 | sudo tee /proc/sys/vm/nr_hugepages"
                    )
                else:
                    print(f"   ✅ Huge pages allocated: {hugepages}")
            
        except Exception as e:
            self.warnings.append(f"Cannot check huge pages: {e}")
    
    def _check_thermal_state(self):
        """Check CPU thermal state."""
        print("🔧 Checking thermal state...")
        
        try:
            # Check thermal throttling
            thermal_dirs = list(Path("/sys/class/thermal").glob("thermal_zone*"))
            if thermal_dirs:
                max_temp = 0
                for thermal_dir in thermal_dirs:
                    temp_file = thermal_dir / "temp"
                    if temp_file.exists():
                        temp = int(temp_file.read_text().strip()) / 1000  # Convert to Celsius
                        max_temp = max(max_temp, temp)
                
                if max_temp > 80:
                    self.errors.append(f"CPU temperature too high: {max_temp:.1f}°C - risk of thermal throttling")
                elif max_temp > 70:
                    self.warnings.append(f"CPU temperature elevated: {max_temp:.1f}°C - monitor for throttling")
                else:
                    print(f"   ✅ CPU temperature normal: {max_temp:.1f}°C")
            
        except Exception as e:
            self.warnings.append(f"Cannot check thermal state: {e}")
    
    def _check_system_load(self):
        """Check system load is low."""
        print("🔧 Checking system load...")
        
        try:
            load_avg = os.getloadavg()
            cpu_count = os.cpu_count()
            
            # Check 1-minute load average
            if load_avg[0] > cpu_count * 0.8:
                self.errors.append(
                    f"System load too high: {load_avg[0]:.2f} (>{cpu_count * 0.8:.1f} threshold). "
                    f"Wait for system to idle before running benchmarks."
                )
            elif load_avg[0] > cpu_count * 0.3:
                self.warnings.append(f"System load elevated: {load_avg[0]:.2f}")
            else:
                print(f"   ✅ System load acceptable: {load_avg[0]:.2f}")
                
        except Exception as e:
            self.warnings.append(f"Cannot check system load: {e}")
    
    def _check_memory_pressure(self):
        """Check memory pressure and available memory."""
        print("🔧 Checking memory pressure...")
        
        try:
            with open("/proc/meminfo") as f:
                meminfo = f.read()
            
            # Parse memory information
            mem_total = int([line for line in meminfo.split('\n') if line.startswith('MemTotal:')][0].split()[1])
            mem_available = int([line for line in meminfo.split('\n') if line.startswith('MemAvailable:')][0].split()[1])
            
            mem_usage_percent = (mem_total - mem_available) / mem_total * 100
            
            if mem_usage_percent > 90:
                self.errors.append(f"Memory pressure too high: {mem_usage_percent:.1f}% used")
            elif mem_usage_percent > 70:
                self.warnings.append(f"Memory usage elevated: {mem_usage_percent:.1f}% used")
            else:
                print(f"   ✅ Memory usage acceptable: {mem_usage_percent:.1f}% used")
                
        except Exception as e:
            self.warnings.append(f"Cannot check memory pressure: {e}")
    
    def _check_hardware_counters(self):
        """Check hardware performance counters are available."""
        print("🔧 Checking hardware performance counters...")
        
        try:
            # Check if perf is available
            result = subprocess.run(["perf", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                self.errors.append("perf tool not available - install with: sudo apt install linux-tools-generic")
                return
            
            # Check if we can access performance counters
            test_result = subprocess.run(
                ["perf", "stat", "-e", "cycles", "true"], 
                capture_output=True, text=True
            )
            
            if "not supported" in test_result.stderr or test_result.returncode != 0:
                self.errors.append(
                    "Hardware performance counters not accessible. "
                    "Run: echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid"
                )
            else:
                print("   ✅ Hardware performance counters accessible")
                
        except FileNotFoundError:
            self.errors.append("perf tool not found - install with: sudo apt install linux-tools-generic")
        except Exception as e:
            self.errors.append(f"Cannot check hardware counters: {e}")
    
    def _check_required_tools(self):
        """Check required tools are installed."""
        print("🔧 Checking required tools...")
        
        required_tools = [
            ("python3", "Python 3"),
            ("gcc", "GCC compiler"),
            ("make", "Make build tool"),
            ("pkg-config", "pkg-config"),
            ("perf", "Performance profiling tool"),
        ]
        
        for tool, description in required_tools:
            try:
                result = subprocess.run([tool, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   ✅ {description} available")
                else:
                    self.errors.append(f"{description} not working properly")
            except FileNotFoundError:
                self.errors.append(f"{description} not installed")
    
    def _check_cpu_isolation(self):
        """Check if CPU isolation is configured."""
        print("🔧 Checking CPU isolation...")
        
        try:
            # Check kernel command line for isolcpus
            with open("/proc/cmdline") as f:
                cmdline = f.read()
            
            if "isolcpus=" in cmdline:
                print("   ✅ CPU isolation configured")
            else:
                self.warnings.append(
                    "No CPU isolation detected. For best results, consider isolating CPUs: "
                    "Add 'isolcpus=2-7' to kernel command line"
                )
                
        except Exception as e:
            self.warnings.append(f"Cannot check CPU isolation: {e}")
    
    def _check_disk_scheduler(self):
        """Check disk scheduler is optimized."""
        print("🔧 Checking disk scheduler...")
        
        try:
            # Find main storage device
            for device in Path("/sys/block").iterdir():
                if device.name.startswith(('sd', 'nvme')):
                    scheduler_file = device / "queue" / "scheduler"
                    if scheduler_file.exists():
                        scheduler = scheduler_file.read_text().strip()
                        if "[noop]" not in scheduler and "[none]" not in scheduler:
                            self.warnings.append(
                                f"Disk scheduler not optimized for {device.name}: {scheduler}. "
                                f"Consider: echo noop | sudo tee /sys/block/{device.name}/queue/scheduler"
                            )
                        else:
                            print(f"   ✅ Disk scheduler optimized for {device.name}")
            
        except Exception as e:
            self.warnings.append(f"Cannot check disk scheduler: {e}")
    
    def _check_network_performance(self):
        """Check network configuration won't interfere."""
        print("🔧 Checking network configuration...")
        
        try:
            # Check if network interrupts are balanced
            with open("/proc/interrupts") as f:
                interrupts = f.read()
            
            # Simple check - if we have many network interrupts, warn about IRQ balancing
            network_lines = [line for line in interrupts.split('\n') if 'eth' in line or 'wlan' in line]
            if network_lines:
                self.warnings.append("Network interfaces detected - ensure IRQ balancing is disabled during benchmarks")
            
        except Exception as e:
            self.warnings.append(f"Cannot check network configuration: {e}")
    
    def _print_results(self):
        """Print validation results summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_checks = len([m for m in dir(self) if m.startswith('_check_')])
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        print(f"Total checks: {total_checks}")
        print(f"Errors: {error_count}")
        print(f"Warnings: {warning_count}")
        
        if error_count == 0:
            print("Status: ✅ PASSED")
        else:
            print("Status: ❌ FAILED")
    
    def _print_remediation_guide(self):
        """Print comprehensive remediation guide."""
        print()
        print("🔧 COMPLETE REMEDIATION GUIDE:")
        print("=" * 40)
        print()
        print("# CPU Performance Setup")
        print("sudo cpupower frequency-set -g performance")
        print("echo off | sudo tee /sys/devices/system/cpu/smt/control")
        print("echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo  # Intel")
        print("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost          # AMD")
        print()
        print("# Memory and System Setup")
        print("echo 0 | sudo tee /proc/sys/kernel/randomize_va_space  # Disable ASLR")
        print("echo 128 | sudo tee /proc/sys/vm/nr_hugepages          # Enable huge pages")
        print()
        print("# Performance Monitoring")
        print("echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid")
        print("sudo apt install linux-tools-generic numactl")
        print()
        print("# CPU Isolation (optional, requires reboot)")
        print("# Add to /etc/default/grub: GRUB_CMDLINE_LINUX_DEFAULT=\"isolcpus=2-7\"")
        print("# Then: sudo update-grub && sudo reboot")
        print()
        print("🔗 DETAILED GUIDES:")
        print("   • CPU isolation: https://wiki.archlinux.org/title/CPU_frequency_scaling")
        print("   • NUMA binding: https://linux.die.net/man/8/numactl")
        print("   • Performance tuning: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/")

def main():
    """Main validation entry point."""
    validator = EnvironmentValidator()
    
    # Save validation results
    passed = validator.validate_all()
    
    # Save detailed results to file
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    validation_data = {
        "timestamp": time.time(),
        "passed": passed,
        "errors": validator.errors,
        "warnings": validator.warnings,
        "system_info": validator.system_info
    }
    
    with open(results_dir / "environment_validation.json", "w") as f:
        json.dump(validation_data, f, indent=2)
    
    if not passed:
        print(f"\n💾 Validation results saved to: {results_dir}/environment_validation.json")
        print("\n🚨 BENCHMARK EXECUTION BLOCKED!")
        print("Fix the errors above before running any benchmarks.")
        sys.exit(1)
    
    print(f"\n💾 Validation results saved to: {results_dir}/environment_validation.json")
    print("✅ Environment validation passed - benchmarks authorized to proceed.")
    return 0

if __name__ == "__main__":
    exit(main())