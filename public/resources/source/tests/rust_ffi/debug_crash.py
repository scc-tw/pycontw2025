#!/usr/bin/env python3
"""
Debug the specific Python 3.14 no-GIL segfault with comprehensive stacktrace
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def debug_python314_nogil_crash():
    """Debug the specific Python 3.14 no-GIL crash with GDB"""
    
    project_root = Path(__file__).parent.parent.parent
    python_nogil = project_root / "cpython3.14.0rc1-nogil" / "bin" / "python3"
    
    if not python_nogil.exists():
        print(f"❌ Python 3.14 no-GIL not found at: {python_nogil}")
        return
    
    print(f"🔍 Debugging crash with: {python_nogil}")
    
    # Create comprehensive GDB script
    gdb_script = f"""
# Enable all debugging features
set environment RUST_BACKTRACE=full
set environment RUST_LIB_BACKTRACE=1
set environment PYTHONFAULTHANDLER=1

# Handle crashes
handle SIGSEGV stop print
handle SIGABRT stop print  
handle SIGBUS stop print

# Set breakpoints on critical functions
break PyInterpreterState_Get
break PyErr_SetString
break Py_INCREF
break Py_DECREF

# Run the failing test
run test_hypothesis_verification.py

# When crashed, show comprehensive info
echo \\n=== CRASH ANALYSIS ===\\n
info program
info signals

echo \\n=== PYTHON STACKTRACE ===\\n
thread apply all bt

echo \\n=== REGISTERS ===\\n  
info registers

echo \\n=== MEMORY AROUND CRASH ===\\n
x/20i $pc-40
x/20wx $sp-80

echo \\n=== PYTHON FRAMES ===\\n
py-list
py-bt

quit
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gdb', delete=False) as f:
        f.write(gdb_script)
        gdb_script_path = f.name
    
    try:
        print("🛠️  Running Python 3.14 no-GIL under GDB...")
        
        cmd = [
            "gdb", 
            "-batch",
            "-x", gdb_script_path,
            "--args",
            str(python_nogil), "test_hypothesis_verification.py"
        ]
        
        env = os.environ.copy()
        env.update({
            "RUST_BACKTRACE": "full",
            "RUST_LIB_BACKTRACE": "1", 
            "PYTHONFAULTHANDLER": "1"
        })
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent,
            env=env,
            timeout=60
        )
        
        print("="*80)
        print("GDB CRASH ANALYSIS OUTPUT:")
        print("="*80)
        print(result.stdout)
        
        if result.stderr:
            print("="*80)
            print("GDB STDERR:")
            print("="*80)
            print(result.stderr)
            
        # Save detailed output
        crash_log = Path(__file__).parent / "crash_analysis.log"
        with open(crash_log, 'w') as f:
            f.write("PYTHON 3.14 NO-GIL CRASH ANALYSIS\\n")
            f.write("="*50 + "\\n")
            f.write(f"Command: {' '.join(cmd)}\\n")
            f.write(f"Return code: {result.returncode}\\n\\n")
            f.write("STDOUT:\\n")
            f.write(result.stdout)
            f.write("\\n\\nSTDERR:\\n")
            f.write(result.stderr)
        
        print(f"\\n📝 Detailed crash analysis saved to: {crash_log}")
        
    except subprocess.TimeoutExpired:
        print("❌ GDB session timed out (60 seconds)")
    except FileNotFoundError:
        print("❌ GDB not found. Install with: brew install gdb (macOS) or apt install gdb (Linux)")
    finally:
        os.unlink(gdb_script_path)

def debug_with_lldb():
    """Alternative debugging with LLDB (macOS default)"""
    project_root = Path(__file__).parent.parent.parent
    python_nogil = project_root / "cpython3.14.0rc1-nogil" / "bin" / "python3"
    
    print(f"🔍 Debugging with LLDB: {python_nogil}")
    
    # Create LLDB script
    lldb_script = f"""
env RUST_BACKTRACE=full
env RUST_LIB_BACKTRACE=1
env PYTHONFAULTHANDLER=1

process launch -- test_hypothesis_verification.py

# When crashed
thread backtrace all
register read
memory read --size 4 --format x --count 20 `$pc-40`
expression -- (void)PyRun_SimpleString("import traceback; traceback.print_stack()")

quit
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
        f.write(lldb_script)
        lldb_script_path = f.name
    
    try:
        cmd = [
            "lldb",
            "-s", lldb_script_path,
            str(python_nogil)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
            timeout=60
        )
        
        print("="*80)
        print("LLDB CRASH ANALYSIS OUTPUT:")
        print("="*80)
        print(result.stdout)
        
        if result.stderr:
            print("\\nLLDB STDERR:")
            print(result.stderr)
            
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ LLDB failed: {e}")
    finally:
        os.unlink(lldb_script_path)

def run_with_core_dump():
    """Enable core dumps and analyze them"""
    import resource
    
    # Enable core dumps
    resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    
    project_root = Path(__file__).parent.parent.parent
    python_nogil = project_root / "cpython3.14.0rc1-nogil" / "bin" / "python3"
    
    print("🗂️  Enabling core dumps and running test...")
    
    env = os.environ.copy()
    env.update({
        "RUST_BACKTRACE": "full",
        "PYTHONFAULTHANDLER": "1"
    })
    
    # Run and let it crash to generate core dump
    result = subprocess.run(
        [str(python_nogil), "test_hypothesis_verification.py"],
        cwd=Path(__file__).parent,
        env=env
    )
    
    print(f"Process exited with code: {result.returncode}")
    
    # Look for core dump
    core_files = list(Path(".").glob("core*"))
    if core_files:
        core_file = core_files[0]
        print(f"📄 Core dump found: {core_file}")
        
        # Analyze with GDB
        gdb_cmd = [
            "gdb", "-batch", 
            "-ex", "thread apply all bt",
            "-ex", "info registers", 
            "-ex", "quit",
            str(python_nogil), str(core_file)
        ]
        
        try:
            analysis = subprocess.run(gdb_cmd, capture_output=True, text=True)
            print("CORE DUMP ANALYSIS:")
            print(analysis.stdout)
        except FileNotFoundError:
            print("❌ GDB not available for core dump analysis")
    else:
        print("❌ No core dump generated")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "gdb":
            debug_python314_nogil_crash()
        elif sys.argv[1] == "lldb":
            debug_with_lldb()
        elif sys.argv[1] == "core":
            run_with_core_dump()
        else:
            print("Usage: python3 debug_crash.py [gdb|lldb|core]")
    else:
        print("Available debugging methods:")
        print("  python3 debug_crash.py gdb   # Debug with GDB")
        print("  python3 debug_crash.py lldb  # Debug with LLDB (macOS)")
        print("  python3 debug_crash.py core  # Generate and analyze core dump")