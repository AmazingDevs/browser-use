#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

# Senior Engineer Level: Docker-Aware Firewall Configuration
# This script properly integrates with Docker networking without breaking it

echo "🌐 Configuring Docker-aware firewall for FULL internet access..."

# Function to check if we're running in a container
is_container() {
    [[ -f /.dockerenv ]] || grep -q docker /proc/1/cgroup 2>/dev/null
}

# Function to check if Docker daemon is running
docker_running() {
    systemctl is-active --quiet docker 2>/dev/null || \
    pgrep dockerd >/dev/null 2>&1 || \
    docker info >/dev/null 2>&1
}

# Function to backup Docker rules
backup_docker_rules() {
    echo "📋 Backing up existing Docker iptables rules..."
    
    # Backup Docker NAT rules (essential for container internet access)
    DOCKER_NAT_BACKUP=$(iptables-save -t nat 2>/dev/null | grep -E "(DOCKER|MASQUERADE)" || true)
    
    # Backup Docker filter rules
    DOCKER_FILTER_BACKUP=$(iptables-save -t filter 2>/dev/null | grep "DOCKER" || true)
    
    # Save to temp files for potential restore
    echo "$DOCKER_NAT_BACKUP" > /tmp/docker_nat_rules.backup 2>/dev/null || true
    echo "$DOCKER_FILTER_BACKUP" > /tmp/docker_filter_rules.backup 2>/dev/null || true
}

# Function to ensure Docker chains exist
ensure_docker_chains() {
    echo "🔧 Ensuring Docker chains are properly configured..."
    
    # Create DOCKER-USER chain if it doesn't exist (this is the official way to add custom rules)
    iptables -t filter -N DOCKER-USER 2>/dev/null || true
    
    # Ensure DOCKER-USER chain is properly integrated into FORWARD chain
    if ! iptables -t filter -C FORWARD -j DOCKER-USER 2>/dev/null; then
        iptables -t filter -I FORWARD -j DOCKER-USER 2>/dev/null || true
    fi
}

# Function to configure permissive policies
configure_permissive_access() {
    echo "🔓 Configuring permissive internet access policies..."
    
    # Set permissive default policies (safest approach for full internet access)
    iptables -P INPUT ACCEPT 2>/dev/null || true
    iptables -P OUTPUT ACCEPT 2>/dev/null || true
    
    # CRITICAL: Only set FORWARD ACCEPT if we're not breaking Docker
    if docker_running; then
        echo "📌 Docker detected - preserving Docker's FORWARD chain management"
        # Let Docker manage FORWARD chain, just ensure permissive user rules
        iptables -F DOCKER-USER 2>/dev/null || true
        iptables -A DOCKER-USER -j ACCEPT 2>/dev/null || true
    else
        echo "📌 No Docker detected - setting permissive FORWARD policy"
        iptables -P FORWARD ACCEPT 2>/dev/null || true
    fi
}

# Function to clean only user-defined restrictive rules (NOT Docker rules)
clean_restrictive_rules() {
    echo "🧹 Removing only restrictive user rules (preserving Docker networking)..."
    
    # Remove restrictive ipsets (but preserve Docker networking)
    ipset destroy allowed-domains 2>/dev/null || true
    
    # Clean only INPUT/OUTPUT chains (preserve Docker's FORWARD chain management)
    # We do NOT flush the nat table as this breaks Docker's masquerading
    iptables -F INPUT 2>/dev/null || true
    iptables -F OUTPUT 2>/dev/null || true
    
    # Remove only custom user chains (NOT Docker chains)
    for chain in $(iptables -t filter -L | grep "^Chain" | grep -v "DOCKER" | awk '{print $2}' | grep -v -E "^(INPUT|OUTPUT|FORWARD)$"); do
        iptables -F "$chain" 2>/dev/null || true
        iptables -X "$chain" 2>/dev/null || true
    done
}

# Function to add essential connectivity rules
add_essential_rules() {
    echo "📡 Adding essential connectivity rules..."
    
    # Loopback (essential for local processes)
    iptables -A INPUT -i lo -j ACCEPT 2>/dev/null || true
    iptables -A OUTPUT -o lo -j ACCEPT 2>/dev/null || true
    
    # Connection tracking (efficient and secure)
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
    iptables -A OUTPUT -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
}

# Function to verify Docker networking
verify_docker_networking() {
    if docker_running; then
        echo "🐳 Verifying Docker networking integrity..."
        
        # Check if Docker bridge exists
        if ip link show docker0 >/dev/null 2>&1; then
            echo "✅ Docker bridge interface exists"
        else
            echo "⚠️  Docker bridge not found - Docker may need restart"
        fi
        
        # Check if Docker NAT rules exist
        if iptables-save -t nat | grep -q DOCKER 2>/dev/null; then
            echo "✅ Docker NAT rules present"
        else
            echo "⚠️  Docker NAT rules missing - container internet access may be broken"
        fi
        
        # Check DOCKER-USER chain
        if iptables -t filter -L DOCKER-USER >/dev/null 2>&1; then
            echo "✅ DOCKER-USER chain properly configured"
        else
            echo "⚠️  DOCKER-USER chain missing"
        fi
    fi
}

