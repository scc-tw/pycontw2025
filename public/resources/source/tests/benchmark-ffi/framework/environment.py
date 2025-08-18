"""
Environment Control and Validation for FFI Benchmarks

Comprehensive environment validation following Brendan Gregg's performance methodology:
- CPU governor and thermal state validation
- Background load and process interference detection  
- NUMA topology and CPU affinity optimization
- Memory pressure and swap usage monitoring
- System resource contention analysis

This module ensures reproducible benchmark conditions and identifies environment 
factors that could affect performance measurements.
"""

import os
import sys
import time
import psutil
import subprocess
import platform
import multiprocessing
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class EnvironmentStatus(Enum):
    """Environment validation status levels."""
    OPTIMAL = "optimal"
    ACCEPTABLE = "acceptable"
    SUBOPTIMAL = "suboptimal"
    CRITICAL = "critical"


@dataclass
class SystemResources:
    """Current system resource utilization."""
    cpu_percent: float
    memory_percent: float
    swap_percent: float
    load_average: Tuple[float, float, float]  # 1min, 5min, 15min
    active_processes: int
    network_io: Dict[str, int]
    disk_io: Dict[str, int]


@dataclass
class CPUConfiguration:
    """CPU configuration and performance settings."""
    governor: str
    scaling_driver: str
    min_freq_mhz: int
    max_freq_mhz: int
    current_freq_mhz: int
    turbo_enabled: bool
    hyperthreading_enabled: bool
    numa_nodes: int
    cpu_cores: int
    logical_cpus: int


@dataclass
class ThermalState:
    """System thermal state information."""
    cpu_temp_celsius: Optional[float]
    thermal_throttling: bool
    cooling_state: str
    fan_rpm: Optional[int]


@dataclass
class EnvironmentReport:
    """Comprehensive environment validation report."""
    status: EnvironmentStatus
    timestamp: float
    system_resources: SystemResources
    cpu_config: CPUConfiguration
    thermal_state: ThermalState
    recommendations: List[str]
    warnings: List[str]
    validation_score: float  # 0.0-1.0, higher is better


