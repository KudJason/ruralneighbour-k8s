#!/bin/bash

# API文档验证脚本
# 验证修复后的API文档配置是否正常工作

# 配置变量
REMOTE_HOST="home.worthwolf.top"
NAMESPACE="ruralneighbour-dev"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "============================================"
echo "🔍 API文档配置验证"
echo "============================================"
echo ""

# 获取远程机器IP
REMOTE_IP=$(ssh $REMOTE_HOST "hostname -I | awk '{print \$1}'")
log_info "🌐 远程服务器IP: $REMOTE_IP"

# 1. 检查Pod状态
log_info "📊 检查API文档服务状态..."
echo ""
echo "API文档相关Pod状态:"

services=("api-docs" "api-docs-scalar" "api-docs-redoc")
all_healthy=true

for service in "${services[@]}"; do
    pod_info=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE -l app=$service --no-headers 2>/dev/null")
    if [ -z "$pod_info" ]; then
        echo -e "  ${RED}❌ $service - 未找到Pod${NC}"
        all_healthy=false
    else
        status=$(echo "$pod_info" | awk '{print $3}')
        ready=$(echo "$pod_info" | awk '{print $2}')
        if [ "$status" = "Running" ]; then
            echo -e "  ${GREEN}✅ $service - 运行中 ($ready)${NC}"
        else
            echo -e "  ${YELLOW}⏳ $service - $status ($ready)${NC}"
            all_healthy=false
        fi
    fi
done

echo ""

# 2. 检查服务端点
log_info "🌐 检查服务端点..."
echo ""
echo "服务状态:"
ssh $REMOTE_HOST "microk8s kubectl get svc -n $NAMESPACE | grep api-docs" | while read line; do
    echo "  $line"
done

echo ""

# 3. 测试OpenAPI端点
log_info "🔍 测试OpenAPI端点..."
echo ""

openapi_endpoints=(
    "/openapi/auth.json"
    "/openapi/users.json" 
    "/openapi/requests.json"
    "/openapi/payments.json"
    "/openapi/locations.json"
)

openapi_working=true

echo "OpenAPI端点测试:"
for endpoint in "${openapi_endpoints[@]}"; do
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://${REMOTE_IP}${endpoint}" 2>/dev/null)
    if [ "$response_code" = "200" ]; then
        echo -e "  ${GREEN}✅ $endpoint - 可访问${NC}"
    else
        echo -e "  ${RED}❌ $endpoint - HTTP $response_code${NC}"
        openapi_working=false
    fi
done

echo ""

# 4. 测试API文档界面
log_info "📚 测试API文档界面..."
echo ""

doc_interfaces=(
    "/api-docs:Swagger UI" 
    "/api-docs-scalar:Scalar API文档"
    "/api-docs-redoc:ReDoc文档"
)

echo "API文档界面测试:"
for interface in "${doc_interfaces[@]}"; do
    IFS=':' read -r path name <<< "$interface"
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://${REMOTE_IP}${path}" 2>/dev/null)
    if [ "$response_code" = "200" ]; then
        echo -e "  ${GREEN}✅ $name ($path) - 可访问${NC}"
    else
        echo -e "  ${RED}❌ $name ($path) - HTTP $response_code${NC}"
    fi
done

echo ""

# 5. 检查Ingress配置
log_info "⚙️ 检查Ingress配置..."
echo ""
ingress_info=$(ssh $REMOTE_HOST "microk8s kubectl get ingress -n $NAMESPACE -o wide 2>/dev/null")
if [ -n "$ingress_info" ]; then
    echo "Ingress状态:"
    echo "$ingress_info" | while read line; do
        echo "  $line"
    done
else
    log_warning "⚠️ 未找到Ingress配置"
fi

echo ""

# 6. 最终报告
echo "============================================"
if $all_healthy && $openapi_working; then
    log_success "✅ 所有API文档服务正常运行！"
    echo ""
    echo "🎉 修复验证成功！您可以通过以下链接访问API文档:"
    echo ""
    echo "  📖 Swagger UI (多服务聚合): http://${REMOTE_IP}/api-docs"
    echo "  🎨 Scalar API文档 (现代界面): http://${REMOTE_IP}/api-docs-scalar"  
    echo "  📑 ReDoc文档 (清晰文档): http://${REMOTE_IP}/api-docs-redoc"
    echo ""
else
    log_error "❌ 检测到一些问题，请检查上述输出"
    echo ""
    echo "🛠️ 故障排除建议:"
    echo "  - 检查Pod日志: ssh $REMOTE_HOST 'microk8s kubectl logs -l app=api-docs -n $NAMESPACE'"
    echo "  - 重新部署: ./deploy_api_docs.sh"
    echo "  - 检查服务状态: ssh $REMOTE_HOST 'microk8s kubectl get all -n $NAMESPACE'"
fi

echo ""
echo "============================================"
