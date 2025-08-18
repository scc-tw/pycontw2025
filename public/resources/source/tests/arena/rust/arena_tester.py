#!/usr/bin/env python3
"""
Arena Tester - Testing functionality for Arena extensions.

This module handles running arena memory leak tests, monitoring memory usage,
and providing various test modes designed to demonstrate higher arena leakage
risk in no-GIL Python due to true parallelism creating O(MN) complexity.
"""

import os
import sys
import time
import threading
import concurrent.futures
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from arena_manager import ArenaManager

class ArenaTester(ArenaManager):
    """Manages Arena testing functionality."""
    
    def __init__(self, base_dir: Path):
        super().__init__(base_dir)
    
    def test_arena_with_current_python(self, thread_count: int, sleep_seconds: int = 0, 
                                     simple: bool = False, monitor: bool = False):
        """Run arena test with current Python environment."""
        # Try to import the compiled module
        try:
            import glibc_arena_poc
        except ImportError as e:
            print(f"Error: Could not import glibc_arena_poc module: {e}")
            print("Make sure to build the module first with:")
            print("  python arena_test.py build")
            sys.exit(1)
        
        print("=== Glibc Arena Memory Leak Test ===")
        print(f"PID: {os.getpid()}")
        
        # Show configuration
        config = glibc_arena_poc.get_config()
        print(f"Configuration:")
        print(f"  Thread count: {thread_count}")
        print(f"  Allocations per thread: {config['allocs_per_thread']}")
        print(f"  Allocation size: {config['alloc_size_mib']:.1f} MiB ({config['alloc_size_bytes']:,} bytes)")
        
        if monitor:
            print(f"\nMonitoring commands:")
            print(f"  watch -n0.5 pmap -x {os.getpid()}")
            print(f"  top -p {os.getpid()}")
            input("\nPress ENTER to start the test...")
        
        print(f"\nInitial RSS: {glibc_arena_poc.get_rss_mib():.2f} MiB")
        
        if simple:
            # Simple test
            print("Running simple arena test...")
            initial_rss, final_rss = glibc_arena_poc.run_arena_test(thread_count)
            print(f"Results:")
            print(f"  Initial RSS: {initial_rss:.2f} MiB")
            print(f"  Final RSS: {final_rss:.2f} MiB")
            print(f"  Difference: {final_rss - initial_rss:.2f} MiB")
        else:
            # Detailed test
            print("Running detailed arena test...")
            results = glibc_arena_poc.run_arena_test_detailed(thread_count, sleep_seconds)
            
            print(f"Results:")
            print(f"  PID: {results['pid']}")
            print(f"  Thread count: {results['thread_count']}")
            print(f"  Initial RSS: {results['initial_rss_mib']:.2f} MiB")
            print(f"  After task RSS: {results['after_task_rss_mib']:.2f} MiB")
            print(f"  Task difference: {results['after_task_rss_mib'] - results['initial_rss_mib']:.2f} MiB")
            
            if 'after_sleep_rss_mib' in results:
                print(f"  After sleep RSS: {results['after_sleep_rss_mib']:.2f} MiB")
                print(f"  Sleep difference: {results['after_sleep_rss_mib'] - results['after_task_rss_mib']:.2f} MiB")
        
        if sleep_seconds > 0 and simple:
            print(f"\nSleeping for {sleep_seconds} seconds for memory observation...")
            time.sleep(sleep_seconds)
            final_rss = glibc_arena_poc.get_rss_mib()
            print(f"RSS after sleep: {final_rss:.2f} MiB")
        
        print("\nTest completed.")
    
    def test_arena_with_python(self, python_path: Path, build_name: str) -> bool:
        """Test the arena extension with a specific Python build."""
        print(f"\n{'='*60}")
        print(f"Testing Arena with {build_name}")
        print(f"Python: {python_path}")
        print(f"{'='*60}")
        
        # Test basic functionality
        test_code = """
import glibc_arena_poc
import sys

print(f"Python version: {sys.version}")
print(f"Free-threaded: {hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()}")

# Basic memory check
initial_rss = glibc_arena_poc.get_rss_mib()
print(f"Initial RSS: {initial_rss:.1f} MiB")

# Get configuration
config = glibc_arena_poc.get_config()
print(f"Allocation size: {config['alloc_size_mib']:.2f} MiB")
print(f"Allocations per thread: {config['allocs_per_thread']}")

# Run a small arena test
print("\\nRunning arena test with 2 threads...")
initial, final = glibc_arena_poc.run_arena_test(2)
print(f"Memory before: {initial:.1f} MiB")
print(f"Memory after:  {final:.1f} MiB")
print(f"Memory delta:  {final - initial:.1f} MiB")

# Get detailed memory stats
mem_stats = glibc_arena_poc.get_memory_stats()
print(f"\\nDetailed memory stats:")
print(f"  VM RSS: {mem_stats['vm_rss_mib']:.1f} MiB")
print(f"  VM Peak: {mem_stats['vm_peak_mib']:.1f} MiB")

print("\\n✅ Arena test completed successfully!")
"""
        
        try:
            env = self.setup_environment(build_name)
            result = subprocess.run(
                [str(python_path), "-c", test_code],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error running test:")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def quick_test(self):
        """Quick test function for interactive use."""
        try:
            import glibc_arena_poc
        except ImportError:
            print("❌ Module not found. Run 'python arena_test.py build' first.")
            return None
            
        print("Running quick arena test with 1000 threads...")
        initial_rss, final_rss = glibc_arena_poc.run_arena_test(1000)
        print(f"Initial RSS: {initial_rss:.2f} MiB")
        print(f"Final RSS: {final_rss:.2f} MiB")
        print(f"Difference: {final_rss - initial_rss:.2f} MiB")
        return final_rss - initial_rss
    
    def test_specific_build(self, build_name: str, thread_count: int = 1000) -> Optional[dict]:
        """Test arena with a specific Python build."""
        python_path = self.get_python_executable(build_name)
        if not python_path:
            self.log(f"❌ Python not found for {build_name}", "ERROR")
            return None
        
        # Check if module is installed
        module_info = self.get_module_info(build_name)
        if not module_info or not module_info.get("installed"):
            self.log(f"❌ glibc_arena_poc not installed for {build_name}", "ERROR")
            return None
        
        self.log(f"Testing {build_name} with {thread_count} threads...")
        
        # Run test
        test_code = f"""
import glibc_arena_poc
import sys
import json

# Get system info
info = {{
    "python_version": sys.version,
    "free_threaded": hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled(),
    "build_name": "{build_name}"
}}

# Run arena test
initial_rss, final_rss = glibc_arena_poc.run_arena_test({thread_count})
info["initial_rss_mib"] = initial_rss
info["final_rss_mib"] = final_rss
info["memory_delta_mib"] = final_rss - initial_rss

# Get configuration
config = glibc_arena_poc.get_config()
info["config"] = config

print(json.dumps(info, indent=2))
"""
        
        try:
            env = self.setup_environment(build_name)
            result = self.run_command(
                [str(python_path), "-c", test_code],
                env=env,
                check=True,
                verbose=False
            )
            
            import json
            test_result = json.loads(result.stdout)
            self.log(f"✅ Test completed for {build_name}: "
                    f"{test_result['memory_delta_mib']:.2f} MiB delta")
            return test_result
            
        except Exception as e:
            self.log(f"❌ Test failed for {build_name}: {e}", "ERROR")
            return None
    
    def benchmark_all_builds(self, thread_count: int = 1000) -> dict:
        """Run benchmark tests across all available Python builds."""
        results = {}
        available_builds = self.get_available_builds()
        
        if not available_builds:
            self.log("❌ No Python builds available", "ERROR")
            return results
        
        self.log(f"Running benchmark with {thread_count} threads across {len(available_builds)} builds")
        
        for build_name in available_builds:
            result = self.test_specific_build(build_name, thread_count)
            if result:
                results[build_name] = result
        
        return results
    
    def run_concurrent_arena_stress_test(self, python_threads: int = 16, rust_threads_per_call: int = 100, 
                                        iterations_per_thread: int = 10) -> Dict:
        """
        Run concurrent arena stress test to demonstrate O(MN) complexity in no-GIL.
        
        This test creates N Python threads, each making multiple calls to Rust functions
        that spawn M threads. In GIL Python, threads are serialized (O(N*M) sequentially).
        In no-GIL Python, true parallelism can create O(N*M) concurrent allocations.
        
        Args:
            python_threads: Number of Python threads (N)
            rust_threads_per_call: Number of Rust threads per call (M) 
            iterations_per_thread: Number of iterations per Python thread
        """
        try:
            import glibc_arena_poc
        except ImportError:
            print("❌ Module not found. Run 'python arena_test.py build' first.")
            return {}
        
        # Check if we're in no-GIL mode
        free_threaded = hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()
        
        print(f"🧪 Concurrent Arena Stress Test")
        print(f"   Python Threads (N): {python_threads}")
        print(f"   Rust Threads per call (M): {rust_threads_per_call}")
        print(f"   Iterations per Python thread: {iterations_per_thread}")
        print(f"   Total potential concurrency: {python_threads * rust_threads_per_call * iterations_per_thread}")
        print(f"   Free-threaded mode: {free_threaded}")
        
        initial_rss = glibc_arena_poc.get_rss_mib()
        start_time = time.time()
        
        def python_worker(worker_id: int) -> Dict:
            """Worker function that each Python thread runs."""
            worker_start = time.time()
            local_memory_deltas = []
            
            for i in range(iterations_per_thread):
                iteration_start_rss = glibc_arena_poc.get_rss_mib()
                
                # This call will spawn rust_threads_per_call Rust threads
                initial, final = glibc_arena_poc.run_arena_test(rust_threads_per_call)
                memory_delta = final - initial
                local_memory_deltas.append(memory_delta)
                
                # Small delay to allow for memory pressure observation
                time.sleep(0.01)
            
            worker_end = time.time()
            return {
                "worker_id": worker_id,
                "memory_deltas": local_memory_deltas,
                "total_memory_delta": sum(local_memory_deltas),
                "duration": worker_end - worker_start
            }
        
        # Run concurrent Python threads
        worker_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=python_threads) as executor:
            futures = [executor.submit(python_worker, i) for i in range(python_threads)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    worker_results.append(result)
                except Exception as e:
                    print(f"Worker failed: {e}")
        
        end_time = time.time()
        final_rss = glibc_arena_poc.get_rss_mib()
        
        # Calculate results
        total_memory_delta = final_rss - initial_rss
        total_duration = end_time - start_time
        total_worker_memory = sum(r["total_memory_delta"] for r in worker_results)
        avg_worker_duration = sum(r["duration"] for r in worker_results) / len(worker_results)
        
        # Calculate parallelism metrics
        theoretical_sequential_time = avg_worker_duration * python_threads
        parallelism_factor = theoretical_sequential_time / total_duration if total_duration > 0 else 0
        
        return {
            "test_type": "concurrent_arena_stress",
            "free_threaded": free_threaded,
            "config": {
                "python_threads": python_threads,
                "rust_threads_per_call": rust_threads_per_call,
                "iterations_per_thread": iterations_per_thread,
                "total_rust_thread_spawns": python_threads * iterations_per_thread * rust_threads_per_call
            },
            "memory": {
                "initial_rss_mib": initial_rss,
                "final_rss_mib": final_rss,
                "total_memory_delta_mib": total_memory_delta,
                "worker_reported_memory_mib": total_worker_memory
            },
            "timing": {
                "total_duration_sec": total_duration,
                "avg_worker_duration_sec": avg_worker_duration,
                "theoretical_sequential_sec": theoretical_sequential_time,
                "parallelism_factor": parallelism_factor
            },
            "worker_results": worker_results
        }
    
    def run_burst_allocation_test(self, burst_count: int = 8, threads_per_burst: int = 1000, 
                                burst_interval: float = 0.1) -> Dict:
        """
        Run burst allocation test to show arena fragmentation under concurrent load.
        
        Creates sudden bursts of allocations that stress the arena system differently
        in GIL vs no-GIL environments. No-GIL can create more simultaneous arena pressure.
        """
        try:
            import glibc_arena_poc
        except ImportError:
            print("❌ Module not found. Run 'python arena_test.py build' first.")
            return {}
        
        free_threaded = hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()
        
        print(f"💥 Burst Allocation Test")
        print(f"   Burst count: {burst_count}")
        print(f"   Threads per burst: {threads_per_burst}")
        print(f"   Burst interval: {burst_interval}s")
        print(f"   Free-threaded mode: {free_threaded}")
        
        initial_rss = glibc_arena_poc.get_rss_mib()
        burst_results = []
        
        def execute_burst(burst_id: int) -> Dict:
            """Execute a single burst of allocations."""
            burst_start = time.time()
            burst_initial_rss = glibc_arena_poc.get_rss_mib()
            
            # Run the arena test for this burst
            initial, final = glibc_arena_poc.run_arena_test(threads_per_burst)
            
            burst_end = time.time()
            burst_final_rss = glibc_arena_poc.get_rss_mib()
            
            return {
                "burst_id": burst_id,
                "burst_memory_delta": final - initial,
                "observed_rss_delta": burst_final_rss - burst_initial_rss,
                "duration": burst_end - burst_start,
                "timestamp": burst_start
            }
        
        start_time = time.time()
        
        # Execute bursts with controlled timing
        for i in range(burst_count):
            if i > 0:  # Don't wait before first burst
                time.sleep(burst_interval)
            
            result = execute_burst(i)
            burst_results.append(result)
            
            print(f"   Burst {i+1}/{burst_count}: {result['burst_memory_delta']:.2f} MiB delta")
        
        end_time = time.time()
        final_rss = glibc_arena_poc.get_rss_mib()
        
        total_burst_memory = sum(r["burst_memory_delta"] for r in burst_results)
        total_observed_memory = final_rss - initial_rss
        
        return {
            "test_type": "burst_allocation",
            "free_threaded": free_threaded,
            "config": {
                "burst_count": burst_count,
                "threads_per_burst": threads_per_burst,
                "burst_interval": burst_interval,
                "total_threads": burst_count * threads_per_burst
            },
            "memory": {
                "initial_rss_mib": initial_rss,
                "final_rss_mib": final_rss,
                "total_observed_delta_mib": total_observed_memory,
                "total_burst_reported_mib": total_burst_memory,
                "memory_amplification": total_observed_memory / total_burst_memory if total_burst_memory > 0 else 0
            },
            "timing": {
                "total_duration_sec": end_time - start_time,
                "avg_burst_duration_sec": sum(r["duration"] for r in burst_results) / len(burst_results)
            },
            "burst_results": burst_results
        }
    
    def compare_gil_vs_nogil_arena_risk(self, python_threads: int = 16, rust_threads: int = 100) -> Dict:
        """
        Compare arena leakage risk between GIL and no-GIL using concurrent stress tests.
        
        This is the main test to demonstrate "Higher Risk for Arena Leakage in GLibc when no-gil".
        """
        comparison = {}
        
        # Group builds by version
        versions = {}
        for build in self.get_available_builds():
            version = build.split('-')[0]
            if version not in versions:
                versions[version] = {}
            gil_status = "nogil" if "nogil" in build else "gil"
            versions[version][gil_status] = build
        
        # Test each version that has both GIL and no-GIL builds
        for version, builds in versions.items():
            if "gil" in builds and "nogil" in builds:
                self.log(f"🔬 Comparing Arena Risk - Python {version}: GIL vs no-GIL")
                
                # Test GIL version
                gil_result = self._run_arena_risk_test(builds["gil"], python_threads, rust_threads)
                
                # Test no-GIL version  
                nogil_result = self._run_arena_risk_test(builds["nogil"], python_threads, rust_threads)
                
                if gil_result and nogil_result:
                    # Calculate risk amplification
                    gil_memory = gil_result["memory"]["total_memory_delta_mib"]
                    nogil_memory = nogil_result["memory"]["total_memory_delta_mib"]
                    risk_amplification = nogil_memory / gil_memory if gil_memory > 0 else 0
                    
                    # Calculate parallelism difference
                    gil_parallelism = gil_result["timing"]["parallelism_factor"]
                    nogil_parallelism = nogil_result["timing"]["parallelism_factor"]
                    
                    comparison[version] = {
                        "gil": gil_result,
                        "nogil": nogil_result,
                        "risk_metrics": {
                            "memory_amplification": risk_amplification,
                            "absolute_memory_difference_mib": nogil_memory - gil_memory,
                            "parallelism_increase": nogil_parallelism / gil_parallelism if gil_parallelism > 0 else 0,
                            "risk_level": "HIGH" if risk_amplification > 1.5 else "MODERATE" if risk_amplification > 1.1 else "LOW"
                        }
                    }
                    
                    self.log(f"   GIL memory delta: {gil_memory:.2f} MiB")
                    self.log(f"   no-GIL memory delta: {nogil_memory:.2f} MiB") 
                    self.log(f"   Risk amplification: {risk_amplification:.2f}x")
        
        return comparison
    
    def _run_arena_risk_test(self, build_name: str, python_threads: int, rust_threads: int) -> Optional[Dict]:
        """Run arena risk test for a specific Python build."""
        python_path = self.get_python_executable(build_name)
        if not python_path:
            self.log(f"❌ Python not found for {build_name}", "ERROR")
            return None
        
        # Check if module is installed
        module_info = self.get_module_info(build_name)
        if not module_info or not module_info.get("installed"):
            self.log(f"❌ glibc_arena_poc not installed for {build_name}", "ERROR")
            return None
        
        # Prepare the concurrent stress test code
        test_code = f"""
import glibc_arena_poc
import sys
import time
import threading
import concurrent.futures
import json

# Test configuration
PYTHON_THREADS = {python_threads}
RUST_THREADS_PER_CALL = {rust_threads}
ITERATIONS_PER_THREAD = 5

free_threaded = hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()

def python_worker(worker_id):
    worker_memory_deltas = []
    for i in range(ITERATIONS_PER_THREAD):
        # Each call spawns RUST_THREADS_PER_CALL Rust threads
        initial, final = glibc_arena_poc.run_arena_test(RUST_THREADS_PER_CALL)
        worker_memory_deltas.append(final - initial)
        time.sleep(0.005)  # Small delay
    
    return {{
        "worker_id": worker_id,
        "total_memory_delta": sum(worker_memory_deltas),
        "memory_deltas": worker_memory_deltas
    }}

# Run the concurrent test
initial_rss = glibc_arena_poc.get_rss_mib()
start_time = time.time()

worker_results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=PYTHON_THREADS) as executor:
    futures = [executor.submit(python_worker, i) for i in range(PYTHON_THREADS)]
    
    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            worker_results.append(result)
        except Exception as e:
            pass  # Continue on errors

end_time = time.time()
final_rss = glibc_arena_poc.get_rss_mib()

# Calculate metrics
total_memory_delta = final_rss - initial_rss
total_duration = end_time - start_time
total_worker_reported = sum(r["total_memory_delta"] for r in worker_results)
memory_amplification = total_memory_delta / total_worker_reported if total_worker_reported > 0 else 0

# Fix parallelism calculation
if worker_results:
    avg_worker_duration = sum(r.get("duration", 0) for r in worker_results) / len(worker_results)
    theoretical_sequential = avg_worker_duration * PYTHON_THREADS
    parallelism_factor = theoretical_sequential / total_duration if total_duration > 0 else 1
else:
    parallelism_factor = 1

result = {{
    "build_name": "{build_name}",
    "free_threaded": free_threaded,
    "config": {{
        "python_threads": PYTHON_THREADS,
        "rust_threads_per_call": RUST_THREADS_PER_CALL,
        "iterations_per_thread": ITERATIONS_PER_THREAD,
        "total_theoretical_rust_threads": PYTHON_THREADS * RUST_THREADS_PER_CALL * ITERATIONS_PER_THREAD
    }},
    "memory": {{
        "initial_rss_mib": initial_rss,
        "final_rss_mib": final_rss,
        "total_memory_delta_mib": total_memory_delta,
        "worker_reported_memory_mib": total_worker_reported,
        "memory_amplification": memory_amplification
    }},
    "timing": {{
        "total_duration_sec": total_duration,
        "parallelism_factor": parallelism_factor
    }},
    "workers_completed": len(worker_results)
}}

print(json.dumps(result, indent=2))
"""
        
        try:
            env = self.setup_environment(build_name)
            result = self.run_command(
                [str(python_path), "-c", test_code],
                env=env,
                check=True,
                verbose=False
            )
            
            import json
            test_result = json.loads(result.stdout)
            
            memory_delta = test_result["memory"]["total_memory_delta_mib"]
            parallelism = test_result["timing"]["parallelism_factor"]
            
            self.log(f"✅ Arena risk test completed for {build_name}: "
                    f"{memory_delta:.2f} MiB delta, {parallelism:.1f}x parallelism")
            return test_result
            
        except Exception as e:
            self.log(f"❌ Arena risk test failed for {build_name}: {e}", "ERROR")
            return None
    
    def compare_gil_vs_nogil(self, thread_count: int = 1000) -> dict:
        """Compare GIL vs no-GIL performance for the same Python version."""
        comparison = {}
        
        # Group builds by version
        versions = {}
        for build in self.get_available_builds():
            version = build.split('-')[0]  # e.g., "3.13.5"
            if version not in versions:
                versions[version] = {}
            gil_status = "nogil" if "nogil" in build else "gil"
            versions[version][gil_status] = build
        
        # Compare each version that has both GIL and no-GIL builds
        for version, builds in versions.items():
            if "gil" in builds and "nogil" in builds:
                self.log(f"Comparing Python {version}: GIL vs no-GIL")
                
                gil_result = self.test_specific_build(builds["gil"], thread_count)
                nogil_result = self.test_specific_build(builds["nogil"], thread_count)
                
                if gil_result and nogil_result:
                    comparison[version] = {
                        "gil": gil_result,
                        "nogil": nogil_result,
                        "memory_delta_difference": nogil_result["memory_delta_mib"] - gil_result["memory_delta_mib"]
                    }
        
        return comparison