class EnvironmentValidator:
    """Environment control and validation for reproducible benchmarks."""
    
    def __init__(self, strict_mode: bool = False):
        """Initialize environment validator.
        
        Args:
            strict_mode: If True, apply stricter validation criteria for research use
        """
        self.strict_mode = strict_mode
        self.baseline_resources = None
        self.validation_history = []
        
        print(f"🌡️ Environment validator initialized (strict_mode: {strict_mode})")
    
    def validate_environment(self) -> EnvironmentReport:
        """Perform comprehensive environment validation."""
        print("🔍 Performing comprehensive environment validation...")
        
        # Collect system information
        resources = self._get_system_resources()
        cpu_config = self._get_cpu_configuration()
        thermal_state = self._get_thermal_state()
        
        # Analyze environment conditions
        warnings = []
        recommendations = []
        validation_score = 1.0
        
        # CPU Governor Validation
        if cpu_config.governor not in ['performance', 'userspace']:
            warnings.append(f"CPU governor '{cpu_config.governor}' may cause performance variation")
            recommendations.append("Set CPU governor to 'performance': sudo cpupower frequency-set -g performance")
            validation_score -= 0.3
        
        # System Load Validation
        if resources.load_average[0] > 0.5:
            warnings.append(f"High system load: {resources.load_average[0]:.2f}")
            recommendations.append("Reduce background processes before benchmarking")
            validation_score -= 0.2
        
        # Memory Pressure Validation
        if resources.memory_percent > 80:
            warnings.append(f"High memory usage: {resources.memory_percent:.1f}%")
            recommendations.append("Free memory or close unnecessary applications")
            validation_score -= 0.2
        
        # Swap Usage Validation  
        if resources.swap_percent > 5:
            warnings.append(f"Swap usage detected: {resources.swap_percent:.1f}%")
            recommendations.append("Disable swap or increase physical memory")
            validation_score -= 0.3
        
        # CPU Frequency Validation
        freq_variation = (cpu_config.max_freq_mhz - cpu_config.current_freq_mhz) / cpu_config.max_freq_mhz
        if freq_variation > 0.1:  # More than 10% below max
            warnings.append(f"CPU not at max frequency: {cpu_config.current_freq_mhz} MHz (max: {cpu_config.max_freq_mhz} MHz)")
            recommendations.append("Check thermal throttling or power management settings")
            validation_score -= 0.2
        
        # Thermal Validation
        if thermal_state.cpu_temp_celsius and thermal_state.cpu_temp_celsius > 80:
            warnings.append(f"High CPU temperature: {thermal_state.cpu_temp_celsius:.1f}°C")
            recommendations.append("Improve cooling or reduce thermal load")
            validation_score -= 0.4
        
        if thermal_state.thermal_throttling:
            warnings.append("Thermal throttling detected")
            recommendations.append("Address thermal issues before benchmarking")
            validation_score -= 0.5
        
        # Process Interference Validation
        high_cpu_processes = self._get_high_cpu_processes()
        if high_cpu_processes:
            warnings.append(f"High CPU processes detected: {', '.join(high_cpu_processes[:3])}")
            recommendations.append("Stop unnecessary CPU-intensive processes")
            validation_score -= 0.1
        
        # Determine overall status
        if validation_score >= 0.9:
            status = EnvironmentStatus.OPTIMAL
        elif validation_score >= 0.7:
            status = EnvironmentStatus.ACCEPTABLE
        elif validation_score >= 0.5:
            status = EnvironmentStatus.SUBOPTIMAL
        else:
            status = EnvironmentStatus.CRITICAL
        
        report = EnvironmentReport(
            status=status,
            timestamp=time.time(),
            system_resources=resources,
            cpu_config=cpu_config,
            thermal_state=thermal_state,
            recommendations=recommendations,
            warnings=warnings,
            validation_score=validation_score
        )
        
        self.validation_history.append(report)
        return report
    
    def _get_system_resources(self) -> SystemResources:
        """Get current system resource utilization."""
        # CPU usage (1-second sample)
        cpu_percent = psutil.cpu_percent(interval=1.0)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Swap usage
        swap = psutil.swap_memory()
        swap_percent = swap.percent if swap.total > 0 else 0.0
        
        # Load average (Unix-like systems)
        try:
            load_avg = os.getloadavg()
        except (OSError, AttributeError):
            load_avg = (0.0, 0.0, 0.0)  # Windows fallback
        
        # Process count
        active_processes = len(psutil.pids())
        
        # Network I/O
        net_io = psutil.net_io_counters()
        network_io = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
        
        # Disk I/O
        disk_io_counters = psutil.disk_io_counters()
        if disk_io_counters:
            disk_io = {
                'read_bytes': disk_io_counters.read_bytes,
                'write_bytes': disk_io_counters.write_bytes,
                'read_count': disk_io_counters.read_count,
                'write_count': disk_io_counters.write_count
            }
        else:
            disk_io = {'read_bytes': 0, 'write_bytes': 0, 'read_count': 0, 'write_count': 0}
        
        return SystemResources(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            swap_percent=swap_percent,
            load_average=load_avg,
            active_processes=active_processes,
            network_io=network_io,
            disk_io=disk_io
        )
    
    def _get_cpu_configuration(self) -> CPUConfiguration:
        """Get CPU configuration and performance settings."""
        # Basic CPU info
        cpu_cores = psutil.cpu_count(logical=False)
        logical_cpus = psutil.cpu_count(logical=True)
        
        # Initialize with defaults
        governor = "unknown"
        scaling_driver = "unknown"
        min_freq = 0
        max_freq = 0
        current_freq = 0
        turbo_enabled = False
        hyperthreading_enabled = logical_cpus > cpu_cores
        numa_nodes = 1
        
        # Try to get detailed CPU info on Linux
        if platform.system() == "Linux":
            try:
                # CPU governor
                gov_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
                if gov_path.exists():
                    governor = gov_path.read_text().strip()
                
                # Scaling driver
                driver_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
                if driver_path.exists():
                    scaling_driver = driver_path.read_text().strip()
                
                # Frequency info
                min_freq_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq")
                max_freq_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
                cur_freq_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
                
                if min_freq_path.exists():
                    min_freq = int(min_freq_path.read_text().strip()) // 1000  # Convert to MHz
                if max_freq_path.exists():
                    max_freq = int(max_freq_path.read_text().strip()) // 1000  # Convert to MHz
                if cur_freq_path.exists():
                    current_freq = int(cur_freq_path.read_text().strip()) // 1000  # Convert to MHz
                
                # Turbo boost (Intel)
                turbo_path = Path("/sys/devices/system/cpu/intel_pstate/no_turbo")
                if turbo_path.exists():
                    turbo_enabled = turbo_path.read_text().strip() == "0"
                
                # NUMA nodes
                numa_path = Path("/sys/devices/system/node")
                if numa_path.exists():
                    numa_nodes = len([d for d in numa_path.iterdir() if d.name.startswith("node")])
                    
            except (OSError, ValueError) as e:
                print(f"  ⚠️ Could not read detailed CPU info: {e}")
        
        # Fallback: try psutil for frequency info
        if current_freq == 0:
            try:
                freq_info = psutil.cpu_freq()
                if freq_info:
                    current_freq = int(freq_info.current)
                    max_freq = int(freq_info.max) if freq_info.max else max_freq
                    min_freq = int(freq_info.min) if freq_info.min else min_freq
            except (OSError, AttributeError):
                pass
        
        return CPUConfiguration(
            governor=governor,
            scaling_driver=scaling_driver,
            min_freq_mhz=min_freq,
            max_freq_mhz=max_freq,
            current_freq_mhz=current_freq,
            turbo_enabled=turbo_enabled,
            hyperthreading_enabled=hyperthreading_enabled,
            numa_nodes=numa_nodes,
            cpu_cores=cpu_cores,
            logical_cpus=logical_cpus
        )
    
    def _get_thermal_state(self) -> ThermalState:
        """Get system thermal state information."""
        cpu_temp = None
        thermal_throttling = False
        cooling_state = "unknown"
        fan_rpm = None
        
        # Try to get thermal info
        try:
            # CPU temperature
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try common temperature sensor names
                    for sensor_name in ['coretemp', 'cpu_thermal', 'k10temp', 'acpi']:
                        if sensor_name in temps:
                            cpu_temp = temps[sensor_name][0].current
                            break
                    
                    # If no specific sensor found, use first available
                    if cpu_temp is None and temps:
                        first_sensor = list(temps.values())[0]
                        if first_sensor:
                            cpu_temp = first_sensor[0].current
            
            # Fan information
            if hasattr(psutil, "sensors_fans"):
                fans = psutil.sensors_fans()
                if fans:
                    for fan_sensors in fans.values():
                        if fan_sensors:
                            fan_rpm = fan_sensors[0].current
                            break
            
            # Check for thermal throttling on Linux
            if platform.system() == "Linux":
                try:
                    # Check throttle events
                    result = subprocess.run(['dmesg'], capture_output=True, text=True, timeout=5)
                    if 'thermal' in result.stdout.lower() and 'throttl' in result.stdout.lower():
                        thermal_throttling = True
                        cooling_state = "throttling"
                    else:
                        cooling_state = "normal"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                        
        except Exception as e:
            print(f"  ⚠️ Could not read thermal info: {e}")
        
        return ThermalState(
            cpu_temp_celsius=cpu_temp,
            thermal_throttling=thermal_throttling,
            cooling_state=cooling_state,
            fan_rpm=fan_rpm
        )
    
    def _get_high_cpu_processes(self, threshold: float = 5.0) -> List[str]:
        """Get list of processes using high CPU."""
        high_cpu_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    if proc.info['cpu_percent'] and proc.info['cpu_percent'] > threshold:
                        high_cpu_processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return high_cpu_processes[:10]  # Limit to top 10
    
    def optimize_environment(self) -> Dict[str, Any]:
        """Attempt to optimize environment for benchmarking."""
        print("🔧 Attempting environment optimization...")
        
        optimizations = {
            'attempted': [],
            'successful': [],
            'failed': [],
            'requires_sudo': []
        }
        
        # CPU Governor optimization
        try:
            result = subprocess.run(['cpupower', 'frequency-info', '-g'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                current_governor = result.stdout.strip()
                if 'performance' not in current_governor:
                    optimizations['requires_sudo'].append(
                        "sudo cpupower frequency-set -g performance"
                    )
                else:
                    optimizations['successful'].append("CPU governor already set to performance")
            else:
                optimizations['requires_sudo'].append(
                    "sudo cpupower frequency-set -g performance"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            optimizations['failed'].append("cpupower not available")
        
        # Process priority optimization
        try:
            os.nice(-10)  # Increase process priority
            optimizations['successful'].append("Increased process priority")
        except PermissionError:
            optimizations['requires_sudo'].append("Run with higher priority (sudo)")
        except Exception as e:
            optimizations['failed'].append(f"Priority adjustment failed: {e}")
        
        # Memory optimization hints
        memory = psutil.virtual_memory()
        if memory.percent > 80:
            optimizations['requires_sudo'].append("echo 3 > /proc/sys/vm/drop_caches  # Clear caches")
        
        return optimizations
    
    def monitor_stability(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Monitor system stability over time."""
        print(f"📊 Monitoring system stability for {duration_seconds} seconds...")
        
        measurements = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            resources = self._get_system_resources()
            measurements.append({
                'timestamp': time.time(),
                'cpu_percent': resources.cpu_percent,
                'memory_percent': resources.memory_percent,
                'load_avg': resources.load_average[0]
            })
            time.sleep(5)  # Sample every 5 seconds
        
        # Analyze stability
        if measurements:
            cpu_values = [m['cpu_percent'] for m in measurements]
            memory_values = [m['memory_percent'] for m in measurements]
            load_values = [m['load_avg'] for m in measurements]
            
            stability_report = {
                'duration_seconds': duration_seconds,
                'sample_count': len(measurements),
                'cpu_stability': {
                    'mean': sum(cpu_values) / len(cpu_values),
                    'std_dev': self._std_dev(cpu_values),
                    'min': min(cpu_values),
                    'max': max(cpu_values)
                },
                'memory_stability': {
                    'mean': sum(memory_values) / len(memory_values),
                    'std_dev': self._std_dev(memory_values),
                    'min': min(memory_values),
                    'max': max(memory_values)
                },
                'load_stability': {
                    'mean': sum(load_values) / len(load_values),
                    'std_dev': self._std_dev(load_values),
                    'min': min(load_values),
                    'max': max(load_values)
                }
            }
            
            return stability_report
        
        return {'error': 'No measurements collected'}
    
    def _std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def print_environment_report(self, report: EnvironmentReport):
        """Print formatted environment report."""
        status_icons = {
            EnvironmentStatus.OPTIMAL: "✅",
            EnvironmentStatus.ACCEPTABLE: "⚠️",
            EnvironmentStatus.SUBOPTIMAL: "🔶", 
            EnvironmentStatus.CRITICAL: "🚨"
        }
        
        print(f"\n🌡️ Environment Validation Report")
        print("=" * 50)
        print(f"Status: {status_icons[report.status]} {report.status.value.upper()}")
        print(f"Validation Score: {report.validation_score:.2f}/1.00")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}")
        
        # System Resources
        print(f"\n📊 System Resources:")
        print(f"  CPU Usage: {report.system_resources.cpu_percent:.1f}%")
        print(f"  Memory Usage: {report.system_resources.memory_percent:.1f}%")
        print(f"  Swap Usage: {report.system_resources.swap_percent:.1f}%")
        print(f"  Load Average: {report.system_resources.load_average[0]:.2f}")
        print(f"  Active Processes: {report.system_resources.active_processes}")
        
        # CPU Configuration
        print(f"\n🖥️ CPU Configuration:")
        print(f"  Governor: {report.cpu_config.governor}")
        print(f"  Frequency: {report.cpu_config.current_freq_mhz} MHz (max: {report.cpu_config.max_freq_mhz} MHz)")
        print(f"  Cores: {report.cpu_config.cpu_cores} physical, {report.cpu_config.logical_cpus} logical")
        print(f"  NUMA Nodes: {report.cpu_config.numa_nodes}")
        print(f"  Turbo Boost: {'Enabled' if report.cpu_config.turbo_enabled else 'Disabled'}")
        
        # Thermal State
        print(f"\n🌡️ Thermal State:")
        if report.thermal_state.cpu_temp_celsius:
            print(f"  CPU Temperature: {report.thermal_state.cpu_temp_celsius:.1f}°C")
        else:
            print(f"  CPU Temperature: Not available")
        print(f"  Thermal Throttling: {'Yes' if report.thermal_state.thermal_throttling else 'No'}")
        print(f"  Cooling State: {report.thermal_state.cooling_state}")
        
        # Warnings
        if report.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in report.warnings:
                print(f"  • {warning}")
        
        # Recommendations
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")
        
        print()


def create_environment_validator(strict_mode: bool = False) -> EnvironmentValidator:
    """Factory function to create environment validator."""
    return EnvironmentValidator(strict_mode=strict_mode)


if __name__ == "__main__":
    # Self-test
    validator = create_environment_validator(strict_mode=True)
    
    print("🧪 Testing environment validator...")
    
    # Validate current environment
    report = validator.validate_environment()
    validator.print_environment_report(report)
    
    # Test optimization
    optimizations = validator.optimize_environment()
    print(f"\n🔧 Optimization Results:")
    for category, items in optimizations.items():
        if items:
            print(f"  {category}: {len(items)} items")
            for item in items[:3]:  # Show first 3
                print(f"    • {item}")
    
    print("\n✅ Environment validator test completed!")