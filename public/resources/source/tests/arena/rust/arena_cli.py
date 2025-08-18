#!/usr/bin/env python3
"""
Arena CLI - Command-line interface for Arena tools.

This module provides the command-line interface and coordinates
between different Arena modules.
"""

import argparse
import sys
from pathlib import Path

from arena_manager import ArenaManager
from arena_builder import ArenaBuilder
from arena_tester import ArenaTester
from arena_demo import ArenaDemo

class ArenaCLI:
    """Command-line interface for Arena tools."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.manager = ArenaManager(base_dir)
        self.builder = ArenaBuilder(base_dir)
        self.tester = ArenaTester(base_dir)
        self.demo = ArenaDemo(base_dir)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            description="Unified Arena Testing and Build Management Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Build extensions for all Python environments
  python arena_test.py build
  
  # Build for specific Python version only
  python arena_test.py build --python 3.13.5-nogil
  
  # Clean and rebuild
  python arena_test.py build --clean
  
  # Run arena test with current Python
  python arena_test.py test 1280000
  
  # Run simple test with monitoring
  python arena_test.py test 1000 --simple --monitor
  
  # Demonstrate all built extensions
  python arena_test.py demo
  
  # Validate all builds
  python arena_test.py validate
  
  # Generate comprehensive report
  python arena_test.py report
  
  # Interactive demo mode
  python arena_test.py interactive
  
  # Show status summary
  python arena_test.py status
  
  # Clean all build artifacts
  python arena_test.py clean
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Build subcommand
        build_parser = subparsers.add_parser("build", help="Build extensions")
        build_parser.add_argument(
            "--profile",
            choices=["release", "instrumented"],
            default="release",
            help="Build profile (release=optimized, instrumented=with frame pointers)"
        )
        build_parser.add_argument(
            "--python",
            help="Build for specific Python version only (e.g., 3.13.5-nogil)"
        )
        build_parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean build artifacts before building"
        )
        
        # Test subcommand
        test_parser = subparsers.add_parser("test", help="Run arena memory leak test")
        test_parser.add_argument("thread_count", type=int, nargs="?", default=1280000,
                               help="Number of threads to spawn (default: 1280000)")
        test_parser.add_argument("--sleep", type=int, default=0,
                               help="Seconds to sleep after test for memory observation (default: 0)")
        test_parser.add_argument("--simple", action="store_true",
                               help="Run simple test that returns only RSS values")
        test_parser.add_argument("--monitor", action="store_true",
                               help="Show monitoring instructions and wait for user input")
        test_parser.add_argument("--quick", action="store_true",
                               help="Run quick test with 1000 threads")
        test_parser.add_argument("--build", 
                               help="Test specific Python build (e.g., 3.13.5-nogil)")
        
        # Demo subcommand
        demo_parser = subparsers.add_parser("demo", help="Demonstrate all built extensions")
        
        # Validate subcommand
        validate_parser = subparsers.add_parser("validate", help="Validate all built extensions")
        
        # Status subcommand
        status_parser = subparsers.add_parser("status", help="Show system status summary")
        
        # Report subcommand  
        report_parser = subparsers.add_parser("report", help="Generate comprehensive report")
        
        # Interactive subcommand
        interactive_parser = subparsers.add_parser("interactive", help="Run interactive demo")
        
        # Benchmark subcommand
        benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmark tests")
        benchmark_parser.add_argument("--threads", type=int, default=1000,
                                    help="Number of threads for benchmark (default: 1000)")
        benchmark_parser.add_argument("--gil-comparison", action="store_true",
                                    help="Compare GIL vs no-GIL performance")
        benchmark_parser.add_argument("--arena-risk", action="store_true",
                                    help="Run arena leakage risk comparison (demonstrates O(MN) complexity)")
        benchmark_parser.add_argument("--python-threads", type=int, default=16,
                                    help="Number of Python threads for arena risk test (default: 16)")
        benchmark_parser.add_argument("--rust-threads", type=int, default=100,
                                    help="Number of Rust threads per Python thread (default: 100)")
        
        # Arena risk subcommand (dedicated)
        arena_parser = subparsers.add_parser("arena-risk", help="Run arena leakage risk tests")
        arena_parser.add_argument("--python-threads", type=int, default=16,
                                help="Number of Python threads (N) (default: 16)")
        arena_parser.add_argument("--rust-threads", type=int, default=100,
                                help="Number of Rust threads per call (M) (default: 100)")
        arena_parser.add_argument("--concurrent-stress", action="store_true",
                                help="Run concurrent stress test with current Python")
        arena_parser.add_argument("--burst-test", action="store_true",
                                help="Run burst allocation test")
        arena_parser.add_argument("--iterations", type=int, default=10,
                                help="Iterations per Python thread (default: 10)")
        
        # Clean subcommand
        clean_parser = subparsers.add_parser("clean", help="Clean build artifacts")
        
        return parser
    
    def handle_build(self, args):
        """Handle build command."""
        if args.clean:
            self.builder.clean_build_artifacts()
        
        results = self.builder.build_all(args.profile, args.python)
        
        # Exit with error if any build failed
        if any(r.get("status") == "failed" for r in results.values()):
            sys.exit(1)
    
    def handle_test(self, args):
        """Handle test command."""
        if args.build:
            # Test specific build
            if not self.manager.validate_build_name(args.build):
                print(f"❌ Unknown build: {args.build}")
                print(f"Available: {', '.join(self.manager.python_builds)}")
                sys.exit(1)
            
            result = self.tester.test_specific_build(args.build, args.thread_count)
            if not result:
                sys.exit(1)
            return
        
        # Test with current Python
        if args.quick:
            self.tester.quick_test()
        else:
            self.tester.test_arena_with_current_python(
                args.thread_count, 
                args.sleep, 
                args.simple, 
                args.monitor
            )
    
    def handle_benchmark(self, args):
        """Handle benchmark command."""
        if args.arena_risk:
            print(f"🔬 Running Arena Risk Analysis...")
            print(f"   Python Threads (N): {args.python_threads}")
            print(f"   Rust Threads per call (M): {args.rust_threads}")
            print(f"   Expected complexity: O(N*M) = O({args.python_threads * args.rust_threads})")
            
            comparison = self.tester.compare_gil_vs_nogil_arena_risk(args.python_threads, args.rust_threads)
            
            if not comparison:
                print("❌ No builds available for arena risk comparison")
                return
            
            print(f"\n🚨 Arena Leakage Risk Analysis Results:")
            print("=" * 80)
            
            for version, data in comparison.items():
                gil_memory = data["gil"]["memory"]["total_memory_delta_mib"]
                nogil_memory = data["nogil"]["memory"]["total_memory_delta_mib"]
                gil_amplification = data["gil"]["memory"].get("memory_amplification", 0)
                nogil_amplification = data["nogil"]["memory"].get("memory_amplification", 0)
                risk_metrics = data["risk_metrics"]
                
                print(f"\nPython {version} - Arena Risk Assessment:")
                print(f"  🔒 GIL Memory Delta:      {gil_memory:8.2f} MiB (amplification: {gil_amplification:.2f}x)")
                print(f"  🆓 no-GIL Memory Delta:   {nogil_memory:8.2f} MiB (amplification: {nogil_amplification:.2f}x)")
                print(f"  📈 Risk Amplification:    {risk_metrics['memory_amplification']:8.2f}x")
                print(f"  🎯 Risk Level:            {risk_metrics['risk_level']}")
                print(f"  🔄 Parallelism Increase:  {risk_metrics['parallelism_increase']:8.2f}x")
                
                if risk_metrics['memory_amplification'] > 1.5:
                    print(f"  ⚠️  HIGH RISK: no-GIL shows significant arena leakage amplification!")
                elif risk_metrics['memory_amplification'] > 1.1:
                    print(f"  ⚠️  MODERATE RISK: no-GIL shows measurable arena leakage increase")
                else:
                    print(f"  ✅ LOW RISK: Minimal difference between GIL and no-GIL")
                    
        elif args.gil_comparison:
            print(f"⚖️ Running GIL vs no-GIL comparison with {args.threads} threads...")
            comparison = self.tester.compare_gil_vs_nogil(args.threads)
            
            if not comparison:
                print("❌ No builds available for comparison")
                return
            
            print(f"\nGIL vs no-GIL Comparison Results ({args.threads} threads):")
            print("=" * 60)
            
            for version, data in comparison.items():
                gil_delta = data["gil"]["memory_delta_mib"]
                nogil_delta = data["nogil"]["memory_delta_mib"]
                diff = data["memory_delta_difference"]
                
                print(f"\nPython {version}:")
                print(f"  GIL:    {gil_delta:.2f} MiB")
                print(f"  no-GIL: {nogil_delta:.2f} MiB")
                print(f"  Diff:   {diff:+.2f} MiB ({'no-GIL uses more' if diff > 0 else 'GIL uses more' if diff < 0 else 'same'})")
        else:
            print(f"🏃 Running benchmark with {args.threads} threads...")
            results = self.tester.benchmark_all_builds(args.threads)
            
            if not results:
                print("❌ No builds available for benchmarking")
                return
            
            print(f"\nBenchmark Results ({args.threads} threads):")
            print("=" * 40)
            
            for build, result in results.items():
                print(f"  {build}: {result['memory_delta_mib']:6.2f} MiB")
    
    def handle_arena_risk(self, args):
        """Handle arena risk command."""
        if args.concurrent_stress:
            print(f"🧪 Running Concurrent Arena Stress Test with current Python...")
            result = self.tester.run_concurrent_arena_stress_test(
                python_threads=args.python_threads,
                rust_threads_per_call=args.rust_threads,
                iterations_per_thread=args.iterations
            )
            
            if result:
                print(f"\nConcurrent Stress Test Results:")
                print(f"  Total Memory Delta: {result['memory']['total_memory_delta_mib']:.2f} MiB")
                print(f"  Parallelism Factor: {result['timing']['parallelism_factor']:.2f}x")
                print(f"  Free-threaded Mode: {result['free_threaded']}")
                
        elif args.burst_test:
            print(f"💥 Running Burst Allocation Test with current Python...")
            result = self.tester.run_burst_allocation_test()
            
            if result:
                print(f"\nBurst Test Results:")
                print(f"  Total Memory Delta: {result['memory']['total_observed_delta_mib']:.2f} MiB")
                print(f"  Memory Amplification: {result['memory']['memory_amplification']:.2f}x")
                print(f"  Free-threaded Mode: {result['free_threaded']}")
        else:
            # Default to arena risk comparison
            print(f"🔬 Running Arena Risk Comparison...")
            comparison = self.tester.compare_gil_vs_nogil_arena_risk(args.python_threads, args.rust_threads)
            
            if not comparison:
                print("❌ No builds available for arena risk comparison")
                return
            
            print(f"\n🚨 Arena Leakage Risk Analysis:")
            print("=" * 60)
            
            for version, data in comparison.items():
                risk_metrics = data["risk_metrics"]
                print(f"\nPython {version}:")
                print(f"  Risk Amplification: {risk_metrics['memory_amplification']:.2f}x")
                print(f"  Risk Level: {risk_metrics['risk_level']}")
                print(f"  Memory Difference: {risk_metrics['absolute_memory_difference_mib']:+.2f} MiB")
    
    def run(self, args=None):
        """Run the CLI with the given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Handle legacy usage (no command specified)
        if not parsed_args.command:
            # Default to test command for backwards compatibility
            legacy_parser = argparse.ArgumentParser(description="Run glibc arena memory leak test")
            legacy_parser.add_argument("thread_count", type=int, nargs="?", default=1280000,
                                     help="Number of threads to spawn (default: 1280000)")
            legacy_parser.add_argument("--sleep", type=int, default=0,
                                     help="Seconds to sleep after test for memory observation (default: 0)")
            legacy_parser.add_argument("--simple", action="store_true",
                                     help="Run simple test that returns only RSS values")
            legacy_parser.add_argument("--monitor", action="store_true",
                                     help="Show monitoring instructions and wait for user input")
            
            legacy_args = legacy_parser.parse_args(args)
            
            self.tester.test_arena_with_current_python(
                legacy_args.thread_count, 
                legacy_args.sleep, 
                legacy_args.simple, 
                legacy_args.monitor
            )
            return
        
        # Handle subcommands
        try:
            if parsed_args.command == "build":
                self.handle_build(parsed_args)
            
            elif parsed_args.command == "test":
                self.handle_test(parsed_args)
            
            elif parsed_args.command == "demo":
                self.demo.demo_all_extensions()
            
            elif parsed_args.command == "validate":
                self.demo.validate_all_builds()
            
            elif parsed_args.command == "status":
                self.demo.print_status_summary()
            
            elif parsed_args.command == "report":
                self.demo.generate_report()
            
            elif parsed_args.command == "interactive":
                self.demo.interactive_demo()
            
            elif parsed_args.command == "benchmark":
                self.handle_benchmark(parsed_args)
            
            elif parsed_args.command == "arena-risk":
                self.handle_arena_risk(parsed_args)
            
            elif parsed_args.command == "clean":
                self.builder.clean_build_artifacts()
                print("✅ Build artifacts cleaned.")
            
            else:
                parser.print_help()
                
        except KeyboardInterrupt:
            print("\n👋 Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    cli = ArenaCLI(Path(__file__).parent)
    cli.run()


if __name__ == "__main__":
    main()
