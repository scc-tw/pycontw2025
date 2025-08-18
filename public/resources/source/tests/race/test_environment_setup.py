#!/usr/bin/env python3
"""
Test: Environment Setup and Free-Threaded Infrastructure Verification
Tests that free-threaded Python builds are properly configured and can demonstrate
the difference between GIL and no-GIL execution.
"""

import sys
import os
import subprocess
import platform
import unittest
import json
from pathlib import Path


class TestEnvironmentSetup(unittest.TestCase):
    """Test suite for verifying free-threaded Python environment setup."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment paths."""
        # Get the project root directory (2 levels up from tests/race/)
        cls.base_dir = Path(__file__).parent.parent.parent
        cls.python_builds = {
            "3.13.5-gil": cls.base_dir / "cpython3.13.5-gil" / "bin" / "python3",
            "3.13.5-nogil": cls.base_dir / "cpython3.13.5-nogil" / "bin" / "python3",
            "3.14.0rc1-gil": cls.base_dir / "cpython3.14.0rc1-gil" / "bin" / "python3",
            "3.14.0rc1-nogil": cls.base_dir / "cpython3.14.0rc1-nogil" / "bin" / "python3",
        }
    
    def test_python_builds_exist(self):
        """Test that all required Python builds are available."""
        for build_name, build_path in self.python_builds.items():
            self.assertTrue(
                build_path.exists(),
                f"Python build {build_name} not found at {build_path}"
            )
            self.assertTrue(
                os.access(build_path, os.X_OK),
                f"Python build {build_name} is not executable"
            )
    
    def test_python_versions(self):
        """Test that Python versions match expected versions."""
        expected_versions = {
            "3.13.5-gil": "3.13.5",
            "3.13.5-nogil": "3.13.5",
            "3.14.0rc1-gil": "3.14.0rc1",
            "3.14.0rc1-nogil": "3.14.0rc1",
        }
        
        for build_name, build_path in self.python_builds.items():
            result = subprocess.run(
                [str(build_path), "--version"],
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0, f"Failed to get version for {build_name}")
            
            version_output = result.stdout.strip()
            expected = expected_versions[build_name]
            self.assertIn(
                expected,
                version_output,
                f"Version mismatch for {build_name}: expected {expected}, got {version_output}"
            )
    
    def test_gil_configuration(self):
        """Test that GIL configuration matches build expectations."""
        gil_test_code = """
import sys
import sysconfig

# Check if GIL is disabled
gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
print(f"GIL_DISABLED: {gil_disabled}")

# Check for free-threaded build
try:
    import _testinternalcapi
    # This will only work on debug builds
    print(f"FREE_THREADED: True")
except ImportError:
    # Alternative check
    print(f"FREE_THREADED: {gil_disabled == 1}")
"""
        
        for build_name, build_path in self.python_builds.items():
            result = subprocess.run(
                [str(build_path), "-c", gil_test_code],
                capture_output=True,
                text=True
            )
            
            output = result.stdout.strip()
            
            if "nogil" in build_name:
                self.assertIn(
                    "GIL_DISABLED: 1",
                    output,
                    f"Build {build_name} should have GIL disabled"
                )
            else:
                self.assertIn(
                    "GIL_DISABLED: 0",
                    output,
                    f"Build {build_name} should have GIL enabled"
                )
    
    def test_threading_support(self):
        """Test that threading module is available and functional."""
        threading_test_code = """
import threading
import time
import sys

counter = 0
lock = threading.Lock()

def increment_unsafe():
    global counter
    for _ in range(100000):
        counter += 1

def increment_safe():
    global counter
    for _ in range(100000):
        with lock:
            counter += 1

# Test unsafe increment (will show race conditions)
counter = 0
threads = [threading.Thread(target=increment_unsafe) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
unsafe_result = counter

# Test safe increment
counter = 0
threads = [threading.Thread(target=increment_safe) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
safe_result = counter

print(f"UNSAFE: {unsafe_result}")
print(f"SAFE: {safe_result}")
print(f"THREAD_COUNT: {threading.active_count()}")
"""
        
        for build_name, build_path in self.python_builds.items():
            result = subprocess.run(
                [str(build_path), "-c", threading_test_code],
                capture_output=True,
                text=True
            )
            
            self.assertEqual(
                result.returncode, 0,
                f"Threading test failed for {build_name}: {result.stderr}"
            )
            
            output = result.stdout.strip()
            lines = output.split('\n')
            
            # Parse results
            unsafe_result = int(lines[0].split(':')[1].strip())
            safe_result = int(lines[1].split(':')[1].strip())
            
            # Safe increment should always be 400000 (4 threads * 100000)
            self.assertEqual(
                safe_result, 400000,
                f"Safe increment failed for {build_name}"
            )
            
            # Unsafe increment might show race conditions (especially in nogil builds)
            if "nogil" in build_name:
                # In nogil builds, race conditions are more likely
                self.assertLessEqual(
                    unsafe_result, 400000,
                    f"Unsafe increment in {build_name} should show potential race conditions"
                )
    
    def test_debug_symbols(self):
        """Test that debug symbols are available for profiling."""
        debug_test_code = """
import sys
print(f"DEBUG: {hasattr(sys, 'gettotalrefcount')}")
print(f"TRACE: {hasattr(sys, 'settrace')}")
"""
        
        for build_name, build_path in self.python_builds.items():
            result = subprocess.run(
                [str(build_path), "-c", debug_test_code],
                capture_output=True,
                text=True
            )
            
            self.assertEqual(
                result.returncode, 0,
                f"Debug test failed for {build_name}"
            )
            
            output = result.stdout.strip()
            self.assertIn("TRACE: True", output, f"Trace support missing in {build_name}")
    
    def test_multiprocessing_support(self):
        """Test that multiprocessing module works correctly."""
        # Note: The `if __name__ == '__main__':` block is essential here.
        # On macOS and Windows, `multiprocessing` uses 'spawn', which creates
        # a new process that re-imports the script. Without the guard,
        # this would lead to an infinite loop of process creation.
        #
        # By passing the script with `-c`, the child process does not have a
        # file to import from, causing issues. To work around this, we
        # explicitly set the start method to 'fork' on non-Windows platforms
        # where it is available. 'fork' inherits the parent process's memory
        # space, avoiding the re-import problem.
        mp_test_code = """
import multiprocessing
import sys

def worker(x):
    return x * x

if __name__ == '__main__':
    if sys.platform != "win32":
        multiprocessing.set_start_method("fork", force=True)
    with multiprocessing.Pool(2) as pool:
        results = pool.map(worker, range(4))
    print(f"RESULTS: {results}")
    print(f"CPU_COUNT: {multiprocessing.cpu_count()}")
"""
        
        for build_name, build_path in self.python_builds.items():
            result = subprocess.run(
                [str(build_path), "-c", mp_test_code],
                capture_output=True,
                text=True
            )
            
            self.assertEqual(
                result.returncode, 0,
                f"Multiprocessing test failed for {build_name}: {result.stderr}"
            )
            
            output = result.stdout.strip()
            self.assertIn("RESULTS: [0, 1, 4, 9]", output)
            self.assertIn("CPU_COUNT:", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)