#!/usr/bin/env bash
set -euo pipefail

# Scripts directory setup: make sure it exists
# (this script is located in repos/wright/scripts/setup-wright-profile.sh)

echo "=== Setting up Wright Hermes Profile ==="

# 1. Check if hermes is installed
if ! command -v hermes &> /dev/null; then
    echo "Error: hermes CLI is not installed or not in PATH."
    exit 1
fi

# 2. Check if wright profile exists, if not create it
if hermes profile list | grep -q "wright"; then
    echo "Wright profile already exists."
else
    echo "Wright profile does not exist. Creating it by cloning the default profile..."
    hermes profile create wright --clone --description "Wright engineering assistant"
    echo "Wright profile created successfully."
fi

# 3. Check if wright WebUI is already running on port 8788
echo "Checking if Hermes WebUI is running on port 8788..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8788/health | grep -q "200"; then
    echo "Hermes WebUI is already running on port 8788."
else
    echo "Hermes WebUI is not running on port 8788. Starting it..."
    # Ensure HERMES_HOME points to the wright profile directory
    export HERMES_HOME="$HOME/.hermes/profiles/wright"
    /home/burhop/hermes-webui/ctl.sh start 8788
    
    # Wait for the WebUI to start
    echo "Waiting for WebUI to boot..."
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8788/health | grep -q "200"; then
            echo "WebUI is up and running!"
            break
        fi
        if [ "$i" -eq 10 ]; then
            echo "Error: WebUI failed to start within 10 seconds."
            exit 1
        fi
        sleep 1
    done
fi

echo "=== Wright Hermes Profile Setup Complete ==="
exit 0
