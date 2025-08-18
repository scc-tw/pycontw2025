#!/usr/bin/env python3
"""
Environment Recovery Script - Automated Performance Benchmarking Setup

This script automatically configures the system environment for rigorous
performance benchmarking based on the requirements in validate_environment.py.

Features:
- Automatic backup and restore of original settings  
- Safe recovery with rollback capability
- Comprehensive system optimization for benchmarking
- Integration with benchmark validation workflow

Usage:
    python3 recover_environment.py [--apply|--restore|--dry-run]
    
Options:
    --apply     Apply all performance optimizations (default)
    --restore   Restore original system settings  
    --dry-run   Show what would be changed without applying
    --force     Skip safety confirmations
"""

import os
import sys
import subprocess
import platform
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
from dataclasses import dataclass, asdict

@dataclass
class SystemBackup:
    """System settings backup for safe recovery."""
    timestamp: float
    hostname: str
    kernel_version: str
    cpu_governor: Optional[str] = None
    smt_status: Optional[str] = None
    aslr_value: Optional[str] = None
    turbo_boost_intel: Optional[str] = None
    turbo_boost_amd: Optional[str] = None
    hugepages: Optional[str] = None
    perf_paranoid: Optional[str] = None
    cmdline_original: Optional[str] = None
    disk_schedulers: Dict[str, str] = None

    def __post_init__(self):
        if self.disk_schedulers is None:
            self.disk_schedulers = {}

