#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

echo "Setting up open internet access for container..."

# Clear any existing restrictive rules
iptables -F 2>/dev/null || true
iptables -X 2>/dev/null || true
iptables -t nat -F 2>/dev/null || true
iptables -t nat -X 2>/dev/null || true

# Set permissive default policies for full internet access
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT  
iptables -P OUTPUT ACCEPT

# Allow all loopback traffic
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow all established and related connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT

echo "Firewall configured for full internet access"

# Test internet connectivity
echo "Testing internet connectivity..."
if curl --connect-timeout 10 -s https://httpbin.org/ip >/dev/null 2>&1; then
    echo "✅ Internet access confirmed - can reach external sites"
else
    echo "❌ Internet access test failed"
    exit 1
fi

# Test multiple endpoints to verify broad access
for url in "https://google.com" "https://github.com" "https://registry.npmjs.org"; do
    if curl --connect-timeout 5 -s "$url" >/dev/null 2>&1; then
        echo "✅ Successfully reached $url"
    else
        echo "⚠️  Could not reach $url"
    fi
done

echo "🎉 Full internet access configured successfully!"