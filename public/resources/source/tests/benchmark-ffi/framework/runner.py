"""
Benchmark runner with environment control and validation.

Orchestrates benchmark execution with proper environment setup and validation
following Brendan Gregg's performance methodology.
"""

import os
import sys
import json
import platform
import subprocess
import tempfile
from typing import Dict, List, Callable, Any, Optional
from pathlib import Path
import gc

# Try to import psutil, but provide fallbacks if unavailable
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False
    # Create psutil-like fallbacks
    class _PsutilFallback:
        @staticmethod
        def cpu_percent():
            return 0.0
        
        @staticmethod
        def cpu_freq():
            class _CPUFreq:
                current = 0.0
                min = 0.0
                max = 0.0
            return _CPUFreq()
        
        @staticmethod
        def virtual_memory():
            class _Memory:
                total = 0
                available = 0
                percent = 0.0
                used = 0
                free = 0
            return _Memory()
        
        @staticmethod
        def sensors_temperatures():
            return {}
    
    psutil = _PsutilFallback()

from .timer import BenchmarkTimer


class BenchmarkRunner:
    """Orchestrates benchmark execution with environment control."""
    
    def __init__(self, validate_environment: bool = True):
        """
        Initialize the benchmark runner.
        
        Args:
            validate_environment: Whether to validate the environment
        """
        self.environment = self._capture_environment()
        if validate_environment:
            self._validate_environment()
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture complete system configuration."""
        env = {
            'cpu': {
                'model': platform.processor() or 'Unknown',
                'count': psutil.cpu_count(logical=False),
                'count_logical': psutil.cpu_count(logical=True),
                'smt_enabled': psutil.cpu_count(logical=True) > psutil.cpu_count(logical=False),
                'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'numa_nodes': self._get_numa_info(),
            },
            'system': {
                'platform': platform.platform(),
                'python': platform.python_version(),
                'python_build': platform.python_build(),
                'gil_disabled': self._check_gil_disabled(),
                'kernel': platform.release(),
                'libc': platform.libc_ver(),
                'machine': platform.machine(),
            },
            'process': {
                'pid': os.getpid(),
                'affinity': list(psutil.Process().cpu_affinity()) if hasattr(psutil.Process(), 'cpu_affinity') else None,
                'nice': psutil.Process().nice() if hasattr(psutil.Process(), 'nice') else None,
            },
            'compiler': self._get_compiler_info(),
            'libraries': self._get_library_versions(),
            'timestamp': self._get_timestamp(),
        }
        
        # Check Linux-specific performance settings
        if platform.system() == 'Linux':
            env['linux'] = self._get_linux_performance_settings()
        
        return env
    
    def _check_gil_disabled(self) -> bool:
        """Check if Python was built with --disable-gil."""
        # Python 3.13+ has sys._is_gil_enabled
        if hasattr(sys, '_is_gil_enabled'):
            return not sys._is_gil_enabled()
        
        # Try to detect from sysconfig
        try:
            import sysconfig
            config_args = sysconfig.get_config_var('CONFIG_ARGS')
            if config_args and '--disable-gil' in config_args:
                return True
        except:
            pass
        
        return False
    
    def _get_numa_info(self) -> Optional[Dict[str, Any]]:
        """Get NUMA topology information."""
        if platform.system() != 'Linux':
            return None
        
        try:
            # Try to get NUMA info using numactl
            result = subprocess.run(['numactl', '--hardware'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Parse basic NUMA info
                lines = result.stdout.strip().split('\n')
                nodes = 0
                for line in lines:
                    if line.startswith('available:'):
                        parts = line.split()
                        if len(parts) >= 2:
                            nodes = int(parts[1])
                        break
                return {'nodes': nodes, 'raw': result.stdout}
        except:
            pass
        
        return None
    
    def _get_compiler_info(self) -> Dict[str, Any]:
        """Get compiler information."""
        info = {}
        
        # Try to get GCC version
        try:
            result = subprocess.run(['gcc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info['gcc'] = result.stdout.split('\n')[0]
        except:
            pass
        
        # Try to get clang version
        try:
            result = subprocess.run(['clang', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info['clang'] = result.stdout.split('\n')[0]
        except:
            pass
        
        # Python compiler info
        import sysconfig
        info['python_cc'] = sysconfig.get_config_var('CC')
        info['python_cflags'] = sysconfig.get_config_var('CFLAGS')
        
        return info
    
    def _get_library_versions(self) -> Dict[str, str]:
        """Get versions of key libraries."""
        versions = {}
        
        # Standard libraries
        libraries = [
            'numpy', 'scipy', 'cffi', 'pybind11', 
            'viztracer', 'psutil', 'maturin'
        ]
        
        for lib in libraries:
            try:
                module = __import__(lib)
                if hasattr(module, '__version__'):
                    versions[lib] = module.__version__
            except ImportError:
                versions[lib] = 'not installed'
        
        return versions
    
    def _get_timestamp(self) -> str:
        """Get ISO timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_linux_performance_settings(self) -> Dict[str, Any]:
        """Get Linux-specific performance settings."""
        settings = {}
        
        # CPU governor
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                settings['cpu_governor'] = f.read().strip()
        except:
            settings['cpu_governor'] = 'unknown'
        
        # Turbo boost status (Intel)
        try:
            with open('/sys/devices/system/cpu/intel_pstate/no_turbo', 'r') as f:
                settings['turbo_disabled'] = f.read().strip() == '1'
        except:
            settings['turbo_disabled'] = None
        
        # SMT status
        try:
            with open('/sys/devices/system/cpu/smt/control', 'r') as f:
                settings['smt_control'] = f.read().strip()
        except:
            settings['smt_control'] = None
        
        # ASLR status
        try:
            with open('/proc/sys/kernel/randomize_va_space', 'r') as f:
                settings['aslr_enabled'] = f.read().strip() != '0'
        except:
            settings['aslr_enabled'] = None
        
        # Performance event paranoid level
        try:
            with open('/proc/sys/kernel/perf_event_paranoid', 'r') as f:
                settings['perf_event_paranoid'] = int(f.read().strip())
        except:
            settings['perf_event_paranoid'] = None
        
        # Transparent huge pages
        try:
            with open('/sys/kernel/mm/transparent_hugepage/enabled', 'r') as f:
                content = f.read().strip()
                # Extract the active setting (enclosed in brackets)
                import re
                match = re.search(r'\[(\w+)\]', content)
                if match:
                    settings['transparent_hugepage'] = match.group(1)
        except:
            settings['transparent_hugepage'] = None
        
        return settings
    
    def _validate_environment(self):
        """Validate environment is suitable for benchmarking."""
        warnings = []
        errors = []
        
        # Check CPU configuration
        if self.environment['cpu'].get('smt_enabled', True):
            warnings.append("SMT/Hyper-Threading is enabled (may affect consistency)")
        
        # Linux-specific checks
        if platform.system() == 'Linux' and 'linux' in self.environment:
            linux_settings = self.environment['linux']
            
            # CPU governor check
            if linux_settings.get('cpu_governor') not in ['performance', 'powersave']:
                warnings.append(f"CPU governor is '{linux_settings.get('cpu_governor')}', "
                              "not 'performance' (may affect consistency)")
            
            # Turbo boost check
            if linux_settings.get('turbo_disabled') is False:
                warnings.append("Turbo Boost is enabled (may cause variance)")
            
            # ASLR check
            if linux_settings.get('aslr_enabled'):
                warnings.append("ASLR is enabled (may affect memory benchmarks)")
            
            # Performance counter access
            paranoid = linux_settings.get('perf_event_paranoid')
            if paranoid is not None and paranoid > 0:
                warnings.append(f"perf_event_paranoid={paranoid} (may limit profiling)")
        
        # Memory checks
        mem_available = self.environment['memory']['available']
        mem_total = self.environment['memory']['total']
        if mem_available < 0.2 * mem_total:
            warnings.append(f"Low available memory: {mem_available / 1e9:.1f} GB "
                          f"({100 * mem_available / mem_total:.1f}% free)")
        
        # Print warnings
        if warnings or errors:
            print("\n⚠️  Environment Validation Results:")
            print("=" * 60)
            
            if errors:
                print("\n❌ ERRORS (these should be fixed):")
                for error in errors:
                    print(f"  • {error}")
            
            if warnings:
                print("\n⚠️  WARNINGS (may affect results):")
                for warning in warnings:
                    print(f"  • {warning}")
            
            print("\nFor best results, see ENVIRONMENT_SETUP.md")
            print("=" * 60)
            print()
    
    def run_benchmark(self, name: str, implementations: Dict[str, Callable], 
                     workload_factory: Optional[Callable[[], Any]] = None,
                     iterations: int = None) -> Dict[str, Any]:
        """
        Run benchmark across all implementations.
        
        Args:
            name: Benchmark name
            implementations: Dictionary mapping names to functions
            workload_factory: Optional factory to create workload data
            iterations: Override iteration count (None for auto-tune)
            
        Returns:
            Dictionary containing results
        """
        results = {
            'name': name,
            'environment': self.environment,
            'implementations': {}
        }
        
        # Create workload if factory provided
        workload = workload_factory() if workload_factory else None
        
        # Run each implementation in isolated subprocess for clean state
        for impl_name, impl_func in implementations.items():
            print(f"Benchmarking {impl_name}...", end='', flush=True)
            
            # For simple cases, run in same process
            if not self._requires_subprocess(impl_func):
                result = self._run_in_process(impl_func, workload, iterations)
            else:
                result = self._run_in_subprocess(name, impl_name, impl_func, 
                                               workload, iterations)
            
            results['implementations'][impl_name] = result
            
            if result and 'wall_time' in result:
                time_ms = result['wall_time']['median_ns'] / 1e6
                print(f" {time_ms:.3f} ms")
            else:
                print(" FAILED")
        
        # Add comparison analysis
        timer = BenchmarkTimer()
        if len(results['implementations']) > 1:
            # Calculate relative performance
            impl_results = results['implementations']
            times = {name: r['wall_time']['median_ns'] 
                    for name, r in impl_results.items() 
                    if r and 'wall_time' in r}
            
            if times:
                fastest = min(times, key=times.get)
                fastest_time = times[fastest]
                
                for name in impl_results:
                    if name in times:
                        impl_results[name]['relative_performance'] = \
                            fastest_time / times[name]
                
                results['summary'] = {
                    'fastest': fastest,
                    'ranking': sorted(times.keys(), key=times.get)
                }
        
        return results
    
    def _requires_subprocess(self, func: Callable) -> bool:
        """Check if function requires subprocess isolation."""
        # For now, only use subprocess for specific cases
        # Can be extended based on function attributes
        return False
    
    def _run_in_process(self, func: Callable, workload: Any, 
                       iterations: Optional[int]) -> Dict[str, Any]:
        """Run benchmark in current process."""
        try:
            # Disable GC during measurement
            gc_was_enabled = gc.isenabled()
            gc.disable()
            
            # Create benchmark function
            if workload is not None:
                bench_func = lambda: func(workload)
            else:
                bench_func = func
            
            # Warmup
            for _ in range(100):
                bench_func()
            
            # Measure
            timer = BenchmarkTimer()
            if iterations:
                # Fixed iteration count
                stats = timer._auto_stop_sampling(bench_func, iterations)
            else:
                # Auto-tune
                stats = timer.auto_tune_iterations(bench_func)
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
        
        finally:
            if gc_was_enabled:
                gc.enable()
    
    def _run_in_subprocess(self, bench_name: str, impl_name: str, 
                         func: Callable, workload: Any, 
                         iterations: Optional[int]) -> Dict[str, Any]:
        """Run benchmark in isolated subprocess."""
        # Create temporary file for results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', 
                                       delete=False) as f:
            result_file = f.name
        
        try:
            # Create subprocess script
            script = self._create_subprocess_script(
                bench_name, impl_name, func, workload, 
                iterations, result_file
            )
            
            # Run in subprocess
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, text=True, 
                                  timeout=60)
            
            if result.returncode != 0:
                return {'error': f"Subprocess failed: {result.stderr}"}
            
            # Read results
            with open(result_file, 'r') as f:
                return json.load(f)
            
        except Exception as e:
            return {'error': str(e)}
        
        finally:
            # Cleanup
            try:
                os.unlink(result_file)
            except:
                pass
    
    def _create_subprocess_script(self, bench_name: str, impl_name: str,
                                func: Callable, workload: Any,
                                iterations: Optional[int], 
                                result_file: str) -> str:
        """Create script for subprocess execution."""
        # This is a simplified version - real implementation would
        # need proper serialization of function and workload
        script = f"""
import json
import sys
sys.path.insert(0, '{os.getcwd()}')

# Run benchmark and save results
try:
    # Import and run benchmark
    # (Implementation details would go here)
    results = {{'placeholder': True}}
    
    with open('{result_file}', 'w') as f:
        json.dump(results, f)
except Exception as e:
    with open('{result_file}', 'w') as f:
        json.dump({{'error': str(e)}}, f)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', 
                                       delete=False) as f:
            f.write(script)
            return f.name
    
    def save_results(self, results: Dict[str, Any], output_dir: str = 'results'):
        """
        Save benchmark results to JSON file.
        
        Args:
            results: Benchmark results
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = self.environment['timestamp'].replace(':', '-')
        filename = f"{results['name']}_{timestamp}.json"
        
        filepath = output_path / filename
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {filepath}")
    
    def print_environment_info(self):
        """Print environment information."""
        env = self.environment
        
        print("\n🖥️  System Information")
        print("=" * 60)
        print(f"Platform: {env['system']['platform']}")
        print(f"Python: {env['system']['python']} "
              f"({'no-GIL' if env['system']['gil_disabled'] else 'with GIL'})")
        print(f"CPU: {env['cpu']['model']} "
              f"({env['cpu']['count']} cores, "
              f"{env['cpu']['count_logical']} logical)")
        
        if env['cpu']['frequency']:
            freq = env['cpu']['frequency']
            print(f"CPU Frequency: {freq['current']:.0f} MHz "
                  f"(min: {freq['min']:.0f}, max: {freq['max']:.0f})")
        
        print(f"Memory: {env['memory']['total'] / 1e9:.1f} GB total, "
              f"{env['memory']['available'] / 1e9:.1f} GB available")
        
        if platform.system() == 'Linux' and 'linux' in env:
            linux = env['linux']
            print(f"\nLinux Performance Settings:")
            print(f"  CPU Governor: {linux.get('cpu_governor', 'unknown')}")
            print(f"  Turbo Boost: {'disabled' if linux.get('turbo_disabled') else 'enabled'}")
            print(f"  SMT Control: {linux.get('smt_control', 'unknown')}")
            print(f"  ASLR: {'enabled' if linux.get('aslr_enabled') else 'disabled'}")
        
        print("=" * 60)


if __name__ == "__main__":
    # Self-test
    runner = BenchmarkRunner()
    runner.print_environment_info()
    
    # Test benchmark
    def test_func():
        return sum(range(1000))
    
    results = runner.run_benchmark(
        "self_test",
        {"test": test_func}
    )
    
    print(f"\nSelf-test median time: "
          f"{results['implementations']['test']['wall_time']['median_ns']/1e6:.2f} ms")