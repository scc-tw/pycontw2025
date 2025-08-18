#!/usr/bin/env python3
"""
Matrix Benchmark Results Search Tool

Provides structured search and analysis capabilities for Python matrix benchmark results.
Enables deep analysis of GIL impact, version differences, and FFI method performance
across different Python configurations.
"""

import os
import sys
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import argparse


class MatrixResultsSearcher:
    """Advanced search tool for matrix benchmark results."""
    
    def __init__(self, results_dir: str = "results"):
        """Initialize searcher with results directory."""
        self.results_dir = Path(results_dir)
        if not self.results_dir.exists():
            raise FileNotFoundError(f"Results directory not found: {results_dir}")
        
        self.results_files = self._discover_results_files()
        
    def _discover_results_files(self) -> List[Path]:
        """Discover all matrix benchmark result files."""
        patterns = [
            "matrix_benchmark_results_*.json",
            "matrix_results_*.json", 
            "*matrix*.json"
        ]
        
        files = []
        for pattern in patterns:
            files.extend(self.results_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return files
    
    def list_available_results(self) -> List[Dict[str, Any]]:
        """List all available result files with metadata."""
        results_info = []
        
        for file_path in self.results_files:
            try:
                with open(file_path) as f:
                    data = json.load(f)
                
                # Extract metadata
                info = {
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "timestamp": data.get("timestamp", "unknown"),
                    "total_builds": data.get("matrix_config", {}).get("total_builds", 0),
                    "success_rate": data.get("execution_summary", {}).get("success_rate", "unknown"),
                    "file_size_kb": file_path.stat().st_size / 1024,
                    "has_analysis": "analysis" in data,
                    "has_performance_matrix": "performance_matrix" in data
                }
                
                results_info.append(info)
                
            except Exception as e:
                print(f"⚠️ Could not read {file_path}: {e}")
        
        return results_info
    
    def load_latest_results(self) -> Optional[Dict[str, Any]]:
        """Load the most recent matrix results."""
        if not self.results_files:
            return None
        
        latest_file = self.results_files[0]
        try:
            with open(latest_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Could not load {latest_file}: {e}")
            return None
    
    def search_gil_impact(self, results: Dict[str, Any] = None, 
                         ffi_method: str = None,
                         python_version: str = None) -> Dict[str, Any]:
        """Search for GIL impact analysis results."""
        if results is None:
            results = self.load_latest_results()
        
        if not results:
            return {"error": "No results available"}
        
        gil_analysis = results.get("analysis", {}).get("gil_impact", {})
        
        if not gil_analysis.get("results"):
            return {"error": "No GIL impact analysis found"}
        
        # Filter results based on criteria
        filtered_results = {}
        
        for version, version_data in gil_analysis["results"].items():
            # Filter by Python version if specified
            if python_version and python_version not in version:
                continue
            
            filtered_version_data = {}
            
            for method, impact_data in version_data.items():
                # Filter by FFI method if specified
                if ffi_method and ffi_method.lower() != method.lower():
                    continue
                
                filtered_version_data[method] = impact_data
            
            if filtered_version_data:
                filtered_results[version] = filtered_version_data
        
        return {
            "methodology": gil_analysis.get("methodology", ""),
            "results": filtered_results,
            "search_criteria": {
                "ffi_method": ffi_method,
                "python_version": python_version
            }
        }
    
    def search_version_differences(self, results: Dict[str, Any] = None,
                                  gil_variant: str = None,
                                  ffi_method: str = None) -> Dict[str, Any]:
        """Search for Python version performance differences."""
        if results is None:
            results = self.load_latest_results()
        
        if not results:
            return {"error": "No results available"}
        
        version_analysis = results.get("analysis", {}).get("version_differences", {})
        comparisons = version_analysis.get("comparisons", {})
        
        if not comparisons:
            return {"error": "No version comparison analysis found"}
        
        # Filter by GIL variant
        filtered_comparisons = {}
        
        for variant, variant_data in comparisons.items():
            if gil_variant and gil_variant.lower() not in variant.lower():
                continue
            
            # Filter by FFI method if specified
            filtered_variant_data = {}
            
            for method, method_data in variant_data.items():
                if ffi_method and ffi_method.lower() != method.lower():
                    continue
                
                filtered_variant_data[method] = method_data
            
            if filtered_variant_data:
                filtered_comparisons[variant] = filtered_variant_data
        
        return {
            "methodology": version_analysis.get("methodology", ""),
            "comparisons": filtered_comparisons,
            "search_criteria": {
                "gil_variant": gil_variant,
                "ffi_method": ffi_method
            }
        }
    
    def search_ffi_rankings(self, results: Dict[str, Any] = None,
                           configuration: str = None) -> Dict[str, Any]:
        """Search for FFI method rankings across configurations."""
        if results is None:
            results = self.load_latest_results()
        
        if not results:
            return {"error": "No results available"}
        
        rankings_analysis = results.get("analysis", {}).get("ffi_method_rankings", {})
        config_rankings = rankings_analysis.get("configuration_rankings", {})
        
        if not config_rankings:
            return {"error": "No FFI rankings analysis found"}
        
        # Filter by configuration if specified
        if configuration:
            filtered_rankings = {
                k: v for k, v in config_rankings.items()
                if configuration.lower() in k.lower()
            }
        else:
            filtered_rankings = config_rankings
        
        return {
            "methodology": rankings_analysis.get("methodology", ""),
            "configuration_rankings": filtered_rankings,
            "consistency_analysis": rankings_analysis.get("consistency_analysis", {}),
            "search_criteria": {
                "configuration": configuration
            }
        }
    
    def search_raw_performance_data(self, results: Dict[str, Any] = None,
                                   python_version: str = None,
                                   gil_variant: str = None,
                                   ffi_method: str = None) -> Dict[str, Any]:
        """Search raw performance data with filters."""
        if results is None:
            results = self.load_latest_results()
        
        if not results:
            return {"error": "No results available"}
        
        performance_matrix = results.get("performance_matrix", {})
        
        if not performance_matrix:
            return {"error": "No performance matrix found"}
        
        # Apply filters
        filtered_data = {}
        
        for version, version_data in performance_matrix.items():
            # Filter by Python version
            if python_version and python_version not in version:
                continue
            
            filtered_version_data = {}
            
            for variant, variant_data in version_data.items():
                # Filter by GIL variant
                if gil_variant and gil_variant.lower() != variant.lower():
                    continue
                
                if "ffi_results" in variant_data:
                    ffi_results = variant_data["ffi_results"]
                    
                    # Filter by FFI method
                    if ffi_method:
                        filtered_ffi_results = {
                            k: v for k, v in ffi_results.items()
                            if ffi_method.lower() in k.lower()
                        }
                    else:
                        filtered_ffi_results = ffi_results
                    
                    if filtered_ffi_results:
                        filtered_variant_data = variant_data.copy()
                        filtered_variant_data["ffi_results"] = filtered_ffi_results
                        filtered_version_data[variant] = filtered_variant_data
            
            if filtered_version_data:
                filtered_data[version] = filtered_version_data
        
        return {
            "performance_data": filtered_data,
            "search_criteria": {
                "python_version": python_version,
                "gil_variant": gil_variant,
                "ffi_method": ffi_method
            }
        }
    
    def generate_comparison_report(self, results: Dict[str, Any] = None) -> str:
        """Generate a comprehensive comparison report."""
        if results is None:
            results = self.load_latest_results()
        
        if not results:
            return "❌ No results available for report generation"
        
        report_lines = []
        report_lines.append("📊 PYTHON MATRIX FFI BENCHMARK REPORT")
        report_lines.append("=" * 60)
        
        # Basic info
        timestamp = results.get("timestamp", "unknown")
        report_lines.append(f"Generated: {timestamp}")
        
        execution = results.get("execution_summary", {})
        success_rate = execution.get("success_rate", "unknown")
        report_lines.append(f"Execution Success Rate: {success_rate}")
        report_lines.append("")
        
        # GIL Impact Analysis
        gil_results = self.search_gil_impact(results)
        if "results" in gil_results:
            report_lines.append("🎯 GIL IMPACT ANALYSIS")
            report_lines.append("-" * 30)
            
            for version, version_data in gil_results["results"].items():
                report_lines.append(f"\nPython {version}:")
                
                for ffi_method, impact_data in version_data.items():
                    improvement = impact_data["improvement_percent"]
                    interpretation = impact_data["interpretation"]
                    nogil_speedup = impact_data["nogil_speedup"]
                    
                    report_lines.append(
                        f"  {ffi_method:>8}: {improvement:+.1f}% "
                        f"({nogil_speedup:.2f}x speedup) - {interpretation}"
                    )
            
            report_lines.append("")
        
        # FFI Method Rankings
        rankings_results = self.search_ffi_rankings(results)
        if "configuration_rankings" in rankings_results:
            report_lines.append("🏆 FFI METHOD RANKINGS BY CONFIGURATION")
            report_lines.append("-" * 40)
            
            for config, ranking in rankings_results["configuration_rankings"].items():
                report_lines.append(f"\n{config}:")
                
                for entry in ranking:
                    method = entry["method"]
                    timing = entry["median_ns"]
                    relative = entry["relative_performance"]
                    rating = entry["performance_rating"]
                    
                    report_lines.append(
                        f"  {entry['rank']}. {method:>8}: {timing:>7.1f}ns "
                        f"({relative:.2f}x relative, {rating})"
                    )
            
            # Consistency analysis
            consistency = rankings_results.get("consistency_analysis", {})
            if consistency:
                report_lines.append("\n📈 RANKING CONSISTENCY ANALYSIS")
                report_lines.append("-" * 35)
                
                for method, analysis in consistency.items():
                    avg_rank = analysis["average_rank"]
                    variance = analysis["rank_variance"]
                    consistency_level = analysis["consistency"]
                    
                    report_lines.append(
                        f"  {method:>8}: Avg rank {avg_rank:.1f}, "
                        f"variance {variance}, consistency {consistency_level}"
                    )
        
        return "\n".join(report_lines)
    
    def export_csv_data(self, results: Dict[str, Any] = None, 
                       output_file: str = None) -> str:
        """Export performance data to CSV format."""
        if results is None:
            results = self.load_latest_results()
        
        if not results:
            return "No results available for CSV export"
        
        performance_matrix = results.get("performance_matrix", {})
        
        if not performance_matrix:
            return "No performance matrix found for CSV export"
        
        # Generate CSV content
        csv_lines = []
        csv_lines.append("python_version,gil_variant,ffi_method,median_ns,speedup_factor")
        
        for version, version_data in performance_matrix.items():
            for gil_variant, variant_data in version_data.items():
                ffi_results = variant_data.get("ffi_results", {})
                
                for ffi_method, performance_data in ffi_results.items():
                    median_ns = performance_data.get("median_ns", 0)
                    speedup = performance_data.get("speedup_factor", 1.0)
                    
                    csv_lines.append(f"{version},{gil_variant},{ffi_method},{median_ns},{speedup}")
        
        csv_content = "\n".join(csv_lines)
        
        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            with open(output_path, 'w') as f:
                f.write(csv_content)
            return f"CSV data exported to: {output_path}"
        
        return csv_content


def main():
    """Command-line interface for matrix results search."""
    parser = argparse.ArgumentParser(description="Search and analyze Python matrix benchmark results")
    parser.add_argument("--results-dir", default="results", help="Results directory path")
    parser.add_argument("--list", action="store_true", help="List available result files")
    parser.add_argument("--gil-impact", action="store_true", help="Show GIL impact analysis")
    parser.add_argument("--version-diff", action="store_true", help="Show version differences")
    parser.add_argument("--ffi-rankings", action="store_true", help="Show FFI method rankings")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive report")
    parser.add_argument("--csv", help="Export to CSV file")
    parser.add_argument("--python-version", help="Filter by Python version (e.g., '3.13.5')")
    parser.add_argument("--gil-variant", help="Filter by GIL variant ('gil' or 'nogil')")
    parser.add_argument("--ffi-method", help="Filter by FFI method")
    parser.add_argument("--config", help="Filter by configuration name")
    
    args = parser.parse_args()
    
    try:
        searcher = MatrixResultsSearcher(args.results_dir)
        
        if args.list:
            print("📁 Available Matrix Benchmark Results:")
            print("-" * 50)
            
            results_info = searcher.list_available_results()
            
            if not results_info:
                print("No matrix benchmark results found.")
                return 1
            
            for info in results_info:
                print(f"📄 {info['file_name']}")
                print(f"   Timestamp: {info['timestamp']}")
                print(f"   Builds: {info['total_builds']}, Success: {info['success_rate']}")
                print(f"   Size: {info['file_size_kb']:.1f} KB")
                print(f"   Analysis: {'✅' if info['has_analysis'] else '❌'}")
                print()
        
        elif args.gil_impact:
            print("🎯 GIL Impact Analysis")
            print("-" * 30)
            
            results = searcher.search_gil_impact(
                ffi_method=args.ffi_method,
                python_version=args.python_version
            )
            
            if "error" in results:
                print(f"❌ {results['error']}")
                return 1
            
            print(json.dumps(results, indent=2))
        
        elif args.version_diff:
            print("📊 Python Version Differences")
            print("-" * 35)
            
            results = searcher.search_version_differences(
                gil_variant=args.gil_variant,
                ffi_method=args.ffi_method
            )
            
            if "error" in results:
                print(f"❌ {results['error']}")
                return 1
            
            print(json.dumps(results, indent=2))
        
        elif args.ffi_rankings:
            print("🏆 FFI Method Rankings")
            print("-" * 25)
            
            results = searcher.search_ffi_rankings(configuration=args.config)
            
            if "error" in results:
                print(f"❌ {results['error']}")
                return 1
            
            print(json.dumps(results, indent=2))
        
        elif args.report:
            report = searcher.generate_comparison_report()
            print(report)
        
        elif args.csv:
            result = searcher.export_csv_data(output_file=args.csv)
            print(result)
        
        else:
            # Default: show summary of latest results
            latest = searcher.load_latest_results()
            
            if not latest:
                print("❌ No matrix benchmark results found.")
                print("📋 Run 'python scripts/run_matrix_benchmarks.py' first.")
                return 1
            
            print("📊 Latest Matrix Benchmark Results Summary")
            print("-" * 50)
            
            execution = latest.get("execution_summary", {})
            print(f"Timestamp: {latest.get('timestamp', 'unknown')}")
            print(f"Success Rate: {execution.get('success_rate', 'unknown')}")
            print(f"Total Builds: {latest.get('matrix_config', {}).get('total_builds', 0)}")
            
            if "analysis" in latest:
                print("\n✅ Analysis available:")
                analysis = latest["analysis"]
                
                if "gil_impact" in analysis:
                    print("   🎯 GIL impact analysis")
                
                if "version_differences" in analysis:
                    print("   📊 Version differences")
                
                if "ffi_method_rankings" in analysis:
                    print("   🏆 FFI method rankings")
            
            print(f"\n💡 Use --help to see search options")
            print(f"💡 Use --report for comprehensive analysis")
        
        return 0
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())