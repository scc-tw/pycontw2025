#!/bin/bash
set -euo pipefail

# Arch Linux Benchmark Environment Setup Script
# 
# This script configures your Arch Linux system for rigorous FFI performance benchmarking
# Based on requirements from validate_environment.py and academic performance standards
#
# REQUIRES: sudo privileges for system configuration
# TESTED ON: Arch Linux with systemd

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/benchmark-setup-$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

check_arch_linux() {
    if [[ ! -f /etc/arch-release ]]; then
        log_error "This script is designed for Arch Linux. Detected: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
        exit 1
    fi
    log_success "Running on Arch Linux"
}

check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Don't run this script as root directly. Use your regular user with sudo privileges."
        exit 1
    fi
    
    if ! sudo -n true 2>/dev/null; then
        log_info "This script requires sudo privileges. You may be prompted for your password."
        sudo -v || {
            log_error "Failed to get sudo privileges"
            exit 1
        }
    fi
    log_success "Sudo privileges confirmed"
}

install_required_packages() {
    log_info "Installing required packages for benchmarking..."
    
    # Update package database
    sudo pacman -Sy --noconfirm
    
    # Install required packages
    PACKAGES=(
        "cpupower"              # CPU frequency scaling control
        "linux-tools"           # perf and other kernel tools  
        "numactl"              # NUMA policy control
        "base-devel"           # gcc, make, pkg-config
        "python"               # Python 3
        "python-pip"           # pip for Python packages
        "python-numpy"         # NumPy for benchmarks
        "python-scipy"         # SciPy for statistics
        "python-matplotlib"    # For crossover analysis graphs
        "git"                  # Version control
        "htop"                 # System monitoring
        "iotop"                # I/O monitoring
        "sysstat"              # System statistics
    )
    
    for package in "${PACKAGES[@]}"; do
        if pacman -Qi "$package" >/dev/null 2>&1; then
            log_info "$package already installed"
        else
            log_info "Installing $package..."
            sudo pacman -S --needed --noconfirm "$package" || {
                log_warning "Failed to install $package, continuing..."
            }
        fi
    done
    
    log_success "Package installation completed"
}

configure_cpu_governor() {
    log_info "Configuring CPU governor for performance..."
    
    # Install cpupower if not already installed
    if ! command -v cpupower >/dev/null 2>&1; then
        log_info "Installing cpupower..."
        sudo pacman -S --needed --noconfirm cpupower
    fi
    
    # Set governor to performance
    log_info "Setting CPU governor to 'performance'..."
    sudo cpupower frequency-set -g performance || {
        log_warning "cpupower failed, trying manual sysfs approach..."
        
        # Manual approach for systems where cpupower doesn't work
        for policy in /sys/devices/system/cpu/cpufreq/policy*; do
            if [[ -f "$policy/scaling_governor" ]]; then
                echo performance | sudo tee "$policy/scaling_governor" >/dev/null
                log_info "Set policy $(basename "$policy") to performance"
            fi
        done
    }
    
    # Verify the setting
    current_governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "unknown")
    if [[ "$current_governor" == "performance" ]]; then
        log_success "CPU governor set to 'performance'"
    else
        log_warning "CPU governor is '$current_governor', expected 'performance'"
    fi
    
    # Create systemd service for persistent configuration
    log_info "Creating systemd service for persistent CPU performance settings..."
    
    sudo tee /etc/systemd/system/benchmark-cpu-performance.service >/dev/null <<'EOF'
[Unit]
Description=CPU Performance Settings for Benchmarking
After=multi-user.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/apply-benchmark-settings.sh

[Install]
WantedBy=multi-user.target
EOF

    # Create the actual settings script
    sudo tee /usr/local/bin/apply-benchmark-settings.sh >/dev/null <<'EOF'
#!/bin/bash
# Apply all benchmark-related system settings

