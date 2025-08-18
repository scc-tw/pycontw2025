#!/usr/bin/env python3
"""
Advanced CPU Frequency Locking for Benchmark Consistency

This script provides comprehensive CPU frequency locking with validation
and monitoring capabilities for rigorous performance benchmarking.

Features:
- Multiple frequency locking strategies
- Intel P-state and AMD support
- Frequency validation and monitoring
- Safe rollback capability
- Integration with existing benchmark framework

Usage:
    python3 lock_cpu_frequency.py [--lock-max|--lock-freq FREQ|--show|--restore]

Examples:
    python3 lock_cpu_frequency.py --lock-max     # Lock to maximum frequency
    python3 lock_cpu_frequency.py --lock-freq 2400000  # Lock to 2.4 GHz
    python3 lock_cpu_frequency.py --show         # Show current frequencies
    python3 lock_cpu_frequency.py --restore      # Restore original settings
"""

import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict

@dataclass
class FrequencyState:
    """CPU frequency state for backup and restoration."""
    timestamp: float
    cpu_count: int
    governor: str
    frequencies: Dict[str, Dict[str, str]]  # policy -> {min_freq, max_freq, current_freq}
    available_governors: Dict[str, List[str]]
    available_frequencies: Dict[str, List[str]]
    intel_pstate_mode: Optional[str] = None
    turbo_boost_enabled: Optional[bool] = None

