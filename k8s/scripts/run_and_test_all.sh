#!/bin/bash
# Complete script to run all services, test APIs, and generate documentation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration (will be set after ensuring minikube is running)
MINIKUBE_IP=""
BASE_URL=""
API_BASE=""

echo -e "${BLUE}🚀 Rural Neighbor Connect - Complete Deployment & Test Suite${NC}"
echo "=================================================================="

# Function to check if minikube is running
check_minikube() {
    echo -e "${YELLOW}📋 Checking minikube status...${NC}"
    if ! minikube status > /dev/null 2>&1; then
        echo -e "${RED}❌ Minikube is not running. Starting minikube...${NC}"
        minikube start
    else
        echo -e "${GREEN}✅ Minikube is running${NC}"
    fi
    # Ensure ingress addon is enabled
    if ! minikube addons list | grep -E "^ingress\s+enabled" >/dev/null 2>&1; then
        echo -e "${YELLOW}🔌 Enabling minikube ingress addon...${NC}"
        minikube addons enable ingress
    fi
}

# Function to build all Docker images
build_images() {
    echo -e "${YELLOW}🔨 Building all Docker images...${NC}"
    cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
    
    # Generate requirements for all services
    echo "Generating requirements.txt files..."
    ./export_requirements.bash
    
    # Build all service images
    services=("auth-service" "user-service" "location-service" "payment-service" "request-service" "notification-service" "content-service" "safety-service")
    
    for service in "${services[@]}"; do
        echo "Building $service..."
        docker build -t neighbor-connect/$service:latest ./$service/
    done
    
    echo -e "${GREEN}✅ All images built successfully${NC}"
}

# Load images into minikube (if not using docker-env)
load_images_to_minikube() {
    echo -e "${YELLOW}📦 Loading images into minikube...${NC}"
    services=("auth-service" "user-service" "location-service" "payment-service" "request-service" "notification-service" "content-service" "safety-service")
    for service in "${services[@]}"; do
        echo "Loading neighbor-connect/$service:latest into minikube..."
        minikube image load neighbor-connect/$service:latest
    done
    echo -e "${GREEN}✅ Images loaded into minikube${NC}"
}

# Function to deploy to Kubernetes
deploy_to_k8s() {
    echo -e "${YELLOW}🚀 Deploying to Kubernetes...${NC}"
    cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/k8s
    
    # Deploy all services
    ./deploy.sh
    
    echo -e "${GREEN}✅ Deployment completed${NC}"
}

# Function to wait for services to be ready
wait_for_services() {
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    
    # Wait for all pods to be running
    kubectl wait --for=condition=ready pod -l tier=backend --timeout=300s || true
    kubectl wait --for=condition=ready pod -l tier=database --timeout=300s || true
    kubectl wait --for=condition=ready pod -l tier=cache --timeout=300s || true
    
    echo -e "${GREEN}✅ Services are ready${NC}"
}

# Function to test service health
test_service_health() {
    echo -e "${YELLOW}🏥 Testing service health endpoints...${NC}"
    
    # Test each service health endpoint
    services=("auth-service" "user-service" "content-service" "notification-service" "request-service")
    
    for service in "${services[@]}"; do
        echo -n "Testing $service health... "
        
        # Get a running pod for port forwarding
        pod_name=$(kubectl get pods -l app=$service --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        
        if [ -n "$pod_name" ]; then
            # Start port forward in background
            kubectl port-forward pod/$pod_name 8080:8000 > /dev/null 2>&1 &
            pf_pid=$!
            
            # Wait for port forward
            sleep 3
            
            # Test health endpoint
            health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health 2>/dev/null)
            
            # Kill port forward
            kill $pf_pid 2>/dev/null
            
            if [ "$health_response" = "200" ]; then
                echo -e "${GREEN}✅ PASS${NC} (HTTP $health_response)"
            else
                echo -e "${RED}❌ FAIL${NC} (HTTP $health_response)"
            fi
        else
            echo -e "${RED}❌ FAIL${NC} (No running pods)"
        fi
    done
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "${YELLOW}🔍 Testing API endpoints...${NC}"
    
    # Test basic API connectivity
    echo -n "Testing API base connectivity... "
    if curl -s "$API_BASE" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL${NC}"
    fi
    
    # Test via ingress (paths aligned with ingress.yaml)
    endpoints=(
        "auth:/health"
        "users:/health"
        "locations:/health"
        "requests:/health"
        "payments:/health"
        "notifications:/health"
        "content:/health"
        "safety:/health"
    )

    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r path_prefix path <<< "$endpoint"
        echo -n "Testing /api/v1/${path_prefix}${path}... "
        service_url="$API_BASE/$path_prefix$path"
        if curl -s -o /dev/null -w "%{http_code}" "$service_url" 2>/dev/null | grep -q "^200$"; then
            echo -e "${GREEN}✅ PASS${NC}"
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
    done
}

