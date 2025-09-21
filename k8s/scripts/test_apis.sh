#!/bin/bash
# Quick API testing and documentation script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MINIKUBE_IP=$(minikube ip)
BASE_URL="http://$MINIKUBE_IP"
API_BASE="$BASE_URL/api/v1"

echo -e "${BLUE}🧪 Rural Neighbor Connect - API Testing & Documentation${NC}"
echo "============================================================="

# Function to test service via port forward
test_service() {
    local service_name=$1
    local port=$2
    local endpoint=$3
    
    echo -n "Testing $service_name$endpoint... "
    
    # Get a running pod
    local pod_name=$(kubectl get pods -l app=$service_name --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        echo -e "${RED}❌ No running pods${NC}"
        return 1
    fi
    
    # Port forward
    kubectl port-forward pod/$pod_name $port:$port > /dev/null 2>&1 &
    local pf_pid=$!
    sleep 3
    
    # Test endpoint
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port$endpoint 2>/dev/null)
    
    # Cleanup
    kill $pf_pid 2>/dev/null
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL (HTTP $response)${NC}"
        return 1
    fi
}

# Function to test API via ingress
test_api_ingress() {
    local service_name=$1
    local endpoint=$2
    
    echo -n "Testing $service_name via ingress... "
    
    local url="$API_BASE/$service_name$endpoint"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL (HTTP $response)${NC}"
        return 1
    fi
}

# Function to show service documentation
show_docs() {
    local service_name=$1
    local port=$2
    
    echo -e "${BLUE}📚 $service_name Documentation:${NC}"
    
    # Get a running pod
    local pod_name=$(kubectl get pods -l app=$service_name --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -n "$pod_name" ]; then
        echo "  - Swagger UI: http://localhost:$port/docs (via port-forward)"
        echo "  - ReDoc: http://localhost:$port/redoc (via port-forward)"
        echo "  - OpenAPI JSON: http://localhost:$port/openapi.json (via port-forward)"
    fi
    
    echo "  - Ingress Swagger UI: $API_BASE/$service_name/docs"
    echo "  - Ingress ReDoc: $API_BASE/$service_name/redoc"
    echo "  - Ingress OpenAPI: $API_BASE/$service_name/openapi.json"
    echo ""
}

# Main testing
echo -e "${YELLOW}🔍 Testing Services via Port Forward...${NC}"
echo "============================================="

# Test running services
test_service "auth-service" 8080 "/health"
test_service "user-service" 8080 "/health"
test_service "request-service" 8080 "/health"
test_service "content-service" 8080 "/health"
test_service "notification-service" 8080 "/health"

echo ""
echo -e "${YELLOW}🌐 Testing Services via Ingress...${NC}"
echo "====================================="

# Test via ingress
test_api_ingress "auth-service" "/health"
test_api_ingress "user-service" "/health"
test_api_ingress "request-service" "/health"
test_api_ingress "content-service" "/health"
test_api_ingress "notification-service" "/health"

echo ""
echo -e "${YELLOW}📊 Service Status${NC}"
echo "=================="
kubectl get pods | grep -E "(Running|CrashLoopBackOff|Error)"

echo ""
echo -e "${YELLOW}📚 API Documentation URLs${NC}"
echo "============================="

# Show documentation for all services
services=("auth-service:8000" "user-service:8000" "location-service:8000" "payment-service:8000" "request-service:8000" "notification-service:8000" "content-service:8000" "safety-service:8000")

for service_info in "${services[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    show_docs "$service_name" "$port"
done

echo -e "${GREEN}🌐 Minikube IP: $MINIKUBE_IP${NC}"
echo -e "${GREEN}🔗 API Base URL: $API_BASE${NC}"

echo ""
echo -e "${YELLOW}💡 Quick Access Commands:${NC}"
echo "=========================="
echo "To access a service directly:"
echo "  kubectl port-forward svc/SERVICE_NAME 8080:80"
echo "  Then visit: http://localhost:8080/docs"
echo ""
echo "To check service logs:"
echo "  kubectl logs -l app=SERVICE_NAME --tail=50"
echo ""
echo "To restart a service:"
echo "  kubectl rollout restart deployment/SERVICE_NAME"

