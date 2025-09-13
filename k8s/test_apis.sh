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
    
    # Port forward (map local $port to container 8000)
    kubectl port-forward pod/$pod_name $port:8000 > /dev/null 2>&1 &
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
    
    # Map service to ingress path prefix
    local path_prefix=""
    case "$service_name" in
        auth-service) path_prefix="auth" ;;
        user-service) path_prefix="users" ;;
        location-service) path_prefix="locations" ;;
        payment-service) path_prefix="payments" ;;
        request-service) path_prefix="requests" ;;
        notification-service) path_prefix="notifications" ;;
        content-service) path_prefix="content" ;;
        safety-service) path_prefix="safety" ;;
    esac
    
    echo "  - Ingress Swagger UI: $API_BASE/$path_prefix/docs"
    echo "  - Ingress ReDoc: $API_BASE/$path_prefix/redoc"
    echo "  - Ingress OpenAPI: $API_BASE/$path_prefix/openapi.json"
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

# Ensure ingress reachability: if direct $API_BASE is not reachable, port-forward ingress controller to localhost:8081
if ! curl -s -o /dev/null -w "%{http_code}" "$API_BASE/auth/health" 2>/dev/null | grep -q "^200$"; then
    echo -e "${YELLOW}⚠️  Ingress via $API_BASE not reachable. Port-forwarding ingress controller to localhost:8081...${NC}"
    kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8081:80 > /dev/null 2>&1 &
    pf_ingress_pid=$!
    trap 'kill ${pf_ingress_pid} 2>/dev/null || true' EXIT
    sleep 3
    API_BASE="http://localhost:8081/api/v1"
fi

# Test via ingress (paths aligned with ingress.yaml)
test_api_ingress "auth" "/health"
test_api_ingress "users" "/health"
test_api_ingress "requests" "/health"
test_api_ingress "content" "/health"
test_api_ingress "notifications" "/health"
test_api_ingress "locations" "/health"
test_api_ingress "payments" "/health"
test_api_ingress "safety" "/health"

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

