#!/bin/bash

# Rural Neighbour 自動化部署測試腳本
# 作者: AI Assistant
# 用途: 自動構建、推送鏡像並部署到 MicroK8s（測試環境 - 單副本）

set -e  # 遇到錯誤立即退出

# 配置變量
REMOTE_HOST="home.worthwolf.top"
REGISTRY_HOST="127.0.0.1:32000"
NAMESPACE="ruralneighbour-dev"
PROJECT_ROOT="/Users/jasonjia/codebase/ruralneighbour/ms-backend"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查遠程連接
check_remote_connection() {
    log_info "檢查遠程服務器連接..."
    if ssh -o ConnectTimeout=10 $REMOTE_HOST "echo 'Connection successful'" > /dev/null 2>&1; then
        log_success "遠程服務器連接正常"
    else
        log_error "無法連接到遠程服務器 $REMOTE_HOST"
        exit 1
    fi
}

# 檢查 Docker 服務
check_docker_service() {
    log_info "檢查遠程 Docker 服務..."
    if ssh $REMOTE_HOST "docker info" > /dev/null 2>&1; then
        log_success "Docker 服務正常"
    else
        log_error "Docker 服務異常，請檢查權限"
        exit 1
    fi
}

# 檢查 MicroK8s 服務
check_microk8s_service() {
    log_info "檢查 MicroK8s 服務..."
    if ssh $REMOTE_HOST "microk8s status" > /dev/null 2>&1; then
        log_success "MicroK8s 服務正常"
    else
        log_error "MicroK8s 服務異常"
        exit 1
    fi
}

# 同步代碼到遠程服務器
sync_code() {
    log_info "同步代碼到遠程服務器..."
    
    # 創建遠程目錄
    ssh $REMOTE_HOST "mkdir -p ~/services"
    
    # 同步服務代碼
    rsync -avz --delete \
        --exclude='.venv/' \
        --exclude='__pycache__/' \
        --exclude='.git/' \
        --exclude='*.db' \
        --exclude='*.pyc' \
        --exclude='node_modules/' \
        $PROJECT_ROOT/services/ $REMOTE_HOST:~/services/
    
    log_success "代碼同步完成"
}