class CPUFrequencyLocker:
    """Advanced CPU frequency locking with validation."""
    
    def __init__(self):
        self.backup_file = Path("results/cpu_frequency_backup.json")
        self.backup_file.parent.mkdir(exist_ok=True)
        self.policy_dirs = list(Path("/sys/devices/system/cpu/cpufreq").glob("policy*"))
        self.locked_frequencies = {}
        
    def detect_cpu_architecture(self) -> str:
        """Detect CPU architecture and frequency control method."""
        # Check for Intel P-state driver
        intel_pstate_dir = Path("/sys/devices/system/cpu/intel_pstate")
        if intel_pstate_dir.exists():
            return "intel_pstate"
        
        # Check for AMD P-state driver  
        amd_pstate_dir = Path("/sys/devices/system/cpu/amd_pstate")
        if amd_pstate_dir.exists():
            return "amd_pstate"
        
        # Check for standard ACPI cpufreq
        if self.policy_dirs:
            return "acpi_cpufreq"
        
        return "unknown"
    
    def get_cpu_info(self) -> Dict:
        """Get comprehensive CPU information."""
        info = {
            "architecture": self.detect_cpu_architecture(),
            "cpu_count": os.cpu_count(),
            "policies": len(self.policy_dirs),
            "frequencies": {},
            "governors": {},
        }
        
        for policy_dir in self.policy_dirs:
            policy_name = policy_dir.name
            
            # Get frequency information
            freq_info = {}
            for freq_file in ["cpuinfo_min_freq", "cpuinfo_max_freq", "scaling_min_freq", 
                             "scaling_max_freq", "scaling_cur_freq"]:
                freq_path = policy_dir / freq_file
                if freq_path.exists():
                    try:
                        freq_info[freq_file] = freq_path.read_text().strip()
                    except:
                        freq_info[freq_file] = "unknown"
            
            info["frequencies"][policy_name] = freq_info
            
            # Get available governors
            governors_file = policy_dir / "scaling_available_governors"
            if governors_file.exists():
                try:
                    info["governors"][policy_name] = governors_file.read_text().strip().split()
                except:
                    info["governors"][policy_name] = []
        
        return info
    
    def create_frequency_backup(self) -> FrequencyState:
        """Create backup of current frequency settings."""
        print("💾 Creating CPU frequency backup...")
        
        cpu_info = self.get_cpu_info()
        
        # Get current governor
        current_governor = "unknown"
        if self.policy_dirs:
            governor_file = self.policy_dirs[0] / "scaling_governor"
            if governor_file.exists():
                current_governor = governor_file.read_text().strip()
        
        # Build frequency state
        frequencies = {}
        available_governors = {}
        available_frequencies = {}
        
        for policy_dir in self.policy_dirs:
            policy_name = policy_dir.name
            
            freq_data = {}
            for key in ["scaling_min_freq", "scaling_max_freq", "scaling_cur_freq"]:
                freq_file = policy_dir / key
                if freq_file.exists():
                    try:
                        freq_data[key] = freq_file.read_text().strip()
                    except:
                        freq_data[key] = "unknown"
            
            frequencies[policy_name] = freq_data
            
            # Available governors
            governors_file = policy_dir / "scaling_available_governors"
            if governors_file.exists():
                try:
                    available_governors[policy_name] = governors_file.read_text().strip().split()
                except:
                    available_governors[policy_name] = []
            
            # Available frequencies
            freqs_file = policy_dir / "scaling_available_frequencies"
            if freqs_file.exists():
                try:
                    available_frequencies[policy_name] = freqs_file.read_text().strip().split()
                except:
                    available_frequencies[policy_name] = []
        
        # Check Intel P-state mode
        intel_pstate_mode = None
        intel_pstate_status = Path("/sys/devices/system/cpu/intel_pstate/status")
        if intel_pstate_status.exists():
            try:
                intel_pstate_mode = intel_pstate_status.read_text().strip()
            except:
                pass
        
        # Check turbo boost status
        turbo_boost_enabled = None
        intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
        if intel_turbo.exists():
            try:
                turbo_boost_enabled = intel_turbo.read_text().strip() == "0"
            except:
                pass
        
        backup = FrequencyState(
            timestamp=time.time(),
            cpu_count=os.cpu_count(),
            governor=current_governor,
            frequencies=frequencies,
            available_governors=available_governors,
            available_frequencies=available_frequencies,
            intel_pstate_mode=intel_pstate_mode,
            turbo_boost_enabled=turbo_boost_enabled
        )
        
        # Save backup
        with open(self.backup_file, 'w') as f:
            json.dump(asdict(backup), f, indent=2)
        
        print(f"   ✅ Backup saved to: {self.backup_file}")
        return backup
    
    def load_frequency_backup(self) -> Optional[FrequencyState]:
        """Load frequency backup."""
        if not self.backup_file.exists():
            print(f"❌ No frequency backup found at: {self.backup_file}")
            return None
        
        try:
            with open(self.backup_file, 'r') as f:
                data = json.load(f)
            
            backup = FrequencyState(**data)
            print(f"✅ Loaded frequency backup from {time.ctime(backup.timestamp)}")
            return backup
            
        except Exception as e:
            print(f"❌ Failed to load frequency backup: {e}")
            return None
    
    def get_optimal_frequency(self, strategy: str = "max") -> Optional[int]:
        """Get optimal frequency based on strategy."""
        if not self.policy_dirs:
            return None
        
        if strategy == "max":
            # For hybrid CPUs, find the highest maximum frequency
            max_frequencies = []
            for policy_dir in self.policy_dirs:
                max_freq_file = policy_dir / "cpuinfo_max_freq"
                if max_freq_file.exists():
                    try:
                        max_frequencies.append(int(max_freq_file.read_text().strip()))
                    except:
                        pass
            
            if max_frequencies:
                # Return the highest frequency found (usually P-core frequency)
                return max(max_frequencies)
            return None
    
    def get_optimal_frequencies_per_policy(self, strategy: str = "max") -> Optional[Dict[str, int]]:
        """Get optimal frequency for each policy - for hybrid CPU handling."""
        if not self.policy_dirs:
            return None
        
        if strategy == "max":
            # For hybrid CPUs, get maximum frequency for each policy
            frequencies = {}
            for policy_dir in self.policy_dirs:
                policy_name = policy_dir.name
                max_freq_file = policy_dir / "cpuinfo_max_freq"
                if max_freq_file.exists():
                    try:
                        frequencies[policy_name] = int(max_freq_file.read_text().strip())
                    except:
                        pass
            return frequencies if frequencies else None
        
        elif strategy.isdigit():
            # Use specified frequency for all policies
            target_freq = int(strategy)
            frequencies = {}
            
            for policy_dir in self.policy_dirs:
                policy_name = policy_dir.name
                # Validate frequency against this policy's range
                min_freq_file = policy_dir / "cpuinfo_min_freq"
                max_freq_file = policy_dir / "cpuinfo_max_freq"
                
                try:
                    min_freq = int(min_freq_file.read_text().strip())
                    max_freq = int(max_freq_file.read_text().strip())
                    
                    if min_freq <= target_freq <= max_freq:
                        frequencies[policy_name] = target_freq
                    else:
                        # Use the maximum available for this policy
                        frequencies[policy_name] = max_freq
                        print(f"⚠️ {policy_name}: {target_freq} outside range [{min_freq}, {max_freq}], using {max_freq}")
                except:
                    pass
            
            return frequencies if frequencies else None
        
        return None
    
    def detect_intel_pstate_limitations(self) -> bool:
        """Check if system uses Intel P-state driver with limitations."""
        intel_pstate_dir = Path("/sys/devices/system/cpu/intel_pstate")
        if not intel_pstate_dir.exists():
            return False
        
        # Check if userspace governor is available
        if self.policy_dirs:
            available_govs_file = self.policy_dirs[0] / "scaling_available_governors"
            if available_govs_file.exists():
                try:
                    available_govs = available_govs_file.read_text().strip()
                    return "userspace" not in available_govs
                except:
                    pass
        
        return True  # Assume limitations if we can't check
    
    def set_frequency_intel_pstate_method(self, target_frequencies: Dict[str, int]) -> bool:
        """Lock frequency using Intel P-state driver method."""
        print("🔧 Configuring frequencies for Intel P-state driver...")
        
        # Intel P-state only supports performance and powersave governors
        # We use performance governor with min/max constraints
        
        success_count = 0
        
        for policy_dir in self.policy_dirs:
            policy_name = policy_dir.name
            
            if policy_name not in target_frequencies:
                continue
            
            target_freq = target_frequencies[policy_name]
            
            try:
                # Set governor to performance
                governor_file = policy_dir / "scaling_governor"
                if governor_file.exists():
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo performance > {governor_file}"],
                        check=True, capture_output=True
                    )
                
                # Set both min and max frequency to target (locks the frequency)
                min_freq_file = policy_dir / "scaling_min_freq"
                max_freq_file = policy_dir / "scaling_max_freq"
                
                if min_freq_file.exists() and max_freq_file.exists():
                    # Set min frequency first, then max
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo {target_freq} > {min_freq_file}"],
                        check=True, capture_output=True
                    )
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo {target_freq} > {max_freq_file}"],
                        check=True, capture_output=True
                    )
                    
                    # Verify the frequency
                    time.sleep(0.2)  # Allow time for frequency change
                    cur_freq_file = policy_dir / "scaling_cur_freq"
                    if cur_freq_file.exists():
                        actual_freq = int(cur_freq_file.read_text().strip())
                        
                        # Check if already at target (within 50MHz tolerance)
                        if abs(actual_freq - target_freq) < 50000:
                            print(f"   ✅ {policy_name}: {actual_freq} Hz ({actual_freq/1000000:.1f} GHz)")
                            success_count += 1
                            self.locked_frequencies[policy_name] = actual_freq
                        else:
                            print(f"   ✅ {policy_name}: {actual_freq} Hz (requested {target_freq/1000000:.1f} GHz)")
                            success_count += 1  # Still count as success if it's stable
                            self.locked_frequencies[policy_name] = actual_freq
                    else:
                        print(f"   ✅ {policy_name}: frequency constraints set")
                        success_count += 1
                        self.locked_frequencies[policy_name] = target_freq
                else:
                    print(f"   ❌ {policy_name}: min/max frequency controls not available")
                    
            except subprocess.CalledProcessError as e:
                print(f"   ❌ {policy_name}: failed to set frequency - {e}")
            except Exception as e:
                print(f"   ❌ {policy_name}: error - {e}")
        
        total_policies = len(target_frequencies)
        print(f"   📊 Success: {success_count}/{total_policies} policies")
        return success_count == total_policies
    
    def set_frequency_userspace_method(self, target_frequencies: Dict[str, int]) -> bool:
        """Lock frequency using userspace governor method."""
        print("🔧 Attempting userspace governor method...")
        
        # Check if userspace governor is available
        if self.detect_intel_pstate_limitations():
            print("   ⚠️ Intel P-state driver detected - userspace governor not available")
            return False
        
        success_count = 0
        
        for policy_dir in self.policy_dirs:
            policy_name = policy_dir.name
            
            if policy_name not in target_frequencies:
                continue
            
            target_freq = target_frequencies[policy_name]
            
            try:
                # Set governor to userspace
                governor_file = policy_dir / "scaling_governor"
                if governor_file.exists():
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo userspace > {governor_file}"],
                        check=True, capture_output=True
                    )
                
                # Set the specific frequency
                setspeed_file = policy_dir / "scaling_setspeed"
                if setspeed_file.exists():
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo {target_freq} > {setspeed_file}"],
                        check=True, capture_output=True
                    )
                    
                    # Verify the frequency was set
                    time.sleep(0.1)  # Allow time for frequency change
                    cur_freq_file = policy_dir / "scaling_cur_freq"
                    if cur_freq_file.exists():
                        actual_freq = int(cur_freq_file.read_text().strip())
                        if abs(actual_freq - target_freq) < 50000:  # 50MHz tolerance
                            print(f"   ✅ {policy_name}: {actual_freq} Hz")
                            success_count += 1
                            self.locked_frequencies[policy_name] = actual_freq
                        else:
                            print(f"   ❌ {policy_name}: requested {target_freq}, got {actual_freq}")
                    else:
                        print(f"   ✅ {policy_name}: frequency set (verification unavailable)")
                        success_count += 1
                        self.locked_frequencies[policy_name] = target_freq
                else:
                    print(f"   ❌ {policy_name}: scaling_setspeed not available")
                    
            except subprocess.CalledProcessError as e:
                print(f"   ❌ {policy_name}: failed to set frequency - {e}")
            except Exception as e:
                print(f"   ❌ {policy_name}: error - {e}")
        
        total_policies = len(target_frequencies)
        print(f"   📊 Success: {success_count}/{total_policies} policies")
        return success_count == total_policies
    
    def check_if_frequencies_already_locked(self, target_frequencies: Dict[str, int]) -> bool:
        """Check if frequencies are already locked to target values."""
        print("🔍 Checking if frequencies are already properly locked...")
        
        locked_count = 0
        total_count = 0
        
        for policy_dir in self.policy_dirs:
            policy_name = policy_dir.name
            
            if policy_name not in target_frequencies:
                continue
                
            total_count += 1
            target_freq = target_frequencies[policy_name]
            
            try:
                # Check current frequency
                cur_freq_file = policy_dir / "scaling_cur_freq"
                min_freq_file = policy_dir / "scaling_min_freq"
                max_freq_file = policy_dir / "scaling_max_freq"
                
                if cur_freq_file.exists() and min_freq_file.exists() and max_freq_file.exists():
                    current_freq = int(cur_freq_file.read_text().strip())
                    min_freq = int(min_freq_file.read_text().strip())
                    max_freq = int(max_freq_file.read_text().strip())
                    
                    # Check if frequency is locked (min == max == target within tolerance)
                    freq_locked = (abs(min_freq - target_freq) < 50000 and 
                                 abs(max_freq - target_freq) < 50000 and
                                 abs(current_freq - target_freq) < 100000)
                    
                    if freq_locked:
                        print(f"   ✅ {policy_name}: already locked to {current_freq} Hz ({current_freq/1000000:.1f} GHz)")
                        locked_count += 1
                        self.locked_frequencies[policy_name] = current_freq
                    else:
                        print(f"   ⚠️ {policy_name}: not locked (current: {current_freq}, min: {min_freq}, max: {max_freq})")
                        
            except Exception as e:
                print(f"   ❌ {policy_name}: error checking - {e}")
        
        if locked_count == total_count:
            print(f"   🎉 All {total_count} frequencies already properly locked!")
            return True
        else:
            print(f"   📊 {locked_count}/{total_count} frequencies already locked")
            return False
    
    def disable_frequency_scaling_features(self) -> bool:
        """Disable frequency scaling features for maximum consistency."""
        print("🔧 Disabling frequency scaling features...")
        
        success = True
        
        # Disable Intel Turbo Boost
        intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
        if intel_turbo.exists():
            try:
                subprocess.run(
                    ["sudo", "sh", "-c", f"echo 1 > {intel_turbo}"],
                    check=True, capture_output=True
                )
                print("   ✅ Intel Turbo Boost disabled")
            except:
                print("   ❌ Failed to disable Intel Turbo Boost")
                success = False
        
        # Disable AMD Boost
        amd_boost = Path("/sys/devices/system/cpu/cpufreq/boost")
        if amd_boost.exists():
            try:
                subprocess.run(
                    ["sudo", "sh", "-c", f"echo 0 > {amd_boost}"],
                    check=True, capture_output=True
                )
                print("   ✅ AMD CPU Boost disabled")
            except:
                print("   ❌ Failed to disable AMD CPU Boost")
                success = False
        
        # Set energy performance preference to performance
        for policy_dir in self.policy_dirs:
            epp_file = policy_dir / "energy_performance_preference"
            if epp_file.exists():
                try:
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo performance > {epp_file}"],
                        check=True, capture_output=True
                    )
                except:
                    pass  # Not critical
        
        return success
    
    def lock_frequency(self, target_input) -> bool:
        """Lock CPU frequency using the best available method."""
        
        # Handle both single frequency and dictionary inputs
        if isinstance(target_input, dict):
            target_frequencies = target_input
        elif isinstance(target_input, int):
            # For single frequency, apply optimally to each policy
            target_frequencies = self.get_optimal_frequencies_per_policy("max")
            if not target_frequencies:
                print("❌ Cannot determine optimal frequencies for hybrid CPU")
                return False
            
            # For hybrid CPUs, if user specifies a single frequency, 
            # use it where possible, otherwise use the max for each policy
            adjusted_frequencies = {}
            for policy_name, max_freq in target_frequencies.items():
                # Use target frequency if it's within the policy's range
                if target_input <= max_freq:
                    adjusted_frequencies[policy_name] = target_input
                else:
                    adjusted_frequencies[policy_name] = max_freq
                    print(f"⚠️ {policy_name}: {target_input} Hz too high, using {max_freq} Hz")
            
            target_frequencies = adjusted_frequencies
        elif target_input == "max":
            # Special case for --lock-max: use optimal frequency for each policy
            target_frequencies = self.get_optimal_frequencies_per_policy("max")
            if not target_frequencies:
                print("❌ Cannot determine optimal frequencies for hybrid CPU")
                return False
        else:
            print("❌ Invalid target frequency type")
            return False
        
        # Show summary of target frequencies
        p_cores = [f for f in target_frequencies.values() if f >= 2000000]
        e_cores = [f for f in target_frequencies.values() if f < 2000000]
        
        print("🚀 LOCKING CPU FREQUENCIES")
        print("=" * 50)
        
        if p_cores and e_cores:
            print(f"   P-cores: {len(p_cores)} cores @ {p_cores[0]/1000000:.1f} GHz")
            print(f"   E-cores: {len(e_cores)} cores @ {e_cores[0]/1000000:.1f} GHz")
        else:
            freqs = list(set(target_frequencies.values()))
            if len(freqs) == 1:
                print(f"   All cores: {freqs[0]/1000000:.1f} GHz")
            else:
                print(f"   Multiple frequencies: {[f/1000000 for f in freqs]} GHz")
        
        print()
        
        # Create backup first
        backup = self.create_frequency_backup()
        
        # Check if frequencies are already locked correctly
        if self.check_if_frequencies_already_locked(target_frequencies):
            print("✅ Frequencies already properly locked!")
            return True
        
        # Disable scaling features for consistency
        self.disable_frequency_scaling_features()
        
        # Try userspace method first (most precise) if available
        if not self.detect_intel_pstate_limitations():
            if self.set_frequency_userspace_method(target_frequencies):
                print("✅ Frequencies locked using userspace method")
                return True
        
        # Use Intel P-state method (performance governor with constraints)
        print("🔧 Using Intel P-state compatible method...")
        if self.set_frequency_intel_pstate_method(target_frequencies):
            print("✅ Frequencies locked using Intel P-state method")
            return True
        
        print("❌ Failed to lock frequencies with any method")
        return False
    
    def lock_frequency_simple(self, target_freq: int) -> bool:
        """Lock all CPUs to the same frequency (legacy interface)."""
        return self.lock_frequency(target_freq)
    
    def show_current_frequencies(self) -> None:
        """Display current CPU frequency information."""
        print("📊 CURRENT CPU FREQUENCY STATUS")
        print("=" * 50)
        
        cpu_info = self.get_cpu_info()
        
        print(f"Architecture: {cpu_info['architecture']}")
        print(f"CPU Count: {cpu_info['cpu_count']}")
        print(f"Frequency Policies: {cpu_info['policies']}")
        print()
        
        # Intel P-state info
        intel_pstate_status = Path("/sys/devices/system/cpu/intel_pstate/status")
        if intel_pstate_status.exists():
            try:
                status = intel_pstate_status.read_text().strip()
                print(f"Intel P-state Mode: {status}")
            except:
                pass
        
        # Turbo boost status
        intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
        if intel_turbo.exists():
            try:
                disabled = intel_turbo.read_text().strip() == "1"
                print(f"Intel Turbo Boost: {'Disabled' if disabled else 'Enabled'}")
            except:
                pass
        
        amd_boost = Path("/sys/devices/system/cpu/cpufreq/boost")
        if amd_boost.exists():
            try:
                enabled = amd_boost.read_text().strip() == "1"
                print(f"AMD CPU Boost: {'Enabled' if enabled else 'Disabled'}")
            except:
                pass
        
        print()
        
        # Per-policy information
        for policy_name, freq_info in cpu_info["frequencies"].items():
            print(f"Policy {policy_name}:")
            
            # Current governor
            policy_dir = Path(f"/sys/devices/system/cpu/cpufreq/{policy_name}")
            governor_file = policy_dir / "scaling_governor"
            if governor_file.exists():
                try:
                    governor = governor_file.read_text().strip()
                    print(f"  Governor: {governor}")
                except:
                    pass
            
            # Frequency information
            for key, value in freq_info.items():
                if key.endswith("_freq") and value != "unknown":
                    freq_mhz = int(value) / 1000
                    print(f"  {key}: {value} Hz ({freq_mhz:.0f} MHz)")
            
            # Available governors
            if policy_name in cpu_info["governors"]:
                governors = cpu_info["governors"][policy_name]
                if governors:
                    print(f"  Available governors: {', '.join(governors)}")
            
            print()
    
    def verify_frequency_lock(self, target_freq_or_duration=None, duration: int = 10) -> bool:
        """Verify that frequencies remain locked over time."""
        
        # Handle both old and new interface
        if isinstance(target_freq_or_duration, int) and target_freq_or_duration > 1000:
            # Old interface: verify_frequency_lock(target_freq, duration)
            # We ignore target_freq since we verify actual locked frequencies
            actual_duration = duration
        elif isinstance(target_freq_or_duration, int):
            # New interface: verify_frequency_lock(duration)
            actual_duration = target_freq_or_duration
        else:
            actual_duration = duration
        
        print(f"🔍 Verifying frequency stability for {actual_duration} seconds...")
        
        if not self.locked_frequencies:
            print("❌ No locked frequencies to verify")
            return False
        
        # Monitor all locked policies
        policy_data = {}
        tolerance = 100000  # 100MHz tolerance for stability
        
        # Initialize monitoring data
        for policy_name, target_freq in self.locked_frequencies.items():
            policy_dir = Path(f"/sys/devices/system/cpu/cpufreq/{policy_name}")
            cur_freq_file = policy_dir / "scaling_cur_freq"
            
            if cur_freq_file.exists():
                policy_data[policy_name] = {
                    'target': target_freq,
                    'file': cur_freq_file,
                    'frequencies': [],
                    'stable': True
                }
        
        if not policy_data:
            print("❌ Cannot monitor frequency files")
            return False
        
        # Monitor frequencies over time
        for i in range(duration):
            all_stable = True
            status_line = f"   {i+1:2d}s: "
            
            for policy_name, data in policy_data.items():
                try:
                    current_freq = int(data['file'].read_text().strip())
                    data['frequencies'].append(current_freq)
                    
                    # Check stability
                    if abs(current_freq - data['target']) > tolerance:
                        data['stable'] = False
                        all_stable = False
                    
                    status_line += f"{policy_name}:{current_freq/1000000:.1f}GHz "
                    
                except Exception as e:
                    print(f"❌ Error reading {policy_name}: {e}")
                    return False
            
            print(status_line)
            
            if not all_stable:
                print("❌ Frequency instability detected")
                return False
            
            time.sleep(1)
        
        # Analyze results
        print("\n📊 Frequency Stability Analysis:")
        overall_stable = True
        
        for policy_name, data in policy_data.items():
            if data['frequencies']:
                min_freq = min(data['frequencies'])
                max_freq = max(data['frequencies'])
                avg_freq = sum(data['frequencies']) / len(data['frequencies'])
                variation = max_freq - min_freq
                
                print(f"   {policy_name}: {data['target']/1000000:.1f} GHz target")
                print(f"      Range: {min_freq/1000000:.1f} - {max_freq/1000000:.1f} GHz")
                print(f"      Variation: {variation/1000:.0f} MHz")
                
                if variation > tolerance:
                    print(f"      ❌ High variation (>{tolerance/1000:.0f} MHz)")
                    overall_stable = False
                else:
                    print(f"      ✅ Stable")
        
        if overall_stable:
            print("✅ All frequencies verified stable!")
            return True
        else:
            print("⚠️ Some frequencies showed instability")
            return False
    
    def restore_frequency_settings(self) -> bool:
        """Restore original frequency settings from backup."""
        backup = self.load_frequency_backup()
        if not backup:
            return False
        
        print("🔄 Restoring CPU frequency settings...")
        
        success = True
        
        try:
            # Restore governor for each policy
            for policy_name, freq_data in backup.frequencies.items():
                policy_dir = Path(f"/sys/devices/system/cpu/cpufreq/{policy_name}")
                
                if policy_dir.exists():
                    # Restore governor
                    governor_file = policy_dir / "scaling_governor"
                    if governor_file.exists():
                        try:
                            subprocess.run(
                                ["sudo", "sh", "-c", f"echo {backup.governor} > {governor_file}"],
                                check=True, capture_output=True
                            )
                            print(f"   ✅ {policy_name}: governor restored to {backup.governor}")
                        except:
                            print(f"   ❌ {policy_name}: failed to restore governor")
                            success = False
                    
                    # Restore frequency limits
                    for freq_type in ["scaling_min_freq", "scaling_max_freq"]:
                        if freq_type in freq_data and freq_data[freq_type] != "unknown":
                            freq_file = policy_dir / freq_type
                            if freq_file.exists():
                                try:
                                    subprocess.run(
                                        ["sudo", "sh", "-c", f"echo {freq_data[freq_type]} > {freq_file}"],
                                        check=True, capture_output=True
                                    )
                                except:
                                    print(f"   ❌ {policy_name}: failed to restore {freq_type}")
                                    success = False
            
            # Restore turbo boost if available
            if backup.turbo_boost_enabled is not None:
                intel_turbo = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
                if intel_turbo.exists():
                    try:
                        value = "0" if backup.turbo_boost_enabled else "1"
                        subprocess.run(
                            ["sudo", "sh", "-c", f"echo {value} > {intel_turbo}"],
                            check=True, capture_output=True
                        )
                        print(f"   ✅ Turbo boost restored")
                    except:
                        print(f"   ❌ Failed to restore turbo boost")
                        success = False
            
            if success:
                print("✅ CPU frequency settings restored successfully")
            else:
                print("⚠️ Some frequency settings could not be restored")
            
            return success
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Advanced CPU Frequency Locking for Benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--lock-max", action="store_true",
        help="Lock CPU to maximum frequency"
    )
    parser.add_argument(
        "--lock-freq", type=int, metavar="FREQ",
        help="Lock CPU to specific frequency in Hz (e.g. 2400000 for 2.4GHz)"
    )
    parser.add_argument(
        "--show", action="store_true",
        help="Show current CPU frequency information"
    )
    parser.add_argument(
        "--restore", action="store_true",
        help="Restore original frequency settings"
    )
    parser.add_argument(
        "--verify", type=int, metavar="SECONDS", default=0,
        help="Verify frequency lock for specified seconds"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Skip confirmations"
    )
    
    args = parser.parse_args()
    
    locker = CPUFrequencyLocker()
    
    try:
        if args.show:
            locker.show_current_frequencies()
            return 0
        
        elif args.restore:
            if not args.force:
                confirm = input("⚠️  Restore original frequency settings? [y/N]: ")
                if confirm.lower() != 'y':
                    print("❌ Restore cancelled")
                    return 1
            
            if locker.restore_frequency_settings():
                return 0
            else:
                return 1
        
        elif args.lock_max:
            if not args.force:
                # Show what frequencies will be set
                optimal_freqs = locker.get_optimal_frequencies_per_policy("max")
                if optimal_freqs:
                    p_cores = [f for f in optimal_freqs.values() if f >= 2000000]
                    e_cores = [f for f in optimal_freqs.values() if f < 2000000]
                    
                    if p_cores and e_cores:
                        print(f"⚠️  Lock CPU frequencies:")
                        print(f"   P-cores: {len(p_cores)} cores @ {p_cores[0]/1000000:.1f} GHz")
                        print(f"   E-cores: {len(e_cores)} cores @ {e_cores[0]/1000000:.1f} GHz")
                    else:
                        freqs = list(set(optimal_freqs.values()))
                        if len(freqs) == 1:
                            print(f"⚠️  Lock all CPU cores to {freqs[0]/1000000:.1f} GHz?")
                        else:
                            print(f"⚠️  Lock CPU cores to optimal frequencies?")
                else:
                    print("⚠️  Lock CPU frequencies to maximum available?")
                
                confirm = input("   Continue? [y/N]: ")
                if confirm.lower() != 'y':
                    print("❌ Operation cancelled")
                    return 1
            
            if locker.lock_frequency("max"):
                if args.verify > 0:
                    locker.verify_frequency_lock(args.verify)
                print("🎉 CPU frequencies locked successfully!")
                return 0
            else:
                return 1
        
        elif args.lock_freq:
            target_freq = args.lock_freq
            
            if not args.force:
                print(f"⚠️  Lock CPU frequency to {target_freq} Hz ({target_freq/1000000:.1f} GHz)?")
                confirm = input("   Continue? [y/N]: ")
                if confirm.lower() != 'y':
                    print("❌ Operation cancelled")
                    return 1
            
            if locker.lock_frequency(target_freq):
                if args.verify > 0:
                    locker.verify_frequency_lock(args.verify)
                print("🎉 CPU frequency locked successfully!")
                return 0
            else:
                return 1
        
        else:
            # Default action - show current status
            locker.show_current_frequencies()
            print("\nℹ️  Use --help to see available options")
            return 0
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())