# CPU Governor and Frequency Settings
for policy in /sys/devices/system/cpu/cpufreq/policy*; do
  [ -f "$policy/scaling_governor" ] && echo performance > "$policy/scaling_governor" 2>/dev/null || true
  [ -f "$policy/energy_performance_preference" ] && echo performance > "$policy/energy_performance_preference" 2>/dev/null || true
  # Lock frequency to maximum for consistency
  if [ -f "$policy/cpuinfo_max_freq" ]; then
    fmax=$(cat "$policy/cpuinfo_max_freq" 2>/dev/null || echo "")
    if [ -n "$fmax" ]; then
      # Try userspace governor for precise frequency locking
      if [ -f "$policy/scaling_available_governors" ] && grep -q "userspace" "$policy/scaling_available_governors" 2>/dev/null; then
        echo userspace > "$policy/scaling_governor" 2>/dev/null || true
        [ -f "$policy/scaling_setspeed" ] && echo "$fmax" > "$policy/scaling_setspeed" 2>/dev/null || true
      else
        # Fallback to performance governor with min/max constraints
        echo performance > "$policy/scaling_governor" 2>/dev/null || true
        [ -f "$policy/scaling_min_freq" ] && echo "$fmax" > "$policy/scaling_min_freq" 2>/dev/null || true
        [ -f "$policy/scaling_max_freq" ] && echo "$fmax" > "$policy/scaling_max_freq" 2>/dev/null || true
      fi
    fi
  fi
done

# Disable SMT/Hyper-Threading
[ -f /sys/devices/system/cpu/smt/control ] && echo off > /sys/devices/system/cpu/smt/control 2>/dev/null || true

# Disable Turbo Boost
[ -f /sys/devices/system/cpu/intel_pstate/no_turbo ] && echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || true
[ -f /sys/devices/system/cpu/cpufreq/boost ] && echo 0 > /sys/devices/system/cpu/cpufreq/boost 2>/dev/null || true

# Memory Settings
echo 0 > /proc/sys/kernel/randomize_va_space 2>/dev/null || true
echo 128 > /proc/sys/vm/nr_hugepages 2>/dev/null || true
[ -f /sys/kernel/mm/transparent_hugepage/enabled ] && echo madvise > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true

# Performance Counters
echo -1 > /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true

echo "Benchmark settings applied successfully"
EOF

    sudo chmod +x /usr/local/bin/apply-benchmark-settings.sh
    
    # Enable the service
    sudo systemctl enable benchmark-cpu-performance.service
    sudo systemctl start benchmark-cpu-performance.service
    
    log_success "CPU performance service created and enabled"
}