# 構建所有服務鏡像
build_images() {
    log_info "開始構建所有服務鏡像..."
    
    local services=(
        "auth-service"
        "user-service"
        "content-service"
        "request-service"
        "location-service"
        "notification-service"
        "payment-service"
        "rating-service"
        "safety-service"
        "investment-service"
    )
    
    local total=${#services[@]}
    local current=0
    
    for service in "${services[@]}"; do
        current=$((current + 1))
        log_info "[$current/$total] 構建 $service 鏡像..."
        echo "  📦 正在構建 $service..."
        
        # 構建鏡像
        if ssh $REMOTE_HOST "
            cd ~/services/$service
            echo '開始構建 $service...'
            docker build -t $REGISTRY_HOST/ruralneighbour/$service:latest .
            echo '構建完成'
        "; then
            log_success "✅ $service 鏡像構建成功"
        else
            log_error "❌ $service 鏡像構建失敗"
            exit 1
        fi
        echo ""
    done
    
    log_success "🎉 所有鏡像構建完成"
}

# 應用第三方 secrets（如果存在）
apply_third_party_secrets() {
    log_info "🔐 檢查第三方 secrets 配置..."
    
    # 檢查本地是否有測試環境 secrets 文件
    local secrets_file="/Users/jasonjia/codebase/ruralneighbour/secrets/example-env.yaml"
    if [ -f "$secrets_file" ]; then
        log_info "📋 發現測試環境 secrets 配置文件，正在同步..."
        rsync -avz /Users/jasonjia/codebase/ruralneighbour/secrets/ $REMOTE_HOST:~/secrets/
        
        log_info "🚀 應用測試環境 secrets..."
        ssh $REMOTE_HOST "
            cd ~/secrets
            microk8s kubectl apply -f example-env.yaml
        "
        log_success "✅ 測試環境 secrets 應用完成"
    else
        log_warning "⚠️ 未發現測試環境 secrets 配置文件"
        log_info "💡 這是測試環境的示例配置，包含所有第三方服務的示例值"
        log_info "💡 生產環境請使用雲端 Secret Manager"
    fi
}

# 推送所有鏡像到 registry
push_images() {
    log_info "推送所有鏡像到 registry..."
    
    local services=(
        "auth-service"
        "user-service"
        "content-service"
        "request-service"
        "location-service"
        "notification-service"
        "payment-service"
        "rating-service"
        "safety-service"
        "investment-service"
    )
    
    local total=${#services[@]}
    local current=0
    
    for service in "${services[@]}"; do
        current=$((current + 1))
        log_info "[$current/$total] 推送 $service 鏡像..."
        echo "  🚀 正在推送 $service..."
        
        # 推送鏡像
        if ssh $REMOTE_HOST "docker push $REGISTRY_HOST/ruralneighbour/$service:latest"; then
            log_success "✅ $service 鏡像推送成功"
        else
            log_error "❌ $service 鏡像推送失敗"
            exit 1
        fi
        echo ""
    done
    
    log_success "🎉 所有鏡像推送完成"
}

# 部署到 MicroK8s
deploy_to_k8s() {
    log_info "部署到 MicroK8s（測試環境 - 強制重建）..."
    
    # 強制刪除現有命名空間（測試環境）
    log_info "🧹 清理現有測試環境..."
    echo "  📋 刪除命名空間 $NAMESPACE..."
    ssh $REMOTE_HOST "microk8s kubectl delete namespace $NAMESPACE --ignore-not-found=true --force --grace-period=0"
    
    # 等待命名空間完全刪除
    log_info "⏳ 等待命名空間完全清理..."
    ssh $REMOTE_HOST "microk8s kubectl wait --for=delete namespace/$NAMESPACE --timeout=60s || true"
    
    # 創建新的命名空間
    log_info "🏗️ 創建新的測試環境命名空間..."
    ssh $REMOTE_HOST "microk8s kubectl create namespace $NAMESPACE"
    
    # 同步 k8s 配置
    log_info "📁 同步 K8s 配置..."
    echo "  📦 正在同步配置文件..."
    rsync -avz $PROJECT_ROOT/k8s/ $REMOTE_HOST:~/k8s/
    
    # 檢查並應用第三方 secrets（如果存在）
    apply_third_party_secrets
    
    # 應用測試環境配置
    log_info "🚀 應用測試環境配置..."
    echo "  ⚙️ 正在部署服務..."
    ssh $REMOTE_HOST "
        cd ~/k8s
        microk8s kubectl apply -k overlays/test-environment
    "
    
    log_success "✅ Kubernetes 部署完成"
}

# 檢查服務狀態（不等待）
check_services_status() {
    log_info "📊 檢查服務狀態..."
    
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
    
    log_success "✅ 服務狀態檢查完成"
}

# 初始化數據庫
init_database() {
    log_info "初始化數據庫..."
    
    ssh $REMOTE_HOST "
        # 等待 PostGIS 就緒
        microk8s kubectl wait --for=condition=ready pod -l app=postgis-pg -n $NAMESPACE --timeout=120s
        
        # 創建數據庫和用戶
        microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- psql -U neighbor -d postgres -c \"
            CREATE USER IF NOT EXISTS neighbor WITH PASSWORD 'password';
            CREATE DATABASE IF NOT EXISTS auth_db;
            CREATE DATABASE IF NOT EXISTS user_db;
            CREATE DATABASE IF NOT EXISTS content_db;
            CREATE DATABASE IF NOT EXISTS request_db;
            CREATE DATABASE IF NOT EXISTS location_db;
            CREATE DATABASE IF NOT EXISTS notification_db;
            CREATE DATABASE IF NOT EXISTS payment_db;
            CREATE DATABASE IF NOT EXISTS rating_db;
            CREATE DATABASE IF NOT EXISTS safety_db;
            CREATE DATABASE IF NOT EXISTS investment_db;
            GRANT ALL PRIVILEGES ON DATABASE auth_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE user_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE content_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE request_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE location_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE notification_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE payment_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE rating_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE safety_db TO neighbor;
            GRANT ALL PRIVILEGES ON DATABASE investment_db TO neighbor;
        \"
        
        # 為 location_db 安裝 PostGIS 擴展
        microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- psql -U neighbor -d location_db -c \"
            CREATE EXTENSION IF NOT EXISTS postgis;
        \"
    "
    
    log_success "數據庫初始化完成"
}

# 檢查服務狀態
check_service_status() {
    log_info "檢查服務狀態..."
    
    echo ""
    echo "=== Pod 狀態 ==="
    ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE"
    
    echo ""
    echo "=== 服務狀態 ==="
    ssh $REMOTE_HOST "microk8s kubectl get svc -n $NAMESPACE"
    
    echo ""
    echo "=== Ingress 狀態 ==="
    ssh $REMOTE_HOST "microk8s kubectl get ingress -n $NAMESPACE"
    
    # 測試健康檢查
    echo ""
    echo "=== 健康檢查測試 ==="
    local ingress_ip=$(ssh $REMOTE_HOST "microk8s kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'")
    if [ ! -z "$ingress_ip" ]; then
        echo "測試健康檢查端點: http://$ingress_ip/health"
        ssh $REMOTE_HOST "curl -s http://$ingress_ip/health || echo '健康檢查失敗'"
    fi
}

# 清理函數
cleanup() {
    log_info "清理資源..."
    ssh $REMOTE_HOST "
        microk8s kubectl delete namespace $NAMESPACE --ignore-not-found=true
    "
    log_success "清理完成"
}

# 主函數
main() {
    echo "=========================================="
    echo "🚀 Rural Neighbour 自動化部署測試"
    echo "=========================================="
    echo ""
    
    # 檢查參數
    if [ "$1" = "cleanup" ]; then
        cleanup
        exit 0
    fi
    
    # 執行部署流程
    check_remote_connection
    check_docker_service
    check_microk8s_service
    sync_code
    build_images
    push_images
    deploy_to_k8s
    check_services_status
    init_database
    check_service_status
    
    echo ""
    echo "=========================================="
    log_success "🎉 測試環境部署完成！"
    echo "=========================================="
    echo ""
    echo "📋 服務端點:"
    echo "   - 主入口: http://192.168.1.183"
    echo "   - API 文檔: http://192.168.1.183/api-docs"
    echo "   - 健康檢查: http://192.168.1.183/health"
    echo ""
    echo "🔧 管理命令:"
    echo "   - 查看 Pod: ssh $REMOTE_HOST 'microk8s kubectl get pods -n $NAMESPACE'"
    echo "   - 查看日誌: ssh $REMOTE_HOST 'microk8s kubectl logs -f <pod-name> -n $NAMESPACE'"
    echo "   - 清理部署: $0 cleanup"
    echo ""
    echo "ℹ️  注意: 這是測試環境，所有服務都配置為單副本"
    echo ""
}

# 執行主函數
main "$@"
