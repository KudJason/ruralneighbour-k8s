#!/bin/bash

# 數據庫初始化腳本
# 用途: 自動創建所有微服務需要的數據庫

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
echo "🗄️ Rural Neighbour 數據庫初始化"
echo "=========================================="
echo ""

# 檢查 PostGIS 是否運行
log_info "🔍 檢查 PostGIS 數據庫狀態..."
if ssh $REMOTE_HOST "microk8s kubectl get pod postgis-pg-0 -n $NAMESPACE --no-headers | grep Running" > /dev/null 2>&1; then
    log_success "✅ PostGIS 數據庫正在運行"
else
    log_error "❌ PostGIS 數據庫未運行"
    exit 1
fi

# 等待數據庫完全就緒
log_info "⏳ 等待數據庫完全就緒..."
ssh $REMOTE_HOST "microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- pg_isready -U neighbor" > /dev/null 2>&1
log_success "✅ 數據庫連接正常"

# 定義需要創建的數據庫
DATABASES=(
    "auth_db"
    "user_db"
    "content_db"
    "request_db"
    "location_db"
    "notification_db"
    "payment_db"
    "rating_db"
    "safety_db"
    "investment_db"
)

log_info "📋 開始創建數據庫..."
echo ""

# 逐個創建數據庫
for db in "${DATABASES[@]}"; do
    log_info "🗄️ 創建數據庫: $db"
    
    if ssh $REMOTE_HOST "microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- psql -U neighbor -d postgres -c 'CREATE DATABASE $db;'" 2>/dev/null; then
        log_success "✅ $db 創建成功"
    else
        log_warning "⚠️ $db 可能已存在"
    fi
done

echo ""
log_info "🌍 為 location_db 安裝 PostGIS 擴展..."
if ssh $REMOTE_HOST "microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- psql -U neighbor -d location_db -c 'CREATE EXTENSION IF NOT EXISTS postgis;'" 2>/dev/null; then
    log_success "✅ PostGIS 擴展安裝成功"
else
    log_warning "⚠️ PostGIS 擴展可能已存在"
fi

echo ""
log_info "📊 驗證數據庫創建結果..."
echo ""

# 列出所有數據庫
ssh $REMOTE_HOST "microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- psql -U neighbor -d postgres -c '\l'" | grep -E "(auth_db|user_db|content_db|request_db|location_db|notification_db|payment_db|rating_db|safety_db|investment_db)"

echo ""
echo "=========================================="
log_success "🎉 數據庫初始化完成！"
echo "=========================================="
echo ""
echo "💡 後續操作:"
echo "  - 重啟有問題的服務: ./restart-failed-services.sh"
echo "  - 檢查服務狀態: ./check-services.sh"
echo ""