disable_smt_hyperthreading() {
    log_info "Checking SMT/Hyper-Threading configuration..."
    
    SMT_CONTROL="/sys/devices/system/cpu/smt/control"
    
    if [[ -f "$SMT_CONTROL" ]]; then
        current_smt=$(cat "$SMT_CONTROL" 2>/dev/null || echo "unknown")
        log_info "Current SMT status: $current_smt"
        
        if [[ "$current_smt" != "off" ]] && [[ "$current_smt" != "forceoff" ]] && [[ "$current_smt" != "notsupported" ]]; then
            log_info "Disabling SMT/Hyper-Threading for consistent performance..."
            
            # Try multiple approaches to disable SMT
            if echo off | sudo tee "$SMT_CONTROL" >/dev/null 2>&1; then
                log_success "SMT/Hyper-Threading disabled via sysfs"
            else
                log_warning "Failed to disable SMT via sysfs, trying alternative methods..."
                
                # Alternative: disable individual CPU threads
                log_info "Disabling sibling threads manually..."
                for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
                    if [[ -f "$cpu/topology/thread_siblings_list" ]]; then
                        siblings=$(cat "$cpu/topology/thread_siblings_list")
                        cpu_id=$(basename "$cpu" | sed 's/cpu//')
                        
                        # If this CPU has a sibling and it's the higher numbered one, disable it
                        if [[ "$siblings" == *","* ]]; then
                            first_cpu=$(echo "$siblings" | cut -d',' -f1)
                            if [[ "$cpu_id" != "$first_cpu" ]] && [[ -f "$cpu/online" ]]; then
                                echo 0 | sudo tee "$cpu/online" >/dev/null 2>&1 || true
                                log_info "Disabled CPU $cpu_id (sibling of CPU $first_cpu)"
                            fi
                        fi
                    fi
                done
                log_success "SMT/Hyper-Threading disabled via CPU offlining"
            fi
            
            # Verify the result
            new_smt=$(cat "$SMT_CONTROL" 2>/dev/null || echo "unknown")
            if [[ "$new_smt" == "off" ]] || [[ "$new_smt" == "forceoff" ]]; then
                log_success "SMT/Hyper-Threading successfully disabled"
            else
                log_warning "SMT status is now: $new_smt - may need manual intervention"
            fi
        else
            log_success "SMT/Hyper-Threading already disabled or not supported"
        fi
    else
        log_warning "SMT control not available on this system"
        
        # Try alternative CPU disabling approach
        log_info "Attempting manual sibling thread detection..."
        disabled_count=0
        for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
            if [[ -f "$cpu/topology/thread_siblings_list" ]]; then
                siblings=$(cat "$cpu/topology/thread_siblings_list")
                cpu_id=$(basename "$cpu" | sed 's/cpu//')
                
                if [[ "$siblings" == *","* ]]; then
                    first_cpu=$(echo "$siblings" | cut -d',' -f1)
                    if [[ "$cpu_id" != "$first_cpu" ]] && [[ -f "$cpu/online" ]]; then
                        if echo 0 | sudo tee "$cpu/online" >/dev/null 2>&1; then
                            ((disabled_count++))
                            log_info "Disabled CPU $cpu_id (sibling of CPU $first_cpu)"
                        fi
                    fi
                fi
            fi
        done
        
        if [[ $disabled_count -gt 0 ]]; then
            log_success "Disabled $disabled_count sibling threads manually"
        else
            log_warning "No sibling threads found or unable to disable"
        fi
    fi
    
    # SMT disable is already in the apply-benchmark-settings.sh script
}

disable_turbo_boost() {
    log_info "Disabling Turbo Boost for consistent performance..."
    
    # Intel Turbo Boost
    INTEL_TURBO="/sys/devices/system/cpu/intel_pstate/no_turbo"
    if [[ -f "$INTEL_TURBO" ]]; then
        echo 1 | sudo tee "$INTEL_TURBO" >/dev/null
        log_success "Intel Turbo Boost disabled"
    fi
    
    # AMD Boost
    AMD_BOOST="/sys/devices/system/cpu/cpufreq/boost"
    if [[ -f "$AMD_BOOST" ]]; then
        echo 0 | sudo tee "$AMD_BOOST" >/dev/null
        log_success "AMD CPU Boost disabled"
    fi
    
    if [[ ! -f "$INTEL_TURBO" && ! -f "$AMD_BOOST" ]]; then
        log_warning "Neither Intel nor AMD boost controls found"
    fi
}

