#!/usr/bin/env python3
"""
Arena Matrix Plotter - Systematic testing and visualization script.

This script runs arena leakage risk tests across a matrix of:
- X-axis: Python thread counts (N)
- Y-axis: Rust thread counts (M)

Then generates GnuPlot-style visualizations showing the O(N*M) complexity
and risk amplification differences between GIL and no-GIL Python.
"""

import os
import sys
import json
import time
import itertools
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import our arena testing framework
from arena_tester import ArenaTester

class ArenaMatrixPlotter:
    """Systematic arena risk testing and visualization."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.tester = ArenaTester(base_dir)
        self.results_dir = self.base_dir / "matrix_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test matrix configuration
        self.python_thread_counts = [2, 4, 6, 8, 12, 16, 20, 24]  # X-axis
        self.rust_thread_counts = [10, 25, 50, 75, 100, 150, 200]  # Y-axis
        
        # Available Python builds for comparison
        self.builds = ["3.13.5-gil", "3.13.5-nogil", "3.14.0rc1-gil", "3.14.0rc1-nogil"]
        
    def run_single_test(self, build_name: str, python_threads: int, rust_threads: int) -> Optional[Dict]:
        """Run a single arena risk test for specific parameters."""
        print(f"  Testing {build_name}: P={python_threads}, R={rust_threads} (O={python_threads*rust_threads})")
        
        python_path = self.tester.get_python_executable(build_name)
        if not python_path:
            print(f"    ❌ Python not found for {build_name}")
            return None
        
        # Check if module is installed
        module_info = self.tester.get_module_info(build_name)
        if not module_info or not module_info.get("installed"):
            print(f"    ❌ Module not installed for {build_name}")
            return None
        
        # Reduced iterations for matrix testing to speed up data collection
        test_code = f"""
import glibc_arena_poc
import sys
import time
import concurrent.futures
import json

# Test configuration
PYTHON_THREADS = {python_threads}
RUST_THREADS_PER_CALL = {rust_threads}
ITERATIONS_PER_THREAD = 3  # Reduced for matrix testing

free_threaded = hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled()

