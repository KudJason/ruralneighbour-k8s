#!/bin/bash

# Rural Neighbour 生產環境自動化部署腳本
# 作者: AI Assistant
# 用途: 自動構建、推送鏡像並部署到 MicroK8s（生產環境 - 多副本）

set -e  # 遇到錯誤立即退出

# 配置變量
REMOTE_HOST="home.worthwolf.top"
REGISTRY_HOST="127.0.0.1:32000"
NAMESPACE="ruralneighbour-prod"
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
    
    for service in "${services[@]}"; do
        log_info "構建 $service 鏡像..."
        
        ssh $REMOTE_HOST "
            cd ~/services/$service
            docker build -t $REGISTRY_HOST/ruralneighbour/$service:latest .
        "
        
        if [ $? -eq 0 ]; then
            log_success "$service 鏡像構建成功"
        else
            log_error "$service 鏡像構建失敗"
            exit 1
        fi
    done
    
    log_success "所有鏡像構建完成"
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
    
    for service in "${services[@]}"; do
        log_info "推送 $service 鏡像..."
        
        ssh $REMOTE_HOST "docker push $REGISTRY_HOST/ruralneighbour/$service:latest"
        
        if [ $? -eq 0 ]; then
            log_success "$service 鏡像推送成功"
        else
            log_error "$service 鏡像推送失敗"
            exit 1
        fi
    done
    
    log_success "所有鏡像推送完成"
}

# 部署到 MicroK8s
deploy_to_k8s() {
    log_info "部署到 MicroK8s（生產環境）..."
    
    # 創建命名空間
    ssh $REMOTE_HOST "microk8s kubectl create namespace $NAMESPACE --dry-run=client -o yaml | microk8s kubectl apply -f -"
    
    # 同步 k8s 配置
    rsync -avz $PROJECT_ROOT/k8s/ $REMOTE_HOST:~/k8s/
    
    # 應用生產環境配置
    ssh $REMOTE_HOST "
        cd ~/k8s
        microk8s kubectl apply -k overlays/production
    "
    
    log_success "Kubernetes 部署完成"
}

# 等待服務啟動
wait_for_services() {
    log_info "等待服務啟動..."
    
    # 等待 StatefulSet 就緒
    ssh $REMOTE_HOST "microk8s kubectl wait --for=condition=ready pod -l app=postgis-pg -n $NAMESPACE --timeout=300s"
    
    # 等待 Redis 就緒
    ssh $REMOTE_HOST "microk8s kubectl wait --for=condition=ready pod -l app=redis-service -n $NAMESPACE --timeout=120s"
    
    # 使用生產環境配置（保持原有的副本數配置）
    log_info "使用生產環境配置（多副本 + 生產資源限制）..."

    # 等待所有 deployment 就緒
    ssh $REMOTE_HOST "microk8s kubectl wait --for=condition=available deployment --all -n $NAMESPACE --timeout=300s"
    
    log_success "所有服務啟動完成"
}

# 初始化數據庫
init_database() {
    log_info "初始化數據庫..."
    
    ssh $REMOTE_HOST "
        # 等待 PostGIS 就緒
        microk8s kubectl wait --for=condition=ready pod -l app=postgis-pg -n $NAMESPACE --timeout=120s
        
        # 逐個創建數據庫
        for db in auth_db user_db content_db request_db location_db notification_db payment_db rating_db safety_db investment_db; do
            echo \"Creating database: \$db\"
            microk8s kubectl exec -n $NAMESPACE postgis-pg-0 -- psql -U neighbor -d postgres -c \"CREATE DATABASE \$db;\" 2>/dev/null || echo \"Database \$db may already exist\"
        done
        
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
    echo "🚀 Rural Neighbour 生產環境自動化部署"
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
    wait_for_services
    init_database
    check_service_status
    
    echo ""
    echo "=========================================="
    log_success "🎉 生產環境部署完成！"
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
    echo "ℹ️  注意: 這是生產環境，使用多副本和高資源配置"
    echo ""
}

# 執行主函數
main "$@"