configure_memory_settings() {
    log_info "Configuring memory settings for benchmarking..."
    
    # Disable ASLR temporarily for consistent memory layout
    log_info "Disabling ASLR for consistent memory layout..."
    ASLR_FILE="/proc/sys/kernel/randomize_va_space"
    current_aslr=$(cat "$ASLR_FILE" 2>/dev/null || echo "2")
    
    if [[ "$current_aslr" != "0" ]]; then
        if echo 0 | sudo tee "$ASLR_FILE" >/dev/null 2>&1; then
            log_success "ASLR disabled (was: $current_aslr)"
        else
            log_error "Failed to disable ASLR"
        fi
    else
        log_success "ASLR already disabled"
    fi
    
    # Verify ASLR is disabled
    new_aslr=$(cat "$ASLR_FILE" 2>/dev/null || echo "unknown")
    if [[ "$new_aslr" != "0" ]]; then
        log_warning "ASLR is still enabled (value: $new_aslr). This may affect benchmark consistency."
    fi
    
    # Configure huge pages
    log_info "Configuring huge pages..."
    HUGEPAGES_FILE="/proc/sys/vm/nr_hugepages"
    current_hugepages=$(cat "$HUGEPAGES_FILE" 2>/dev/null || echo "0")
    
    if [[ "$current_hugepages" -eq 0 ]] || [[ "$current_hugepages" -lt 128 ]]; then
        log_info "Allocating 128 huge pages..."
        if echo 128 | sudo tee "$HUGEPAGES_FILE" >/dev/null 2>&1; then
            actual_hugepages=$(cat "$HUGEPAGES_FILE")
            log_success "Allocated $actual_hugepages huge pages"
        else
            log_warning "Failed to allocate huge pages - may need to check system limits"
        fi
    else
        log_info "Huge pages already configured: $current_hugepages"
    fi
    
    # Configure transparent huge pages for madvise mode
    THP_FILE="/sys/kernel/mm/transparent_hugepage/enabled"
    if [[ -f "$THP_FILE" ]]; then
        log_info "Setting transparent huge pages to 'madvise' mode..."
        if echo madvise | sudo tee "$THP_FILE" >/dev/null 2>&1; then
            log_success "Transparent huge pages set to 'madvise'"
        else
            log_warning "Failed to configure transparent huge pages"
        fi
    fi
    
    # Memory settings are already in the apply-benchmark-settings.sh script
}

configure_perf_counters() {
    log_info "Configuring hardware performance counters..."
    
    # Enable perf counters for non-root users
    PERF_PARANOID="/proc/sys/kernel/perf_event_paranoid"
    current_paranoid=$(cat "$PERF_PARANOID")
    
    if [[ "$current_paranoid" != "-1" ]]; then
        log_info "Enabling hardware performance counters for non-root users..."
        echo -1 | sudo tee "$PERF_PARANOID" >/dev/null
        log_success "Hardware performance counters enabled"
    else
        log_success "Hardware performance counters already enabled"
    fi
    
    # Test perf functionality
    if command -v perf >/dev/null 2>&1; then
        if perf stat -e cycles true >/dev/null 2>&1; then
            log_success "perf functionality verified"
        else
            log_warning "perf test failed - may need kernel tools package"
        fi
    else
        log_warning "perf command not found - install linux-tools package"
    fi
}

optimize_disk_scheduler() {
    log_info "Optimizing disk scheduler for benchmarking..."
    
    for device in /sys/block/sd* /sys/block/nvme*; do
        if [[ -d "$device" ]]; then
            device_name=$(basename "$device")
            scheduler_file="$device/queue/scheduler"
            
            if [[ -f "$scheduler_file" ]]; then
                current_scheduler=$(cat "$scheduler_file")
                log_info "Current scheduler for $device_name: $current_scheduler"
                
                # Set to noop or none for minimal overhead
                if [[ "$current_scheduler" == *"[none]"* ]]; then
                    log_success "$device_name already using 'none' scheduler"
                elif [[ "$current_scheduler" == *"[noop]"* ]]; then
                    log_success "$device_name already using 'noop' scheduler"
                else
                    # Try to set to none first, then noop
                    if echo none | sudo tee "$scheduler_file" >/dev/null 2>&1; then
                        log_success "Set $device_name scheduler to 'none'"
                    elif echo noop | sudo tee "$scheduler_file" >/dev/null 2>&1; then
                        log_success "Set $device_name scheduler to 'noop'"
                    else
                        log_warning "Could not optimize scheduler for $device_name"
                    fi
                fi
            fi
        fi
    done
}