# Function to generate and display API documentation URLs
show_api_docs() {
    echo -e "${YELLOW}📚 API Documentation URLs${NC}"
    echo "=================================="
    
    services=("auth-service" "user-service" "location-service" "payment-service" "request-service" "notification-service" "content-service" "safety-service")

    ingress_path_for_service() {
        case "$1" in
            auth-service) echo "auth" ;;
            user-service) echo "users" ;;
            location-service) echo "locations" ;;
            payment-service) echo "payments" ;;
            request-service) echo "requests" ;;
            notification-service) echo "notifications" ;;
            content-service) echo "content" ;;
            safety-service) echo "safety" ;;
        esac
    }

    for service in "${services[@]}"; do
        path_prefix="$(ingress_path_for_service "$service")"
        echo -e "${BLUE}$service:${NC}"
        echo "  - Swagger UI: $API_BASE/$path_prefix/docs"
        echo "  - ReDoc: $API_BASE/$path_prefix/redoc"
        echo "  - OpenAPI JSON: $API_BASE/$path_prefix/openapi.json"
        echo ""
    done
    
    echo -e "${GREEN}🌐 Main API Base: $API_BASE${NC}"
    echo -e "${GREEN}🔗 Minikube IP: $MINIKUBE_IP${NC}"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    echo -e "${YELLOW}🧪 Running comprehensive tests...${NC}"
    
    # Run the test script if it exists
    if [ -f "test_deployment.sh" ]; then
        chmod +x test_deployment.sh
        ./test_deployment.sh
    else
        echo -e "${YELLOW}⚠️  Test script not found, running basic tests...${NC}"
        test_service_health
        test_api_endpoints
    fi
}

# Function to show deployment status
show_deployment_status() {
    echo -e "${YELLOW}📊 Deployment Status${NC}"
    echo "===================="
    
    echo -e "${BLUE}Pods:${NC}"
    kubectl get pods
    
    echo ""
    echo -e "${BLUE}Services:${NC}"
    kubectl get services
    
    echo ""
    echo -e "${BLUE}Ingress:${NC}"
    kubectl get ingress
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up port forwards...${NC}"
    pkill -f "kubectl port-forward" 2>/dev/null || true
}

# Main execution
main() {
    # Set up cleanup on exit
    trap cleanup EXIT
    
    # Step 1: Check minikube
    check_minikube
    # Now that minikube is ensured running, set networking variables
    MINIKUBE_IP=$(minikube ip)
    BASE_URL="http://$MINIKUBE_IP"
    API_BASE="$BASE_URL/api/v1"
    
    # Step 2: Build images
    build_images

    # Step 2.5: Ensure images are available inside minikube
    load_images_to_minikube
    
    # Step 3: Deploy to Kubernetes
    deploy_to_k8s
    
    # Step 4: Wait for services
    wait_for_services
    
    # Step 5: Show deployment status
    show_deployment_status
    
    # Step 6: Test services
    test_service_health
    test_api_endpoints
    
    # Step 7: Run comprehensive tests
    run_comprehensive_tests
    
    # Step 8: Show API documentation
    show_api_docs
    
    echo ""
    echo -e "${GREEN}🎉 All done! Your Rural Neighbor Connect services are running.${NC}"
    echo -e "${GREEN}📖 Check the API documentation URLs above to explore the APIs.${NC}"
}

# Run main function
main "$@"

