#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

echo "Setting up custom firewall with Docker integration and full internet access..."

# Save Docker's existing NAT rules before any changes
DOCKER_NAT_RULES=$(iptables-save -t nat | grep -E "(DOCKER|MASQUERADE)" || true)
DOCKER_FILTER_RULES=$(iptables-save -t filter | grep "DOCKER" || true)

# Clear only user-defined rules, preserve Docker chains
iptables -F INPUT 2>/dev/null || true
iptables -F OUTPUT 2>/dev/null || true

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

# If you want to add any custom restrictions, use DOCKER-USER chain instead:
# Example (commented out): Block specific outgoing port
# iptables -I DOCKER-USER -p tcp --dport 25 -j DROP

# Allow all DNS queries (essential for internet access)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT -p udp --sport 53 -j ACCEPT
iptables -A INPUT -p tcp --sport 53 -j ACCEPT

# Allow standard HTTP/HTTPS traffic
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --sport 80 -m state --state ESTABLISHED -j ACCEPT  
iptables -A INPUT -p tcp --sport 443 -m state --state ESTABLISHED -j ACCEPT

# Allow all other outbound traffic (full internet access)
iptables -A OUTPUT -j ACCEPT

echo "Custom firewall rules applied with full internet access"

# Test internet connectivity
echo "Testing internet connectivity..."
if curl --connect-timeout 10 -s https://httpbin.org/ip >/dev/null 2>&1; then
    echo "✅ Internet access confirmed"
else
    echo "❌ Internet access test failed"
    exit 1
fi

echo "🎉 Custom firewall configured with full internet access!"