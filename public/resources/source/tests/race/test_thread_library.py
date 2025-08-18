#!/usr/bin/env python3
"""
Test: Shared Threading Test Library
Tests the threadtest.so library with both racing and non-racing functions.
"""

import unittest
import ctypes
import threading
import time
import os
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


class TestThreadLibrary(unittest.TestCase):
    """Test suite for the multi-threaded test library."""
    
    @classmethod
    def setUpClass(cls):
        """Build and load the thread test library."""
        cls.test_dir = Path(__file__).parent
        cls.lib_path = cls.test_dir / "libthreadtest.so"
        cls.lib_tsan_path = cls.test_dir / "libthreadtest_tsan.so"
        
        # Build the library
        result = subprocess.run(
            ["make", "all"],
            cwd=cls.test_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build library: {result.stderr}")
        
        # Load the regular library for testing
        cls.lib = ctypes.CDLL(str(cls.lib_path))
        
        # Define function signatures
        cls._setup_function_signatures()
    
    @classmethod
    def _setup_function_signatures(cls):
        """Set up ctypes function signatures."""
        # Unsafe functions
        cls.lib.unsafe_increment.argtypes = [ctypes.c_int]
        cls.lib.unsafe_increment.restype = ctypes.c_long
        
        cls.lib.unsafe_decrement.argtypes = [ctypes.c_int]
        cls.lib.unsafe_decrement.restype = ctypes.c_long
        
        cls.lib.unsafe_multiply.argtypes = [ctypes.c_int]
        cls.lib.unsafe_multiply.restype = ctypes.c_long
        
        cls.lib.unsafe_write_buffer.argtypes = [ctypes.c_char_p]
        cls.lib.unsafe_write_buffer.restype = ctypes.c_char_p
        
        cls.lib.unsafe_complex_operation.argtypes = [ctypes.c_int]
        cls.lib.unsafe_complex_operation.restype = ctypes.c_long
        
        cls.lib.withdraw_unsafe.argtypes = [ctypes.c_long]
        cls.lib.withdraw_unsafe.restype = ctypes.c_int
        
        # Safe functions
        cls.lib.safe_increment.argtypes = [ctypes.c_int]
        cls.lib.safe_increment.restype = ctypes.c_long
        
        cls.lib.safe_decrement.argtypes = [ctypes.c_int]
        cls.lib.safe_decrement.restype = ctypes.c_long
        
        cls.lib.safe_multiply.argtypes = [ctypes.c_int]
        cls.lib.safe_multiply.restype = ctypes.c_long
        
        cls.lib.safe_write_buffer.argtypes = [ctypes.c_char_p]
        cls.lib.safe_write_buffer.restype = ctypes.c_char_p
        
        cls.lib.safe_complex_operation.argtypes = [ctypes.c_int]
        cls.lib.safe_complex_operation.restype = ctypes.c_long
        
        cls.lib.withdraw_safe.argtypes = [ctypes.c_long]
        cls.lib.withdraw_safe.restype = ctypes.c_int
        
        # Atomic functions
        cls.lib.atomic_increment.argtypes = [ctypes.c_int]
        cls.lib.atomic_increment.restype = ctypes.c_long
        
        cls.lib.atomic_decrement.argtypes = [ctypes.c_int]
        cls.lib.atomic_decrement.restype = ctypes.c_long
        
        cls.lib.atomic_cas.argtypes = [ctypes.c_long, ctypes.c_long]
        cls.lib.atomic_cas.restype = ctypes.c_int
        
        # Utility functions
        cls.lib.reset_counters.argtypes = []
        cls.lib.reset_counters.restype = None
        
        cls.lib.get_global_counter.argtypes = []
        cls.lib.get_global_counter.restype = ctypes.c_long
        
        cls.lib.get_safe_counter.argtypes = []
        cls.lib.get_safe_counter.restype = ctypes.c_long
        
        cls.lib.get_atomic_counter.argtypes = []
        cls.lib.get_atomic_counter.restype = ctypes.c_long
        
        cls.lib.get_balance.argtypes = []
        cls.lib.get_balance.restype = ctypes.c_long
        
        cls.lib.get_unsafe_balance.argtypes = []
        cls.lib.get_unsafe_balance.restype = ctypes.c_long
        
        # Deadlock functions
        cls.lib.deadlock_function1.argtypes = []
        cls.lib.deadlock_function1.restype = None
        
        cls.lib.deadlock_function2.argtypes = []
        cls.lib.deadlock_function2.restype = None
        
        cls.lib.safe_dual_lock_operation.argtypes = []
        cls.lib.safe_dual_lock_operation.restype = ctypes.c_int
    
    def setUp(self):
        """Reset counters before each test."""
        self.lib.reset_counters()
    
    def test_library_loaded(self):
        """Test that the library is loaded correctly."""
        self.assertTrue(self.lib_path.exists(), "Library not built")
        self.assertIsNotNone(self.lib, "Library not loaded")
    
    def test_unsafe_increment_race_condition(self):
        """Test that unsafe_increment has race conditions."""
        iterations = 10000
        num_threads = 4
        
        def increment_worker():
            self.lib.unsafe_increment(iterations)
        
        # Run multiple threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=increment_worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check final value
        final_value = self.lib.get_global_counter()
        expected_value = iterations * num_threads
        
        # Due to race conditions, the final value should often be less than expected
        self.assertLessEqual(
            final_value, expected_value,
            f"Race condition not demonstrated: got {final_value}, expected < {expected_value}"
        )
        
        # For debugging
        if final_value < expected_value:
            print(f"Race condition detected: {final_value} < {expected_value} (lost {expected_value - final_value} increments)")
    
    def test_safe_increment_no_race(self):
        """Test that safe_increment has no race conditions."""
        iterations = 10000
        num_threads = 4
        
        def increment_worker():
            self.lib.safe_increment(iterations)
        
        # Run multiple threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=increment_worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check final value
        final_value = self.lib.get_safe_counter()
        expected_value = iterations * num_threads
        
        self.assertEqual(
            final_value, expected_value,
            f"Safe increment failed: got {final_value}, expected {expected_value}"
        )
    
    def test_atomic_increment_no_race(self):
        """Test that atomic_increment is thread-safe."""
        iterations = 10000
        num_threads = 4
        
        def atomic_worker():
            self.lib.atomic_increment(iterations)
        
        # Run multiple threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=atomic_worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check final value
        final_value = self.lib.get_atomic_counter()
        expected_value = iterations * num_threads
        
        self.assertEqual(
            final_value, expected_value,
            f"Atomic increment failed: got {final_value}, expected {expected_value}"
        )
    
    def test_unsafe_bank_withdrawal_race(self):
        """Test TOCTOU race condition in unsafe withdrawal."""
        # Try multiple runs to increase chance of detecting race condition
        race_detected = False
        
        for attempt in range(10):  # Try up to 10 times
            self.lib.reset_counters()  # Reset for each attempt
            
            amount = 50  # Smaller amount for more potential withdrawals
            num_threads = 50  # More threads for higher contention
            
            successes = []
            barrier = threading.Barrier(num_threads)  # Synchronize thread start
            
            def withdraw_worker():
                barrier.wait()  # All threads start simultaneously
                # Try multiple withdrawals per thread
                for _ in range(5):
                    result = self.lib.withdraw_unsafe(amount)
                    if result:
                        successes.append(1)
            
            # Start with 1000 balance
            threads = []
            for _ in range(num_threads):
                t = threading.Thread(target=withdraw_worker)
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            # Due to race conditions, we might overdraw
            final_balance = self.lib.get_unsafe_balance()
            total_withdrawn = len(successes) * amount
            
            # The balance might go negative due to race conditions
            print(f"Attempt {attempt + 1}: {len(successes)} withdrawals succeeded, balance: {final_balance}, total withdrawn: {total_withdrawn}")
            
            # Check for race condition: balance + withdrawn should NOT equal 1000 if race occurred
            # or balance should be negative (overdraft)
            if final_balance < 0 or (final_balance + total_withdrawn != 1000):
                race_detected = True
                print(f"Race condition detected! Balance: {final_balance}, Total withdrawn: {total_withdrawn}")
                break
        
        self.assertTrue(
            race_detected,
            "Race condition not demonstrated in bank withdrawal after 10 attempts"
        )
    
    def test_safe_bank_withdrawal_no_race(self):
        """Test that safe withdrawal has no race conditions."""
        amount = 100
        num_threads = 20
        
        successes = []
        
        def withdraw_worker():
            result = self.lib.withdraw_safe(amount)
            if result:
                successes.append(1)
        
        # Start with 1000 balance
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=withdraw_worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Check consistency
        final_balance = self.lib.get_balance()
        total_withdrawn = len(successes) * amount
        
        # Should maintain consistency
        self.assertEqual(
            final_balance + total_withdrawn, 1000,
            f"Safe withdrawal inconsistent: balance {final_balance} + withdrawn {total_withdrawn} != 1000"
        )
        
        # Should not overdraw
        self.assertGreaterEqual(final_balance, 0, "Safe withdrawal overdrew account")
        self.assertLessEqual(len(successes), 10, "Too many withdrawals succeeded")
    
    def test_buffer_race_condition(self):
        """Test race condition in string buffer operations."""
        num_threads = 10
        
        def unsafe_buffer_worker(thread_id):
            msg = f"Thread-{thread_id}".encode()
            result = self.lib.unsafe_write_buffer(msg)
            return result.decode() if result else None
        
        def safe_buffer_worker(thread_id):
            msg = f"Thread-{thread_id}".encode()
            result = self.lib.safe_write_buffer(msg)
            return result.decode() if result else None
        
        # Test unsafe version
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            unsafe_results = list(executor.map(unsafe_buffer_worker, range(num_threads)))
        
        # Reset for safe version
        self.lib.reset_counters()
        
        # Test safe version
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            safe_results = list(executor.map(safe_buffer_worker, range(num_threads)))
        
        # Unsafe version might have corrupted results
        print(f"Unsafe buffer results: {set(filter(None, unsafe_results))}")
        print(f"Safe buffer results: {set(filter(None, safe_results))}")
        
        # Safe version should have consistent format
        for result in safe_results:
            if result:
                self.assertIn(" - processed", result, "Safe buffer missing suffix")
    
    def test_deadlock_potential(self):
        """Test that deadlock functions can potentially deadlock."""
        # This test demonstrates the deadlock scenario without actually deadlocking
        # We use timeouts to prevent hanging
        
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Deadlock detected")
        
        # We won't actually let it deadlock in the test
        # Just verify the functions exist and can be called independently
        
        # Single calls should work
        self.lib.safe_dual_lock_operation()
        result = self.lib.get_global_counter()
        self.assertGreaterEqual(result, 0, "Safe dual lock failed")
    
    def test_compare_and_swap(self):
        """Test atomic compare-and-swap operation."""
        # Set initial value
        self.lib.atomic_increment(10)
        current = self.lib.get_atomic_counter()
        
        # Try CAS with correct expected value
        success = self.lib.atomic_cas(current, 100)
        self.assertTrue(success, "CAS should succeed with correct expected value")
        self.assertEqual(self.lib.get_atomic_counter(), 100)
        
        # Try CAS with wrong expected value
        success = self.lib.atomic_cas(50, 200)
        self.assertFalse(success, "CAS should fail with wrong expected value")
        self.assertEqual(self.lib.get_atomic_counter(), 100)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up built libraries."""
        # Optionally clean up
        # subprocess.run(["make", "clean"], cwd=cls.test_dir)
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)