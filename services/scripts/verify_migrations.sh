#!/bin/bash
# 验证所有服务的 Alembic 迁移状态

set -e

echo "=================================================="
echo "验证所有服务的 Alembic 迁移状态"
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
    exit 1
fi

echo -e "${GREEN}✓ Kubernetes 集群连接正常${NC}"
echo ""

# 验证函数
verify_service() {
    local service=$1
    
    echo -e "${BLUE}=== $service ===${NC}"
    
    # 获取 Pod
    local pod_name=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        echo -e "${RED}❌ 未找到 Pod${NC}"
        return 1
    fi
    
    echo "Pod: $pod_name"
    
    # 检查 Pod 状态
    local pod_status=$(kubectl get pod $pod_name -o jsonpath='{.status.phase}' 2>/dev/null)
    if [ "$pod_status" != "Running" ]; then
        echo -e "${YELLOW}⚠️  Pod 状态: $pod_status${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Pod 正在运行${NC}"
    
    # 检查迁移状态
    echo "检查迁移状态..."
    local migration_status=$(kubectl exec $pod_name -- alembic current 2>/dev/null || echo "No migration applied")
    echo "迁移状态: $migration_status"
    
    # 检查数据库连接
    echo "检查数据库连接..."
    if kubectl exec $pod_name -- python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    conn = engine.connect()
    conn.close()
    print('Database connection: OK')
except Exception as e:
    print(f'Database connection: FAILED - {e}')
    exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}✓ 数据库连接正常${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
        return 1
    fi
    
    # 检查表是否存在
    echo "检查表结构..."
    local table_check=$(kubectl exec $pod_name -- python -c "
import os
from sqlalchemy import create_engine, text
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute(text('SELECT table_name FROM information_schema.tables WHERE table_schema = \\'public\\' ORDER BY table_name'))
        tables = [row[0] for row in result]
        print(f'Tables found: {len(tables)}')
        for table in tables[:5]:  # 显示前5个表
            print(f'  - {table}')
        if len(tables) > 5:
            print(f'  ... and {len(tables) - 5} more')
except Exception as e:
    print(f'Table check failed: {e}')
    exit(1)
" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 表结构检查通过${NC}"
        echo "$table_check"
    else
        echo -e "${RED}❌ 表结构检查失败${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ $service 验证通过${NC}"
    echo ""
    return 0
}

# 主验证流程
SUCCESS_COUNT=0
TOTAL_COUNT=${#SERVICES[@]}

for service in "${SERVICES[@]}"; do
    if verify_service $service; then
        ((SUCCESS_COUNT++))
    else
        echo -e "${RED}❌ $service 验证失败${NC}"
        echo ""
    fi
done

# 总结
echo "=================================================="
echo "验证总结"
echo "=================================================="
echo "总服务数: $TOTAL_COUNT"
echo -e "${GREEN}成功: $SUCCESS_COUNT${NC}"
echo -e "${RED}失败: $((TOTAL_COUNT - SUCCESS_COUNT))${NC}"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo -e "${GREEN}🎉 所有服务验证通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  有 $((TOTAL_COUNT - SUCCESS_COUNT)) 个服务验证失败${NC}"
    exit 1
fi
