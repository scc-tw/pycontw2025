#!/bin/bash
# Demonstrate FFI race conditions: GIL vs no-GIL comparison

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python paths
GIL_PYTHON="${SCRIPT_DIR}/../../cpython3.13.5-gil/bin/python3"
NOGIL_PYTHON="${SCRIPT_DIR}/../../cpython3.13.5-nogil/bin/python3"

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to print section headers
print_header() {
    echo
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo
}

# Check Python versions
check_python() {
    local python_path=$1
    local python_name=$2
    
    if [ ! -f "$python_path" ]; then
        print_color "$RED" "✗ $python_name not found at $python_path"
        return 1
    else
        print_color "$GREEN" "✓ $python_name found"
        return 0
    fi
}

# Main execution
print_header "FFI Race Condition Demo: GIL vs No-GIL Comparison"

print_color "$BLUE" "Checking Python installations..."
echo

# Check both Python versions
gil_available=false
nogil_available=false

if check_python "$GIL_PYTHON" "Python 3.13.5 (with GIL)"; then
    gil_available=true
fi

if check_python "$NOGIL_PYTHON" "Python 3.13.5 (no-GIL)"; then
    nogil_available=true
fi

# If neither is available, provide instructions
if [ "$gil_available" = false ] && [ "$nogil_available" = false ]; then
    echo
    print_color "$RED" "Error: No Python versions found!"
    echo
    echo "Please build Python 3.13.5 with both configurations:"
    echo
    echo "1. With GIL (standard):"
    echo "   cd cpython-3.13.5"
    echo "   ./configure --prefix=\$(pwd)/../cpython3.13.5-gil"
    echo "   make -j\$(nproc) && make install"
    echo
    echo "2. Without GIL (experimental):"
    echo "   cd cpython-3.13.5"
    echo "   ./configure --disable-gil --prefix=\$(pwd)/../cpython3.13.5-nogil"
    echo "   make -j\$(nproc) && make install"
    exit 1
fi

# Build the C++ library
print_header "Building C++23 Thread Test Library"
make -C "$SCRIPT_DIR" clean all > /dev/null 2>&1
print_color "$GREEN" "✓ Library built successfully"

# Now using unified demo_race_condition.py for both modes

# Run tests with both Python versions if available
if [ "$gil_available" = true ]; then
    print_header "Testing with GIL-enabled Python (Standard)"
    
    print_color "$YELLOW" "Running race condition tests..."
    gil_output=$(cd "$SCRIPT_DIR" && uv run --python "$GIL_PYTHON" python demo_race_condition.py --json --iterations 5 2>/dev/null)
    
    # Parse results
    counter_races_gil=$(echo "$gil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['counter_test']['races_detected'])")
    fast_bank_races_gil=$(echo "$gil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['fast_bank_test']['races_detected'])")
    avg_accuracy_gil=$(echo "$gil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['counter_test']['avg_accuracy']:.1f}\")")
    
    echo
    print_color "$BLUE" "Results with GIL:"
    echo "  Counter Test:"
    echo "    • Race conditions detected: $counter_races_gil / 5"
    echo "    • Average accuracy: ${avg_accuracy_gil}%"
    echo "  Fast Bank Test (no sleep - GIL protected):"
    echo "    • Race conditions detected: $fast_bank_races_gil / 5"
    
    if [ "$counter_races_gil" -eq 0 ] && [ "$fast_bank_races_gil" -eq 0 ]; then
        print_color "$GREEN" "  ✓ GIL is protecting against races in fast operations (as expected)"
    else
        print_color "$YELLOW" "  ⚠ Some race conditions detected even with GIL"
    fi
fi

if [ "$nogil_available" = true ]; then
    print_header "Testing with No-GIL Python (Experimental)"
    
    print_color "$YELLOW" "Running race condition tests..."
    nogil_output=$(cd "$SCRIPT_DIR" && uv run --python "$NOGIL_PYTHON" python demo_race_condition.py --json --iterations 5 2>/dev/null)
    
    # Parse results
    counter_races_nogil=$(echo "$nogil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['counter_test']['races_detected'])")
    fast_bank_races_nogil=$(echo "$nogil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['fast_bank_test']['races_detected'])")
    avg_accuracy_nogil=$(echo "$nogil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data['counter_test']['avg_accuracy']:.1f}\")")
    avg_lost_nogil=$(echo "$nogil_output" | python3 -c "import sys, json; data=json.load(sys.stdin); print(int(data['counter_test']['avg_lost_increments']))")
    
    echo
    print_color "$BLUE" "Results without GIL:"
    echo "  Counter Test:"
    echo "    • Race conditions detected: $counter_races_nogil / 5"
    echo "    • Average accuracy: ${avg_accuracy_nogil}%"
    echo "    • Average lost increments: $avg_lost_nogil"
    echo "  Fast Bank Test (no sleep - TRUE PARALLELISM):"
    echo "    • Race conditions detected: $fast_bank_races_nogil / 5"
    
    if [ "$counter_races_nogil" -gt 0 ] || [ "$fast_bank_races_nogil" -gt 0 ]; then
        print_color "$RED" "  ⚠ RACE CONDITIONS EXPOSED! (as expected without GIL)"
    else
        print_color "$YELLOW" "  ⚠ Unexpected: No race conditions detected"
    fi
fi

# Comparison summary if both versions were tested
if [ "$gil_available" = true ] && [ "$nogil_available" = true ]; then
    print_header "Comparison Summary"
    
    echo -e "${BOLD}Impact of GIL on Race Condition Detection:${NC}"
    echo
    echo "                          │  With GIL  │ Without GIL │"
    echo "  ────────────────────────┼────────────┼─────────────┤"
    printf "  Counter Races           │     %d/5    │     %d/5     │\n" "$counter_races_gil" "$counter_races_nogil"
    printf "  Counter Accuracy        │   %5s%%   │   %5s%%    │\n" "$avg_accuracy_gil" "$avg_accuracy_nogil"
    printf "  Fast Bank (no sleep)    │     %d/5    │     %d/5     │\n" "$fast_bank_races_gil" "$fast_bank_races_nogil"
    echo "  ────────────────────────┴────────────┴─────────────┘"
    echo
    
    print_color "$MAGENTA" "Key Insights:"
    echo "  • GIL prevents true parallelism, masking race conditions"
    echo "  • No-GIL allows true parallelism, exposing race conditions"
    echo "  • Unsafe FFI code is dangerous with no-GIL Python"
    echo "  • Always use thread-safe implementations (mutex, atomic)"
fi

# Option to run full demo
echo
print_color "$CYAN" "To run the full interactive demo with Rich UI:"
if [ "$nogil_available" = true ]; then
    echo "  uv run --python $NOGIL_PYTHON python demo_race_condition.py"
else
    echo "  uv run python demo_race_condition.py"
fi

echo
print_color "$CYAN" "Command examples:"
echo "  Interactive Rich UI:    ./demo_race_condition.py"
echo "  JSON output for tests:  ./demo_race_condition.py --json"
echo "  Custom iterations:      ./demo_race_condition.py --json --iterations 10"

print_header "Demo Complete"