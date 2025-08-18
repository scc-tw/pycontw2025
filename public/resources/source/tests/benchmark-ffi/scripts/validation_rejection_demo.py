#!/usr/bin/env python3
"""Validation Rejection Demo - Show validation actually rejecting bad results"""

import sys
import time
import json
from pathlib import Path
import subprocess

# Add framework to path  
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.realtime_monitor import create_realtime_monitor
from scripts.validate_environment import EnvironmentValidator

def simulate_bad_environment_conditions():
    """Simulate bad environment conditions to trigger validation rejection."""
    
    print("🧪 DEMONSTRATING VALIDATION REJECTION")
    print("=" * 50)
    
    # Test 1: Environment Validator Rejection
    print("\n1️⃣ ENVIRONMENT VALIDATOR REJECTION TEST")
    print("-" * 40)
    
    validator = EnvironmentValidator()
    
    # Inject fake bad conditions for demo
    original_check_governor = validator._check_cpu_governor
    original_check_temp = validator._check_thermal_state
    
    def fake_bad_governor():
        validator.errors.append("CPU governor set to 'powersave' instead of 'performance' (DEMO)")
        print("   ❌ Simulated bad CPU governor condition")
    
    def fake_high_temp():
        validator.errors.append("CPU temperature 85.2°C exceeds 80°C threshold (DEMO)")
        print("   ❌ Simulated high temperature condition")
    
    # Replace methods with demo versions
    validator._check_cpu_governor = fake_bad_governor
    validator._check_thermal_state = fake_high_temp
    
    print("🔧 Running validation with simulated bad conditions...")
    validation_passed = validator.validate_all()
    
    if not validation_passed:
        print("\n✅ VALIDATION CORRECTLY REJECTED BAD CONDITIONS!")
        print("🚨 Benchmark would be BLOCKED from running")
        print(f"📋 Errors detected: {len(validator.errors)}")
        for error in validator.errors:
            print(f"   • {error}")
    else:
        print("\n❌ VALIDATION FAILED TO REJECT - This would be a bug!")
    
    # Test 2: Real-time Monitor Abortion
    print("\n2️⃣ REAL-TIME MONITOR ABORTION TEST")
    print("-" * 40)
    
    # Create monitor with very strict thresholds
    monitor = create_realtime_monitor(
        temp_threshold=30.0,  # Impossibly low threshold
        load_threshold=0.1,   # Very low load threshold
        memory_threshold=50.0, # Low memory threshold
        check_interval=0.5
    )
    
    print("🔧 Starting monitor with strict thresholds (will trigger abort)...")
    
    abort_triggered = False
    abort_reason = ""
    
    def on_abort(reason):
        nonlocal abort_triggered, abort_reason
        abort_triggered = True
        abort_reason = reason
        print(f"🚨 ABORT CALLBACK TRIGGERED: {reason}")
    
    monitor.on_abort = on_abort
    
    if monitor.start_monitoring():
        print("📊 Monitoring for 3 seconds...")
        
        # Wait for abort to trigger
        for i in range(6):  # 6 * 0.5s = 3s
            time.sleep(0.5)
            
            should_abort, reason = monitor.should_abort()
            if should_abort:
                print(f"\n✅ MONITOR CORRECTLY TRIGGERED ABORT!")
                print(f"❌ Benchmark would be terminated: {reason}")
                break
            
            print(f"   {i+1}/6: Monitoring...")
        
        monitor.stop_monitoring()
        
        if abort_triggered:
            print("\n🎯 REAL-TIME MONITORING ABORTION SUCCESSFUL")
        else:
            print("\n⚠️ Abort not triggered - thresholds may need adjustment")
    
    return validation_passed == False and abort_triggered  # Success if validation rejected AND abort triggered

if __name__ == "__main__":
    try:
        success = simulate_bad_environment_conditions()
        if success:
            print("\n✅ VALIDATION REJECTION DEMO SUCCESSFUL")
            print("🛡️ System correctly blocks execution under bad conditions")
        else:
            print("\n⚠️ Demo results mixed - some protection mechanisms may need tuning")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
