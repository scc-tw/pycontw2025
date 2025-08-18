"""
Advanced Profiling Integration with Brendan Gregg's Performance Methodology.

Multi-tool profiling support following "Systems Performance" book methodology:
- CPU profiling with flame graphs
- Cache analysis with hardware counters  
- Off-CPU analysis with scheduler events
- Memory allocation tracking
- Branch prediction analysis
"""

import subprocess
import tempfile
import os
import sys
import time
import shutil
import json
import re
from typing import Callable, Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass

from .timer import BenchmarkTimer


@dataclass
class PerfProfile:
    """Results from perf profiling session."""
    profile_type: str
    duration_seconds: float
    events: Dict[str, Union[int, float]]
    flame_graph_path: Optional[str] = None
    perf_data_path: Optional[str] = None
    overhead_percent: Optional[float] = None


@dataclass  
class CacheAnalysis:
    """Cache performance analysis results."""
    l1_miss_rate: float
    l2_miss_rate: float
    l3_miss_rate: float
    cache_references: int
    cache_misses: int
    instructions_per_cycle: float
    branch_miss_rate: float


class AdvancedProfiler:
    """Advanced profiling following Brendan Gregg's Systems Performance methodology."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize profiler with tool availability check."""
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "profiling_results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.check_tools()
        self.timer = BenchmarkTimer()
        
        # Standard perf event sets from Brendan Gregg's methodology
        self.cpu_events = [
            "task-clock", "cycles", "instructions", "branches", "branch-misses"
        ]
        
        self.cache_events = [
            "cache-references", "cache-misses", 
            "L1-dcache-loads", "L1-dcache-load-misses",
            "LLC-loads", "LLC-load-misses",
            "dTLB-loads", "dTLB-load-misses"
        ]
        
        self.memory_events = [
            "page-faults", "context-switches", "cpu-migrations"
        ]
        
    def check_tools(self):
        """Verify profiling tools are available."""
        self.has_perf = self._check_command(['perf', '--version'])
        self.has_flamegraph = self._check_flamegraph_tools()
        self.has_viztracer = self._check_module('viztracer')
        self.can_profile = self._check_perf_permissions()
        
        # Print tool availability
        print(f"🔧 Profiling Tools Available:")
        print(f"  perf: {'✅' if self.has_perf else '❌'}")
        print(f"  FlameGraph: {'✅' if self.has_flamegraph else '❌'}")
        print(f"  VizTracer: {'✅' if self.has_viztracer else '❌'}")
        print(f"  perf permissions: {'✅' if self.can_profile else '❌'}")
        
        if not self.can_profile:
            print("⚠️  Run: sudo sysctl kernel.perf_event_paranoid=-1")
    
    def _check_flamegraph_tools(self) -> bool:
        """Check if FlameGraph tools are available."""
        # Check common locations for FlameGraph tools
        flamegraph_paths = [
            "/usr/local/bin/flamegraph.pl",
            "/usr/bin/flamegraph.pl",
            shutil.which("flamegraph.pl"),
            shutil.which("stackcollapse-perf.pl")
        ]
        
        return any(path and Path(path).exists() for path in flamegraph_paths)
    
    def _check_perf_permissions(self) -> bool:
        """Check if perf can access hardware counters."""
        try:
            result = subprocess.run(['perf', 'stat', '-e', 'cycles', 'true'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def profile_cpu_with_flamegraph(self, func: Callable, duration_seconds: float = 5, 
                                   freq: int = 997) -> PerfProfile:
        """
        CPU profiling with flame graph generation following Brendan Gregg's methodology.
        
        Args:
            func: Function to profile
            duration_seconds: Profiling duration
            freq: Sampling frequency (997 Hz recommended by Brendan Gregg)
        """
        if not self.has_perf:
            raise RuntimeError("perf not available")
        
        timestamp = int(time.time())
        perf_data = self.output_dir / f"cpu_profile_{timestamp}.perf.data"
        flame_svg = self.output_dir / f"cpu_flamegraph_{timestamp}.svg"
        
        # Step 1: Record with perf (Brendan Gregg's preferred settings)
        cmd = [
            'perf', 'record',
            '-F', str(freq),  # 997 Hz sampling
            '-g',             # Call graphs
            '--call-graph=dwarf',  # DWARF unwinding for better accuracy
            '-o', str(perf_data),
            '--'
        ]
        
        print(f"🔥 Recording CPU profile for {duration_seconds}s at {freq} Hz...")
        
        # Run the profiling
        start_time = time.time()
        process = subprocess.Popen(cmd + [sys.executable, '-c', f'''
import time
import sys
sys.path.insert(0, "{Path(__file__).parent.parent}")

# Import and run the function
target_func = {func.__name__}
end_time = time.time() + {duration_seconds}

while time.time() < end_time:
    target_func()
'''])
        
        time.sleep(duration_seconds + 0.5)  # Allow some buffer
        process.terminate()
        process.wait()
        
        actual_duration = time.time() - start_time
        
        # Step 2: Generate flame graph if tools available
        flame_graph_path = None
        if self.has_flamegraph:
            try:
                flame_graph_path = self._generate_flamegraph(perf_data, flame_svg)
            except Exception as e:
                print(f"⚠️  Flame graph generation failed: {e}")
        
        # Step 3: Extract basic statistics
        events = self._extract_perf_stats(perf_data)
        
        return PerfProfile(
            profile_type="cpu_flamegraph",
            duration_seconds=actual_duration,
            events=events,
            flame_graph_path=str(flame_graph_path) if flame_graph_path else None,
            perf_data_path=str(perf_data)
        )
    
    def analyze_cache_performance(self, func: Callable, iterations: int = 10000) -> CacheAnalysis:
        """
        Cache analysis following Brendan Gregg's cache profiling methodology.
        
        Chapter 7 of Systems Performance - Memory and cache analysis.
        """
        if not self.has_perf or not self.can_profile:
            raise RuntimeError("perf with hardware counters not available")
        
        # Hardware counter events for cache analysis
        events = ','.join(self.cache_events + self.cpu_events)
        
        cmd = [
            'perf', 'stat',
            '-e', events,
            '-r', '3',  # Run 3 times for statistical significance
            '--',
            sys.executable, '-c', f'''
import sys
sys.path.insert(0, "{Path(__file__).parent.parent}")

target_func = {func.__name__}
for _ in range({iterations}):
    target_func()
'''
        ]
        
        print(f"📊 Analyzing cache performance for {iterations} iterations...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"perf stat failed: {result.stderr}")
            
            # Parse perf stat output
            stats = self._parse_perf_stat_output(result.stderr)
            
            # Calculate derived metrics
            cache_refs = stats.get('cache-references', 0)
            cache_misses = stats.get('cache-misses', 0)
            l1_loads = stats.get('L1-dcache-loads', 0)
            l1_misses = stats.get('L1-dcache-load-misses', 0)
            llc_loads = stats.get('LLC-loads', 0)
            llc_misses = stats.get('LLC-load-misses', 0)
            cycles = stats.get('cycles', 0)
            instructions = stats.get('instructions', 0)
            branches = stats.get('branches', 0)
            branch_misses = stats.get('branch-misses', 0)
            
            return CacheAnalysis(
                l1_miss_rate=l1_misses / l1_loads if l1_loads > 0 else 0.0,
                l2_miss_rate=0.0,  # L2 not directly available on all systems
                l3_miss_rate=llc_misses / llc_loads if llc_loads > 0 else 0.0,
                cache_references=cache_refs,
                cache_misses=cache_misses,
                instructions_per_cycle=instructions / cycles if cycles > 0 else 0.0,
                branch_miss_rate=branch_misses / branches if branches > 0 else 0.0
            )
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Cache analysis timed out")
    
    def benchmark_profiling_overhead(self, func: Callable, iterations: int = 1000) -> Dict[str, Any]:
        """
        Quantify profiling overhead for different tools.
        
        Important for understanding measurement accuracy.
        """
        results = {}
        
        # Baseline measurement (no profiling)
        print("📏 Measuring baseline performance...")
        baseline_times = []
        for _ in range(10):
            start = time.perf_counter_ns()
            for _ in range(iterations):
                func()
            end = time.perf_counter_ns()
            baseline_times.append(end - start)
        
        baseline_median = sorted(baseline_times)[len(baseline_times)//2]
        results['baseline_ns'] = baseline_median
        results['profilers'] = {}
        
        # VizTracer overhead
        if self.has_viztracer:
            try:
                import viztracer
                
                print("📊 Measuring VizTracer overhead...")
                tracer_times = []
                
                for _ in range(5):  # Fewer runs due to overhead
                    tracer = viztracer.VizTracer()
                    tracer.start()
                    
                    start = time.perf_counter_ns()
                    for _ in range(iterations // 10):  # Reduce iterations for tracer
                        func()
                    end = time.perf_counter_ns()
                    
                    tracer.stop()
                    tracer_times.append(end - start)
                
                tracer_median = sorted(tracer_times)[len(tracer_times)//2]
                # Scale up to match baseline iteration count
                tracer_median *= 10
                
                results['profilers']['viztracer'] = {
                    'time_ns': tracer_median,
                    'overhead_percent': ((tracer_median - baseline_median) / baseline_median) * 100
                }
                
            except Exception as e:
                results['profilers']['viztracer'] = {'error': str(e)}
        
        # perf stat overhead
        if self.has_perf and self.can_profile:
            try:
                print("📈 Measuring perf stat overhead...")
                
                # Run with perf stat
                cmd = [
                    'perf', 'stat',
                    '-e', 'cycles,instructions',
                    '--',
                    sys.executable, '-c', f'''
import time
import sys
sys.path.insert(0, "{Path(__file__).parent.parent}")

target_func = {func.__name__}
start = time.perf_counter_ns()
for _ in range({iterations}):
    target_func()
end = time.perf_counter_ns()
print(f"TIME_NS: {{end - start}}")
'''
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Extract time from output
                    time_match = re.search(r'TIME_NS: (\d+)', result.stdout)
                    if time_match:
                        perf_time = int(time_match.group(1))
                        
                        results['profilers']['perf_stat'] = {
                            'time_ns': perf_time,
                            'overhead_percent': ((perf_time - baseline_median) / baseline_median) * 100
                        }
                
            except Exception as e:
                results['profilers']['perf_stat'] = {'error': str(e)}
        
        return results
    
    def _generate_flamegraph(self, perf_data: Path, output_svg: Path) -> Optional[Path]:
        """Generate flame graph from perf data."""
        # Try different FlameGraph tool locations
        stackcollapse = None
        flamegraph = None
        
        for tool_dir in ["/usr/local/bin", "/usr/bin", ""]:
            stackcollapse_path = shutil.which("stackcollapse-perf.pl") or f"{tool_dir}/stackcollapse-perf.pl"
            flamegraph_path = shutil.which("flamegraph.pl") or f"{tool_dir}/flamegraph.pl"
            
            if Path(stackcollapse_path).exists() and Path(flamegraph_path).exists():
                stackcollapse = stackcollapse_path
                flamegraph = flamegraph_path
                break
        
        if not stackcollapse or not flamegraph:
            raise RuntimeError("FlameGraph tools not found. Install from: https://github.com/brendangregg/FlameGraph")
        
        # Generate flame graph
        cmd1 = ['perf', 'script', '-i', str(perf_data)]
        cmd2 = [stackcollapse]
        cmd3 = [flamegraph]
        
        with open(output_svg, 'w') as svg_file:
            p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
            p3 = subprocess.Popen(cmd3, stdin=p2.stdout, stdout=svg_file)
            
            p1.stdout.close()
            p2.stdout.close()
            p3.wait()
        
        if output_svg.exists() and output_svg.stat().st_size > 0:
            return output_svg
        else:
            raise RuntimeError("Flame graph generation produced empty output")
    
    def _extract_perf_stats(self, perf_data: Path) -> Dict[str, Any]:
        """Extract basic statistics from perf data."""
        cmd = ['perf', 'report', '-i', str(perf_data), '--stdio', '--header']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            stats = {'samples': 0, 'events': []}
            
            # Parse header for basic info
            for line in result.stdout.split('\n'):
                if 'samples' in line:
                    # Extract sample count
                    match = re.search(r'(\d+)\s+samples', line)
                    if match:
                        stats['samples'] = int(match.group(1))
                elif 'event' in line:
                    stats['events'].append(line.strip())
            
            return stats
            
        except subprocess.TimeoutExpired:
            return {'error': 'perf report timed out'}
    
    def _parse_perf_stat_output(self, stderr_output: str) -> Dict[str, int]:
        """Parse perf stat output to extract counter values."""
        stats = {}
        
        for line in stderr_output.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse lines like: "1,234,567  cache-references"
            parts = line.split()
            if len(parts) >= 2:
                value_str = parts[0].replace(',', '')
                event_name = parts[1] if len(parts) > 1 else 'unknown'
                
                try:
                    value = int(value_str)
                    stats[event_name] = value
                except ValueError:
                    continue
        
        return stats
    
    def _check_command(self, cmd: List[str]) -> bool:
        """Check if a command is available."""
        try:
            subprocess.run(cmd, capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_module(self, module_name: str) -> bool:
        """Check if a Python module is available."""
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False


# Legacy compatibility
class ProfilerIntegration(AdvancedProfiler):
    """Legacy compatibility class."""
    pass


def create_advanced_profiler(output_dir: str = None) -> AdvancedProfiler:
    """Factory function to create advanced profiler instance."""
    return AdvancedProfiler(output_dir)


def create_simple_profiler() -> AdvancedProfiler:
    """Create simple profiler for basic usage."""
    return AdvancedProfiler()


if __name__ == "__main__":
    # Self-test
    profiler = create_advanced_profiler()
    
    def test_function():
        """Simple test function."""
        return sum(i * i for i in range(1000))
    
    print("\n🧪 Testing advanced profiler...")
    
    # Test overhead measurement
    overhead = profiler.benchmark_profiling_overhead(test_function, 100)
    print(f"\nBaseline time: {overhead['baseline_ns']/1e6:.2f} ms")
    
    for tool, result in overhead['profilers'].items():
        if 'overhead_percent' in result:
            print(f"{tool} overhead: {result['overhead_percent']:.1f}%")
        else:
            print(f"{tool}: {result.get('status', 'unknown')}")
    
    print("\n✅ Advanced profiler test completed!")