#!/bin/bash
# scripts/deploy.sh - 统一部署脚本

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
DRY_RUN=false
VERBOSE=false

# 显示帮助信息
show_help() {
    echo "RuralNeighbour Kubernetes 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -e, --environment ENV    部署环境 (development|staging|production) [默认: development]"
    echo "  -n, --namespace NS       命名空间 [默认: 根据环境自动设置]"
    echo "  -d, --dry-run           仅显示将要执行的命令，不实际执行"
    echo "  -v, --verbose           显示详细输出"
    echo "  -h, --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --environment development"
    echo "  $0 --environment production --dry-run"
    echo "  $0 --environment staging --namespace test"
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
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
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

# 设置覆盖层路径
OVERLAY_PATH="overlays/$ENVIRONMENT"

echo -e "${BLUE}🚀 部署 RuralNeighbour 到 $ENVIRONMENT 环境${NC}"
echo "=============================================="
echo -e "${YELLOW}环境: $ENVIRONMENT${NC}"
echo -e "${YELLOW}命名空间: $NAMESPACE${NC}"
echo -e "${YELLOW}覆盖层: $OVERLAY_PATH${NC}"
echo -e "${YELLOW}Kubectl: $KUBECTL_CMD${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}🔍 干运行模式${NC}"
fi

# 检查覆盖层是否存在
if [ ! -d "$OVERLAY_PATH" ]; then
    echo -e "${RED}❌ 覆盖层不存在: $OVERLAY_PATH${NC}"
    exit 1
fi

# 检查 .env 文件
if [ ! -f "$OVERLAY_PATH/.env" ]; then
    echo -e "${YELLOW}⚠️  警告: $OVERLAY_PATH/.env 文件不存在${NC}"
    echo "请确保环境配置文件存在"
fi

# 创建命名空间
echo -e "${YELLOW}📦 创建命名空间...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo "$KUBECTL_CMD create namespace $NAMESPACE --dry-run=client -o yaml | $KUBECTL_CMD apply -f -"
else
    $KUBECTL_CMD create namespace $NAMESPACE --dry-run=client -o yaml | $KUBECTL_CMD apply -f -
fi

# 部署应用
echo -e "${YELLOW}🚀 部署应用...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo "$KUBECTL_CMD apply -k $OVERLAY_PATH"
else
    $KUBECTL_CMD apply -k $OVERLAY_PATH
fi

# 等待部署完成
if [ "$DRY_RUN" = false ]; then
    echo -e "${YELLOW}⏳ 等待部署完成...${NC}"
    $KUBECTL_CMD wait --for=condition=ready pod -l tier=backend --timeout=300s -n $NAMESPACE || true
fi

# 显示部署状态
echo -e "${YELLOW}📊 部署状态:${NC}"
if [ "$DRY_RUN" = true ]; then
    echo "$KUBECTL_CMD get pods -n $NAMESPACE"
    echo "$KUBECTL_CMD get services -n $NAMESPACE"
    echo "$KUBECTL_CMD get ingress -n $NAMESPACE"
else
    $KUBECTL_CMD get pods -n $NAMESPACE
    echo ""
    $KUBECTL_CMD get services -n $NAMESPACE
    echo ""
    $KUBECTL_CMD get ingress -n $NAMESPACE
fi

# 运行测试
if [ "$DRY_RUN" = false ] && [ -f "test_deployment.sh" ]; then
    echo -e "${YELLOW}🧪 运行部署测试...${NC}"
    chmod +x test_deployment.sh
    ./test_deployment.sh
fi

echo -e "${GREEN}✅ 部署完成！${NC}"