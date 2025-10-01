#!/bin/bash

# 重啟失敗服務腳本
# 用途: 自動重啟有問題的服務

set -e

# 配置變量
REMOTE_HOST="home.worthwolf.top"
NAMESPACE="ruralneighbour-dev"

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
echo "🔄 Rural Neighbour 重啟失敗服務"
echo "=========================================="
echo ""

# 同步修復後的代碼
log_info "📁 同步修復後的代碼..."
rsync -avz /Users/jasonjia/codebase/ruralneighbour/ms-backend/services/ $REMOTE_HOST:/home/masterjia/services/ > /dev/null 2>&1
log_success "✅ 代碼同步完成"

# 同步修復後的 K8s 配置
log_info "📁 同步修復後的 K8s 配置..."
rsync -avz /Users/jasonjia/codebase/ruralneighbour/ms-backend/k8s/ $REMOTE_HOST:~/k8s/ > /dev/null 2>&1
log_success "✅ K8s 配置同步完成"

# 重新構建有問題的服務
log_info "🔨 重新構建有問題的服務..."

SERVICES_TO_REBUILD=(
    "payment-service"
    "location-service"
    "content-service"
)

for service in "${SERVICES_TO_REBUILD[@]}"; do
    log_info "🔨 重新構建 $service..."
    ssh $REMOTE_HOST "cd /home/masterjia/services/$service && docker build -t 127.0.0.1:32000/ruralneighbour/$service:latest . && docker push 127.0.0.1:32000/ruralneighbour/$service:latest" > /dev/null 2>&1
    log_success "✅ $service 重新構建完成"
done

# 重啟所有有問題的服務
log_info "🔄 重啟有問題的服務..."

FAILED_SERVICES=(
    "content-service"
    "location-service"
    "notification-service"
    "payment-service"
)

for service in "${FAILED_SERVICES[@]}"; do
    log_info "🔄 重啟 $service..."
    ssh $REMOTE_HOST "microk8s kubectl rollout restart deployment/$service -n $NAMESPACE" > /dev/null 2>&1
    log_success "✅ $service 重啟完成"
done

echo ""
log_info "⏳ 等待服務重啟..."
sleep 30

echo ""
log_info "📊 檢查重啟後的狀態..."
ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --no-headers | grep -E '(Error|CrashLoopBackOff)' | wc -l" | while read count; do
    if [ "$count" -eq 0 ]; then
        log_success "🎉 所有服務重啟成功！"
    else
        log_warning "⚠️ 還有 $count 個服務有問題"
    fi
done

echo ""
echo "=========================================="
log_success "✅ 服務重啟完成！"
echo "=========================================="
echo ""
echo "💡 後續操作:"
echo "  - 檢查服務狀態: ./check-services.sh"
echo "  - 初始化數據庫: ./init-databases.sh"
echo ""






