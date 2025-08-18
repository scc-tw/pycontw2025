#!/bin/bash
# Automated CPU Isolation Configuration Helper
# Usage: sudo bash -c 'PARAMS="isolcpus=managed,2-7 nohz_full=2-7 rcu_nocbs=2-7 irqaffinity=0-1" && source /home/scc/git/pycon2025-ffi-hidden-corner/tests/benchmark-ffi/scripts/setup/arch/configure-isolation.sh'

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

PARAMS="${PARAMS:-isolcpus=managed,2-7 nohz_full=2-7 rcu_nocbs=2-7 irqaffinity=0-1}"

echo "🔧 Configuring CPU isolation: $PARAMS"

if [[ -d /boot/loader/entries ]]; then
    # systemd-boot
    echo "📋 Configuring systemd-boot..."
    entry=$(ls /boot/loader/entries/*.conf | head -n1)
    if [[ -n "$entry" ]]; then
        cp "$entry" "${entry}.bak.$(date +%s)"
        if grep -q "^options " "$entry"; then
            sed -i "s/^options \(.*\)$/options \1 $PARAMS/" "$entry"
        else
            echo "options $PARAMS" >> "$entry"
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
    cp /etc/default/grub /etc/default/grub.bak.$(date +%s)
    if grep -q '^GRUB_CMDLINE_LINUX_DEFAULT=' /etc/default/grub; then
        sed -i "s/^GRUB_CMDLINE_LINUX_DEFAULT=\"\(.*\)\"/GRUB_CMDLINE_LINUX_DEFAULT=\"\1 $PARAMS\"/" /etc/default/grub
    else
        echo "GRUB_CMDLINE_LINUX_DEFAULT=\"$PARAMS\"" >> /etc/default/grub
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
    echo "   $PARAMS"
    exit 1
fi

echo ""
echo "✅ CPU isolation configuration complete!"
echo "After reboot, verify with: cat /proc/cmdline"
