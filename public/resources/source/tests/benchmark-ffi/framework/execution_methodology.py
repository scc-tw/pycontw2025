"""
5-Phase Execution Methodology Framework

Implementation of Brendan Gregg's performance analysis methodology from "Systems Performance"
for FFI benchmark execution as specified in docs/benchmark-ffi/execution-methodology.md.

The 5 phases are:
1. Validation Phase - Verify correctness across all FFI methods
2. Baseline Establishment - USE method system baseline
3. Trace Phase - Small N with VizTracer for flow analysis
4. Perf Phase - Medium N with hardware counters and flame graphs  
5. Measurement Phase - Large N with statistical rigor
"""

import os
import sys
import json
import time
import subprocess
import platform
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import tempfile

# Add parent directory for framework imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.timer import BenchmarkTimer, format_nanoseconds
from framework.statistics import create_statistical_analyzer
from framework.profiling import create_advanced_profiler


class ExecutionPhase(Enum):
    """Execution phases following Brendan Gregg's methodology."""
    VALIDATION = "validation"
    BASELINE = "baseline"
    TRACE = "trace"
    PERF = "perf"
    MEASUREMENT = "measurement"


@dataclass
class SystemEnvironment:
    """System environment information for reproducible benchmarks."""
    cpu_model: str
    cpu_governor: str
    smt_enabled: bool
    isolated_cores: List[int]
    kernel_version: str
    glibc_version: str
    perf_version: str
    python_version: str
    python_binary: str
    timestamp: str


@dataclass
class PhaseResult:
    """Results from a single execution phase."""
    phase: ExecutionPhase
    success: bool
    duration_seconds: float
    artifacts: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class BenchmarkExecution:
    """Complete benchmark execution results."""
    benchmark_name: str
    hypothesis: str
    environment: SystemEnvironment
    phases: Dict[ExecutionPhase, PhaseResult] = field(default_factory=dict)
    final_results: Dict[str, Any] = field(default_factory=dict)
    statistical_analysis: Dict[str, Any] = field(default_factory=dict)


