#!/bin/bash
# scripts/cleanup.sh - 清理部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认配置
ENVIRONMENT="development"
NAMESPACE="default"
KUBECTL_CMD="kubectl"
FORCE=false

# 显示帮助信息
show_help() {
    echo "RuralNeighbour Kubernetes 清理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -e, --environment ENV    清理环境 (development|staging|production) [默认: development]"
    echo "  -n, --namespace NS       命名空间 [默认: 根据环境自动设置]"
    echo "  -f, --force             强制删除，不询问确认"
    echo "  -h, --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --environment development"
    echo "  $0 --environment production --force"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证环境参数
case $ENVIRONMENT in
    development|staging|production)
        ;;
    *)
        echo -e "${RED}❌ 无效的环境: $ENVIRONMENT${NC}"
        echo "支持的环境: development, staging, production"
        exit 1
        ;;
esac

# 设置命名空间
if [ "$NAMESPACE" = "default" ]; then
    case $ENVIRONMENT in
        development)
            NAMESPACE="default"
            ;;
        staging)
            NAMESPACE="ruralneighbour-staging"
            ;;
        production)
            NAMESPACE="ruralneighbour"
            ;;
    esac
fi

# 设置 kubectl 命令
if command -v microk8s &> /dev/null; then
    KUBECTL_CMD="microk8s kubectl"
fi

echo -e "${BLUE}🧹 清理 RuralNeighbour 部署${NC}"
echo "=============================================="
echo -e "${YELLOW}环境: $ENVIRONMENT${NC}"
echo -e "${YELLOW}命名空间: $NAMESPACE${NC}"
echo -e "${YELLOW}Kubectl: $KUBECTL_CMD${NC}"

# 确认删除
if [ "$FORCE" = false ]; then
    echo -e "${RED}⚠️  警告: 这将删除 $NAMESPACE 命名空间中的所有资源${NC}"
    read -p "确定要继续吗? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消清理操作"
        exit 0
    fi
fi

# 删除应用
echo -e "${YELLOW}🗑️  删除应用...${NC}"
$KUBECTL_CMD delete -k overlays/$ENVIRONMENT --ignore-not-found=true

# 删除命名空间
echo -e "${YELLOW}🗑️  删除命名空间...${NC}"
$KUBECTL_CMD delete namespace $NAMESPACE --ignore-not-found=true

# 等待命名空间删除完成
echo -e "${YELLOW}⏳ 等待命名空间删除完成...${NC}"
$KUBECTL_CMD wait --for=delete namespace/$NAMESPACE --timeout=60s || true

echo -e "${GREEN}✅ 清理完成！${NC}"






