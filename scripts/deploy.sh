#!/bin/bash
# scripts/deploy.sh - 本地部署脚本

set -e

# 配置
REMOTE_HOST="home.worthwolf.top"
REMOTE_USER="masterjia"
REMOTE_PATH="/home/masterjia/ruralneighbour"
PROJECT_NAME="ruralneighbour"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 部署 RuralNeighbour 后端服务${NC}"
echo "=============================================="

# 检查参数
if [ "$1" = "quick" ]; then
    echo -e "${YELLOW}⚡ 快速部署模式（仅同步代码）${NC}"
    QUICK_DEPLOY=true
else
    echo -e "${YELLOW}🔨 完整部署模式（构建 + 部署）${NC}"
    QUICK_DEPLOY=false
fi

# 检查 SSH 连接
echo -e "${YELLOW}🔍 检查服务器连接...${NC}"
if ! ssh -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST "echo '连接成功'" 2>/dev/null; then
    echo -e "${RED}❌ 无法连接到服务器 $REMOTE_HOST${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 服务器连接正常${NC}"

# 同步代码到远程服务器
echo -e "${YELLOW}📤 同步代码到远程服务器...${NC}"
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='*.log' \
    ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/ms-backend/

echo -e "${GREEN}✅ 代码同步完成${NC}"

# 在远程服务器上执行部署
echo -e "${YELLOW}🔧 在远程服务器上执行部署...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << EOF
cd /home/masterjia/ruralneighbour/ms-backend

if [ "$QUICK_DEPLOY" = "true" ]; then
    echo "⚡ 快速部署模式..."
    cd k8s
    microk8s kubectl apply -k overlays/microk8s/
    microk8s kubectl rollout restart deployment/auth-service -n ruralneighbour
    microk8s kubectl rollout restart deployment/user-service -n ruralneighbour
    microk8s kubectl rollout restart deployment/request-service -n ruralneighbour
    echo "✅ 快速部署完成！"
else
    echo "🔧 检查 MicroK8s 环境..."
    if ! command -v microk8s &> /dev/null; then
        echo "❌ MicroK8s 未安装，正在安装..."
        sudo snap install microk8s --classic --channel=1.30/stable
        sudo usermod -a -G microk8s \$USER
        echo "✅ MicroK8s 安装完成"
    else
        echo "✅ MicroK8s 已安装"
    fi
    
    # 确保用户有 MicroK8s 权限
    sudo usermod -a -G microk8s \$USER
    
    echo "🚀 启动 MicroK8s..."
    if ! microk8s status | grep -q "microk8s is running"; then
        microk8s start
    fi
    
    echo "🔧 启用必要的 MicroK8s 插件..."
    microk8s enable dns storage ingress
    
    echo "⏳ 等待插件启动..."
    sleep 30
    
    echo "🔨 构建 Docker 镜像..."
    cd services
    
    # 生成依赖文件
    ./export_requirements.bash
    
    # 构建所有服务的镜像
    services=("auth-service" "user-service" "location-service" "request-service" "payment-service" "notification-service" "content-service" "safety-service")
    
    for service in "\${services[@]}"; do
        echo "🔨 构建 \$service 镜像..."
        cd \$service
        docker build -t neighbor-connect/\$service:latest .
        
        # 导入到 MicroK8s
        echo "📦 导入 \$service 镜像到 MicroK8s..."
        microk8s ctr images import - < \$(docker save neighbor-connect/\$service:latest)
        cd ..
    done
    
    echo "🚀 部署到 MicroK8s..."
    cd ../k8s
    
    # 创建命名空间
    microk8s kubectl create namespace ruralneighbour --dry-run=client -o yaml | microk8s kubectl apply -f -
    
    # 使用 Kustomize 部署
    microk8s kubectl apply -k overlays/microk8s/
    
    echo "⏳ 等待部署完成..."
    microk8s kubectl wait --for=condition=ready pod -l tier=backend --timeout=300s -n ruralneighbour || true
    
    echo "🧪 运行部署测试..."
    if [ -f "test_deployment.sh" ]; then
        chmod +x test_deployment.sh
        ./test_deployment.sh
    fi
fi

echo "📊 显示部署状态..."
microk8s kubectl get pods -n ruralneighbour
microk8s kubectl get services -n ruralneighbour
microk8s kubectl get ingress -n ruralneighbour

# 获取访问信息
MICROK8S_IP=\$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo "🌐 访问信息："
echo "  - MicroK8s IP: \$MICROK8S_IP"
echo "  - API 文档: http://\$MICROK8S_IP/api/v1/auth/docs"
echo "  - 健康检查: http://\$MICROK8S_IP/api/v1/auth/health"

echo "✅ 部署完成！"
EOF

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${BLUE}🌐 访问信息：${NC}"
echo "  - 服务器: $REMOTE_HOST"
echo "  - 项目路径: $REMOTE_PATH/ms-backend"
echo ""
echo -e "${YELLOW}🔧 管理命令：${NC}"
echo "1. SSH 连接到服务器:"
echo "   ssh $REMOTE_USER@$REMOTE_HOST"
echo ""
echo "2. 进入项目目录:"
echo "   cd $REMOTE_PATH/ms-backend"
echo ""
echo "3. 查看服务状态:"
echo "   microk8s kubectl get pods -n ruralneighbour"
echo ""
echo "4. 查看服务日志:"
echo "   microk8s kubectl logs -l app=auth-service -n ruralneighbour -f"
echo ""
echo "5. 重启服务:"
echo "   microk8s kubectl rollout restart deployment/auth-service -n ruralneighbour"
echo ""
echo "6. 快速部署:"
echo "   ./scripts/deploy.sh quick"

