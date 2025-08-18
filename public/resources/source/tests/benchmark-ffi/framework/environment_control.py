"""
Environment Control Validation for FFI Benchmarks

This module implements environment control validation as required by
review.md criticism of "missing environment control".

Addresses academic standards for reproducible performance benchmarking.
"""

import os
import sys
import subprocess
import psutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EnvironmentCheck:
    """Results from a single environment validation check."""
    name: str
    status: str  # 'pass', 'fail', 'warning', 'skip'
    current_value: str
    expected_value: str
    error_message: Optional[str] = None


@dataclass 
class EnvironmentValidationResult:
    """Complete environment validation results."""
    overall_status: str  # 'pass', 'fail', 'warning'
    checks: List[EnvironmentCheck]
    warnings: List[str]
    recommendations: List[str]


class EnvironmentValidator:
    """
    Validates benchmark environment for reproducible results.
    
    Implements requirements from docs/benchmark-ffi/environment-setup.md
    and addresses review.md criticism of missing environment control.
    """
    
    def __init__(self):
        """Initialize environment validator."""
        self.checks = []
        self.warnings = []
        self.recommendations = []
    
    def validate_all(self) -> EnvironmentValidationResult:
        """
        Perform complete environment validation.
        
        Returns:
            EnvironmentValidationResult with all check results
        """
        print("🔍 Validating benchmark environment...")
        
        # Reset state
        self.checks = []
        self.warnings = []
        self.recommendations = []
        
        # Perform all validation checks
        self._check_cpu_governor()
        self._check_cpu_isolation()
        self._check_thermal_state()
        self._check_background_load()
        self._check_memory_configuration()
        self._check_performance_counters()
        self._check_numa_topology()
        self._check_compiler_flags()
        
        # Determine overall status
        failed_checks = [c for c in self.checks if c.status == 'fail']
        warning_checks = [c for c in self.checks if c.status == 'warning']
        
        if failed_checks:
            overall_status = 'fail'
        elif warning_checks:
            overall_status = 'warning'
        else:
            overall_status = 'pass'
        
        return EnvironmentValidationResult(
            overall_status=overall_status,
            checks=self.checks,
            warnings=self.warnings,
            recommendations=self.recommendations
        )
    
    def _check_cpu_governor(self):
        """Check CPU frequency scaling governor."""
        try:
            # Read current governor
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                current_governor = f.read().strip()
            
            expected_governor = 'performance'
            
            if current_governor == expected_governor:
                status = 'pass'
                error_msg = None
            else:
                status = 'fail'
                error_msg = f"Use: sudo cpupower frequency-set -g {expected_governor}"
                self.recommendations.append(
                    f"Set CPU governor to performance mode: {error_msg}"
                )
            
            self.checks.append(EnvironmentCheck(
                name="CPU Frequency Governor",
                status=status,
                current_value=current_governor,
                expected_value=expected_governor,
                error_message=error_msg
            ))
            
        except (FileNotFoundError, PermissionError) as e:
            self.checks.append(EnvironmentCheck(
                name="CPU Frequency Governor",
                status='skip',
                current_value='unknown',
                expected_value='performance',
                error_message=f"Cannot read governor: {e}"
            ))
            self.warnings.append("CPU governor check skipped - may affect results")
    
    def _check_cpu_isolation(self):
        """Check CPU isolation configuration."""
        try:
            # Check kernel command line for isolcpus
            with open('/proc/cmdline', 'r') as f:
                cmdline = f.read().strip()
            
            if 'isolcpus=' in cmdline:
                # Extract isolated CPUs
                for param in cmdline.split():
                    if param.startswith('isolcpus='):
                        isolated_cpus = param.split('=', 1)[1]
                        
                        self.checks.append(EnvironmentCheck(
                            name="CPU Isolation",
                            status='pass',
                            current_value=f"isolcpus={isolated_cpus}",
                            expected_value='isolcpus=<cpu_list>',
                            error_message=None
                        ))
                        return
            
            # No CPU isolation found
            self.checks.append(EnvironmentCheck(
                name="CPU Isolation",
                status='warning',
                current_value='none',
                expected_value='isolcpus=<cpu_list>',
                error_message="Add isolcpus=<cpu_list> to kernel parameters"
            ))
            self.warnings.append("No CPU isolation - results may have higher variance")
            self.recommendations.append(
                "Add isolcpus=2,3,4,5 to /etc/default/grub GRUB_CMDLINE_LINUX"
            )
            
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="CPU Isolation", 
                status='skip',
                current_value='unknown',
                expected_value='isolcpus=<cpu_list>',
                error_message=f"Cannot check isolation: {e}"
            ))
    
    def _check_thermal_state(self):
        """Check thermal throttling state."""
        try:
            # Check thermal zones
            thermal_zones = list(Path('/sys/class/thermal').glob('thermal_zone*'))
            
            if not thermal_zones:
                self.checks.append(EnvironmentCheck(
                    name="Thermal State",
                    status='skip',
                    current_value='no_thermal_zones',
                    expected_value='<85°C',
                    error_message="No thermal zones found"
                ))
                return
            
            max_temp = 0
            temp_readings = []
            
            for zone in thermal_zones:
                try:
                    temp_file = zone / 'temp'
                    if temp_file.exists():
                        with open(temp_file, 'r') as f:
                            temp_millic = int(f.read().strip())
                            temp_celsius = temp_millic / 1000
                            temp_readings.append(temp_celsius)
                            max_temp = max(max_temp, temp_celsius)
                except (ValueError, FileNotFoundError):
                    continue
            
            if max_temp > 85:
                status = 'fail'
                error_msg = "CPU temperature too high - thermal throttling likely"
                self.recommendations.append("Allow CPU to cool before benchmarking")
            elif max_temp > 75:
                status = 'warning'
                error_msg = "CPU temperature elevated - monitor for throttling"
                self.warnings.append(f"CPU temperature: {max_temp:.1f}°C")
            else:
                status = 'pass'
                error_msg = None
            
            self.checks.append(EnvironmentCheck(
                name="Thermal State",
                status=status,
                current_value=f"{max_temp:.1f}°C",
                expected_value='<85°C',
                error_message=error_msg
            ))
            
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="Thermal State",
                status='skip',
                current_value='unknown',
                expected_value='<85°C',
                error_message=f"Cannot check thermal state: {e}"
            ))
    
    def _check_background_load(self):
        """Check system background load."""
        try:
            # Get CPU utilization over 1 second
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get process count
            process_count = len(psutil.pids())
            
            if cpu_percent > 20:
                status = 'fail'
                error_msg = f"High CPU usage ({cpu_percent:.1f}%) - close background processes"
                self.recommendations.append("Stop unnecessary background processes")
            elif cpu_percent > 10:
                status = 'warning'
                error_msg = f"Moderate CPU usage ({cpu_percent:.1f}%) - may affect results"
                self.warnings.append(f"Background CPU usage: {cpu_percent:.1f}%")
            else:
                status = 'pass'
                error_msg = None
            
            self.checks.append(EnvironmentCheck(
                name="Background Load",
                status=status,
                current_value=f"{cpu_percent:.1f}% CPU, {process_count} processes",
                expected_value='<10% CPU',
                error_message=error_msg
            ))
            
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="Background Load",
                status='skip',
                current_value='unknown',
                expected_value='<10% CPU',
                error_message=f"Cannot check load: {e}"
            ))
    
    def _check_memory_configuration(self):
        """Check memory configuration for benchmarking."""
        try:
            memory = psutil.virtual_memory()
            
            # Check available memory (should be >2GB)
            available_gb = memory.available / (1024**3)
            
            if available_gb < 1:
                status = 'fail'
                error_msg = f"Low memory ({available_gb:.1f}GB) - may cause swapping"
                self.recommendations.append("Free up memory or add more RAM")
            elif available_gb < 2:
                status = 'warning'
                error_msg = f"Limited memory ({available_gb:.1f}GB) - monitor for swapping"
                self.warnings.append(f"Available memory: {available_gb:.1f}GB")
            else:
                status = 'pass'
                error_msg = None
            
            # Check swap usage
            swap = psutil.swap_memory()
            swap_percent = swap.percent
            
            if swap_percent > 10:
                if status == 'pass':
                    status = 'warning'
                error_msg = f"Active swapping ({swap_percent:.1f}%) detected"
                self.warnings.append(f"Swap usage: {swap_percent:.1f}%")
            
            self.checks.append(EnvironmentCheck(
                name="Memory Configuration",
                status=status,
                current_value=f"{available_gb:.1f}GB available, {swap_percent:.1f}% swap",
                expected_value='>2GB available, <10% swap',
                error_message=error_msg
            ))
            
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="Memory Configuration",
                status='skip',
                current_value='unknown',
                expected_value='>2GB available',
                error_message=f"Cannot check memory: {e}"
            ))
    
    def _check_performance_counters(self):
        """Check performance counter accessibility."""
        try:
            # Check perf_event_paranoid setting
            paranoid_file = '/proc/sys/kernel/perf_event_paranoid'
            
            if Path(paranoid_file).exists():
                with open(paranoid_file, 'r') as f:
                    paranoid_level = int(f.read().strip())
                
                if paranoid_level <= 1:
                    status = 'pass'
                    error_msg = None
                else:
                    status = 'fail'
                    error_msg = f"Set paranoid level: echo -1 | sudo tee {paranoid_file}"
                    self.recommendations.append(
                        f"Enable performance counters: {error_msg}"
                    )
                
                self.checks.append(EnvironmentCheck(
                    name="Performance Counters",
                    status=status,
                    current_value=str(paranoid_level),
                    expected_value='≤1',
                    error_message=error_msg
                ))
            else:
                self.checks.append(EnvironmentCheck(
                    name="Performance Counters",
                    status='skip',
                    current_value='unknown',
                    expected_value='accessible',
                    error_message="Cannot check perf_event_paranoid"
                ))
                
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="Performance Counters",
                status='skip',
                current_value='unknown',
                expected_value='accessible',
                error_message=f"Cannot check counters: {e}"
            ))
    
    def _check_numa_topology(self):
        """Check NUMA topology for memory locality."""
        try:
            # Simple NUMA check - count nodes
            numa_nodes = list(Path('/sys/devices/system/node').glob('node*'))
            numa_count = len([n for n in numa_nodes if n.is_dir()])
            
            if numa_count > 1:
                status = 'warning'
                error_msg = f"NUMA system ({numa_count} nodes) - consider memory binding"
                self.warnings.append(f"NUMA nodes: {numa_count}")
                self.recommendations.append("Consider using numactl for memory binding")
            else:
                status = 'pass'
                error_msg = None
            
            self.checks.append(EnvironmentCheck(
                name="NUMA Topology",
                status=status,
                current_value=f"{numa_count} nodes",
                expected_value='single node or bound',
                error_message=error_msg
            ))
            
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="NUMA Topology",
                status='skip',
                current_value='unknown',
                expected_value='single node',
                error_message=f"Cannot check NUMA: {e}"
            ))
    
    def _check_compiler_flags(self):
        """Check compiler configuration for benchlib."""
        try:
            # Check if benchlib was compiled with correct flags
            benchlib_path = Path(__file__).parent.parent / 'benchlib.so'
            
            if benchlib_path.exists():
                # Use objdump to check compilation flags (if available)
                try:
                    result = subprocess.run(
                        ['objdump', '-s', '-j', '.comment', str(benchlib_path)],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0 and 'GCC' in result.stdout:
                        status = 'pass'
                        error_msg = None
                        compiler_info = 'GCC (flags unknown)'
                    else:
                        status = 'warning'
                        error_msg = "Cannot verify compiler flags"
                        compiler_info = 'unknown'
                except FileNotFoundError:
                    status = 'warning'
                    error_msg = "objdump not available for flag verification"
                    compiler_info = 'unknown'
                
                self.checks.append(EnvironmentCheck(
                    name="Compiler Flags",
                    status=status,
                    current_value=compiler_info,
                    expected_value='GCC with -O3 -march=native -fno-omit-frame-pointer',
                    error_message=error_msg
                ))
            else:
                self.checks.append(EnvironmentCheck(
                    name="Compiler Flags",
                    status='fail',
                    current_value='benchlib.so missing',
                    expected_value='compiled with optimization flags',
                    error_message="Compile benchlib.so first"
                ))
                self.recommendations.append("Run 'make' to build benchlib.so")
                
        except Exception as e:
            self.checks.append(EnvironmentCheck(
                name="Compiler Flags",
                status='skip',
                current_value='unknown',
                expected_value='optimized compilation',
                error_message=f"Cannot check compilation: {e}"
            ))
    
    def generate_report(self, result: EnvironmentValidationResult) -> str:
        """
        Generate human-readable environment validation report.
        
        Args:
            result: Validation result to format
            
        Returns:
            Formatted report string
        """
        status_emoji = {
            'pass': '✅',
            'fail': '❌', 
            'warning': '⚠️',
            'skip': '⏭️'
        }
        
        overall_emoji = status_emoji.get(result.overall_status, '❓')
        
        lines = [
            "# Environment Validation Report",
            "",
            f"**Overall Status**: {overall_emoji} {result.overall_status.upper()}",
            "",
            "## Validation Checks",
            ""
        ]
        
        for check in result.checks:
            emoji = status_emoji.get(check.status, '❓')
            lines.extend([
                f"### {check.name}",
                f"**Status**: {emoji} {check.status.upper()}",
                f"**Current**: {check.current_value}",
                f"**Expected**: {check.expected_value}",
            ])
            
            if check.error_message:
                lines.append(f"**Action**: {check.error_message}")
            
            lines.append("")
        
        if result.warnings:
            lines.extend([
                "## Warnings",
                ""
            ])
            for warning in result.warnings:
                lines.append(f"⚠️ {warning}")
            lines.append("")
        
        if result.recommendations:
            lines.extend([
                "## Recommendations",
                ""
            ])
            for i, rec in enumerate(result.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Academic compliance assessment
        failed_count = len([c for c in result.checks if c.status == 'fail'])
        warning_count = len([c for c in result.checks if c.status == 'warning'])
        
        lines.extend([
            "## Academic Compliance Assessment",
            ""
        ])
        
        if result.overall_status == 'pass':
            lines.extend([
                "✅ **ENVIRONMENT COMPLIANT**",
                "",
                "Environment meets academic standards for reproducible benchmarking.",
                "Results should be scientifically valid and reproducible.",
            ])
        elif result.overall_status == 'warning':
            lines.extend([
                "⚠️ **ENVIRONMENT ACCEPTABLE WITH CAVEATS**",
                "",
                f"Environment has {warning_count} warning(s) that may affect reproducibility.",
                "Results are valid but should note environmental limitations.",
                "Consider addressing warnings for optimal results.",
            ])
        else:
            lines.extend([
                "❌ **ENVIRONMENT NON-COMPLIANT**",
                "",
                f"Environment has {failed_count} critical issue(s) that compromise validity.",
                "**RECOMMENDATION**: Fix all critical issues before benchmarking.",
                "Results from this environment may not be scientifically valid.",
            ])
        
        return "\\n".join(lines)


def main():
    """Run environment validation when script is executed directly."""
    validator = EnvironmentValidator()
    result = validator.validate_all()
    
    print()
    print("=== ENVIRONMENT VALIDATION RESULTS ===")
    print()
    
    status_symbols = {
        'pass': '✅',
        'fail': '❌',
        'warning': '⚠️', 
        'skip': '⏭️'
    }
    
    for check in result.checks:
        symbol = status_symbols.get(check.status, '❓')
        print(f"{symbol} {check.name}: {check.current_value}")
        if check.error_message and check.status in ['fail', 'warning']:
            print(f"   → {check.error_message}")
    
    print()
    print(f"Overall Status: {result.overall_status.upper()}")
    
    if result.recommendations:
        print()
        print("Recommendations:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")


if __name__ == "__main__":
    main()