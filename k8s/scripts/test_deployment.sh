#!/bin/bash
# Test script for deployed Kubernetes pods

echo "🧪 Starting Kubernetes deployment tests..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_pod_status() {
    local service_name=$1
    local expected_replicas=$2
    
    echo -n "Testing $service_name pod status... "
    
    local running_pods=$(kubectl get pods -l app=$service_name --field-selector=status.phase=Running --no-headers | wc -l)
    local total_pods=$(kubectl get pods -l app=$service_name --no-headers | wc -l)
    
    if [ "$running_pods" -eq "$expected_replicas" ] && [ "$total_pods" -eq "$expected_replicas" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($running_pods/$expected_replicas running)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} ($running_pods/$expected_replicas running, $total_pods total)"
        return 1
    fi
}

test_service_health() {
    local service_name=$1
    local port=$2
    
    echo -n "Testing $service_name health endpoint... "
    
    # Get a pod name for port forwarding
    local pod_name=$(kubectl get pods -l app=$service_name --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        echo -e "${RED}❌ FAIL${NC} (No running pods found)"
        return 1
    fi
    
    # Start port forward in background
    kubectl port-forward pod/$pod_name $port:$port > /dev/null 2>&1 &
    local pf_pid=$!
    
    # Wait for port forward to be ready
    sleep 3
    
    # Test health endpoint
    local health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
    
    # Kill port forward
    kill $pf_pid 2>/dev/null
    
    if [ "$health_response" = "200" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $health_response)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $health_response)"
        return 1
    fi
}

test_service_connectivity() {
    local service_name=$1
    local port=$2
    
    echo -n "Testing $service_name service connectivity... "
    
    # Test service DNS resolution
    local service_ip=$(kubectl get service $service_name -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
    
    if [ -z "$service_ip" ]; then
        echo -e "${RED}❌ FAIL${NC} (Service not found)"
        return 1
    fi
    
    # Test service port
    local port_check=$(kubectl get service $service_name -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
    
    if [ "$port_check" = "$port" ]; then
        echo -e "${GREEN}✅ PASS${NC} (Service IP: $service_ip, Port: $port)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Port mismatch: expected $port, got $port_check)"
        return 1
    fi
}

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0

# Run tests for each service
echo ""
echo "📊 Running pod status tests..."
echo "================================"

# Test pod statuses
services=("auth-service:2" "user-service:2" "content-service:2" "notification-service:2" "request-service:3" "location-service:2" "payment-service:2" "safety-service:2")

for service_info in "${services[@]}"; do
    IFS=':' read -r service_name expected_replicas <<< "$service_info"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if test_pod_status "$service_name" "$expected_replicas"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
done

echo ""
echo "🏥 Running health endpoint tests..."
echo "=================================="

# Test health endpoints for running services
running_services=("auth-service:8000" "user-service:8000" "content-service:8000" "notification-service:8000" "request-service:8000")

for service_info in "${running_services[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if test_service_health "$service_name" "$port"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
done

echo ""
echo "🔗 Running service connectivity tests..."
echo "======================================="

# Test service connectivity
all_services=("auth-service:80" "user-service:80" "content-service:80" "notification-service:80" "request-service:80" "location-service:80" "payment-service:80" "safety-service:80")

for service_info in "${all_services[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if test_service_connectivity "$service_name" "$port"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
done

echo ""
echo "📈 Test Summary"
echo "==============="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed.${NC}"
    exit 1
fi











