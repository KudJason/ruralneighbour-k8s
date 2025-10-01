#!/bin/bash
# 执行所有服务的 Alembic 迁移

set -e

echo "=================================================="
echo "执行所有服务的 Alembic 迁移"
echo "=================================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务列表
SERVICES=(
    "auth-service"
    "user-service"
    "location-service"
    "content-service"
    "request-service"
    "notification-service"
    "payment-service"
    "safety-service"
    "rating-service"
)

# 检查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}错误: kubectl 未安装或不在 PATH 中${NC}"
    exit 1
fi

# 检查是否连接到 K8s 集群
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}错误: 无法连接到 Kubernetes 集群${NC}"
    echo "请确保 kubectl 已配置并连接到正确的集群"
    exit 1
fi

echo -e "${GREEN}✓ Kubernetes 集群连接正常${NC}"
echo ""

# 函数：检查服务状态
check_service_status() {
    local service=$1
    local pod_count=$(kubectl get pods -l app=$service --no-headers 2>/dev/null | wc -l)
    
    if [ "$pod_count" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  $service: 没有找到 Pod${NC}"
        return 1
    elif [ "$pod_count" -gt 1 ]; then
        echo -e "${YELLOW}⚠️  $service: 找到多个 Pod ($pod_count 个)${NC}"
        return 1
    else
        local pod_name=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        local pod_status=$(kubectl get pod $pod_name -o jsonpath='{.status.phase}' 2>/dev/null)
        
        if [ "$pod_status" = "Running" ]; then
            echo -e "${GREEN}✓ $service: Pod $pod_name 正在运行${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service: Pod $pod_name 状态为 $pod_status${NC}"
            return 1
        fi
    fi
}

# 函数：运行单个服务的迁移
run_migration() {
    local service=$1
    
    echo -e "${BLUE}=== 处理 $service ===${NC}"
    
    # 检查服务状态
    if ! check_service_status $service; then
        echo -e "${RED}❌ 跳过 $service (Pod 状态异常)${NC}"
        return 1
    fi
    
    # 获取 Pod 名称
    local pod_name=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        echo -e "${RED}❌ 无法获取 $service 的 Pod 名称${NC}"
        return 1
    fi
    
    echo "Pod: $pod_name"
    
    # 检查当前迁移状态
    echo "检查当前迁移状态..."
    local current_status=$(kubectl exec $pod_name -- alembic current 2>/dev/null || echo "No migration applied")
    echo "当前状态: $current_status"
    
    # 运行迁移
    echo "运行迁移..."
    if kubectl exec $pod_name -- alembic upgrade head; then
        echo -e "${GREEN}✓ $service 迁移成功${NC}"
        
        # 验证迁移结果
        local new_status=$(kubectl exec $pod_name -- alembic current 2>/dev/null || echo "No migration applied")
        echo "新状态: $new_status"
        return 0
    else
        echo -e "${RED}❌ $service 迁移失败${NC}"
        return 1
    fi
}

# 主执行流程
echo "检查所有服务状态..."
echo ""

FAILED_SERVICES=()
SUCCESS_SERVICES=()

for service in "${SERVICES[@]}"; do
    if run_migration $service; then
        SUCCESS_SERVICES+=("$service")
    else
        FAILED_SERVICES+=("$service")
    fi
    echo ""
done

# 总结结果
echo "=================================================="
echo "迁移执行总结"
echo "=================================================="

if [ ${#SUCCESS_SERVICES[@]} -gt 0 ]; then
    echo -e "${GREEN}✓ 成功完成的服务 (${#SUCCESS_SERVICES[@]} 个):${NC}"
    for service in "${SUCCESS_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
fi

if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo -e "${RED}❌ 失败的服务 (${#FAILED_SERVICES[@]} 个):${NC}"
    for service in "${FAILED_SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
fi

# 最终状态检查
echo "=================================================="
echo "最终状态检查"
echo "=================================================="

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}=== $service ===${NC}"
    POD=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD" ]; then
        kubectl exec $POD -- alembic current 2>/dev/null || echo "No migration applied"
    else
        echo "Pod not found"
    fi
    echo ""
done

# 退出状态
if [ ${#FAILED_SERVICES[@]} -eq 0 ]; then
    echo -e "${GREEN}🎉 所有迁移执行成功！${NC}"
    exit 0
else
    echo -e "${RED}⚠️  有 ${#FAILED_SERVICES[@]} 个服务迁移失败${NC}"
    exit 1
fi
