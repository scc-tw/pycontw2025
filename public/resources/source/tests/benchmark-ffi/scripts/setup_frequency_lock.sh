#!/bin/bash
# Quick CPU Frequency Locking Setup for Benchmarks
# 
# This script provides simple commands to lock/unlock CPU frequency
# for consistent benchmark performance.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK_SCRIPT="$SCRIPT_DIR/lock_cpu_frequency.py"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo -e "${BLUE}🔧 CPU Frequency Locking for Benchmarks${NC}"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  lock-max     Lock CPU to maximum frequency"
    echo "  lock [FREQ]  Lock CPU to specific frequency (Hz)"
    echo "  show         Show current CPU frequency status"
    echo "  restore      Restore original frequency settings"
    echo "  verify       Lock to max and verify stability (10s)"
    echo ""
    echo "Examples:"
    echo "  $0 lock-max                    # Lock to maximum frequency"
    echo "  $0 lock 2400000               # Lock to 2.4 GHz"
    echo "  $0 show                       # Show current status"
    echo "  $0 restore                    # Restore original settings"
    echo ""
    echo "For advanced options, use: python3 $LOCK_SCRIPT --help"
}

check_requirements() {
    if [[ ! -f "$LOCK_SCRIPT" ]]; then
        echo -e "${RED}❌ Lock script not found: $LOCK_SCRIPT${NC}"
        exit 1
    fi
    
    if [[ $EUID -eq 0 ]]; then
        echo -e "${RED}❌ Don't run this script as root. It will prompt for sudo when needed.${NC}"
        exit 1
    fi
    
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
}

lock_max_frequency() {
    echo -e "${GREEN}🚀 Locking CPU to maximum frequency...${NC}"
    python3 "$LOCK_SCRIPT" --lock-max --verify 5 --force || {
        echo -e "${RED}❌ Failed to lock frequency${NC}"
        exit 1
    }
}

lock_specific_frequency() {
    local freq="$1"
    
    # Validate frequency format
    if ! [[ "$freq" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}❌ Invalid frequency format. Use Hz (e.g., 2400000 for 2.4 GHz)${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🚀 Locking CPU to ${freq} Hz...${NC}"
    python3 "$LOCK_SCRIPT" --lock-freq "$freq" --verify 5 --force || {
        echo -e "${RED}❌ Failed to lock frequency${NC}"
        exit 1
    }
}

show_frequency_status() {
    echo -e "${BLUE}📊 Current CPU Frequency Status${NC}"
    python3 "$LOCK_SCRIPT" --show
}

restore_frequency() {
    echo -e "${YELLOW}🔄 Restoring original frequency settings...${NC}"
    python3 "$LOCK_SCRIPT" --restore || {
        echo -e "${RED}❌ Failed to restore frequency settings${NC}"
        exit 1
    }
}

verify_frequency_lock() {
    echo -e "${GREEN}🔍 Locking to maximum frequency and verifying stability...${NC}"
    python3 "$LOCK_SCRIPT" --lock-max --verify 10 --force || {
        echo -e "${RED}❌ Frequency lock verification failed${NC}"
        exit 1
    }
}

main() {
    check_requirements
    
    case "${1:-show}" in
        "lock-max")
            lock_max_frequency
            ;;
        "lock")
            if [[ $# -lt 2 ]]; then
                echo -e "${RED}❌ Frequency value required${NC}"
                echo "Usage: $0 lock <frequency_in_hz>"
                echo "Example: $0 lock 2400000"
                exit 1
            fi
            lock_specific_frequency "$2"
            ;;
        "show")
            show_frequency_status
            ;;
        "restore")
            restore_frequency
            ;;
        "verify")
            verify_frequency_lock
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"