#!/bin/bash

# Rural Neighbour Secrets 管理工具
# 作者: AI Assistant
# 用途: 管理第三方服務的 secrets 配置

set -e

# 配置變量
PROJECT_ROOT="/Users/jasonjia/codebase/ruralneighbour"
SECRETS_DIR="${PROJECT_ROOT}/secrets"
REMOTE_HOST="home.worthwolf.top"
THIRD_PARTY_FILE="${SECRETS_DIR}/third-party-secrets.yaml"

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

# 檢查 secrets 目錄
check_secrets_dir() {
    if [ ! -d "$SECRETS_DIR" ]; then
        log_error "Secrets 目錄不存在: $SECRETS_DIR"
        exit 1
    fi
}

# 顯示 secrets 狀態
show_secrets_status() {
    log_info "檢查第三方 secrets 狀態..."
    
    if [ -f "$THIRD_PARTY_FILE" ]; then
        log_success "✅ 第三方 secrets 配置文件存在"
        echo "📁 文件位置: $THIRD_PARTY_FILE"
        echo "📋 包含的資源:"
        grep -E "^kind:|^  name:" -n "$THIRD_PARTY_FILE" | sed 's/^.*kind: /  - kind: /;s/^.*name: /    name: /'
        echo ""
    fi

    if [ -f "$SECRETS_DIR/example-env.yaml" ]; then
        log_success "✅ 測試環境 secrets 配置文件存在"
        echo "📁 文件位置: $SECRETS_DIR/example-env.yaml"
        echo "📋 包含的服務:"
        grep -E "^metadata:" -A 1 "$SECRETS_DIR/example-env.yaml" | grep "name:" | sed 's/.*name: /  - /'
        echo ""
        log_info "💡 這是測試環境的示例配置，包含所有第三方服務的示例值"
        log_info "💡 生產環境請使用雲端 Secret Manager 或替換為真實的 API 密鑰"
    else
        log_warning "⚠️ 測試環境 secrets 配置文件不存在"
        log_info "💡 請先創建配置文件:"
        log_info "   cp $SECRETS_DIR/example-env.yaml.template $SECRETS_DIR/example-env.yaml"
    fi
}

# 同步 secrets 到遠程服務器
sync_secrets() {
    log_info "同步 secrets 到遠程服務器..."
    
    if [ ! -f "$SECRETS_DIR/example-env.yaml" ]; then
        log_error "測試環境 secrets 配置文件不存在: $SECRETS_DIR/example-env.yaml"
        exit 1
    fi
    
    # 同步到遠程服務器
    rsync -avz "$SECRETS_DIR/" "$REMOTE_HOST:~/secrets/"
    
    log_success "✅ Secrets 同步完成"
}

# 應用 secrets 到 Kubernetes
apply_secrets() {
    log_info "應用 secrets 到 Kubernetes..."
    
    # 檢查遠程文件是否存在
    NEED_APPLY_EXAMPLE=0
    NEED_APPLY_THIRD_PARTY=0
    ssh "$REMOTE_HOST" "[ -f ~/secrets/example-env.yaml ]" && NEED_APPLY_EXAMPLE=1 || true
    ssh "$REMOTE_HOST" "[ -f ~/secrets/third-party-secrets.yaml ]" && NEED_APPLY_THIRD_PARTY=1 || true
    if [ "$NEED_APPLY_EXAMPLE" -eq 0 ] && [ "$NEED_APPLY_THIRD_PARTY" -eq 0 ]; then
        log_error "遠程 secrets 文件不存在，請先同步"
        exit 1
    fi
    
    # 應用 secrets
    ssh "$REMOTE_HOST" "
        cd ~/secrets
        if [ -f third-party-secrets.yaml ]; then
            microk8s kubectl apply -f third-party-secrets.yaml
        fi
        if [ -f example-env.yaml ]; then
            microk8s kubectl apply -f example-env.yaml
        fi
    "
    
    log_success "✅ Secrets 應用完成"
}

# 檢查 Kubernetes 中的 secrets
check_k8s_secrets() {
    log_info "檢查 Kubernetes 中的 secrets..."
    
    ssh "$REMOTE_HOST" "
        echo '📋 當前命名空間中的 secrets:'
        microk8s kubectl get secrets -n ruralneighbour-dev | grep -E '(auth-secrets|sendgrid-secrets|stripe|paypal|twilio|smtp|aws|google|safety|investment|geocoding|weather|analytics|monitoring|logging)' || echo '未找到第三方服務 secrets'
    "
}

# 刪除 secrets
delete_secrets() {
    log_info "刪除 Kubernetes 中的第三方 secrets..."
    
    ssh "$REMOTE_HOST" "
        microk8s kubectl delete -f ~/secrets/example-env.yaml --ignore-not-found=true
    "
    
    log_success "✅ Secrets 刪除完成"
}

# 創建 secrets 模板
create_template() {
    log_info "創建 secrets 模板文件..."
    
    if [ -f "$SECRETS_DIR/example-env.yaml" ]; then
        log_warning "⚠️ 配置文件已存在，是否覆蓋？(y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "取消創建模板"
            exit 0
        fi
    fi
    
    # 複製模板
    cp "$SECRETS_DIR/example-env.yaml" "$SECRETS_DIR/example-env.yaml.template"
    
    log_success "✅ 模板文件創建完成"
    log_info "📁 模板位置: $SECRETS_DIR/example-env.yaml.template"
    log_info "💡 這是測試環境的示例配置，生產環境請使用雲端 Secret Manager"
}

# 主函數
main() {
    check_secrets_dir
    
    case "$1" in
        "status")
            show_secrets_status
            ;;
        "sync")
            sync_secrets
            ;;
        "apply")
            apply_secrets
            ;;
        "check")
            check_k8s_secrets
            ;;
        "delete")
            delete_secrets
            ;;
        "template")
            create_template
            ;;
        "deploy")
            sync_secrets
            apply_secrets
            check_k8s_secrets
            ;;
        *)
            echo "使用方法:"
            echo "  $0 status     # 顯示 secrets 狀態"
            echo "  $0 sync       # 同步 secrets 到遠程服務器"
            echo "  $0 apply      # 應用 secrets 到 Kubernetes"
            echo "  $0 check      # 檢查 Kubernetes 中的 secrets"
            echo "  $0 delete     # 刪除 Kubernetes 中的 secrets"
            echo "  $0 template   # 創建 secrets 模板文件"
            echo "  $0 deploy     # 完整部署 (同步 + 應用 + 檢查)"
            echo ""
            echo "示例:"
            echo "  $0 status"
            echo "  $0 deploy"
            echo "  $0 check"
            ;;
    esac
}

# 執行主函數
main "$@"