setup_cpu_isolation() {
    log_info "Checking CPU isolation configuration..."
    
    current_cmdline=$(cat /proc/cmdline)
    
    if [[ "$current_cmdline" == *"isolcpus="* ]]; then
        log_success "CPU isolation already configured"
        return
    fi
    
    # Detect CPU topology
    cpu_count=$(nproc)
    log_info "Detected $cpu_count CPU cores"
    
    if [[ $cpu_count -gt 4 ]]; then
        # Suggest isolating cores 2 onwards, leaving 0-1 for system
        if [[ $cpu_count -ge 8 ]]; then
            suggested_isolation="2-7"
        else
            suggested_isolation="2-$((cpu_count-1))"
        fi
        
        ISOLATION_PARAMS="isolcpus=managed,$suggested_isolation nohz_full=$suggested_isolation rcu_nocbs=$suggested_isolation irqaffinity=0-1"
        
        log_warning "CPU isolation not configured."
        log_info "For optimal benchmarking performance, CPU isolation is recommended."
        log_info "This will isolate CPUs $suggested_isolation for dedicated benchmark use."
        log_info ""
        
        # Detect bootloader and provide appropriate instructions
        if [[ -d /boot/loader/entries ]]; then
            # systemd-boot detected
            log_info "🔧 systemd-boot detected - CPU isolation setup:"
            log_info ""
            
            # Find the boot entry
            boot_entry=$(ls /boot/loader/entries/*.conf 2>/dev/null | head -n1)
            if [[ -n "$boot_entry" ]]; then
                log_info "1. Backup current boot entry:"
                log_info "   sudo cp \"$boot_entry\" \"${boot_entry}.bak.\$(date +%s)\""
                log_info ""
                log_info "2. Edit boot entry:"
                log_info "   sudo vim \"$boot_entry\""
                log_info ""
                log_info "3. Add to the 'options' line:"
                log_info "   $ISOLATION_PARAMS"
                log_info ""
                log_info "4. Update systemd-boot and reboot:"
                log_info "   sudo bootctl update"
                log_info "   sudo reboot"
            else
                log_warning "No systemd-boot entries found in /boot/loader/entries/"
                log_info "Manually add to your boot entry's options line:"
                log_info "   $ISOLATION_PARAMS"
            fi
            
        elif [[ -f /etc/default/grub ]]; then
            # GRUB detected
            log_info "🔧 GRUB detected - CPU isolation setup:"
            log_info ""
            log_info "1. Edit GRUB configuration:"
            log_info "   sudo vim /etc/default/grub"
            log_info ""
            log_info "2. Add to GRUB_CMDLINE_LINUX_DEFAULT:"
            log_info "   $ISOLATION_PARAMS"
            log_info ""
            log_info "3. Update GRUB and reboot:"
            log_info "   sudo grub-mkconfig -o /boot/grub/grub.cfg"
            log_info "   sudo reboot"
            
        else
            # Unknown bootloader
            log_warning "Unknown bootloader configuration."
            log_info "Add these parameters to your kernel command line:"
            log_info "   $ISOLATION_PARAMS"
        fi
        
        log_info ""
        log_info "📝 Alternative: Automated setup (advanced users):"
        log_info "   Run the automated bootloader configuration helper:"
        log_info "   sudo bash -c 'PARAMS=\"$ISOLATION_PARAMS\" && source $SCRIPT_DIR/configure-isolation.sh'"
        
        # Create automated helper script
        create_isolation_helper "$ISOLATION_PARAMS"
        
    else
        log_info "CPU isolation not recommended for systems with <= 4 cores"
    fi
}

create_isolation_helper() {
    local isolation_params="$1"
    log_info "Creating automated CPU isolation helper..."
    
    ISOLATION_HELPER="$SCRIPT_DIR/configure-isolation.sh"
    
    cat > "$ISOLATION_HELPER" <<EOF
#!/bin/bash
# Automated CPU Isolation Configuration Helper
# Usage: sudo bash -c 'PARAMS="$isolation_params" && source $SCRIPT_DIR/configure-isolation.sh'

set -euo pipefail

if [[ \$EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

PARAMS="\${PARAMS:-$isolation_params}"

echo "🔧 Configuring CPU isolation: \$PARAMS"

if [[ -d /boot/loader/entries ]]; then
    # systemd-boot
    echo "📋 Configuring systemd-boot..."
    entry=\$(ls /boot/loader/entries/*.conf | head -n1)
    if [[ -n "\$entry" ]]; then
        cp "\$entry" "\${entry}.bak.\$(date +%s)"
        if grep -q "^options " "\$entry"; then
            sed -i "s/^options \\(.*\\)\$/options \\1 \$PARAMS/" "\$entry"
        else
            echo "options \$PARAMS" >> "\$entry"
        fi
        bootctl update
        echo "✅ systemd-boot configuration updated"
        echo "🔄 Reboot required: sudo reboot"
    else
        echo "❌ No systemd-boot entries found"
        exit 1
    fi
    
elif [[ -f /etc/default/grub ]]; then
    # GRUB
    echo "📋 Configuring GRUB..."
    cp /etc/default/grub /etc/default/grub.bak.\$(date +%s)
    if grep -q '^GRUB_CMDLINE_LINUX_DEFAULT=' /etc/default/grub; then
        sed -i "s/^GRUB_CMDLINE_LINUX_DEFAULT=\"\\(.*\\)\"/GRUB_CMDLINE_LINUX_DEFAULT=\"\\1 \$PARAMS\"/" /etc/default/grub
    else
        echo "GRUB_CMDLINE_LINUX_DEFAULT=\"\$PARAMS\"" >> /etc/default/grub
    fi
    
    if command -v update-grub >/dev/null; then
        update-grub
    else
        grub-mkconfig -o /boot/grub/grub.cfg
    fi
    echo "✅ GRUB configuration updated"
    echo "🔄 Reboot required: sudo reboot"
    
else
    echo "❌ No known bootloader configuration found"
    echo "Add these parameters manually to your kernel command line:"
    echo "   \$PARAMS"
    exit 1
fi

echo ""
echo "✅ CPU isolation configuration complete!"
echo "After reboot, verify with: cat /proc/cmdline"
EOF
    
    chmod +x "$ISOLATION_HELPER"
    log_success "CPU isolation helper created at $ISOLATION_HELPER"
}

create_benchmark_wrapper() {
    log_info "Creating benchmark wrapper script..."
    
    WRAPPER_SCRIPT="/usr/local/bin/benchmark-runner"
    
    sudo tee "$WRAPPER_SCRIPT" >/dev/null <<'EOF'
#!/bin/bash
# Benchmark Runner Wrapper
# Automatically applies optimal settings for running benchmarks

set -euo pipefail

# Check if we're in the right directory
if [[ ! -f "scripts/validate_environment.py" ]]; then
    echo "❌ Run this from the benchmark-ffi directory containing scripts/validate_environment.py"
    exit 1
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Benchmark Runner - Arch Linux Optimized${NC}"
echo "=============================================="

# Validate environment first
echo -e "${YELLOW}🔬 Validating environment...${NC}"
if ! python scripts/validate_environment.py; then
    echo -e "${RED}❌ Environment validation failed!${NC}"
    echo "Run the setup script again or follow the remediation guide."
    exit 1
fi

echo -e "${GREEN}✅ Environment validation passed${NC}"

# Detect NUMA topology and suggest numactl usage
if command -v numactl >/dev/null 2>&1; then
    numa_nodes=$(numactl --hardware | grep "available:" | awk '{print $2}')
    if [[ "$numa_nodes" -gt 1 ]]; then
        echo -e "${YELLOW}🔧 NUMA system detected ($numa_nodes nodes)${NC}"
        echo "Consider running benchmarks with NUMA binding:"
        echo "  numactl --physcpubind=0-7 --membind=0 -- $*"
        echo ""
        
        read -p "Use NUMA binding? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}🎯 Running with NUMA binding...${NC}"
            exec numactl --physcpubind=0-7 --membind=0 -- "$@"
        fi
    fi
fi

# Run the command
echo -e "${GREEN}🏃 Running benchmark command: $*${NC}"
exec "$@"
EOF
    
    sudo chmod +x "$WRAPPER_SCRIPT"
    log_success "Benchmark wrapper created at $WRAPPER_SCRIPT"
}

create_monitoring_script() {
    log_info "Creating system monitoring script..."
    
    MONITOR_SCRIPT="$SCRIPT_DIR/monitor-system.sh"
    
    cat > "$MONITOR_SCRIPT" <<'EOF'
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
EOF
    
    chmod +x "$MONITOR_SCRIPT"
    log_success "System monitor created at $MONITOR_SCRIPT"
}

print_summary() {
    log_info "Setup Summary"
    echo "============="
    echo ""
    echo "✅ Arch Linux benchmarking environment configured successfully!"
    echo ""
    echo "📋 Configuration Applied:"
    echo "   • CPU governor set to 'performance'"
    echo "   • SMT/Hyper-Threading disabled"
    echo "   • Turbo Boost disabled"
    echo "   • ASLR disabled (temporary)"
    echo "   • Huge pages configured"
    echo "   • Hardware performance counters enabled"
    echo "   • Disk scheduler optimized"
    echo "   • Required packages installed"
    echo ""
    echo "🛠️  Tools Created:"
    echo "   • Benchmark wrapper: /usr/local/bin/benchmark-runner"
    echo "   • System monitor: $SCRIPT_DIR/monitor-system.sh"
    echo "   • Frequency locking: tests/benchmark-ffi/scripts/setup_frequency_lock.sh"
    echo "   • Advanced frequency control: tests/benchmark-ffi/scripts/lock_cpu_frequency.py"
    echo "   • Setup log: $LOG_FILE"
    echo ""
    echo "🚀 Usage Examples:"
    echo "   # Validate environment"
    echo "   python scripts/validate_environment.py"
    echo ""
    echo "   # Run benchmarks with wrapper"
    echo "   benchmark-runner python scripts/plt_aware_benchmark.py"
    echo ""
    echo "   # Monitor system during benchmarks"
    echo "   $SCRIPT_DIR/monitor-system.sh"
    echo ""
    echo "   # Generate all evidence"
    echo "   benchmark-runner python scripts/generate_all_evidence.py"
    echo ""
    echo "   # Lock CPU frequency for maximum consistency"
    echo "   tests/benchmark-ffi/scripts/setup_frequency_lock.sh lock-max"
    echo "   tests/benchmark-ffi/scripts/setup_frequency_lock.sh show"
    echo "   tests/benchmark-ffi/scripts/setup_frequency_lock.sh restore"
    echo ""
    
    if [[ ! "$current_cmdline" == *"isolcpus="* ]]; then
        echo "⚠️  CPU Isolation Not Configured:"
        echo "   For maximum performance, consider configuring CPU isolation"
        echo "   See the CPU isolation section in the setup log for instructions."
        echo ""
    fi
    
    echo "📖 Next Steps:"
    echo "   1. Validate environment: python scripts/validate_environment.py"
    echo "   2. Run PLT cache benchmarks: python scripts/plt_aware_benchmark.py"
    echo "   3. Generate statistical analysis: python scripts/run_statistical_analysis.py"
    echo "   4. Review results in the results/ directory"
    echo ""
    echo "🔗 Log file saved to: $LOG_FILE"
}

apply_all_settings_now() {
    log_info "Applying all benchmark settings immediately..."
    
    # Run the settings script we created
    if [[ -f /usr/local/bin/apply-benchmark-settings.sh ]]; then
        if sudo /usr/local/bin/apply-benchmark-settings.sh; then
            log_success "All benchmark settings applied successfully"
        else
            log_warning "Some settings may have failed to apply"
        fi
    fi
    
    # Restart the systemd service to ensure persistence
    sudo systemctl daemon-reload
    sudo systemctl restart benchmark-cpu-performance.service || true
}

main() {
    log_info "Starting Arch Linux FFI Benchmark Environment Setup"
    log_info "Log file: $LOG_FILE"
    echo ""
    
    check_arch_linux
    check_sudo
    install_required_packages
    configure_cpu_governor
    disable_smt_hyperthreading
    disable_turbo_boost
    configure_memory_settings
    configure_perf_counters
    optimize_disk_scheduler
    setup_cpu_isolation
    create_benchmark_wrapper
    create_monitoring_script
    
    # Apply all settings immediately
    apply_all_settings_now
    
    echo ""
    print_summary
}

# Run main function
main "$@"