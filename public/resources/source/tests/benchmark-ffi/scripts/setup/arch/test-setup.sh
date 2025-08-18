#!/bin/bash
# Test script to verify the Arch Linux setup works correctly
# This is a dry-run test that doesn't require sudo

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Testing Arch Linux Benchmark Setup${NC}"
echo "====================================="
echo ""

test_count=0
pass_count=0
fail_count=0

test_check() {
    local description="$1"
    local command="$2"
    
    test_count=$((test_count + 1))
    echo -n "Testing: $description... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}❌ FAIL${NC}"
        fail_count=$((fail_count + 1))
    fi
}

# Test 1: Check if we're on Arch Linux
test_check "Arch Linux detection" "test -f /etc/arch-release"

# Test 2: Check pacman availability
test_check "Package manager (pacman)" "command -v pacman"

# Test 3: Check required system files
test_check "CPU frequency control files" "test -d /sys/devices/system/cpu/cpu0/cpufreq"

# Test 4: Check thermal monitoring
test_check "Thermal monitoring files" "test -d /sys/class/thermal"

# Test 5: Check memory info files
test_check "Memory information files" "test -f /proc/meminfo"

# Test 6: Check if user has sudo access (without actually using it)
test_check "Sudo configuration" "sudo -n true || groups | grep -q sudo || groups | grep -q wheel"

# Test 7: Check systemd availability
test_check "Systemd availability" "command -v systemctl"

# Test 8: Check if we can read CPU governor
test_check "CPU governor readable" "test -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"

# Test 9: Check kernel command line access
test_check "Kernel command line access" "test -r /proc/cmdline"

# Test 10: Check if perf_event_paranoid is accessible
test_check "Perf paranoid settings" "test -r /proc/sys/kernel/perf_event_paranoid"

echo ""
echo "==================================="
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "==================================="
echo "Total tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo ""

if [[ $fail_count -eq 0 ]]; then
    echo -e "${GREEN}🎉 All tests passed! Your system is compatible with the Arch Linux setup script.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: ./setup-benchmarking.sh"
    echo "2. Validate: python ../../validate_environment.py"
    echo "3. Test benchmarks: python ../../plt_aware_benchmark.py"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Your system may not be fully compatible.${NC}"
    echo ""
    echo "Common issues:"
    echo "• Not running on Arch Linux"
    echo "• User not in sudo/wheel group"
    echo "• Missing systemd or sysfs files"
    echo ""
    echo "You can still try running the setup script, but some features may not work."
    exit 1
fi