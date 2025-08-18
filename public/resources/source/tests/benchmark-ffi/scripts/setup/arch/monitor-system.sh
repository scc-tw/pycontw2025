#!/bin/bash
# System Monitoring for Benchmarks
# Shows key system metrics during benchmark runs

set -euo pipefail

echo "🔬 System Monitor for FFI Benchmarks"
echo "===================================="
echo "Press Ctrl+C to stop monitoring"
echo ""

trap 'echo "Monitoring stopped."; exit 0' INT

while true; do
    clear
    echo "🔬 System Monitor - $(date)"
    echo "===================================="
    
    # CPU Information
    echo "🖥️  CPU Status:"
    governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
    echo "   Governor: $governor"
    
    if [[ -f /sys/devices/system/cpu/smt/control ]]; then
        smt_status=$(cat /sys/devices/system/cpu/smt/control)
        echo "   SMT: $smt_status"
    fi
    
    # Temperature
    if [[ -d /sys/class/thermal ]]; then
        max_temp=0
        for thermal in /sys/class/thermal/thermal_zone*/temp; do
            if [[ -f "$thermal" ]]; then
                temp=$(($(cat "$thermal") / 1000))
                if [[ $temp -gt $max_temp ]]; then
                    max_temp=$temp
                fi
            fi
        done
        echo "   Temperature: ${max_temp}°C"
    fi
    
    # Load Average
    load_avg=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
    echo "   Load Average: $load_avg"
    
    # Memory Usage
    mem_info=$(free -h | grep Mem:)
    echo "   Memory: $mem_info"
    
    echo ""
    echo "📊 Performance Counters (last 1 second):"
    if command -v perf >/dev/null 2>&1 && [[ $(cat /proc/sys/kernel/perf_event_paranoid) -le 1 ]]; then
        timeout 1s perf stat -e cycles,instructions,cache-references,cache-misses sleep 1 2>&1 | grep -E "(cycles|instructions|cache)" | head -4 || echo "   (perf monitoring failed)"
    else
        echo "   (perf not available or permissions insufficient)"
    fi
    
    echo ""
    echo "🔄 Updating in 2 seconds... (Ctrl+C to stop)"
    sleep 2
done
