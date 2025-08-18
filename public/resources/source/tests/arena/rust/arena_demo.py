#!/usr/bin/env python3
"""
Arena Demo - Demonstration and validation functionality for Arena extensions.

This module handles demonstrating extensions across all Python environments,
validating builds, and providing comprehensive testing reports.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

from arena_manager import ArenaManager
from arena_tester import ArenaTester
from arena_builder import ArenaBuilder

class ArenaDemo(ArenaManager):
    """Manages Arena demonstration and validation functionality."""
    
    def __init__(self, base_dir: Path):
        super().__init__(base_dir)
        self.tester = ArenaTester(base_dir)
        self.builder = ArenaBuilder(base_dir)
    
    def demo_all_extensions(self):
        """Demonstrate all built extensions."""
        build_results = self.builder.get_build_results()
        if not build_results:
            print("❌ Arena build results not found. Run 'python arena_test.py build' first.")
            sys.exit(1)
        
        print("Arena Extension Demo")
        print("=" * 60)
        print(f"Found {len(build_results)} built extensions:")
        
        for build_name, result in build_results.items():
            if result.get("status") == "success":
                print(f"  ✅ {build_name}: {result.get('so_file', 'N/A')}")
            else:
                print(f"  ❌ {build_name}: {result.get('error', 'Unknown error')}")
        
        # Test with each successful build
        successful_tests = 0
        total_tests = 0
        
        for build_name, result in build_results.items():
            if result.get("status") != "success":
                continue
                
            total_tests += 1
            
            # Find Python executable
            python_path = self.get_python_executable(build_name)
            if not python_path:
                print(f"⚠️ Python executable not found for {build_name}")
                continue
            
            if self.tester.test_arena_with_python(python_path, build_name):
                successful_tests += 1
        
        print(f"\n{'='*60}")
        print(f"DEMO SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        
        if successful_tests == total_tests:
            print("\n🎉 All arena extensions are working correctly!")
        else:
            print(f"\n⚠️ {total_tests - successful_tests} test(s) failed.")
            sys.exit(1)
    
    def validate_all_builds(self) -> Dict:
        """Validate all built extensions with comprehensive testing."""
        build_results = self.builder.get_build_results()
        if not build_results:
            self.log("❌ No build results found", "ERROR")
            return {}
        
        validation_results = {}
        
        print("=" * 60)
        print("ARENA VALIDATION REPORT")
        print("=" * 60)
        
        for build_name, build_result in build_results.items():
            print(f"\nValidating {build_name}...")
            
            validation = {
                "build_status": build_result.get("status"),
                "build_timestamp": build_result.get("timestamp"),
                "python_available": False,
                "module_installed": False,
                "basic_test": False,
                "memory_test": False
            }
            
            # Check Python availability
            python_path = self.get_python_executable(build_name)
            if python_path:
                validation["python_available"] = True
                validation["python_path"] = str(python_path)
                
                # Check module installation
                module_info = self.get_module_info(build_name)
                if module_info and module_info.get("installed"):
                    validation["module_installed"] = True
                    validation["module_path"] = module_info.get("path")
                    
                    # Run basic test
                    try:
                        test_result = self.tester.test_specific_build(build_name, thread_count=100)
                        if test_result:
                            validation["basic_test"] = True
                            validation["test_result"] = test_result
                            
                            # Memory test (check if memory delta is reasonable)
                            memory_delta = test_result.get("memory_delta_mib", 0)
                            if 0 <= memory_delta <= 1000:  # Reasonable range
                                validation["memory_test"] = True
                    except Exception as e:
                        validation["test_error"] = str(e)
            
            validation_results[build_name] = validation
            
            # Print status
            status_emoji = "✅" if all([
                validation["python_available"],
                validation["module_installed"], 
                validation["basic_test"],
                validation["memory_test"]
            ]) else "❌"
            
            print(f"  {status_emoji} {build_name}")
            print(f"    Python: {'✅' if validation['python_available'] else '❌'}")
            print(f"    Module: {'✅' if validation['module_installed'] else '❌'}")
            print(f"    Basic Test: {'✅' if validation['basic_test'] else '❌'}")
            print(f"    Memory Test: {'✅' if validation['memory_test'] else '❌'}")
            
            if validation.get("test_result"):
                tr = validation["test_result"]
                print(f"    Memory Delta: {tr.get('memory_delta_mib', 0):.2f} MiB")
        
        # Save validation results
        validation_file = self.base_dir / "arena_validation_results.json"
        with open(validation_file, "w") as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"\n📊 Validation results saved to: {validation_file}")
        
        return validation_results
    
    def generate_report(self) -> Dict:
        """Generate comprehensive report of Arena status."""
        report = {
            "timestamp": self.log("", level="", timestamp=True).split("]")[0][1:],
            "python_availability": self.check_python_availability(),
            "build_status": self.builder.get_build_status(),
            "validation": None,
            "benchmark": None
        }
        
        # Add validation if builds exist
        if self.builder.get_build_results():
            report["validation"] = self.validate_all_builds()
            
            # Add benchmark results
            try:
                report["benchmark"] = self.tester.benchmark_all_builds(thread_count=500)
                
                # Add GIL vs no-GIL comparison
                report["gil_comparison"] = self.tester.compare_gil_vs_nogil(thread_count=500)
            except Exception as e:
                report["benchmark_error"] = str(e)
        
        # Save complete report
        report_file = self.base_dir / "arena_complete_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Complete report saved to: {report_file}")
        
        return report
    
    def print_status_summary(self):
        """Print a concise status summary."""
        print("Arena System Status")
        print("=" * 40)
        
        # Python availability
        python_status = self.check_python_availability()
        available_count = sum(1 for available in python_status.values() if available)
        print(f"Python Builds: {available_count}/{len(self.python_builds)} available")
        
        for build, available in python_status.items():
            emoji = "✅" if available else "❌"
            print(f"  {emoji} {build}")
        
        # Build status
        build_status = self.builder.get_build_status()
        built_count = sum(1 for status in build_status.values() if status == "success")
        print(f"\nBuilt Extensions: {built_count}/{len(self.python_builds)}")
        
        for build, status in build_status.items():
            if status == "success":
                emoji = "✅"
            elif status == "failed":
                emoji = "❌"
            else:
                emoji = "⚪"
            print(f"  {emoji} {build}: {status}")
        
        # Quick module check
        if built_count > 0:
            print(f"\nModule Status:")
            for build in self.python_builds:
                if build_status.get(build) == "success":
                    module_info = self.get_module_info(build)
                    if module_info:
                        emoji = "✅" if module_info.get("installed") else "❌"
                        print(f"  {emoji} {build}: {'installed' if module_info.get('installed') else 'not found'}")
    
    def interactive_demo(self):
        """Run an interactive demonstration."""
        print("🎯 Arena Interactive Demo")
        print("=" * 40)
        
        while True:
            print("\nOptions:")
            print("1. Show status summary")
            print("2. Test specific build")
            print("3. Benchmark all builds")
            print("4. Compare GIL vs no-GIL")
            print("5. Generate full report")
            print("6. Exit")
            
            try:
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == "1":
                    self.print_status_summary()
                
                elif choice == "2":
                    available = self.get_available_builds()
                    if not available:
                        print("❌ No builds available")
                        continue
                    
                    print("\nAvailable builds:")
                    for i, build in enumerate(available, 1):
                        print(f"  {i}. {build}")
                    
                    try:
                        build_idx = int(input("Select build: ")) - 1
                        if 0 <= build_idx < len(available):
                            build = available[build_idx]
                            threads = int(input("Thread count (default 1000): ") or "1000")
                            result = self.tester.test_specific_build(build, threads)
                            if result:
                                print(f"\n🎉 Test completed: {result['memory_delta_mib']:.2f} MiB delta")
                    except ValueError:
                        print("❌ Invalid selection")
                
                elif choice == "3":
                    threads = int(input("Thread count (default 1000): ") or "1000")
                    results = self.tester.benchmark_all_builds(threads)
                    print(f"\n📊 Benchmark Results ({threads} threads):")
                    for build, result in results.items():
                        print(f"  {build}: {result['memory_delta_mib']:.2f} MiB")
                
                elif choice == "4":
                    threads = int(input("Thread count (default 1000): ") or "1000")
                    comparison = self.tester.compare_gil_vs_nogil(threads)
                    print(f"\n⚖️ GIL vs no-GIL Comparison ({threads} threads):")
                    for version, data in comparison.items():
                        gil_delta = data["gil"]["memory_delta_mib"]
                        nogil_delta = data["nogil"]["memory_delta_mib"]
                        diff = data["memory_delta_difference"]
                        print(f"  Python {version}:")
                        print(f"    GIL:    {gil_delta:.2f} MiB")
                        print(f"    no-GIL: {nogil_delta:.2f} MiB")
                        print(f"    Diff:   {diff:+.2f} MiB")
                
                elif choice == "5":
                    print("📋 Generating comprehensive report...")
                    self.generate_report()
                    print("✅ Report generated!")
                
                elif choice == "6":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid option")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
