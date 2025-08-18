#!/usr/bin/env python3
"""
Demonstration of FFI Race Conditions with C++23 and Python nogil

This script demonstrates race conditions when using FFI with Python's experimental
--disable-gil mode. It shows both unsafe and safe approaches to multi-threaded
operations through C++ library calls.

PyCon Taiwan 2025: Python FFI's Hidden Corners
"""

import ctypes
import threading
import time
import sys
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

# Parse command line arguments
parser = argparse.ArgumentParser(description='FFI Race Condition Demonstration')
parser.add_argument('--json', action='store_true', help='Output results as JSON')
parser.add_argument('--iterations', type=int, default=5, help='Number of test iterations')
args = parser.parse_args()

console = Console()

# Load the shared library
lib_path = Path(__file__).parent / "libthreadtest.so"
if not lib_path.exists():
    if not args.json:
        console.print("[red]Error: Library not found. Run 'make all' first![/red]")
    else:
        print(json.dumps({"error": "Library not found. Run 'make all' first!"}))
    sys.exit(1)

# Use PyDLL for better GIL handling
lib = ctypes.PyDLL(str(lib_path))

# Define function signatures
lib.withdraw_unsafe.argtypes = [ctypes.c_long]
lib.withdraw_unsafe.restype = ctypes.c_int

lib.withdraw_unsafe_fast.argtypes = [ctypes.c_long]
lib.withdraw_unsafe_fast.restype = ctypes.c_int

lib.withdraw_safe.argtypes = [ctypes.c_long]
lib.withdraw_safe.restype = ctypes.c_int

lib.get_unsafe_balance.argtypes = []
lib.get_unsafe_balance.restype = ctypes.c_long

lib.get_fast_bank_balance.argtypes = []
lib.get_fast_bank_balance.restype = ctypes.c_long

lib.get_balance.argtypes = []
lib.get_balance.restype = ctypes.c_long

lib.reset_counters.argtypes = []
lib.reset_counters.restype = None

lib.reset_fast_bank.argtypes = []
lib.reset_fast_bank.restype = None

lib.unsafe_increment.argtypes = [ctypes.c_int]
lib.unsafe_increment.restype = ctypes.c_long

lib.safe_increment.argtypes = [ctypes.c_int]
lib.safe_increment.restype = ctypes.c_long

lib.atomic_increment.argtypes = [ctypes.c_int]
lib.atomic_increment.restype = ctypes.c_long

lib.get_global_counter.argtypes = []
lib.get_global_counter.restype = ctypes.c_long

lib.get_safe_counter.argtypes = []
lib.get_safe_counter.restype = ctypes.c_long

lib.get_atomic_counter.argtypes = []
lib.get_atomic_counter.restype = ctypes.c_long


def demo_fast_bank_withdrawal_race(iterations=5):
    """Demonstrate TOCTOU race condition in fast bank withdrawals (no sleep - GIL matters)."""
    if not args.json:
        console.print("\n[bold cyan]═══ Fast Bank Withdrawal Race (No Sleep) ═══[/bold cyan]\n")
    
    results = []
    for i in range(iterations):
        lib.reset_fast_bank()
        
        num_threads = 100
        amount = 20
        successes = []
        barrier = threading.Barrier(num_threads)
        
        def withdraw_worker():
            barrier.wait()
            for _ in range(5):
                if lib.withdraw_unsafe_fast(amount):
                    successes.append(1)
        
        threads = [threading.Thread(target=withdraw_worker) for _ in range(num_threads)]
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start_time
        
        balance = lib.get_fast_bank_balance()
        withdrawn = len(successes) * amount
        
        results.append({
            'withdrawals': len(successes),
            'balance': balance,
            'withdrawn': withdrawn,
            'total': balance + withdrawn,
            'overdraft': balance < 0,
            'inconsistent': (balance + withdrawn) != 1000,
            'time': elapsed
        })
    
    # Calculate statistics
    races_detected = sum(1 for r in results if r['inconsistent'])
    avg_withdrawals = sum(r['withdrawals'] for r in results) / len(results)
    
    if not args.json:
        console.print(f"Iterations: {iterations}")
        console.print(f"Race conditions detected: {races_detected}/{iterations}")
        console.print(f"Average withdrawals: {avg_withdrawals:.1f}")
        
        if races_detected > 0:
            console.print(f"\n[red bold]⚠️  RACE CONDITIONS DETECTED in {races_detected}/{iterations} runs![/red bold]")
        else:
            console.print(f"\n[green]✓ No race conditions detected (GIL protected)[/green]")
    
    return {
        'test': 'fast_bank_withdrawal',
        'iterations': iterations,
        'races_detected': races_detected,
        'results': results
    }