def python_worker(worker_id):
    worker_memory_deltas = []
    start_time = time.time()
    
    for i in range(ITERATIONS_PER_THREAD):
        # Each call spawns RUST_THREADS_PER_CALL Rust threads
        initial, final = glibc_arena_poc.run_arena_test(RUST_THREADS_PER_CALL)
        worker_memory_deltas.append(final - initial)
        time.sleep(0.002)  # Very small delay for matrix testing
    
    end_time = time.time()
    return {{
        "worker_id": worker_id,
        "total_memory_delta": sum(worker_memory_deltas),
        "memory_deltas": worker_memory_deltas,
        "duration": end_time - start_time
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

# Parallelism calculation
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
            env = self.tester.setup_environment(build_name)
            result = self.tester.run_command(
                [str(python_path), "-c", test_code],
                env=env,
                check=True,
                verbose=False
            )
            
            test_result = json.loads(result.stdout)
            
            # Add matrix coordinates
            test_result["matrix_coords"] = {
                "python_threads": python_threads,
                "rust_threads": rust_threads,
                "complexity": python_threads * rust_threads
            }
            
            memory_delta = test_result["memory"]["total_memory_delta_mib"]
            amplification = test_result["memory"]["memory_amplification"]
            
            print(f"    ✅ {memory_delta:.2f} MiB (amp: {amplification:.1f}x)")
            return test_result
            
        except Exception as e:
            print(f"    ❌ Test failed: {e}")
            return None
    
    def run_matrix_tests(self) -> Dict:
        """Run the complete matrix of tests for all builds."""
        print("🔬 Running Arena Risk Matrix Tests")
        print("=" * 60)
        print(f"Python threads: {self.python_thread_counts}")
        print(f"Rust threads: {self.rust_thread_counts}")
        print(f"Total test points: {len(self.python_thread_counts) * len(self.rust_thread_counts)}")
        print(f"Builds: {self.builds}")
        print()
        
        all_results = {}
        total_tests = len(self.builds) * len(self.python_thread_counts) * len(self.rust_thread_counts)
        current_test = 0
        
        for build_name in self.builds:
            if build_name not in self.tester.get_available_builds():
                print(f"⚠️ Skipping {build_name} - not available")
                continue
                
            print(f"\n📊 Testing {build_name}")
            all_results[build_name] = {}
            
            for python_threads in self.python_thread_counts:
                all_results[build_name][python_threads] = {}
                
                for rust_threads in self.rust_thread_counts:
                    current_test += 1
                    print(f"[{current_test}/{total_tests}]", end=" ")
                    
                    result = self.run_single_test(build_name, python_threads, rust_threads)
                    if result:
                        all_results[build_name][python_threads][rust_threads] = result
                    else:
                        all_results[build_name][python_threads][rust_threads] = None
                    
                    # Small delay to prevent system overload
                    time.sleep(0.1)
        
        # Save raw results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"matrix_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n📊 Matrix test results saved to: {results_file}")
        return all_results
    
    def create_risk_matrix_plot(self, results: Dict, save_path: Optional[Path] = None):
        """Create GnuPlot-style heatmap visualization."""
        print("\n🎨 Creating Arena Risk Matrix Visualization...")
        
        # Set GnuPlot-like style
        plt.style.use('seaborn-v0_8-darkgrid')  # Closest to GnuPlot grid style
        
        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Arena Leakage Risk Matrix: GIL vs no-GIL\n(X: Python Threads, Y: Rust Threads)', 
                    fontsize=16, fontweight='bold')
        
        build_configs = [
            ("3.13.5-gil", "Python 3.13.5 with GIL"),
            ("3.13.5-nogil", "Python 3.13.5 no-GIL"), 
            ("3.14.0rc1-gil", "Python 3.14.0rc1 with GIL"),
            ("3.14.0rc1-nogil", "Python 3.14.0rc1 no-GIL")
        ]
        
        for idx, (build_name, title) in enumerate(build_configs):
            if build_name not in results:
                continue
                
            ax = axes[idx // 2, idx % 2]
            
            # Prepare data matrix
            matrix_data = np.zeros((len(self.rust_thread_counts), len(self.python_thread_counts)))
            
            for i, rust_threads in enumerate(self.rust_thread_counts):
                for j, python_threads in enumerate(self.python_thread_counts):
                    if (python_threads in results[build_name] and 
                        rust_threads in results[build_name][python_threads] and
                        results[build_name][python_threads][rust_threads] is not None):
                        
                        result = results[build_name][python_threads][rust_threads]
                        # Use memory amplification as the metric
                        value = result["memory"]["memory_amplification"]
                        matrix_data[i, j] = value
                    else:
                        matrix_data[i, j] = np.nan
            
            # Create heatmap with GnuPlot-style colormap
            im = ax.imshow(matrix_data, cmap='hot', aspect='auto', interpolation='bilinear')
            
            # Set ticks and labels
            ax.set_xticks(range(len(self.python_thread_counts)))
            ax.set_xticklabels(self.python_thread_counts)
            ax.set_yticks(range(len(self.rust_thread_counts)))
            ax.set_yticklabels(self.rust_thread_counts)
            
            ax.set_xlabel('Python Threads (N)', fontweight='bold')
            ax.set_ylabel('Rust Threads (M)', fontweight='bold')
            ax.set_title(f'{title}\nMemory Amplification Factor', fontweight='bold')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Memory Amplification (x)', rotation=270, labelpad=20)
            
            # Add text annotations for values
            for i in range(len(self.rust_thread_counts)):
                for j in range(len(self.python_thread_counts)):
                    if not np.isnan(matrix_data[i, j]):
                        text = f'{matrix_data[i, j]:.1f}'
                        ax.text(j, i, text, ha="center", va="center", 
                               color="white" if matrix_data[i, j] > np.nanmean(matrix_data) else "black",
                               fontsize=8, fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.results_dir / f"arena_risk_matrix_{timestamp}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Matrix visualization saved to: {save_path}")
        
        # Also save as SVG for vector graphics
        svg_path = save_path.with_suffix('.svg')
        plt.savefig(svg_path, format='svg', bbox_inches='tight')
        print(f"✅ Vector version saved to: {svg_path}")
        
        plt.show()
        
        return save_path
    
    def create_3d_surface_plot(self, results: Dict, save_path: Optional[Path] = None):
        """Create 3D surface plot showing O(N*M) complexity."""
        print("\n🎨 Creating 3D Surface Plot...")
        
        fig = plt.figure(figsize=(16, 12))
        
        build_configs = [
            ("3.13.5-gil", "Python 3.13.5 with GIL"),
            ("3.13.5-nogil", "Python 3.13.5 no-GIL"), 
            ("3.14.0rc1-gil", "Python 3.14.0rc1 with GIL"),
            ("3.14.0rc1-nogil", "Python 3.14.0rc1 no-GIL")
        ]
        
        for idx, (build_name, title) in enumerate(build_configs):
            if build_name not in results:
                continue
                
            ax = fig.add_subplot(2, 2, idx + 1, projection='3d')
            
            # Prepare data
            X, Y, Z = [], [], []
            
            for python_threads in self.python_thread_counts:
                for rust_threads in self.rust_thread_counts:
                    if (python_threads in results[build_name] and 
                        rust_threads in results[build_name][python_threads] and
                        results[build_name][python_threads][rust_threads] is not None):
                        
                        result = results[build_name][python_threads][rust_threads]
                        X.append(python_threads)
                        Y.append(rust_threads)
                        Z.append(result["memory"]["memory_amplification"])
            
            if X:  # Only plot if we have data
                # Create surface plot
                ax.scatter(X, Y, Z, c=Z, cmap='hot', s=60, alpha=0.8)
                
                ax.set_xlabel('Python Threads (N)', fontweight='bold')
                ax.set_ylabel('Rust Threads (M)', fontweight='bold')
                ax.set_zlabel('Memory Amplification', fontweight='bold')
                ax.set_title(title, fontweight='bold')
        
        plt.suptitle('3D Arena Risk Analysis: Memory Amplification vs Thread Counts', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = self.results_dir / f"arena_risk_3d_{timestamp}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ 3D visualization saved to: {save_path}")
        
        plt.show()
        
        return save_path
    
    def generate_summary_report(self, results: Dict) -> Dict:
        """Generate summary statistics from the matrix results."""
        print("\n📊 Generating Summary Report...")
        
        summary = {
            "test_matrix": {
                "python_threads": self.python_thread_counts,
                "rust_threads": self.rust_thread_counts,
                "total_test_points": len(self.python_thread_counts) * len(self.rust_thread_counts)
            },
            "build_summaries": {}
        }
        
        for build_name in results:
            print(f"\n📈 {build_name} Summary:")
            
            memory_deltas = []
            amplifications = []
            complexities = []
            
            for python_threads in self.python_thread_counts:
                if python_threads in results[build_name]:
                    for rust_threads in self.rust_thread_counts:
                        if (rust_threads in results[build_name][python_threads] and
                            results[build_name][python_threads][rust_threads] is not None):
                            
                            result = results[build_name][python_threads][rust_threads]
                            memory_deltas.append(result["memory"]["total_memory_delta_mib"])
                            amplifications.append(result["memory"]["memory_amplification"])
                            complexities.append(python_threads * rust_threads)
            
            if memory_deltas:
                build_summary = {
                    "test_points": len(memory_deltas),
                    "memory_delta": {
                        "min": min(memory_deltas),
                        "max": max(memory_deltas),
                        "mean": np.mean(memory_deltas),
                        "std": np.std(memory_deltas)
                    },
                    "amplification": {
                        "min": min(amplifications),
                        "max": max(amplifications),
                        "mean": np.mean(amplifications),
                        "std": np.std(amplifications)
                    },
                    "complexity_range": {
                        "min": min(complexities),
                        "max": max(complexities)
                    }
                }
                
                summary["build_summaries"][build_name] = build_summary
                
                print(f"  Test points: {build_summary['test_points']}")
                print(f"  Memory delta: {build_summary['memory_delta']['mean']:.2f} ± {build_summary['memory_delta']['std']:.2f} MiB")
                print(f"  Amplification: {build_summary['amplification']['mean']:.2f} ± {build_summary['amplification']['std']:.2f}x")
                print(f"  Complexity range: {build_summary['complexity_range']['min']} - {build_summary['complexity_range']['max']}")
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.results_dir / f"matrix_summary_{timestamp}.json"
        
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Summary report saved to: {summary_file}")
        return summary


def main():
    """Main entry point for matrix testing and plotting."""
    print("🔬 Arena Risk Matrix Testing and Visualization")
    print("=" * 60)
    
    plotter = ArenaMatrixPlotter(Path(__file__).parent)
    
    # Check available builds
    available_builds = plotter.tester.get_available_builds()
    print(f"Available builds: {available_builds}")
    
    if not available_builds:
        print("❌ No Python builds available. Run 'python arena_test.py build' first.")
        return
    
    try:
        # Run matrix tests
        results = plotter.run_matrix_tests()
        
        # Generate visualizations
        plotter.create_risk_matrix_plot(results)
        plotter.create_3d_surface_plot(results)
        
        # Generate summary report
        plotter.generate_summary_report(results)
        
        print("\n🎉 Matrix testing and visualization complete!")
        print(f"📁 Results saved in: {plotter.results_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Matrix testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during matrix testing: {e}")


if __name__ == "__main__":
    main()