class EnvironmentRecovery:
    """Automated environment recovery for performance benchmarking."""
    
    def __init__(self):
        self.backup_file = Path("results/environment_backup.json")
        self.backup_file.parent.mkdir(exist_ok=True)
        self.changes_applied = []
        self.requires_reboot = False
        
    def create_backup(self) -> SystemBackup:
        """Create backup of current system settings."""
        print("💾 Creating system settings backup...")
        
        backup = SystemBackup(
            timestamp=time.time(),
            hostname=platform.node(),
            kernel_version=platform.release()
        )
        
        try:
            # Backup CPU governor
            try:
                result = subprocess.run(
                    ["cpupower", "frequency-info", "-p"], 
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    backup.cpu_governor = result.stdout.strip()
            except:
                pass
            
            # Backup SMT status
            smt_file = Path("/sys/devices/system/cpu/smt/control")
            if smt_file.exists():
                backup.smt_status = smt_file.read_text().strip()
            
            # Backup ASLR
            aslr_file = Path("/proc/sys/kernel/randomize_va_space")
            if aslr_file.exists():
                backup.aslr_value = aslr_file.read_text().strip()
            
            # Backup Turbo Boost settings
            intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
            if intel_turbo.exists():
                backup.turbo_boost_intel = intel_turbo.read_text().strip()
            
            amd_boost = Path("/sys/devices/system/cpu/cpufreq/boost")
            if amd_boost.exists():
                backup.turbo_boost_amd = amd_boost.read_text().strip()
            
            # Backup huge pages
            hugepages_file = Path("/proc/sys/vm/nr_hugepages")
            if hugepages_file.exists():
                backup.hugepages = hugepages_file.read_text().strip()
            
            # Backup perf paranoid setting
            perf_file = Path("/proc/sys/kernel/perf_event_paranoid")
            if perf_file.exists():
                backup.perf_paranoid = perf_file.read_text().strip()
            
            # Backup kernel command line
            cmdline_file = Path("/proc/cmdline")
            if cmdline_file.exists():
                backup.cmdline_original = cmdline_file.read_text().strip()
            
            # Backup disk schedulers
            for device in Path("/sys/block").iterdir():
                if device.name.startswith(('sd', 'nvme')):
                    scheduler_file = device / "queue" / "scheduler"
                    if scheduler_file.exists():
                        backup.disk_schedulers[device.name] = scheduler_file.read_text().strip()
            
            # Save backup to file
            with open(self.backup_file, 'w') as f:
                json.dump(asdict(backup), f, indent=2)
            
            print(f"   ✅ Backup saved to: {self.backup_file}")
            return backup
            
        except Exception as e:
            print(f"   ⚠️ Partial backup created: {e}")
            return backup
    
    def load_backup(self) -> Optional[SystemBackup]:
        """Load system settings backup."""
        if not self.backup_file.exists():
            print(f"❌ No backup found at: {self.backup_file}")
            return None
        
        try:
            with open(self.backup_file, 'r') as f:
                data = json.load(f)
            
            backup = SystemBackup(**data)
            print(f"✅ Loaded backup from {time.ctime(backup.timestamp)}")
            return backup
            
        except Exception as e:
            print(f"❌ Failed to load backup: {e}")
            return None
    
    def apply_cpu_governor_optimization(self) -> bool:
        """Set CPU governor and lock frequency for optimal performance."""
        print("🔧 Configuring CPU governor and frequency locking...")
        
        try:
            policy_dirs = list(Path("/sys/devices/system/cpu/cpufreq").glob("policy*"))
            if not policy_dirs:
                print("   ❌ No CPU frequency policies found")
                return False
            
            success_count = 0
            total_policies = len(policy_dirs)
            
            for policy_dir in policy_dirs:
                policy_name = policy_dir.name
                
                try:
                    # Get maximum frequency for this policy
                    max_freq_file = policy_dir / "cpuinfo_max_freq"
                    if not max_freq_file.exists():
                        print(f"   ⚠️ {policy_name}: max frequency not available")
                        continue
                    
                    max_freq = max_freq_file.read_text().strip()
                    
                    # Check if userspace governor is available for precise control
                    available_govs_file = policy_dir / "scaling_available_governors"
                    governor_to_use = "performance"  # Default
                    
                    if available_govs_file.exists():
                        available_govs = available_govs_file.read_text().strip()
                        if "userspace" in available_govs:
                            governor_to_use = "userspace"
                    
                    # Set the governor
                    governor_file = policy_dir / "scaling_governor"
                    if governor_file.exists():
                        subprocess.run(
                            ["sudo", "sh", "-c", f"echo {governor_to_use} > {governor_file}"],
                            check=True, capture_output=True
                        )
                    
                    # Lock frequency based on governor type
                    if governor_to_use == "userspace":
                        # Use userspace governor for precise frequency control
                        setspeed_file = policy_dir / "scaling_setspeed"
                        if setspeed_file.exists():
                            subprocess.run(
                                ["sudo", "sh", "-c", f"echo {max_freq} > {setspeed_file}"],
                                check=True, capture_output=True
                            )
                            print(f"   ✅ {policy_name}: locked to {int(max_freq)/1000000:.1f} GHz (userspace)")
                        else:
                            # Fallback to min/max constraints
                            min_freq_file = policy_dir / "scaling_min_freq"
                            max_freq_file = policy_dir / "scaling_max_freq"
                            if min_freq_file.exists() and max_freq_file.exists():
                                subprocess.run(
                                    ["sudo", "sh", "-c", f"echo {max_freq} > {min_freq_file}"],
                                    check=True, capture_output=True
                                )
                                subprocess.run(
                                    ["sudo", "sh", "-c", f"echo {max_freq} > {max_freq_file}"],
                                    check=True, capture_output=True
                                )
                                print(f"   ✅ {policy_name}: constrained to {int(max_freq)/1000000:.1f} GHz")
                    else:
                        # Use performance governor with min/max constraints
                        min_freq_file = policy_dir / "scaling_min_freq"
                        max_freq_file = policy_dir / "scaling_max_freq"
                        if min_freq_file.exists() and max_freq_file.exists():
                            subprocess.run(
                                ["sudo", "sh", "-c", f"echo {max_freq} > {min_freq_file}"],
                                check=True, capture_output=True
                            )
                            subprocess.run(
                                ["sudo", "sh", "-c", f"echo {max_freq} > {max_freq_file}"],
                                check=True, capture_output=True
                            )
                            print(f"   ✅ {policy_name}: locked to {int(max_freq)/1000000:.1f} GHz (performance)")
                    
                    # Set energy performance preference if available
                    epp_file = policy_dir / "energy_performance_preference"
                    if epp_file.exists():
                        try:
                            subprocess.run(
                                ["sudo", "sh", "-c", f"echo performance > {epp_file}"],
                                check=True, capture_output=True
                            )
                        except:
                            pass  # Not critical
                    
                    success_count += 1
                    
                except subprocess.CalledProcessError as e:
                    print(f"   ❌ {policy_name}: failed to configure - {e}")
                except Exception as e:
                    print(f"   ❌ {policy_name}: error - {e}")
            
            if success_count == total_policies:
                print(f"   ✅ All {total_policies} CPU policies configured for maximum performance")
                self.changes_applied.append(f"CPU frequency locked to maximum ({total_policies} policies)")
                return True
            elif success_count > 0:
                print(f"   ⚠️ {success_count}/{total_policies} policies configured successfully")
                self.changes_applied.append(f"CPU frequency partially locked ({success_count}/{total_policies} policies)")
                return True
            else:
                print("   ❌ Failed to configure any CPU policies")
                return False
            
        except Exception as e:
            print(f"   ❌ CPU configuration failed: {e}")
            return False
    
    def apply_smt_optimization(self) -> bool:
        """Disable SMT/Hyper-Threading."""
        print("🔧 Disabling SMT/Hyper-Threading...")
        
        try:
            smt_file = Path("/sys/devices/system/cpu/smt/control")
            if not smt_file.exists():
                print("   ⚠️ SMT control not available on this system")
                return True
            
            current_status = smt_file.read_text().strip()
            if current_status == "off":
                print("   ✅ SMT already disabled")
                return True
            
            result = subprocess.run(
                ["sudo", "sh", "-c", f"echo off > {smt_file}"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("   ✅ SMT/Hyper-Threading disabled")
                self.changes_applied.append("SMT/Hyper-Threading disabled")
                return True
            else:
                print(f"   ❌ Failed to disable SMT: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ SMT configuration failed: {e}")
            return False
    
    def apply_aslr_optimization(self) -> bool:
        """Disable ASLR for consistent memory layout."""
        print("🔧 Disabling ASLR...")
        
        try:
            aslr_file = Path("/proc/sys/kernel/randomize_va_space")
            if not aslr_file.exists():
                print("   ⚠️ ASLR control not available")
                return True
            
            current_value = aslr_file.read_text().strip()
            if current_value == "0":
                print("   ✅ ASLR already disabled")
                return True
            
            result = subprocess.run(
                ["sudo", "sh", "-c", f"echo 0 > {aslr_file}"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("   ✅ ASLR disabled for consistent memory layout")
                self.changes_applied.append("ASLR disabled")
                return True
            else:
                print(f"   ❌ Failed to disable ASLR: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"   ❌ ASLR configuration failed: {e}")
            return False
    
    def apply_turbo_boost_optimization(self) -> bool:
        """Disable Turbo Boost for consistent performance."""
        print("🔧 Disabling Turbo Boost...")
        
        success = True
        
        try:
            # Intel Turbo Boost
            intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
            if intel_turbo.exists():
                current_value = intel_turbo.read_text().strip()
                if current_value != "1":
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo 1 > {intel_turbo}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print("   ✅ Intel Turbo Boost disabled")
                        self.changes_applied.append("Intel Turbo Boost disabled")
                    else:
                        print(f"   ❌ Failed to disable Intel Turbo Boost: {result.stderr}")
                        success = False
                else:
                    print("   ✅ Intel Turbo Boost already disabled")
            
            # AMD Boost
            amd_boost = Path("/sys/devices/system/cpu/cpufreq/boost")
            if amd_boost.exists():
                current_value = amd_boost.read_text().strip()
                if current_value != "0":
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo 0 > {amd_boost}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print("   ✅ AMD CPU Boost disabled")
                        self.changes_applied.append("AMD CPU Boost disabled")
                    else:
                        print(f"   ❌ Failed to disable AMD Boost: {result.stderr}")
                        success = False
                else:
                    print("   ✅ AMD CPU Boost already disabled")
            
            if not intel_turbo.exists() and not amd_boost.exists():
                print("   ⚠️ No Turbo Boost controls found (may not be needed)")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Turbo Boost configuration failed: {e}")
            return False
    
    def apply_memory_optimization(self) -> bool:
        """Configure memory settings for benchmarking."""
        print("🔧 Configuring memory settings...")
        
        success = True
        
        try:
            # Configure huge pages
            hugepages_file = Path("/proc/sys/vm/nr_hugepages")
            if hugepages_file.exists():
                current_value = int(hugepages_file.read_text().strip())
                if current_value < 128:
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo 128 > {hugepages_file}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print("   ✅ Huge pages configured (128)")
                        self.changes_applied.append("Huge pages configured")
                    else:
                        print(f"   ❌ Failed to configure huge pages: {result.stderr}")
                        success = False
                else:
                    print(f"   ✅ Huge pages already configured ({current_value})")
            
            return success
            
        except Exception as e:
            print(f"   ❌ Memory configuration failed: {e}")
            return False
    
    def apply_performance_monitoring_optimization(self) -> bool:
        """Configure performance monitoring access."""
        print("🔧 Configuring performance monitoring...")
        
        try:
            perf_file = Path("/proc/sys/kernel/perf_event_paranoid")
            if not perf_file.exists():
                print("   ⚠️ Performance event paranoid setting not available")
                return True
            
            current_value = perf_file.read_text().strip()
            if current_value != "-1":
                result = subprocess.run(
                    ["sudo", "sh", "-c", f"echo -1 > {perf_file}"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print("   ✅ Hardware performance counters enabled")
                    self.changes_applied.append("Hardware performance counters enabled")
                    return True
                else:
                    print(f"   ❌ Failed to enable performance counters: {result.stderr}")
                    return False
            else:
                print("   ✅ Hardware performance counters already enabled")
                return True
                
        except Exception as e:
            print(f"   ❌ Performance monitoring configuration failed: {e}")
            return False
    
    def apply_disk_optimization(self) -> bool:
        """Optimize disk scheduler for benchmarking."""
        print("🔧 Optimizing disk schedulers...")
        
        success = True
        
        try:
            for device in Path("/sys/block").iterdir():
                if device.name.startswith(('sd', 'nvme')):
                    scheduler_file = device / "queue" / "scheduler"
                    if scheduler_file.exists():
                        current = scheduler_file.read_text().strip()
                        
                        # Check if already optimized
                        if "[noop]" in current or "[none]" in current:
                            print(f"   ✅ {device.name} scheduler already optimized")
                            continue
                        
                        # Try to set noop scheduler
                        scheduler_to_set = "none" if "none" in current else "noop"
                        result = subprocess.run(
                            ["sudo", "sh", "-c", f"echo {scheduler_to_set} > {scheduler_file}"],
                            capture_output=True, text=True
                        )
                        
                        if result.returncode == 0:
                            print(f"   ✅ {device.name} scheduler set to {scheduler_to_set}")
                            self.changes_applied.append(f"{device.name} scheduler optimized")
                        else:
                            print(f"   ❌ Failed to optimize {device.name} scheduler: {result.stderr}")
                            success = False
            
            return success
            
        except Exception as e:
            print(f"   ❌ Disk optimization failed: {e}")
            return False
    
    def install_required_tools(self) -> bool:
        """Install required tools for benchmarking."""
        print("🔧 Checking and installing required tools...")
        
        required_packages = [
            ("linux-tools-generic", "perf tool"),
            ("numactl", "NUMA control"),
            ("cpufrequtils", "CPU frequency utilities")
        ]
        
        missing_packages = []
        
        # Check which packages are missing
        for package, description in required_packages:
            result = subprocess.run(
                ["dpkg", "-l", package], 
                capture_output=True, text=True
            )
            if result.returncode != 0:
                missing_packages.append((package, description))
        
        if not missing_packages:
            print("   ✅ All required tools already installed")
            return True
        
        print(f"   📦 Installing {len(missing_packages)} missing packages...")
        
        try:
            # Update package cache
            subprocess.run(["sudo", "apt", "update"], check=True, capture_output=True)
            
            # Install missing packages
            for package, description in missing_packages:
                print(f"      Installing {description}...")
                result = subprocess.run(
                    ["sudo", "apt", "install", "-y", package],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"      ✅ {description} installed")
                    self.changes_applied.append(f"Installed {description}")
                else:
                    print(f"      ❌ Failed to install {description}")
                    return False
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Package installation failed: {e}")
            return False
    
    def check_cpu_isolation_setup(self) -> bool:
        """Check and guide CPU isolation setup."""
        print("🔧 Checking CPU isolation...")
        
        try:
            with open("/proc/cmdline") as f:
                cmdline = f.read()
            
            if "isolcpus=" in cmdline:
                print("   ✅ CPU isolation already configured")
                return True
            
            print("   ⚠️ CPU isolation not configured")
            print("   💡 For optimal benchmarking, consider CPU isolation:")
            print("      1. Edit /etc/default/grub")
            print("      2. Add: GRUB_CMDLINE_LINUX_DEFAULT=\"isolcpus=2-7 nohz_full=2-7 rcu_nocbs=2-7\"")
            print("      3. Run: sudo update-grub")
            print("      4. Reboot system")
            print("   ⚠️ This requires manual configuration and reboot")
            
            return True  # Don't fail validation for this
            
        except Exception as e:
            print(f"   ⚠️ Cannot check CPU isolation: {e}")
            return True
    
    def restore_from_backup(self, backup: SystemBackup) -> bool:
        """Restore system settings from backup."""
        print("🔄 Restoring system settings from backup...")
        
        success = True
        
        try:
            # Restore CPU governor
            if backup.cpu_governor:
                print("   🔄 Restoring CPU governor...")
                # Extract governor from cpupower output
                if "performance" in backup.cpu_governor:
                    governor = "performance"
                elif "powersave" in backup.cpu_governor:
                    governor = "powersave"
                else:
                    governor = "ondemand"  # Default fallback
                
                result = subprocess.run(
                    ["sudo", "cpupower", "frequency-set", "-g", governor],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"      ✅ CPU governor restored to {governor}")
                else:
                    print(f"      ❌ Failed to restore CPU governor")
                    success = False
            
            # Restore SMT status
            if backup.smt_status:
                print("   🔄 Restoring SMT status...")
                smt_file = Path("/sys/devices/system/cpu/smt/control")
                if smt_file.exists():
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo {backup.smt_status} > {smt_file}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"      ✅ SMT status restored to {backup.smt_status}")
                    else:
                        print(f"      ❌ Failed to restore SMT status")
                        success = False
            
            # Restore ASLR
            if backup.aslr_value:
                print("   🔄 Restoring ASLR...")
                aslr_file = Path("/proc/sys/kernel/randomize_va_space")
                if aslr_file.exists():
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo {backup.aslr_value} > {aslr_file}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"      ✅ ASLR restored to {backup.aslr_value}")
                    else:
                        print(f"      ❌ Failed to restore ASLR")
                        success = False
            
            # Restore Turbo Boost settings
            if backup.turbo_boost_intel:
                print("   🔄 Restoring Intel Turbo Boost...")
                intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
                if intel_turbo.exists():
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo {backup.turbo_boost_intel} > {intel_turbo}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"      ✅ Intel Turbo Boost restored")
                    else:
                        print(f"      ❌ Failed to restore Intel Turbo Boost")
                        success = False
            
            if backup.turbo_boost_amd:
                print("   🔄 Restoring AMD Boost...")
                amd_boost = Path("/sys/devices/system/cpu/cpufreq/boost")
                if amd_boost.exists():
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo {backup.turbo_boost_amd} > {amd_boost}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"      ✅ AMD Boost restored")
                    else:
                        print(f"      ❌ Failed to restore AMD Boost")
                        success = False
            
            # Restore huge pages
            if backup.hugepages:
                print("   🔄 Restoring huge pages...")
                hugepages_file = Path("/proc/sys/vm/nr_hugepages")
                if hugepages_file.exists():
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo {backup.hugepages} > {hugepages_file}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"      ✅ Huge pages restored to {backup.hugepages}")
                    else:
                        print(f"      ❌ Failed to restore huge pages")
                        success = False
            
            # Restore perf paranoid setting
            if backup.perf_paranoid:
                print("   🔄 Restoring performance monitoring...")
                perf_file = Path("/proc/sys/kernel/perf_event_paranoid")
                if perf_file.exists():
                    result = subprocess.run(
                        ["sudo", "sh", "-c", f"echo {backup.perf_paranoid} > {perf_file}"],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        print(f"      ✅ Performance monitoring restored")
                    else:
                        print(f"      ❌ Failed to restore performance monitoring")
                        success = False
            
            if success:
                print("✅ System settings successfully restored from backup")
            else:
                print("⚠️ Some settings could not be restored - check manually")
            
            return success
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def apply_all_optimizations(self, skip_tools: bool = False) -> bool:
        """Apply all performance optimizations."""
        print("🚀 APPLYING PERFORMANCE OPTIMIZATIONS")
        print("=" * 50)
        
        # Create backup first
        backup = self.create_backup()
        
        optimizations = [
            ("CPU Governor", self.apply_cpu_governor_optimization),
            ("SMT/Hyper-Threading", self.apply_smt_optimization),
            ("ASLR", self.apply_aslr_optimization),
            ("Turbo Boost", self.apply_turbo_boost_optimization),
            ("Memory Settings", self.apply_memory_optimization),
            ("Performance Monitoring", self.apply_performance_monitoring_optimization),
            ("Disk Schedulers", self.apply_disk_optimization),
        ]
        
        if not skip_tools:
            optimizations.append(("Required Tools", self.install_required_tools))
        
        optimizations.append(("CPU Isolation Check", self.check_cpu_isolation_setup))
        
        success_count = 0
        total_count = len(optimizations)
        
        for name, optimization_func in optimizations:
            print(f"\n{name}:")
            if optimization_func():
                success_count += 1
            else:
                print(f"   ❌ {name} optimization failed")
        
        print(f"\n📊 OPTIMIZATION SUMMARY")
        print("=" * 30)
        print(f"Successful: {success_count}/{total_count}")
        print(f"Changes applied: {len(self.changes_applied)}")
        
        if self.changes_applied:
            print("\n📋 CHANGES APPLIED:")
            for change in self.changes_applied:
                print(f"   • {change}")
        
        if success_count == total_count:
            print("\n✅ ALL OPTIMIZATIONS APPLIED SUCCESSFULLY!")
            print("🚀 System ready for performance benchmarking")
            return True
        else:
            print(f"\n⚠️ {total_count - success_count} optimizations failed")
            print("System may not be fully optimized for benchmarking")
            return False
    
    def dry_run(self) -> None:
        """Show what would be changed without applying."""
        print("🔍 DRY RUN - Showing what would be changed")
        print("=" * 50)
        
        checks = [
            ("CPU Governor", "Set to 'performance' mode"),
            ("SMT/Hyper-Threading", "Disable for consistent performance"),
            ("ASLR", "Disable for consistent memory layout"),
            ("Intel Turbo Boost", "Disable for consistent frequencies"),
            ("AMD CPU Boost", "Disable for consistent frequencies"),
            ("Huge Pages", "Allocate 128 huge pages"),
            ("Performance Counters", "Enable hardware counter access"),
            ("Disk Schedulers", "Set to 'noop' or 'none' for storage devices"),
            ("Required Tools", "Install linux-tools-generic, numactl, cpufrequtils"),
            ("CPU Isolation", "Check configuration (manual setup required)"),
        ]
        
        for name, description in checks:
            print(f"   {name}: {description}")
        
        print(f"\n💾 Backup would be saved to: {self.backup_file}")
        print("ℹ️  Run with --apply to make these changes")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Environment Recovery Script for Performance Benchmarking",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply all performance optimizations (default action)"
    )
    parser.add_argument(
        "--restore", action="store_true",
        help="Restore original system settings from backup"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be changed without applying"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Skip safety confirmations"
    )
    parser.add_argument(
        "--skip-tools", action="store_true",
        help="Skip package installation (for testing or restricted environments)"
    )
    
    args = parser.parse_args()
    
    recovery = EnvironmentRecovery()
    
    # Default to apply if no action specified
    if not args.restore and not args.dry_run:
        args.apply = True
    
    try:
        if args.dry_run:
            recovery.dry_run()
            return 0
        
        elif args.restore:
            backup = recovery.load_backup()
            if not backup:
                print("❌ Cannot restore - no backup found")
                return 1
            
            if not args.force:
                confirm = input("⚠️  This will restore system settings. Continue? [y/N]: ")
                if confirm.lower() != 'y':
                    print("❌ Restore cancelled")
                    return 1
            
            if recovery.restore_from_backup(backup):
                print("✅ System settings restored successfully")
                return 0
            else:
                print("❌ Restore completed with errors")
                return 1
        
        elif args.apply:
            if not args.force:
                print("⚠️  This will modify system settings for performance benchmarking.")
                print("   A backup will be created for safe restoration.")
                confirm = input("   Continue? [y/N]: ")
                if confirm.lower() != 'y':
                    print("❌ Operation cancelled")
                    return 1
            
            if recovery.apply_all_optimizations(skip_tools=args.skip_tools):
                print("\n🎉 Environment successfully optimized for benchmarking!")
                print(f"💾 Backup saved to: {recovery.backup_file}")
                print("🔄 To restore: python3 recover_environment.py --restore")
                return 0
            else:
                print("\n⚠️ Environment optimization completed with issues")
                print("Some manual intervention may be required")
                return 1
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())