def demo_bank_withdrawal_race():
    """Demonstrate TOCTOU race condition in bank withdrawals."""
    console.print("\n[bold cyan]═══ Bank Withdrawal Race Condition Demo ═══[/bold cyan]\n")
    
    # Test parameters
    num_threads = 100
    withdraw_amount = 50
    attempts_per_thread = 3
    
    console.print(f"Initial balance: $1000")
    console.print(f"Threads: {num_threads}")
    console.print(f"Withdrawal amount: ${withdraw_amount}")
    console.print(f"Attempts per thread: {attempts_per_thread}")
    console.print(f"Max possible withdrawals: {num_threads * attempts_per_thread} = ${num_threads * attempts_per_thread * withdraw_amount}\n")
    
    # First, demonstrate unsafe version
    console.print("[yellow]Testing UNSAFE withdrawal (with race condition)...[/yellow]")
    lib.reset_counters()
    
    unsafe_successes = []
    barrier = threading.Barrier(num_threads)
    
    def unsafe_withdraw():
        barrier.wait()  # Synchronize thread start
        for _ in range(attempts_per_thread):
            if lib.withdraw_unsafe(withdraw_amount):
                unsafe_successes.append(1)
    
    threads = [threading.Thread(target=unsafe_withdraw) for _ in range(num_threads)]
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    unsafe_time = time.time() - start_time
    
    unsafe_balance = lib.get_unsafe_balance()
    unsafe_withdrawn = len(unsafe_successes) * withdraw_amount
    
    # Now demonstrate safe version
    console.print("\n[green]Testing SAFE withdrawal (thread-safe)...[/green]")
    lib.reset_counters()
    
    safe_successes = []
    barrier = threading.Barrier(num_threads)
    
    def safe_withdraw():
        barrier.wait()  # Synchronize thread start
        for _ in range(attempts_per_thread):
            if lib.withdraw_safe(withdraw_amount):
                safe_successes.append(1)
    
    threads = [threading.Thread(target=safe_withdraw) for _ in range(num_threads)]
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    safe_time = time.time() - start_time
    
    safe_balance = lib.get_balance()
    safe_withdrawn = len(safe_successes) * withdraw_amount
    
    # Display results
    table = Table(title="Race Condition Comparison", show_header=True, header_style="bold magenta")
    table.add_column("Method", style="cyan", no_wrap=True)
    table.add_column("Successful Withdrawals", justify="right")
    table.add_column("Total Withdrawn", justify="right")
    table.add_column("Final Balance", justify="right")
    table.add_column("Balance + Withdrawn", justify="right")
    table.add_column("Consistency", justify="center")
    table.add_column("Time (s)", justify="right")
    
    unsafe_consistent = "❌ BROKEN" if (unsafe_balance + unsafe_withdrawn != 1000 or unsafe_balance < 0) else "✅ OK"
    safe_consistent = "✅ OK" if (safe_balance + safe_withdrawn == 1000 and safe_balance >= 0) else "❌ BROKEN"
    
    table.add_row(
        "UNSAFE",
        str(len(unsafe_successes)),
        f"${unsafe_withdrawn}",
        f"${unsafe_balance}",
        f"${unsafe_balance + unsafe_withdrawn}",
        unsafe_consistent,
        f"{unsafe_time:.3f}"
    )
    
    table.add_row(
        "SAFE",
        str(len(safe_successes)),
        f"${safe_withdrawn}",
        f"${safe_balance}",
        f"${safe_balance + safe_withdrawn}",
        safe_consistent,
        f"{safe_time:.3f}"
    )
    
    console.print("\n", table)
    
    if unsafe_balance < 0:
        console.print(f"\n[red bold]⚠️  RACE CONDITION DETECTED: Account overdrafted by ${-unsafe_balance}![/red bold]")
    elif unsafe_balance + unsafe_withdrawn != 1000:
        diff = (unsafe_balance + unsafe_withdrawn) - 1000
        console.print(f"\n[red bold]⚠️  RACE CONDITION DETECTED: Total is off by ${abs(diff)}![/red bold]")


