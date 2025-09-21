#!/bin/bash
# Show API documentation URLs for all services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MINIKUBE_IP=$(minikube ip)
BASE_URL="http://$MINIKUBE_IP"
API_BASE="$BASE_URL/api/v1"

echo -e "${BLUE}📚 Rural Neighbor Connect - API Documentation${NC}"
echo "=============================================="

# Function to test and show service docs
show_service_docs() {
    local service_name=$1
    local port=$2
    
    echo -e "${YELLOW}🔍 $service_name${NC}"
    
    # Check if service has running pods
    local running_pods=$(kubectl get pods -l app=$service_name --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [ "$running_pods" -gt 0 ]; then
        echo -e "  Status: ${GREEN}✅ Running ($running_pods pods)${NC}"
        echo -e "  ${BLUE}Direct Access (Port Forward):${NC}"
        echo "    kubectl port-forward svc/$service_name 8080:80"
        echo "    Then visit: http://localhost:8080/docs"
        echo ""
        echo -e "  ${BLUE}Swagger UI:${NC} http://localhost:8080/docs"
        echo -e "  ${BLUE}ReDoc:${NC} http://localhost:8080/redoc"
        echo -e "  ${BLUE}OpenAPI JSON:${NC} http://localhost:8080/openapi.json"
    else
        echo -e "  Status: ${RED}❌ Not Running${NC}"
    fi
    
    echo -e "  ${BLUE}Ingress Access:${NC}"
    echo "    Swagger UI: $API_BASE/$service_name/docs"
    echo "    ReDoc: $API_BASE/$service_name/redoc"
    echo "    OpenAPI JSON: $API_BASE/$service_name/openapi.json"
    echo ""
}

# Show docs for all services
services=("auth-service:8000" "user-service:8000" "location-service:8000" "payment-service:8000" "request-service:8000" "notification-service:8000" "content-service:8000" "safety-service:8000")

for service_info in "${services[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    show_service_docs "$service_name" "$port"
done

echo -e "${GREEN}🌐 Minikube IP: $MINIKUBE_IP${NC}"
echo -e "${GREEN}🔗 API Base URL: $API_BASE${NC}"

echo ""
echo -e "${YELLOW}📚 Swagger UI Aggregator${NC}"
echo "  Portal:       $BASE_URL/api-docs"
echo ""
echo -e "${YELLOW}📊 Service Status Summary${NC}"
echo "========================"
kubectl get pods | grep -E "(Running|CrashLoopBackOff|Error)" | awk '{print "  " $1 ": " $3}'

echo ""
echo -e "${YELLOW}💡 Quick Commands${NC}"
echo "==============="
echo "Test a service:"
echo "  kubectl port-forward svc/SERVICE_NAME 8080:80"
echo "  curl http://localhost:8080/health"
echo ""
echo "Check logs:"
echo "  kubectl logs -l app=SERVICE_NAME --tail=50"
echo ""
echo "Restart service:"
echo "  kubectl rollout restart deployment/SERVICE_NAME"