# Main execution starts here
echo "🚀 Starting Docker-aware firewall configuration..."

# Environment detection
if is_container; then
    echo "📦 Running inside container - limited iptables operations"
    # In container, we have limited capabilities
    echo "💡 For containers, internet access is controlled by the host Docker daemon"
    echo "✅ If you can run this script, you likely already have internet access"
else
    echo "🖥️  Running on host system - full iptables control available"
    
    # Full configuration for host system
    backup_docker_rules
    clean_restrictive_rules
    ensure_docker_chains
    configure_permissive_access
    add_essential_rules
    verify_docker_networking
fi

echo "✅ Docker-aware firewall configuration completed"

# Comprehensive connectivity testing
test_connectivity() {
    echo "🧪 Testing internet connectivity..."
    
    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        echo "⚠️  curl not available - installing for testing..."
        if command -v apt-get >/dev/null 2>&1; then
            apt-get update -qq && apt-get install -y curl 2>/dev/null || true
        elif command -v yum >/dev/null 2>&1; then
            yum install -y curl 2>/dev/null || true
        fi
    fi
    
    # Test DNS resolution first
    echo "🔍 Testing DNS resolution..."
    if nslookup google.com >/dev/null 2>&1 || dig google.com >/dev/null 2>&1; then
        echo "✅ DNS resolution working"
    else
        echo "❌ DNS resolution failed - this will block internet access"
        return 1
    fi
    
    # Test basic connectivity with robust timeout handling
    echo "🌐 Testing HTTP/HTTPS connectivity..."
    
    # Test sites with different protocols and CDNs
    test_urls=(
        "https://httpbin.org/ip"
        "https://www.google.com"
        "https://github.com"
        "https://registry.npmjs.org"
        "http://httpbin.org/get"  # HTTP test
        "https://api.github.com/zen"
    )
    
    successful_tests=0
    total_tests=${#test_urls[@]}
    
    for url in "${test_urls[@]}"; do
        echo -n "  Testing $url ... "
        if timeout 10 curl -s --max-time 8 --connect-timeout 5 "$url" >/dev/null 2>&1; then
            echo "✅"
            ((successful_tests++))
        else
            echo "❌"
        fi
    done
    
    # Report results
    echo ""
    if [ $successful_tests -eq $total_tests ]; then
        echo "🎉 PERFECT! All connectivity tests passed ($successful_tests/$total_tests)"
        echo "🔓 Full internet access confirmed"
        return 0
    elif [ $successful_tests -gt $((total_tests / 2)) ]; then
        echo "✅ Good connectivity: $successful_tests/$total_tests tests passed"
        echo "🔓 Internet access is working (some sites may have rate limiting)"
        return 0
    elif [ $successful_tests -gt 0 ]; then
        echo "⚠️  Partial connectivity: $successful_tests/$total_tests tests passed"
        echo "💡 Some internet access working, but there may be restrictions"
        return 1
    else
        echo "❌ No connectivity: All tests failed"
        echo "🚨 Internet access appears to be blocked"
        return 1
    fi
}

# Additional diagnostic information
show_network_info() {
    echo ""
    echo "📊 Network Diagnostic Information:"
    
    # Show routing table
    if command -v ip >/dev/null 2>&1; then
        echo "🛣️  Default routes:"
        ip route show default 2>/dev/null | head -3 || echo "  Unable to show routes"
    fi
    
    # Show Docker network info if available
    if docker_running && command -v docker >/dev/null 2>&1; then
        echo "🐳 Docker network status:"
        docker network ls 2>/dev/null | head -5 || echo "  Unable to show Docker networks"
        
        # Show docker0 bridge if it exists
        if ip link show docker0 >/dev/null 2>&1; then
            docker0_ip=$(ip addr show docker0 2>/dev/null | grep 'inet ' | awk '{print $2}' | head -1)
            echo "🌉 Docker bridge: ${docker0_ip:-unknown}"
        fi
    fi
    
    # Show iptables policy summary
    echo "🔥 Firewall policies:"
    for table in INPUT OUTPUT FORWARD; do
        policy=$(iptables -L "$table" 2>/dev/null | head -1 | awk '{print $4}' | tr -d '()')
        echo "  $table: ${policy:-unknown}"
    done
}

# Run connectivity tests
if test_connectivity; then
    echo ""
    echo "🎯 SUCCESS: Full internet access configured and verified!"
    echo "🏁 Your container/system now has unrestricted internet connectivity"
else
    echo ""
    echo "⚠️  WARNING: Connectivity issues detected"
    echo "💡 This may be due to network configuration, DNS issues, or external restrictions"
    
    show_network_info
    
    echo ""
    echo "🔧 Troubleshooting suggestions:"
    echo "  1. Check your host network connection"
    echo "  2. Verify DNS settings (try: echo 'nameserver 8.8.8.8' > /etc/resolv.conf)"
    echo "  3. Restart Docker daemon if running containers"
    echo "  4. Check for corporate firewall/proxy restrictions"
fi

echo ""
echo "📋 Script execution completed - $(date)"