def demo_counter_race(test_iterations=5):
    """Demonstrate race conditions in counter operations."""
    console.print("\n[bold cyan]═══ Counter Increment Race Condition Demo ═══[/bold cyan]\n")
    
    num_threads = 50
    increments_per_thread = 10000
    expected = num_threads * increments_per_thread
    
    console.print(f"Threads: {num_threads}")
    console.print(f"Iterations per thread: {increments_per_thread:,}")
    console.print(f"Expected final value: {expected:,}\n")
    
    # Test unsafe increment with manual thread management
    console.print("[yellow]Testing UNSAFE increment...[/yellow]")
    lib.reset_counters()
    
    barrier = threading.Barrier(num_threads)
    def unsafe_worker():
        barrier.wait()  # Synchronize start
        lib.unsafe_increment(increments_per_thread)
    
    threads = [threading.Thread(target=unsafe_worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    unsafe_result = lib.get_global_counter()
    
    # Test safe increment with manual thread management
    console.print("[green]Testing SAFE increment (mutex)...[/green]")
    lib.reset_counters()
    
    barrier = threading.Barrier(num_threads)
    def safe_worker():
        barrier.wait()  # Synchronize start
        lib.safe_increment(increments_per_thread)
    
    threads = [threading.Thread(target=safe_worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    safe_result = lib.get_safe_counter()
    
    # Test atomic increment with manual thread management
    console.print("[blue]Testing ATOMIC increment...[/blue]")
    lib.reset_counters()
    
    barrier = threading.Barrier(num_threads)
    def atomic_worker():
        barrier.wait()  # Synchronize start
        lib.atomic_increment(increments_per_thread)
    
    threads = [threading.Thread(target=atomic_worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    atomic_result = lib.get_atomic_counter()
    
    # Display results
    table = Table(title="Counter Increment Comparison", show_header=True, header_style="bold magenta")
    table.add_column("Method", style="cyan", no_wrap=True)
    table.add_column("Final Value", justify="right")
    table.add_column("Expected", justify="right")
    table.add_column("Lost Increments", justify="right")
    table.add_column("Accuracy", justify="right")
    table.add_column("Status", justify="center")
    
    unsafe_lost = expected - unsafe_result
    unsafe_accuracy = (unsafe_result / expected) * 100
    
    table.add_row(
        "UNSAFE",
        f"{unsafe_result:,}",
        f"{expected:,}",
        f"{unsafe_lost:,}" if unsafe_lost > 0 else "0",
        f"{unsafe_accuracy:.1f}%",
        "❌ RACE" if unsafe_lost > 0 else "✅ OK"
    )
    
    table.add_row(
        "SAFE (mutex)",
        f"{safe_result:,}",
        f"{expected:,}",
        "0",
        "100.0%",
        "✅ OK"
    )
    
    table.add_row(
        "ATOMIC",
        f"{atomic_result:,}",
        f"{expected:,}",
        "0",
        "100.0%",
        "✅ OK"
    )
    
    console.print("\n", table)
    
    if unsafe_lost > 0:
        console.print(f"\n[red bold]⚠️  RACE CONDITION: Lost {unsafe_lost:,} increments ({100 - unsafe_accuracy:.1f}% data loss)![/red bold]")


def main():
    """Run all demonstrations."""
    # Check GIL status
    gil_enabled = not (hasattr(sys, '_is_gil_enabled') and not sys._is_gil_enabled())
    
    if args.json:
        # JSON mode for automated testing
        try:
            # Run fast bank test (key for GIL vs no-GIL comparison)
            fast_bank_results = demo_fast_bank_withdrawal_race(args.iterations)
            
            # Run counter test for completeness 
            counter_results = []
            for i in range(args.iterations):
                lib.reset_counters()
                
                num_threads = 50
                increments_per_thread = 10000
                expected = num_threads * increments_per_thread
                
                barrier = threading.Barrier(num_threads)
                def increment_worker():
                    barrier.wait()
                    lib.unsafe_increment(increments_per_thread)
                
                threads = [threading.Thread(target=increment_worker) for _ in range(num_threads)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                
                final = lib.get_global_counter()
                lost = expected - final
                counter_results.append({
                    'final': final,
                    'expected': expected,
                    'lost': lost,
                    'accuracy': (final / expected) * 100
                })
            
            counter_races = sum(1 for r in counter_results if r['lost'] > 0)
            avg_counter_loss = sum(r['lost'] for r in counter_results) / len(counter_results)
            avg_counter_accuracy = sum(r['accuracy'] for r in counter_results) / len(counter_results)
            
            # Output JSON results
            output = {
                'gil_enabled': gil_enabled,
                'python_version': sys.version,
                'counter_test': {
                    'races_detected': counter_races,
                    'total_runs': len(counter_results),
                    'avg_lost_increments': avg_counter_loss,
                    'avg_accuracy': avg_counter_accuracy,
                    'details': counter_results
                },
                'fast_bank_test': {
                    'races_detected': fast_bank_results['races_detected'],
                    'total_runs': fast_bank_results['iterations'],
                    'details': fast_bank_results['results']
                }
            }
            print(json.dumps(output))
            
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        # Rich UI mode for interactive demonstration
        console.print(Panel.fit(
            "[bold white]FFI Race Condition Demonstration[/bold white]\n"
            "[dim]Python FFI with C++23 and nogil mode[/dim]",
            title="PyCon Taiwan 2025",
            border_style="bright_blue"
        ))
        
        if hasattr(sys, '_is_gil_enabled'):
            if not sys._is_gil_enabled():
                console.print("\n[green]✓ Running with Python nogil mode[/green]")
            else:
                console.print("\n[yellow]⚠ Running with standard Python (GIL enabled)[/yellow]")
        else:
            console.print("\n[dim]Python version doesn't report GIL status[/dim]")
        
        try:
            demo_counter_race()
            demo_bank_withdrawal_race()
            demo_fast_bank_withdrawal_race()
            
            console.print("\n[bold green]═══ Demo Complete ═══[/bold green]")
            console.print("\n[dim]Key takeaways:[/dim]")
            console.print("[dim]• Race conditions are real and dangerous in multi-threaded FFI[/dim]")
            console.print("[dim]• C++23 provides modern synchronization primitives (atomic, mutex, etc.)[/dim]")
            console.print("[dim]• Python's nogil mode makes these issues more visible[/dim]")
            console.print("[dim]• Always use thread-safe implementations in production code[/dim]\n")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            raise


if __name__ == "__main__":
    main()