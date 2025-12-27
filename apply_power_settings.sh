#!/bin/bash
# Script to apply power management settings
# Run this script to ensure screen turns off after 20 min and system never sleeps

# Set screen blanking to 20 minutes (1200 seconds)
export DISPLAY=:0
gsettings set org.gnome.desktop.session idle-delay 1200 2>/dev/null || echo "Note: gsettings may require GUI session"

# Disable sleep when inactive
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 2>/dev/null
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0 2>/dev/null

# Verify settings
echo "Screen blanking timeout: $(gsettings get org.gnome.desktop.session idle-delay 2>/dev/null || echo 'N/A')"
echo "AC sleep timeout: $(gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 2>/dev/null || echo 'N/A')"
echo "Battery sleep timeout: $(gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 2>/dev/null || echo 'N/A')"

echo ""
echo "Power management configuration complete!"
echo "Screen will turn off after 20 minutes, but system will remain awake for SSH access."


