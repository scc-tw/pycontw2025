#!/usr/bin/env python3
"""
Python Matrix Benchmark Runner - PyCon 2025 FFI Analysis

Executes FFI benchmarks across the full Python version matrix:
- Python 3.13.5 & 3.14.0rc1
- GIL enabled & disabled variants
- All FFI methods (ctypes, cffi, pybind11, pyo3)

Produces structured results for deep analysis of:
- GIL vs No-GIL performance impact
- Python version performance differences  
- FFI method effectiveness across configurations
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the benchmark-ffi root to Python path
benchmark_root = Path(__file__).parent.parent
sys.path.insert(0, str(benchmark_root))

from framework.python_matrix import create_python_matrix_detector, create_python_matrix_executor
from framework.timer import BenchmarkTimer, format_nanoseconds
from framework.statistics import create_statistical_analyzer


class MatrixBenchmarkRunner:
    """Advanced matrix benchmark runner with statistical analysis."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize matrix runner."""
        self.output_dir = Path(output_dir) if output_dir else Path("results")
        self.output_dir.mkdir(exist_ok=True)
        
        self.detector = create_python_matrix_detector()
        self.builds = []
        self.results = {}
        
    def setup_matrix(self) -> bool:
        """Detect and validate Python matrix."""
        print("🔧 Setting up Python Version Matrix")
        print("=" * 50)
        
        # Detect available builds
        self.builds = self.detector.detect_python_builds()
        
        if not self.builds:
            print("❌ No Python builds detected!")
            print("📋 Expected builds:")
            print("   - ./cpython3.13.5-gil/bin/python3")
            print("   - ./cpython3.13.5-nogil/bin/python3") 
            print("   - ./cpython3.14.0rc1-gil/bin/python3")
            print("   - ./cpython3.14.0rc1-nogil/bin/python3")
            return False
        
        # Show matrix status
        summary = self.detector.get_matrix_summary()
        print(f"\n📊 Matrix Status:")
        print(f"   Detected builds: {summary['total_builds']}/4")
        print(f"   Matrix complete: {'✅' if summary['matrix_complete'] else '❌'}")
        
        if summary['missing_variants']:
            print(f"   Missing: {', '.join(summary['missing_variants'])}")
        
        print(f"\n📋 Available builds:")
        for build in self.builds:
            gil_status = "GIL" if build.gil_enabled else "No-GIL"
            print(f"   ✅ Python {build.version} ({gil_status}) at {build.executable_path}")
        
        return len(self.builds) >= 2  # Need at least 2 builds for comparison
    
    def run_basic_ffi_benchmarks(self) -> Dict[str, Any]:
        """Run basic FFI benchmarks across the matrix."""
        print(f"\n🚀 Running FFI Benchmark Matrix")
        print("=" * 60)
        
        # Create executor
        executor = create_python_matrix_executor(self.builds)
        
        # Run the basic benchmark script across all Python builds
        matrix_results = executor.run_benchmark_matrix(
            "scripts/run_all_benchmarks.py",
            timeout=300  # 5 minutes per build
        )
        
        # Process and enhance results
        enhanced_results = self._process_matrix_results(matrix_results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"matrix_benchmark_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(enhanced_results, f, indent=2)
        
        print(f"\n💾 Matrix results saved: {results_file}")
        
        return enhanced_results
    
    def _process_matrix_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance raw matrix results with analysis."""
        print("\n📊 Processing matrix results...")
        
        enhanced = raw_results.copy()
        enhanced["analysis"] = {}
        
        # Extract performance data from stdout parsing
        performance_data = self._extract_performance_data(raw_results)
        enhanced["performance_matrix"] = performance_data
        
        if performance_data:
            # Analyze GIL impact
            gil_analysis = self._analyze_gil_impact(performance_data)
            enhanced["analysis"]["gil_impact"] = gil_analysis
            
            # Analyze version differences
            version_analysis = self._analyze_version_differences(performance_data)
            enhanced["analysis"]["version_differences"] = version_analysis
            
            # Analyze FFI method rankings
            ffi_analysis = self._analyze_ffi_method_rankings(performance_data)
            enhanced["analysis"]["ffi_method_rankings"] = ffi_analysis
        
        return enhanced
    
    def _extract_performance_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics from benchmark stdout."""
        performance_data = {}
        
        for version, version_data in results.get("results", {}).items():
            performance_data[version] = {}
            
            for gil_variant, run_data in version_data.items():
                benchmark_result = run_data.get("benchmark_result", {})
                
                if not benchmark_result.get("success", False):
                    continue
                
                stdout = benchmark_result.get("stdout", "")
                
                # Parse performance results from stdout
                ffi_results = self._parse_ffi_results(stdout)
                
                performance_data[version][gil_variant] = {
                    "python_executable": run_data.get("python_executable", ""),
                    "success": True,
                    "ffi_results": ffi_results,
                    "raw_output": stdout
                }
        
        return performance_data
    
    def _parse_ffi_results(self, stdout: str) -> Dict[str, Dict[str, Any]]:
        """Parse FFI benchmark results from stdout."""
        ffi_results = {}
        lines = stdout.split('\n')
        
        # Look for performance comparison section
        in_comparison = False
        for line in lines:
            line = line.strip()
            
            if "Performance Comparison:" in line:
                in_comparison = True
                continue
            
            if in_comparison and ":" in line and "ns" in line:
                # Parse lines like "ctypes: 139.5 ns (1.57x)"
                try:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        method_name = parts[0].strip()
                        perf_part = parts[1].strip()
                        
                        # Extract timing (e.g., "139.5 ns")
                        if "ns" in perf_part:
                            ns_part = perf_part.split("ns")[0].strip()
                            try:
                                timing_ns = float(ns_part)
                                
                                # Extract speedup factor if present
                                speedup = 1.0
                                if "(" in perf_part and "x)" in perf_part:
                                    speedup_part = perf_part.split("(")[1].split("x)")[0]
                                    speedup = float(speedup_part)
                                
                                ffi_results[method_name] = {
                                    "median_ns": timing_ns,
                                    "speedup_factor": speedup
                                }
                            except ValueError:
                                continue
                except Exception:
                    continue
        
        return ffi_results
    
    def _analyze_gil_impact(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GIL vs No-GIL performance impact."""
        gil_analysis = {
            "summary": "GIL Impact Analysis Across Python Versions",
            "methodology": "Compare GIL vs No-GIL performance for each version/FFI combination",
            "results": {}
        }
        
        for version in performance_data:
            if "gil" in performance_data[version] and "nogil" in performance_data[version]:
                gil_data = performance_data[version]["gil"]["ffi_results"]
                nogil_data = performance_data[version]["nogil"]["ffi_results"]
                
                version_analysis = {}
                
                # Compare each FFI method
                for ffi_method in set(gil_data.keys()) | set(nogil_data.keys()):
                    if ffi_method in gil_data and ffi_method in nogil_data:
                        gil_time = gil_data[ffi_method]["median_ns"]
                        nogil_time = nogil_data[ffi_method]["median_ns"]
                        
                        # Calculate improvement (negative = slower without GIL)
                        improvement = (gil_time - nogil_time) / gil_time * 100
                        speedup = gil_time / nogil_time
                        
                        version_analysis[ffi_method] = {
                            "gil_time_ns": gil_time,
                            "nogil_time_ns": nogil_time,
                            "improvement_percent": improvement,
                            "nogil_speedup": speedup,
                            "interpretation": self._interpret_gil_impact(improvement)
                        }
                
                gil_analysis["results"][version] = version_analysis
        
        return gil_analysis
    
    def _interpret_gil_impact(self, improvement_percent: float) -> str:
        """Interpret GIL impact percentage."""
        if improvement_percent > 10:
            return "Significant improvement without GIL"
        elif improvement_percent > 2:
            return "Moderate improvement without GIL"
        elif improvement_percent > -2:
            return "Negligible GIL impact"
        elif improvement_percent > -10:
            return "Moderate regression without GIL"
        else:
            return "Significant regression without GIL"
    
    def _analyze_version_differences(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance differences between Python versions."""
        version_analysis = {
            "summary": "Python Version Performance Comparison",
            "methodology": "Compare 3.13.5 vs 3.14.0rc1 for each GIL/FFI combination"
        }
        
        versions = list(performance_data.keys())
        if len(versions) >= 2:
            version_comparisons = {}
            
            for gil_variant in ["gil", "nogil"]:
                if all(gil_variant in performance_data[v] for v in versions):
                    comparison = {}
                    
                    for ffi_method in set().union(*[
                        performance_data[v][gil_variant]["ffi_results"].keys() 
                        for v in versions
                    ]):
                        method_comparison = {}
                        
                        for version in versions:
                            if ffi_method in performance_data[version][gil_variant]["ffi_results"]:
                                timing = performance_data[version][gil_variant]["ffi_results"][ffi_method]["median_ns"]
                                method_comparison[version] = timing
                        
                        if len(method_comparison) >= 2:
                            # Find fastest version
                            fastest_version = min(method_comparison, key=method_comparison.get)
                            fastest_time = method_comparison[fastest_version]
                            
                            method_comparison["fastest_version"] = fastest_version
                            method_comparison["performance_ratios"] = {
                                v: method_comparison[v] / fastest_time 
                                for v in method_comparison if v != "fastest_version"
                            }
                        
                        comparison[ffi_method] = method_comparison
                    
                    version_comparisons[gil_variant] = comparison
            
            version_analysis["comparisons"] = version_comparisons
        
        return version_analysis
    
    def _analyze_ffi_method_rankings(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FFI method rankings across all configurations."""
        rankings_analysis = {
            "summary": "FFI Method Performance Rankings",
            "methodology": "Rank FFI methods by performance in each Python configuration"
        }
        
        configuration_rankings = {}
        
        for version in performance_data:
            for gil_variant in performance_data[version]:
                config_name = f"{version}-{gil_variant}"
                ffi_results = performance_data[version][gil_variant]["ffi_results"]
                
                if ffi_results:
                    # Sort by median timing (lower is better)
                    sorted_methods = sorted(
                        ffi_results.items(),
                        key=lambda x: x[1]["median_ns"]
                    )
                    
                    rankings = []
                    for rank, (method, data) in enumerate(sorted_methods, 1):
                        fastest_time = sorted_methods[0][1]["median_ns"]
                        relative_performance = data["median_ns"] / fastest_time
                        
                        rankings.append({
                            "rank": rank,
                            "method": method,
                            "median_ns": data["median_ns"],
                            "relative_performance": relative_performance,
                            "performance_rating": self._rate_performance(relative_performance)
                        })
                    
                    configuration_rankings[config_name] = rankings
        
        rankings_analysis["configuration_rankings"] = configuration_rankings
        
        # Overall method consistency analysis
        rankings_analysis["consistency_analysis"] = self._analyze_ranking_consistency(configuration_rankings)
        
        return rankings_analysis
    
    def _rate_performance(self, relative_performance: float) -> str:
        """Rate performance relative to fastest method."""
        if relative_performance <= 1.1:
            return "Excellent"
        elif relative_performance <= 1.3:
            return "Good"
        elif relative_performance <= 1.6:
            return "Fair"
        else:
            return "Poor"
    
    def _analyze_ranking_consistency(self, rankings: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze how consistent FFI method rankings are across configurations."""
        method_ranks = {}
        
        for config, ranking in rankings.items():
            for entry in ranking:
                method = entry["method"]
                if method not in method_ranks:
                    method_ranks[method] = []
                method_ranks[method].append(entry["rank"])
        
        consistency_scores = {}
        for method, ranks in method_ranks.items():
            if len(ranks) > 1:
                rank_variance = max(ranks) - min(ranks)
                avg_rank = sum(ranks) / len(ranks)
                consistency_scores[method] = {
                    "average_rank": avg_rank,
                    "rank_variance": rank_variance,
                    "consistency": "High" if rank_variance <= 1 else "Medium" if rank_variance <= 2 else "Low"
                }
        
        return consistency_scores
    
    def print_matrix_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of matrix results."""
        print(f"\n📊 PYTHON MATRIX BENCHMARK SUMMARY")
        print("=" * 60)
        
        execution = results.get("execution_summary", {})
        print(f"Execution Success Rate: {execution.get('success_rate', 'N/A')}")
        print(f"Completion Percentage: {execution.get('completion_percentage', 0):.1f}%")
        
        # GIL Impact Summary
        gil_analysis = results.get("analysis", {}).get("gil_impact", {})
        if gil_analysis.get("results"):
            print(f"\n🎯 GIL IMPACT HIGHLIGHTS:")
            
            for version, version_data in gil_analysis["results"].items():
                print(f"\n   Python {version}:")
                for ffi_method, impact_data in version_data.items():
                    improvement = impact_data["improvement_percent"]
                    interpretation = impact_data["interpretation"]
                    print(f"     {ffi_method:>8}: {improvement:+.1f}% ({interpretation})")
        
        # FFI Rankings Summary
        rankings = results.get("analysis", {}).get("ffi_method_rankings", {})
        if rankings.get("configuration_rankings"):
            print(f"\n🏆 FFI METHOD RANKINGS:")
            
            for config, ranking in rankings["configuration_rankings"].items():
                print(f"\n   {config}:")
                for entry in ranking:
                    method = entry["method"]
                    timing = entry["median_ns"]
                    relative = entry["relative_performance"]
                    rating = entry["performance_rating"]
                    print(f"     {entry['rank']}. {method:>8}: {timing:>7.1f}ns ({relative:.2f}x, {rating})")
        
        print(f"\n💾 Detailed results available in: {self.output_dir}")


def main():
    """Main entry point for matrix benchmark runner."""
    print("🧪 Python Matrix FFI Benchmark Runner - PyCon 2025")
    print("=" * 70)
    print("📋 Analyzing FFI performance across Python version matrix:")
    print("   • Python 3.13.5 vs 3.14.0rc1")
    print("   • GIL enabled vs disabled")
    print("   • All FFI methods (ctypes, cffi, pybind11, pyo3)")
    
    runner = MatrixBenchmarkRunner()
    
    # Setup matrix
    if not runner.setup_matrix():
        print("\n❌ Matrix setup failed! Cannot proceed with benchmarks.")
        print("📋 Ensure Python builds are available at expected paths.")
        return 1
    
    try:
        # Run matrix benchmarks
        results = runner.run_basic_ffi_benchmarks()
        
        # Print summary
        runner.print_matrix_summary(results)
        
        print(f"\n✅ Matrix benchmark completed successfully!")
        print(f"🎯 Results provide comprehensive Python version × GIL × FFI analysis")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 Matrix benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())