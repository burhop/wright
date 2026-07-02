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

# 3. Configure the wright profile for native API gateway
echo "Configuring the Wright profile..."
hermes -p wright config set API_SERVER_ENABLED true
hermes -p wright config set API_SERVER_KEY "wright-local-dev-key-000000000000000000000000"
hermes -p wright config set API_SERVER_PORT 8642

# 4. Check if wright gateway is already running on port 8642
echo "Checking if Hermes gateway is running on port 8642..."
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8642/health | grep -q "200"; then
    echo "Hermes gateway is already running on port 8642."
else
    echo "Hermes gateway is not running on port 8642. Starting it..."
    # Ensure HERMES_HOME points to the wright profile directory
    export HERMES_HOME="$HOME/.hermes/profiles/wright"
    hermes -p wright gateway start
    
    # Wait for the gateway to start
    echo "Waiting for gateway to boot..."
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8642/health | grep -q "200"; then
            echo "Gateway is up and running!"
            break
        fi
        if [ "$i" -eq 10 ]; then
            echo "Error: Gateway failed to start within 10 seconds."
            exit 1
        fi
        sleep 1
    done
fi

echo "=== Wright Hermes Profile Setup Complete ==="
exit 0