class ExecutionMethodologyFramework:
    """5-Phase execution methodology framework following Brendan Gregg's approach."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the execution framework."""
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "execution_results"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize analysis tools
        self.timer = BenchmarkTimer()
        self.stats_analyzer = create_statistical_analyzer()
        self.profiler = create_advanced_profiler(str(self.output_dir))
        
        # Standard perf events from Brendan Gregg's recommendations
        self.perf_events = [
            "task-clock", "cycles", "instructions", "branches", "branch-misses",
            "cache-references", "cache-misses", "L1-dcache-loads", "L1-dcache-load-misses",
            "LLC-loads", "LLC-load-misses", "dTLB-loads", "dTLB-load-misses",
            "context-switches", "cpu-migrations", "page-faults"
        ]
        
        print(f"🚀 5-Phase Execution Methodology Framework initialized")
        print(f"📁 Results directory: {self.output_dir}")
    
    def execute_benchmark(self, benchmark_name: str, hypothesis: str, 
                         implementations: Dict[str, Callable],
                         iterations_config: Optional[Dict[str, int]] = None) -> BenchmarkExecution:
        """
        Execute complete 5-phase benchmark following Brendan Gregg's methodology.
        
        Args:
            benchmark_name: Name of the benchmark
            hypothesis: Hypothesis being tested (e.g., 'H1_cffi_faster_than_ctypes')
            implementations: Dictionary mapping FFI method names to benchmark functions
            iterations_config: Optional iteration counts for each phase
        """
        print(f"\n🚀 Starting 5-phase execution for: {benchmark_name}")
        print(f"🧪 Testing hypothesis: {hypothesis}")
        print("=" * 80)
        
        # Set default iteration configuration
        if iterations_config is None:
            iterations_config = {
                'validation': 10,
                'trace': 1000,
                'perf': 10000,
                'measurement': 0  # Auto-tuned
            }
        
        # Create execution record
        execution = BenchmarkExecution(
            benchmark_name=benchmark_name,
            hypothesis=hypothesis,
            environment=self._capture_environment()
        )
        
        # Execute each phase in sequence
        try:
            # Phase 1: Validation
            execution.phases[ExecutionPhase.VALIDATION] = self._phase_1_validation(
                implementations, iterations_config['validation']
            )
            
            # Phase 2: Baseline Establishment
            execution.phases[ExecutionPhase.BASELINE] = self._phase_2_baseline()
            
            # Phase 3: Trace Phase
            execution.phases[ExecutionPhase.TRACE] = self._phase_3_trace(
                implementations, iterations_config['trace']
            )
            
            # Phase 4: Perf Phase
            execution.phases[ExecutionPhase.PERF] = self._phase_4_perf(
                implementations, iterations_config['perf']
            )
            
            # Phase 5: Measurement Phase
            execution.phases[ExecutionPhase.MEASUREMENT] = self._phase_5_measurement(
                implementations, iterations_config['measurement']
            )
            
            # Generate final analysis
            execution.final_results = self._generate_final_results(execution)
            execution.statistical_analysis = self._generate_statistical_analysis(execution)
            
        except Exception as e:
            print(f"❌ Execution failed: {e}")
            # Record the error
            current_phase = ExecutionPhase.VALIDATION  # Default if no phase is running
            for phase in ExecutionPhase:
                if phase in execution.phases and not execution.phases[phase].success:
                    current_phase = phase
                    break
            
            if current_phase not in execution.phases:
                execution.phases[current_phase] = PhaseResult(
                    phase=current_phase,
                    success=False,
                    duration_seconds=0,
                    errors=[str(e)]
                )
        
        # Save execution results
        self._save_execution_results(execution)
        
        return execution
    
    def _capture_environment(self) -> SystemEnvironment:
        """Capture system environment information."""
        print("📊 Capturing system environment...")
        
        # Get CPU information
        cpu_model = "Unknown"
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        cpu_model = line.split(':')[1].strip()
                        break
        except:
            pass
        
        # Get CPU governor
        cpu_governor = "Unknown"
        try:
            with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
                cpu_governor = f.read().strip()
        except:
            pass
        
        # Check SMT status
        smt_enabled = True
        try:
            with open('/sys/devices/system/cpu/smt/active', 'r') as f:
                smt_enabled = f.read().strip() == '1'
        except:
            pass
        
        # Check for isolated cores
        isolated_cores = []
        try:
            with open('/sys/devices/system/cpu/isolated', 'r') as f:
                isolated_str = f.read().strip()
                if isolated_str:
                    # Parse ranges like "2-5" or "2,3,4,5"
                    for part in isolated_str.split(','):
                        if '-' in part:
                            start, end = map(int, part.split('-'))
                            isolated_cores.extend(range(start, end + 1))
                        else:
                            isolated_cores.append(int(part))
        except:
            pass
        
        # Get system versions
        kernel_version = platform.release()
        
        glibc_version = "Unknown"
        try:
            result = subprocess.run(['ldd', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                first_line = result.stdout.split('\n')[0]
                if 'glibc' in first_line.lower():
                    glibc_version = first_line.split()[-1]
        except:
            pass
        
        perf_version = "Unknown"
        try:
            result = subprocess.run(['perf', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                perf_version = result.stdout.strip()
        except:
            pass
        
        python_version = platform.python_version()
        python_binary = sys.executable
        
        return SystemEnvironment(
            cpu_model=cpu_model,
            cpu_governor=cpu_governor,
            smt_enabled=smt_enabled,
            isolated_cores=isolated_cores,
            kernel_version=kernel_version,
            glibc_version=glibc_version,
            perf_version=perf_version,
            python_version=python_version,
            python_binary=python_binary,
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        )
    
    def _phase_1_validation(self, implementations: Dict[str, Callable], iterations: int) -> PhaseResult:
        """
        Phase 1: Validation - Verify all FFI methods produce identical results.
        """
        print("\n1️⃣ Phase 1: Validation")
        print("-" * 40)
        
        start_time = time.time()
        artifacts = {}
        metrics = {}
        errors = []
        
        try:
            print(f"🧪 Validating {len(implementations)} implementations with {iterations} iterations each...")
            
            # Collect results from all implementations
            results = {}
            for name, func in implementations.items():
                print(f"  Testing {name}...")
                impl_results = []
                
                for i in range(iterations):
                    try:
                        result = func()
                        impl_results.append(result)
                    except Exception as e:
                        errors.append(f"{name}: iteration {i}: {str(e)}")
                        continue
                
                results[name] = impl_results
            
            # Validate consistency across implementations
            validation_errors = self._validate_result_consistency(results)
            errors.extend(validation_errors)
            
            metrics['implementations_tested'] = len(implementations)
            metrics['iterations_per_implementation'] = iterations
            metrics['validation_errors'] = len(validation_errors)
            metrics['success_rate'] = (iterations * len(implementations) - len(errors)) / (iterations * len(implementations))
            
            success = len(validation_errors) == 0
            
            if success:
                print("✅ All implementations produce consistent results")
            else:
                print(f"❌ Found {len(validation_errors)} validation errors")
                for error in validation_errors[:5]:  # Show first 5 errors
                    print(f"   - {error}")
            
            # Save validation report
            validation_report = {
                'implementations': list(implementations.keys()),
                'iterations': iterations,
                'results_summary': {name: {'count': len(res), 'sample': res[:3]} for name, res in results.items()},
                'errors': errors,
                'success': success
            }
            
            report_path = self.output_dir / "validation_report.json"
            with open(report_path, 'w') as f:
                json.dump(validation_report, f, indent=2, default=str)
            artifacts['validation_report'] = str(report_path)
            
        except Exception as e:
            errors.append(f"Validation phase failed: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        print(f"⏱️  Phase 1 completed in {duration:.2f} seconds")
        
        return PhaseResult(
            phase=ExecutionPhase.VALIDATION,
            success=success,
            duration_seconds=duration,
            artifacts=artifacts,
            metrics=metrics,
            errors=errors
        )
    
    def _phase_2_baseline(self) -> PhaseResult:
        """
        Phase 2: Baseline Establishment using Brendan Gregg's USE method.
        """
        print("\n2️⃣ Phase 2: Baseline Establishment (USE Method)")
        print("-" * 40)
        
        start_time = time.time()
        artifacts = {}
        metrics = {}
        errors = []
        
        try:
            print("📊 Establishing system baseline using USE method...")
            
            # System utilization baseline
            print("  🔍 Capturing system utilization baseline...")
            try:
                result = subprocess.run(['perf', 'stat', '-a', 'sleep', '10'], 
                                      capture_output=True, text=True, timeout=15)
                metrics['system_utilization'] = result.stderr
                
                baseline_path = self.output_dir / "system_baseline.txt"
                with open(baseline_path, 'w') as f:
                    f.write("System Utilization Baseline (perf stat -a sleep 10):\n")
                    f.write(result.stderr)
                artifacts['system_baseline'] = str(baseline_path)
                
            except Exception as e:
                errors.append(f"System utilization baseline failed: {str(e)}")
            
            # CPU saturation check
            print("  💻 Checking CPU saturation...")
            try:
                result = subprocess.run(['vmstat', '1', '5'], capture_output=True, text=True, timeout=10)
                metrics['cpu_saturation'] = result.stdout
                
                vmstat_path = self.output_dir / "cpu_saturation.txt"
                with open(vmstat_path, 'w') as f:
                    f.write("CPU Saturation Check (vmstat 1 5):\n")
                    f.write(result.stdout)
                artifacts['cpu_saturation'] = str(vmstat_path)
                
            except Exception as e:
                errors.append(f"CPU saturation check failed: {str(e)}")
            
            # Memory baseline
            print("  🧠 Capturing memory baseline...")
            try:
                result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
                metrics['memory_baseline'] = result.stdout
                
                memory_path = self.output_dir / "memory_baseline.txt"
                with open(memory_path, 'w') as f:
                    f.write("Memory Baseline (free -h):\n")
                    f.write(result.stdout)
                artifacts['memory_baseline'] = str(memory_path)
                
            except Exception as e:
                errors.append(f"Memory baseline failed: {str(e)}")
            
            # Check perf access
            print("  🔧 Verifying perf access...")
            try:
                result = subprocess.run(['perf', 'stat', 'true'], capture_output=True, text=True, timeout=5)
                metrics['perf_access'] = result.returncode == 0
                
                if result.returncode != 0:
                    errors.append("perf access denied - run: sudo sysctl kernel.perf_event_paranoid=-1")
                
            except Exception as e:
                errors.append(f"Perf access check failed: {str(e)}")
            
            success = len(errors) == 0
            
            if success:
                print("✅ System baseline established successfully")
            else:
                print(f"⚠️  Baseline established with {len(errors)} warnings")
            
        except Exception as e:
            errors.append(f"Baseline phase failed: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        print(f"⏱️  Phase 2 completed in {duration:.2f} seconds")
        
        return PhaseResult(
            phase=ExecutionPhase.BASELINE,
            success=success,
            duration_seconds=duration,
            artifacts=artifacts,
            metrics=metrics,
            errors=errors
        )
    
    def _phase_3_trace(self, implementations: Dict[str, Callable], iterations: int) -> PhaseResult:
        """
        Phase 3: Trace Phase - Small N with VizTracer for execution flow analysis.
        """
        print("\n3️⃣ Phase 3: Trace Phase (VizTracer)")
        print("-" * 40)
        
        start_time = time.time()
        artifacts = {}
        metrics = {}
        errors = []
        
        try:
            print(f"📈 Tracing execution flow with {iterations} iterations...")
            
            # Check if VizTracer is available
            has_viztracer = self.profiler.has_viztracer
            
            if has_viztracer:
                print("✅ VizTracer available - generating execution traces")
                
                for name, func in implementations.items():
                    print(f"  🔍 Tracing {name}...")
                    
                    try:
                        # Measure VizTracer overhead
                        overhead_result = self.profiler.benchmark_profiling_overhead(func, iterations)
                        
                        if 'viztracer' in overhead_result['profilers']:
                            overhead_data = overhead_result['profilers']['viztracer']
                            if 'overhead_percent' in overhead_data:
                                metrics[f'{name}_viztracer_overhead'] = overhead_data['overhead_percent']
                            
                        trace_path = self.output_dir / f"trace_{name}.json"
                        artifacts[f'trace_{name}'] = str(trace_path)
                        
                    except Exception as e:
                        errors.append(f"Tracing {name} failed: {str(e)}")
                
            else:
                print("⚠️  VizTracer not available - skipping trace generation")
                errors.append("VizTracer not available for trace generation")
            
            # Alternative: Simple timing trace for flow analysis
            print("  ⏱️  Generating timing traces...")
            
            for name, func in implementations.items():
                timing_trace = []
                
                for i in range(min(iterations, 100)):  # Limit to 100 for trace analysis
                    start = time.perf_counter_ns()
                    try:
                        func()
                        end = time.perf_counter_ns()
                        timing_trace.append({
                            'iteration': i,
                            'duration_ns': end - start,
                            'timestamp': start
                        })
                    except Exception as e:
                        errors.append(f"Timing trace {name} iteration {i}: {str(e)}")
                
                # Save timing trace
                trace_path = self.output_dir / f"timing_trace_{name}.json"
                with open(trace_path, 'w') as f:
                    json.dump(timing_trace, f, indent=2)
                artifacts[f'timing_trace_{name}'] = str(trace_path)
                
                # Calculate trace metrics
                if timing_trace:
                    durations = [t['duration_ns'] for t in timing_trace]
                    metrics[f'{name}_trace_median_ns'] = int(np.median(durations)) if durations else 0
                    metrics[f'{name}_trace_variance'] = float(np.var(durations)) if durations else 0
            
            success = len(errors) < len(implementations)  # Allow some errors
            
        except Exception as e:
            errors.append(f"Trace phase failed: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        print(f"⏱️  Phase 3 completed in {duration:.2f} seconds")
        
        return PhaseResult(
            phase=ExecutionPhase.TRACE,
            success=success,
            duration_seconds=duration,
            artifacts=artifacts,
            metrics=metrics,
            errors=errors
        )
    
    def _phase_4_perf(self, implementations: Dict[str, Callable], iterations: int) -> PhaseResult:
        """
        Phase 4: Perf Phase - Medium N with hardware counters and flame graphs.
        """
        print("\n4️⃣ Phase 4: Perf Phase (Hardware Counters & Flame Graphs)")
        print("-" * 40)
        
        start_time = time.time()
        artifacts = {}
        metrics = {}
        errors = []
        
        try:
            print(f"🔥 Hardware profiling with {iterations} iterations...")
            
            # Check perf availability
            has_perf = self.profiler.has_perf
            can_profile = self.profiler.can_profile
            
            if not has_perf:
                errors.append("perf not available for hardware profiling")
                success = False
            elif not can_profile:
                errors.append("perf permissions denied - run: sudo sysctl kernel.perf_event_paranoid=-1")
                success = False
            else:
                success = True
                
                for name, func in implementations.items():
                    print(f"  📊 Profiling {name} with hardware counters...")
                    
                    try:
                        # CPU profiling with flame graphs
                        if self.profiler.has_flamegraph:
                            print(f"    🔥 Generating flame graph for {name}...")
                            flame_result = self.profiler.profile_cpu_with_flamegraph(func, duration_seconds=5)
                            
                            if flame_result.flame_graph_path:
                                artifacts[f'flamegraph_{name}'] = flame_result.flame_graph_path
                                metrics[f'{name}_samples'] = flame_result.events.get('samples', 0)
                        
                        # Cache performance analysis
                        print(f"    💾 Analyzing cache performance for {name}...")
                        cache_result = self.profiler.analyze_cache_performance(func, iterations)
                        
                        metrics.update({
                            f'{name}_l1_miss_rate': cache_result.l1_miss_rate,
                            f'{name}_l3_miss_rate': cache_result.l3_miss_rate,
                            f'{name}_cache_references': cache_result.cache_references,
                            f'{name}_cache_misses': cache_result.cache_misses,
                            f'{name}_ipc': cache_result.instructions_per_cycle,
                            f'{name}_branch_miss_rate': cache_result.branch_miss_rate
                        })
                        
                    except Exception as e:
                        errors.append(f"Perf profiling {name} failed: {str(e)}")
                
                # Generate perf comparison report
                perf_report = {
                    'implementations': list(implementations.keys()),
                    'hardware_metrics': {k: v for k, v in metrics.items() if any(impl in k for impl in implementations.keys())},
                    'profiling_errors': errors
                }
                
                report_path = self.output_dir / "perf_analysis.json"
                with open(report_path, 'w') as f:
                    json.dump(perf_report, f, indent=2, default=str)
                artifacts['perf_analysis'] = str(report_path)
        
        except Exception as e:
            errors.append(f"Perf phase failed: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        print(f"⏱️  Phase 4 completed in {duration:.2f} seconds")
        
        return PhaseResult(
            phase=ExecutionPhase.PERF,
            success=success,
            duration_seconds=duration,
            artifacts=artifacts,
            metrics=metrics,
            errors=errors
        )
    
    def _phase_5_measurement(self, implementations: Dict[str, Callable], iterations: int) -> PhaseResult:
        """
        Phase 5: Measurement Phase - Large N with statistical rigor.
        """
        print("\n5️⃣ Phase 5: Measurement Phase (Statistical Rigor)")
        print("-" * 40)
        
        start_time = time.time()
        artifacts = {}
        metrics = {}
        errors = []
        
        try:
            print(f"📏 Statistical measurement with {'auto-tuned' if iterations == 0 else str(iterations)} iterations...")
            
            if iterations == 0:
                # Auto-tuned measurement using statistical comparison
                results = self.timer.statistical_comparison(implementations)
                
                # Store raw statistical results
                metrics['statistical_analysis'] = results['statistical_analysis']
                metrics['methodology'] = results['methodology']
                
                # Extract performance data
                for name, samples in results['raw_samples'].items():
                    if samples:
                        metrics[f'{name}_median_ns'] = np.median(samples)
                        metrics[f'{name}_mean_ns'] = np.mean(samples)
                        metrics[f'{name}_std_ns'] = np.std(samples)
                        metrics[f'{name}_samples'] = len(samples)
                
            else:
                # Fixed iteration measurement
                results = self.timer.compare_implementations(implementations)
                
                for name, result in results['implementations'].items():
                    wall_time = result['wall_time']
                    metrics[f'{name}_median_ns'] = wall_time['median_ns']
                    metrics[f'{name}_mean_ns'] = wall_time['mean_ns']
                    metrics[f'{name}_std_ns'] = wall_time['std_ns']
                    metrics[f'{name}_samples'] = wall_time['samples']
            
            # Save detailed measurement results
            measurement_path = self.output_dir / "measurement_results.json"
            with open(measurement_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            artifacts['measurement_results'] = str(measurement_path)
            
            success = True
            print("✅ Statistical measurement completed")
            
        except Exception as e:
            errors.append(f"Measurement phase failed: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        print(f"⏱️  Phase 5 completed in {duration:.2f} seconds")
        
        return PhaseResult(
            phase=ExecutionPhase.MEASUREMENT,
            success=success,
            duration_seconds=duration,
            artifacts=artifacts,
            metrics=metrics,
            errors=errors
        )
    
    def _validate_result_consistency(self, results: Dict[str, List[Any]]) -> List[str]:
        """Validate that all implementations produce consistent results."""
        errors = []
        
        if len(results) < 2:
            return errors
        
        # Get reference implementation (first one)
        reference_name = list(results.keys())[0]
        reference_results = results[reference_name]
        
        # Compare all other implementations to reference
        for name, impl_results in results.items():
            if name == reference_name:
                continue
            
            if len(impl_results) != len(reference_results):
                errors.append(f"{name}: Different number of results ({len(impl_results)} vs {len(reference_results)})")
                continue
            
            # Compare individual results
            for i, (ref_val, impl_val) in enumerate(zip(reference_results, impl_results)):
                if not self._values_equal(ref_val, impl_val):
                    errors.append(f"{name}: Result mismatch at iteration {i}: {impl_val} != {ref_val}")
                    break  # Only report first mismatch per implementation
        
        return errors
    
    def _values_equal(self, val1: Any, val2: Any, tolerance: float = 1e-10) -> bool:
        """Check if two values are equal within tolerance."""
        if type(val1) != type(val2):
            return False
        
        if isinstance(val1, (int, float)):
            if isinstance(val1, float) or isinstance(val2, float):
                return abs(val1 - val2) <= tolerance
            else:
                return val1 == val2
        
        return val1 == val2
    
    def _generate_final_results(self, execution: BenchmarkExecution) -> Dict[str, Any]:
        """Generate final benchmark results from all phases."""
        final_results = {
            'benchmark_name': execution.benchmark_name,
            'hypothesis': execution.hypothesis,
            'timestamp': execution.environment.timestamp,
            'phases_completed': len([p for p in execution.phases.values() if p.success]),
            'total_phases': len(ExecutionPhase),
            'overall_success': all(p.success for p in execution.phases.values())
        }
        
        # Extract measurement results if available
        measurement_phase = execution.phases.get(ExecutionPhase.MEASUREMENT)
        if measurement_phase and measurement_phase.success:
            measurement_metrics = measurement_phase.metrics
            
            # Extract performance data
            implementations = set()
            for key in measurement_metrics.keys():
                if '_median_ns' in key:
                    impl_name = key.replace('_median_ns', '')
                    implementations.add(impl_name)
            
            final_results['implementations'] = {}
            for impl in implementations:
                final_results['implementations'][impl] = {
                    'median_ns': measurement_metrics.get(f'{impl}_median_ns', 0),
                    'mean_ns': measurement_metrics.get(f'{impl}_mean_ns', 0),
                    'std_ns': measurement_metrics.get(f'{impl}_std_ns', 0),
                    'samples': measurement_metrics.get(f'{impl}_samples', 0)
                }
        
        return final_results
    
    def _generate_statistical_analysis(self, execution: BenchmarkExecution) -> Dict[str, Any]:
        """Generate statistical analysis from measurement phase."""
        statistical_analysis = {}
        
        measurement_phase = execution.phases.get(ExecutionPhase.MEASUREMENT)
        if measurement_phase and measurement_phase.success:
            if 'statistical_analysis' in measurement_phase.metrics:
                statistical_analysis = measurement_phase.metrics['statistical_analysis']
        
        return statistical_analysis
    
    def _save_execution_results(self, execution: BenchmarkExecution):
        """Save complete execution results in JSON format."""
        results_file = self.output_dir / f"{execution.benchmark_name}_execution.json"
        
        # Convert to serializable format
        execution_dict = {
            'benchmark_name': execution.benchmark_name,
            'hypothesis': execution.hypothesis,
            'environment': execution.environment.__dict__,
            'phases': {
                phase.value: {
                    'success': result.success,
                    'duration_seconds': result.duration_seconds,
                    'artifacts': result.artifacts,
                    'metrics': result.metrics,
                    'errors': result.errors
                }
                for phase, result in execution.phases.items()
            },
            'final_results': execution.final_results,
            'statistical_analysis': execution.statistical_analysis
        }
        
        with open(results_file, 'w') as f:
            json.dump(execution_dict, f, indent=2, default=str)
        
        print(f"\n💾 Execution results saved: {results_file}")


def create_execution_methodology_framework(output_dir: str = None) -> ExecutionMethodologyFramework:
    """Factory function to create execution methodology framework."""
    return ExecutionMethodologyFramework(output_dir)


if __name__ == "__main__":
    # Example usage
    framework = create_execution_methodology_framework()
    
    def dummy_ctypes():
        return sum(range(100))
    
    def dummy_cffi():
        return sum(range(100))
    
    # Test with dummy implementations
    implementations = {
        'ctypes': dummy_ctypes,
        'cffi': dummy_cffi
    }
    
    execution = framework.execute_benchmark(
        benchmark_name="test_benchmark",
        hypothesis="H1_test_hypothesis",
        implementations=implementations
    )
    
    print(f"\n🎯 Execution completed: {execution.final_results['overall_success']}")
    print(f"📊 Phases completed: {execution.final_results['phases_completed']}/{execution.final_results['total_phases']}")