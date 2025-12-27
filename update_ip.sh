#!/bin/bash
# Script to update IP address in address file and push to GitHub
# This script detects IP changes and automatically updates GitHub

REPO_DIR="/home/trex/Downloads/printing"
ADDRESS_FILE="$REPO_DIR/address"
cd "$REPO_DIR"

# Get current primary IP address (IPv4, excluding loopback and docker)
CURRENT_IP=$(ip addr show | grep -E "inet.*scope global" | grep -v "inet6" | grep -v "172.17\|172.18\|100\." | awk '{print $2}' | cut -d/ -f1 | head -1)

# If no IP found with that filter, get any IPv4 global IP
if [ -z "$CURRENT_IP" ]; then
    CURRENT_IP=$(ip addr show | grep -E "inet.*scope global" | grep -v "inet6" | awk '{print $2}' | cut -d/ -f1 | head -1)
fi

if [ -z "$CURRENT_IP" ]; then
    echo "Error: Could not determine IP address"
    exit 1
fi

# Read current IP from file
if [ -f "$ADDRESS_FILE" ]; then
    OLD_IP=$(cat "$ADDRESS_FILE" | head -1 | tr -d '[:space:]')
else
    OLD_IP=""
fi

# Update file if IP has changed
if [ "$CURRENT_IP" != "$OLD_IP" ]; then
    echo "IP address changed from $OLD_IP to $CURRENT_IP"
    echo "$CURRENT_IP" > "$ADDRESS_FILE"
    
    # Add, commit, and push to GitHub
    cd "$REPO_DIR"
    git add address
    git commit -m "Update IP address to $CURRENT_IP" 2>&1
    
    # Only push if there's something to push
    if git diff --quiet HEAD origin/master 2>/dev/null || [ -z "$(git log HEAD ^origin/master 2>/dev/null)" ]; then
        git push origin master 2>&1
        echo "IP address updated and pushed to GitHub: $CURRENT_IP"
    else
        git push origin master 2>&1
        echo "IP address updated and pushed to GitHub: $CURRENT_IP"
    fi
else
    echo "IP address unchanged: $CURRENT_IP"
fi

