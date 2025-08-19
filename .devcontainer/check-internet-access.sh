#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Senior Engineer Level: Internet Access Diagnostic Tool
# This script ONLY checks connectivity without modifying any firewall rules
# Safe to run in any environment

echo "🔍 Internet Access Diagnostic Tool"
echo "=================================="
echo "This tool checks your current internet connectivity without making changes"
echo ""

# Function to check if we're in a container
is_container() {
    [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null
}

# Function to test DNS resolution
test_dns() {
    echo "🔍 Testing DNS Resolution..."
    
    dns_servers=("8.8.8.8" "1.1.1.1" "208.67.222.222")
    dns_working=false
    
    for dns in "${dns_servers[@]}"; do
        if nslookup google.com "$dns" >/dev/null 2>&1; then
            echo "✅ DNS working via $dns"
            dns_working=true
            break
        fi
    done
    
    if ! $dns_working; then
        echo "❌ DNS resolution failed on all tested servers"
        echo "💡 This is likely the root cause of internet access issues"
        return 1
    fi
    
    return 0
}

# Function to test HTTP connectivity
test_http_connectivity() {
    echo ""
    echo "🌐 Testing HTTP/HTTPS Connectivity..."
    
    # Test different types of sites
    test_sites=(
        "https://httpbin.org/ip|JSON API"
        "https://www.google.com|Search Engine"
        "https://github.com|Code Repository" 
        "https://registry.npmjs.org|Package Registry"
        "http://neverssl.com|Plain HTTP"
        "https://api.github.com/zen|API Endpoint"
    )
    
    working_sites=0
    total_sites=${#test_sites[@]}
    
    for site_info in "${test_sites[@]}"; do
        url=$(echo "$site_info" | cut -d'|' -f1)
        description=$(echo "$site_info" | cut -d'|' -f2)
        
        echo -n "  Testing $description ($url)... "
        
        if timeout 10 curl -s --max-time 8 --connect-timeout 5 "$url" >/dev/null 2>&1; then
            echo "✅"
            ((working_sites++))
        else
            echo "❌"
        fi
    done
    
    echo ""
    echo "📊 Connectivity Results: $working_sites/$total_sites sites reachable"
    
    if [ $working_sites -eq $total_sites ]; then
        echo "🎉 EXCELLENT: Full internet access confirmed!"
        return 0
    elif [ $working_sites -gt $((total_sites / 2)) ]; then
        echo "✅ GOOD: Most sites reachable, internet access is working"
        return 0
    elif [ $working_sites -gt 0 ]; then
        echo "⚠️ PARTIAL: Some connectivity, but restrictions may be present"
        return 1
    else
        echo "❌ BLOCKED: No sites reachable, internet access is blocked"
        return 2
    fi
}

# Function to show network configuration
show_network_config() {
    echo ""
    echo "📋 Current Network Configuration:"
    echo "================================="
    
    # Environment detection
    if is_container; then
        echo "📦 Environment: Container"
        if [[ -f /.dockerenv ]]; then
            echo "🐳 Docker container detected"
        fi
    else
        echo "🖥️ Environment: Host system"
    fi
    
    # Network interfaces
    echo ""
    echo "🔌 Network Interfaces:"
    if command -v ip >/dev/null 2>&1; then
        ip addr show | grep -E "^[0-9]+:|inet " | head -10
    else
        ifconfig 2>/dev/null | grep -E "^[a-z]|inet " | head -10 || echo "  Network info not available"
    fi
    
    # Default routes
    echo ""
    echo "🛣️ Routing Information:"
    if command -v ip >/dev/null 2>&1; then
        ip route show 2>/dev/null | head -5 || echo "  Route info not available"
    else
        route -n 2>/dev/null | head -5 || echo "  Route info not available"
    fi
    
    # DNS configuration
    echo ""
    echo "🔍 DNS Configuration:"
    if [[ -f /etc/resolv.conf ]]; then
        echo "  From /etc/resolv.conf:"
        grep -E "^nameserver|^search" /etc/resolv.conf 2>/dev/null | head -5 || echo "  No DNS servers configured"
    else
        echo "  /etc/resolv.conf not found"
    fi
    
    # Docker networking (if applicable)
    if ! is_container && command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        echo ""
        echo "🐳 Docker Network Status:"
        docker network ls 2>/dev/null | head -5 || echo "  Docker network info not available"
        
        if ip link show docker0 >/dev/null 2>&1; then
            docker0_info=$(ip addr show docker0 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -1)
            echo "🌉 Docker bridge: ${docker0_info:-not configured}"
        fi
    fi
    
    # Firewall status
    echo ""
    echo "🔥 Firewall Status:"
    if command -v iptables >/dev/null 2>&1; then
        echo "  Default policies:"
        for chain in INPUT OUTPUT FORWARD; do
            policy=$(iptables -L "$chain" 2>/dev/null | head -1 | awk '{print $4}' | tr -d '()' 2>/dev/null || echo "unknown")
            echo "    $chain: $policy"
        done
        
        # Check for Docker chains
        if iptables -t filter -L DOCKER-USER >/dev/null 2>&1; then
            echo "  ✅ DOCKER-USER chain exists"
        else
            echo "  ⚠️ DOCKER-USER chain missing"
        fi
    else
        echo "  iptables not available"
    fi
}

# Function to provide recommendations
provide_recommendations() {
    local dns_ok=$1
    local http_ok=$2
    
    echo ""
    echo "💡 Recommendations:"
    echo "=================="
    
    if ! $dns_ok; then
        echo "🔧 DNS Issues Detected:"
        echo "  1. Check /etc/resolv.conf for valid DNS servers"
        echo "  2. Try setting DNS manually: echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
        echo "  3. Restart network service or Docker daemon"
        echo ""
    fi
    
    if ! $http_ok; then
        echo "🔧 HTTP Connectivity Issues:"
        echo "  1. Check if you're behind a corporate firewall/proxy"
        echo "  2. Verify firewall rules are not blocking outbound traffic"
        echo "  3. For Docker containers, ensure Docker daemon has internet access"
        echo "  4. Check if specific ports (80, 443) are blocked"
        echo ""
    fi
    
    echo "🛠️ Next Steps:"
    if is_container; then
        echo "  For containers:"
        echo "  • Internet access is controlled by the host Docker daemon"
        echo "  • Contact your system administrator if access is blocked"
        echo "  • Verify the host system has internet connectivity"
    else
        echo "  For host systems:"
        echo "  • Run the Docker-aware firewall script to enable access"
        echo "  • Check network configuration and routing"
        echo "  • Verify external network connectivity"
    fi
    
    echo ""
    echo "📞 Support Information:"
    echo "  • This diagnostic can be shared with your system administrator"
    echo "  • Include the network configuration above when reporting issues"
    echo "  • Check Docker documentation: https://docs.docker.com/network/"
}

# Main execution
echo "🚀 Starting Internet Access Diagnostic..."
echo ""

# Run tests
dns_success=false
http_success=false

if test_dns; then
    dns_success=true
fi

if test_http_connectivity; then
    http_success=true
fi

# Show detailed configuration
show_network_config

# Provide recommendations
provide_recommendations $dns_success $http_success

# Final summary
echo ""
echo "📋 DIAGNOSTIC SUMMARY"
echo "===================="
echo "DNS Resolution: $([ $dns_success = true ] && echo "✅ Working" || echo "❌ Failed")"
echo "HTTP Access: $([ $http_success = true ] && echo "✅ Working" || echo "❌ Limited/Blocked")"
echo "Environment: $(is_container && echo "Container" || echo "Host")"
echo "Timestamp: $(date)"

if $dns_success && $http_success; then
    echo ""
    echo "🎉 RESULT: Internet access is working properly!"
    exit 0
elif $dns_success; then
    echo ""
    echo "⚠️ RESULT: DNS works but HTTP access is limited"
    exit 1
else
    echo ""
    echo "❌ RESULT: Internet access is blocked or misconfigured"
    exit 2
fi