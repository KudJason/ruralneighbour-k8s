#!/bin/bash
# ms-backend/k8s/deploy_to_home.sh
# 部署到 home.worthwolf.top 服务器的脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 服务器配置
REMOTE_HOST="home.worthwolf.top"
REMOTE_USER="masterjia"
REMOTE_PATH="/home/masterjia/ruralneighbour"
LOCAL_PATH="/Users/jasonjia/codebase/ruralneighbour"

echo -e "${BLUE}🚀 部署到 home.worthwolf.top 服务器${NC}"
echo "=============================================="

# 检查 SSH 连接
echo -e "${YELLOW}🔍 检查服务器连接...${NC}"
if ! ssh -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST "echo '连接成功'" 2>/dev/null; then
    echo -e "${RED}❌ 无法连接到服务器 $REMOTE_HOST${NC}"
    echo "请检查："
    echo "1. SSH 密钥是否正确配置"
    echo "2. 服务器是否运行"
    echo "3. 网络连接是否正常"
    exit 1
fi
echo -e "${GREEN}✅ 服务器连接正常${NC}"

# 检查远程目录
echo -e "${YELLOW}📁 检查远程目录...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH"

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
    $LOCAL_PATH/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

echo -e "${GREEN}✅ 代码同步完成${NC}"

# 在远程服务器上执行部署
echo -e "${YELLOW}🔧 在远程服务器上执行部署...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd /home/masterjia/ruralneighbour/ms-backend/k8s

echo "🔧 检查 Docker 和 Kubernetes 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安装，正在安装..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
fi

if ! command -v minikube &> /dev/null; then
    echo "❌ minikube 未安装，正在安装..."
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    sudo install minikube-linux-amd64 /usr/local/bin/minikube
fi

echo "🚀 启动 Minikube..."
if ! minikube status &> /dev/null; then
    echo "启动 Minikube 集群..."
    minikube start --driver=docker --memory=4096 --cpus=2
else
    echo "Minikube 已在运行"
fi

echo "🔧 构建 Docker 镜像..."
cd /home/masterjia/ruralneighbour/ms-backend/services

# 构建所有服务的镜像
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
    echo "构建 $service 镜像..."
    cd $service
    docker build -t neighbor-connect/$service:latest .
    minikube image load neighbor-connect/$service:latest
    cd ..
done

echo "🚀 部署到 Kubernetes..."
cd /home/masterjia/ruralneighbour/ms-backend/k8s

# 设置镜像注册表为本地
export IMAGE_REGISTRY="neighbor-connect"

# 执行部署
chmod +x deploy.sh
./deploy.sh

echo "🌐 获取服务访问信息..."
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"
echo "API Base URL: http://$MINIKUBE_IP/api/v1"

# 显示服务状态
echo "📊 服务状态："
kubectl get pods
kubectl get services
kubectl get ingress

echo "🔗 访问地址："
echo "  - API 文档: http://$MINIKUBE_IP/api/v1/auth/docs"
echo "  - 健康检查: http://$MINIKUBE_IP/api/v1/auth/health"
echo "  - 统一文档: http://$MINIKUBE_IP:8080/combined-api-docs.html"

# 创建统一文档
echo "📚 创建统一 API 文档..."
chmod +x combine_api_docs.sh
./combine_api_docs.sh

# 启动文档服务器
echo "🌐 启动文档服务器..."
nohup python3 -m http.server 8080 > /dev/null 2>&1 &
echo "文档服务器已启动在端口 8080"

EOF

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${BLUE}🌐 访问信息：${NC}"
echo "  - 服务器: $REMOTE_HOST"
echo "  - 用户: $REMOTE_USER"
echo "  - 项目路径: $REMOTE_PATH"
echo ""
echo -e "${YELLOW}🔧 后续操作：${NC}"
echo "1. SSH 连接到服务器:"
echo "   ssh $REMOTE_USER@$REMOTE_HOST"
echo ""
echo "2. 进入项目目录:"
echo "   cd $REMOTE_PATH/ms-backend/k8s"
echo ""
echo "3. 查看服务状态:"
echo "   kubectl get pods"
echo "   kubectl get services"
echo ""
echo "4. 访问统一文档:"
echo "   http://$REMOTE_HOST:8080/combined-api-docs.html"
echo ""
echo "5. 查看 Minikube 状态:"
echo "   minikube status"
echo "   minikube ip"








