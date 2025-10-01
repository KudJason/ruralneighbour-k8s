#!/bin/bash

# 智能部署腳本 - 不會卡在等待階段
# 用途: 快速部署並立即檢查狀態，不等待所有服務完全就緒

set -e

# 配置變量
REMOTE_HOST="home.worthwolf.top"
NAMESPACE="ruralneighbour-dev"
PROJECT_ROOT="/Users/jasonjia/codebase/ruralneighbour/ms-backend"

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
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

echo "=========================================="
echo "🚀 Rural Neighbour 智能部署（不等待）"
echo "=========================================="
echo ""

# 1. 檢查連接
log_info "🔍 檢查遠程服務器連接..."
if ssh -o ConnectTimeout=5 $REMOTE_HOST "echo 'OK'" > /dev/null 2>&1; then
    log_success "✅ 遠程服務器連接正常"
else
    log_error "❌ 無法連接到遠程服務器"
    exit 1
fi

# 2. 強制清理並創建命名空間
log_info "🧹 清理並創建命名空間..."
echo "  📋 刪除現有命名空間..."
ssh $REMOTE_HOST "microk8s kubectl delete namespace $NAMESPACE --ignore-not-found=true --force --grace-period=0" 2>/dev/null || true
sleep 2
echo "  🏗️ 創建新命名空間..."
ssh $REMOTE_HOST "microk8s kubectl create namespace $NAMESPACE"

# 3. 同步配置
log_info "📁 同步 K8s 配置..."
rsync -avz $PROJECT_ROOT/k8s/ $REMOTE_HOST:~/k8s/ > /dev/null 2>&1
log_success "✅ 配置同步完成"

# 4. 部署服務（不等待）
log_info "🚀 部署服務..."
ssh $REMOTE_HOST "cd ~/k8s && microk8s kubectl apply -k overlays/test-environment" > /dev/null 2>&1
log_success "✅ 服務部署命令執行完成"

# 5. 立即檢查狀態（不等待）
log_info "📊 檢查當前狀態..."
echo ""

echo "📋 Pod 狀態:"
ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --no-headers" 2>/dev/null | while read line; do
    name=$(echo $line | awk '{print $1}')
    ready=$(echo $line | awk '{print $2}')
    status=$(echo $line | awk '{print $3}')
    restarts=$(echo $line | awk '{print $4}')
    
    if [ "$status" = "Running" ]; then
        echo -e "  ${GREEN}✅${NC} $name - $status (重啟: $restarts)"
    elif [ "$status" = "Pending" ]; then
        echo -e "  ${YELLOW}⏳${NC} $name - $status (重啟: $restarts)"
    elif [ "$status" = "ContainerCreating" ]; then
        echo -e "  ${BLUE}🔄${NC} $name - $status (重啟: $restarts)"
    else
        echo -e "  ${RED}❌${NC} $name - $status (重啟: $restarts)"
    fi
done

echo ""
echo "📊 統計信息:"
TOTAL_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l")
RUNNING_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l")
FAILED_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers 2>/dev/null | wc -l")

echo "  總 Pod 數: $TOTAL_PODS"
echo "  運行中: $RUNNING_PODS"
echo "  失敗: $FAILED_PODS"

if [ "$TOTAL_PODS" -gt 0 ]; then
    RUNNING_PERCENT=$(( (RUNNING_PODS * 100) / TOTAL_PODS ))
    echo "  運行率: ${RUNNING_PERCENT}%"
fi

echo ""
echo "🔍 有問題的服務:"
ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers 2>/dev/null" | while read line; do
    name=$(echo $line | awk '{print $1}')
    status=$(echo $line | awk '{print $3}')
    if [ "$status" != "Completed" ]; then
        echo -e "  ${RED}❌ $name - $status${NC}"
    fi
done

echo ""
echo "=========================================="
log_success "✅ 智能部署完成！"
echo "=========================================="
echo ""
echo "💡 後續操作:"
echo "  - 查看詳細狀態: ssh $REMOTE_HOST 'microk8s kubectl get pods -n $NAMESPACE'"
echo "  - 查看日誌: ssh $REMOTE_HOST 'microk8s kubectl logs -f <pod-name> -n $NAMESPACE'"
echo "  - 檢查服務: ./check-services.sh"
echo ""
echo "🌐 服務端點:"
echo "  - 主入口: http://192.168.1.183"
echo "  - API 文檔: http://192.168.1.183/api-docs"
echo ""
