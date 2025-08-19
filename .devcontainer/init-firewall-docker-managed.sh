#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

echo "Configuring Docker-managed networking for full internet access..."

# Create Docker daemon config to ensure iptables management is enabled
DAEMON_CONFIG="/etc/docker/daemon.json"

# Read existing config or create new one
if [ -f "$DAEMON_CONFIG" ]; then
    # Backup existing config
    cp "$DAEMON_CONFIG" "${DAEMON_CONFIG}.backup.$(date +%s)"
    
    # Add iptables: true to existing config
    jq '. + {"iptables": true}' "$DAEMON_CONFIG" > "${DAEMON_CONFIG}.tmp" && mv "${DAEMON_CONFIG}.tmp" "$DAEMON_CONFIG"
else
    # Create new config with iptables enabled
    echo '{"iptables": true}' > "$DAEMON_CONFIG"
fi

echo "Docker daemon.json updated to enable iptables management"

# Restart Docker to apply changes
if systemctl is-active --quiet docker; then
    echo "Restarting Docker service..."
    systemctl restart docker
    sleep 5  # Wait for Docker to restart
else
    echo "Starting Docker service..."
    systemctl start docker
    sleep 5
fi

# Clear any existing custom rules that might interfere
iptables -F DOCKER-USER 2>/dev/null || true

# Set permissive policies (Docker will manage the specifics)
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

echo "Docker networking configured for full internet access"

# Test connectivity
echo "Testing internet connectivity..."
sleep 3  # Give Docker time to set up networking

if curl --connect-timeout 10 -s https://httpbin.org/ip >/dev/null 2>&1; then
    echo "✅ Internet access confirmed"
    
    # Show Docker network info
    echo "Docker bridge network:"
    docker network inspect bridge --format '{{.IPAM.Config}}' 2>/dev/null || echo "Bridge network info not available"
else
    echo "❌ Internet access test failed"
    echo "Docker may need more time to initialize networking"
fi

echo "🎉 Docker-managed networking configured for full internet access!"