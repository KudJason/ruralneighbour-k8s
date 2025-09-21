#!/bin/bash
# ms-backend/k8s/deploy_microk8s.sh
# 使用 MicroK8s 的部署脚本

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

echo -e "${BLUE}🚀 使用 MicroK8s 部署到 home.worthwolf.top${NC}"
echo "=============================================="

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
    $LOCAL_PATH/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

echo -e "${GREEN}✅ 代码同步完成${NC}"

# 在远程服务器上执行部署
echo -e "${YELLOW}🔧 在远程服务器上执行 MicroK8s 部署...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd /home/masterjia/ruralneighbour/ms-backend/k8s

echo "🔧 检查 MicroK8s 环境..."
if ! command -v microk8s &> /dev/null; then
    echo "❌ MicroK8s 未安装，正在安装..."
    sudo snap install microk8s --classic
    sudo usermod -a -G microk8s $USER
    echo "✅ MicroK8s 安装完成"
else
    echo "✅ MicroK8s 已安装"
fi

# 确保用户有 MicroK8s 权限
echo "🔐 配置 MicroK8s 权限..."
sudo usermod -a -G microk8s $USER

echo "🚀 启动 MicroK8s..."
if ! microk8s status | grep -q "microk8s is running"; then
    echo "启动 MicroK8s 集群..."
    microk8s start
else
    echo "MicroK8s 已在运行"
fi

echo "🔧 启用必要的 MicroK8s 插件..."
microk8s enable dns
microk8s enable storage
microk8s enable ingress
microk8s enable dashboard

echo "⏳ 等待插件启动..."
sleep 30

echo "🔧 构建 Docker 镜像..."
cd /home/masterjia/ruralneighbour/ms-backend/services

# 构建所有服务的镜像
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
    echo "构建 $service 镜像..."
    cd $service
    docker build -t neighbor-connect/$service:latest .
    microk8s ctr images import - < $(docker save neighbor-connect/$service:latest)
    cd ..
done

echo "🚀 部署到 MicroK8s..."
cd /home/masterjia/ruralneighbour/ms-backend/k8s

# 创建命名空间
microk8s kubectl create namespace ruralneighbour --dry-run=client -o yaml | microk8s kubectl apply -f -

# 部署共享基础设施
echo "📦 部署共享基础设施..."
microk8s kubectl apply -f _shared/postgres-secrets.yaml
microk8s kubectl apply -f _shared/redis-secrets.yaml
microk8s kubectl apply -f _shared/postgres-deployment.yaml
microk8s kubectl apply -f _shared/redis-deployment.yaml

echo "⏳ 等待基础设施启动..."
microk8s kubectl wait --for=condition=ready pod -l app=postgres-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=redis-service --timeout=300s -n ruralneighbour

echo "🔧 部署微服务..."
# 部署微服务
microk8s kubectl apply -f auth-service/ -n ruralneighbour
microk8s kubectl apply -f user-service/ -n ruralneighbour
microk8s kubectl apply -f location-service/ -n ruralneighbour
microk8s kubectl apply -f request-service/ -n ruralneighbour
microk8s kubectl apply -f payment-service/ -n ruralneighbour
microk8s kubectl apply -f notification-service/ -n ruralneighbour
microk8s kubectl apply -f content-service/ -n ruralneighbour
microk8s kubectl apply -f safety-service/ -n ruralneighbour

echo "⏳ 等待微服务启动..."
microk8s kubectl wait --for=condition=ready pod -l app=auth-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=user-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=location-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=request-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=payment-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=notification-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=content-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=safety-service --timeout=300s -n ruralneighbour

echo "🌐 部署 Ingress..."
microk8s kubectl apply -f _shared/ingress.yaml -n ruralneighbour

echo "🌐 获取服务访问信息..."
# 获取 MicroK8s 节点 IP
MICROK8S_IP=$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo "MicroK8s IP: $MICROK8S_IP"

# 显示服务状态
echo "📊 服务状态："
microk8s kubectl get pods -n ruralneighbour
microk8s kubectl get services -n ruralneighbour
microk8s kubectl get ingress -n ruralneighbour

echo "🔗 访问地址："
echo "  - API 文档: http://$MICROK8S_IP/api/v1/auth/docs"
echo "  - 健康检查: http://$MICROK8S_IP/api/v1/auth/health"
echo "  - 统一文档: http://$MICROK8S_IP:8080/combined-api-docs.html"

# 创建统一文档
echo "📚 创建统一 API 文档..."
chmod +x combine_api_docs.sh
# 修改脚本以使用 MicroK8s IP
sed -i "s/MINIKUBE_IP=\$(minikube ip)/MICROK8S_IP=\$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}')/g" combine_api_docs.sh
sed -i "s/BASE_URL=\"http:\/\/\$MINIKUBE_IP\"/BASE_URL=\"http:\/\/\$MICROK8S_IP\"/g" combine_api_docs.sh
./combine_api_docs.sh

# 启动文档服务器
echo "🌐 启动文档服务器..."
nohup python3 -m http.server 8080 > /dev/null 2>&1 &
echo "文档服务器已启动在端口 8080"

# 显示 MicroK8s 仪表板访问信息
echo "📊 MicroK8s 仪表板访问："
microk8s kubectl -n kube-system get secret/kubernetes-dashboard-token -o jsonpath='{.data.token}' | base64 -d
echo ""
echo "访问仪表板: https://$MICROK8S_IP:16443"
echo "使用上面的令牌进行登录"

EOF

echo ""
echo -e "${GREEN}✅ MicroK8s 部署完成！${NC}"
echo ""
echo -e "${BLUE}🌐 访问信息：${NC}"
echo "  - 服务器: $REMOTE_HOST"
echo "  - 统一文档: http://$REMOTE_HOST:8080/combined-api-docs.html"
echo "  - MicroK8s 仪表板: https://$REMOTE_HOST:16443"
echo ""
echo -e "${YELLOW}🔧 管理命令：${NC}"
echo "1. SSH 连接到服务器:"
echo "   ssh $REMOTE_USER@$REMOTE_HOST"
echo ""
echo "2. 进入项目目录:"
echo "   cd $REMOTE_PATH/ms-backend/k8s"
echo ""
echo "3. 查看服务状态:"
echo "   microk8s kubectl get pods -n ruralneighbour"
echo "   microk8s kubectl get services -n ruralneighbour"
echo ""
echo "4. 查看服务日志:"
echo "   microk8s kubectl logs -l app=auth-service -n ruralneighbour"
echo ""
echo "5. 重启服务:"
echo "   microk8s kubectl rollout restart deployment/auth-service -n ruralneighbour"
echo ""
echo "6. 停止所有服务:"
echo "   microk8s kubectl delete namespace ruralneighbour"








