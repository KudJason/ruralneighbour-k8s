#!/bin/bash
# ms-backend/k8s/deploy_microk8s_optimized.sh
# 优化的 MicroK8s 部署脚本

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

echo -e "${BLUE}🚀 使用 MicroK8s 部署到 home.worthwolf.top (优化版)${NC}"
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
    echo "⚠️  请重新登录以应用组权限，然后重新运行此脚本"
    exit 1
else
    echo "✅ MicroK8s 已安装"
fi

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
    # 将镜像导入到 MicroK8s
    docker save neighbor-connect/$service:latest | microk8s ctr images import -
    cd ..
done

echo "🚀 部署到 MicroK8s..."
cd /home/masterjia/ruralneighbour/ms-backend/k8s

# 创建命名空间
microk8s kubectl create namespace ruralneighbour --dry-run=client -o yaml | microk8s kubectl apply -f -

# 创建 ConfigMaps
echo "📦 创建 ConfigMaps..."
cat > postgres-config.yaml << 'EOL'
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
  namespace: ruralneighbour
data:
  auth-db: "auth_db"
  user-db: "user_db"
  location-db: "location_db"
  request-db: "request_db"
  payment-db: "payment_db"
  notification-db: "notification_db"
  content-db: "content_db"
  safety-db: "safety_db"
EOL

cat > redis-config.yaml << 'EOL'
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: ruralneighbour
data:
  user-lifecycle-stream: "user_lifecycle"
  payment-stream: "payment_events"
  notification-stream: "notification_events"
EOL

microk8s kubectl apply -f postgres-config.yaml
microk8s kubectl apply -f redis-config.yaml

# 部署共享基础设施
echo "📦 部署共享基础设施..."
microk8s kubectl apply -f _shared/postgres-secrets.yaml -n ruralneighbour
microk8s kubectl apply -f _shared/redis-secrets.yaml -n ruralneighbour
microk8s kubectl apply -f _shared/postgres-deployment.yaml -n ruralneighbour
microk8s kubectl apply -f _shared/redis-deployment.yaml -n ruralneighbour

echo "⏳ 等待基础设施启动..."
microk8s kubectl wait --for=condition=ready pod -l app=postgres-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=redis-service --timeout=300s -n ruralneighbour

echo "🔧 部署微服务..."
# 修改所有部署文件以使用正确的命名空间
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
    echo "部署 $service..."
    # 修改部署文件中的命名空间
    sed 's/namespace: default/namespace: ruralneighbour/g' $service/deployment.yaml > $service/deployment-ruralneighbour.yaml
    microk8s kubectl apply -f $service/deployment-ruralneighbour.yaml
    microk8s kubectl apply -f $service/service.yaml -n ruralneighbour
done

echo "⏳ 等待微服务启动..."
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
    echo "等待 $service 启动..."
    microk8s kubectl wait --for=condition=ready pod -l app=$service --timeout=300s -n ruralneighbour
done

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
cat > combined-api-docs.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Rural Neighbor Connect - 统一 API 文档</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .service-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #fafafa; }
        .service-card h3 { color: #007bff; margin-top: 0; }
        .service-card p { color: #666; margin: 10px 0; }
        .service-links { margin-top: 15px; }
        .service-links a { display: inline-block; margin: 5px 10px 5px 0; padding: 8px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; }
        .service-links a:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Rural Neighbor Connect - 统一 API 文档</h1>
        <p style="text-align: center; color: #666;">所有微服务的 API 文档入口</p>
        
        <div class="service-grid">
            <div class="service-card">
                <h3>🔐 认证服务 (Auth Service)</h3>
                <p>处理用户认证、登录、注册和令牌管理</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/auth/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/auth/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/auth/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>👤 用户服务 (User Service)</h3>
                <p>管理用户信息、个人资料和用户数据</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/users/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/users/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/users/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>📍 位置服务 (Location Service)</h3>
                <p>处理地理位置、地址管理和位置验证</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/locations/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/locations/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/locations/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>📋 请求服务 (Request Service)</h3>
                <p>管理服务请求、任务分配和请求状态</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/requests/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/requests/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/requests/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>💳 支付服务 (Payment Service)</h3>
                <p>处理支付、交易和支付方式管理</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/payments/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/payments/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/payments/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>🔔 通知服务 (Notification Service)</h3>
                <p>发送通知、消息和事件处理</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/notifications/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/notifications/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/notifications/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>📰 内容服务 (Content Service)</h3>
                <p>管理新闻、文章和内容发布</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/content/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/content/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/content/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>🛡️ 安全服务 (Safety Service)</h3>
                <p>处理安全报告、争议和指标统计</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/safety/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/safety/redoc" target="_blank">ReDoc</a>
                    <a href="http://$MICROK8S_IP/api/v1/safety/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>📊 服务状态</h3>
            <p>要查看服务状态，请在服务器上运行：</p>
            <code>microk8s kubectl get pods -n ruralneighbour</code>
        </div>
    </div>
</body>
</html>
EOL

# 启动文档服务器
echo "🌐 启动文档服务器..."
nohup python3 -m http.server 8080 > /dev/null 2>&1 &
echo "文档服务器已启动在端口 8080"

# 显示 MicroK8s 仪表板访问信息
echo "📊 MicroK8s 仪表板访问："
DASHBOARD_TOKEN=$(microk8s kubectl -n kube-system get secret/kubernetes-dashboard-token -o jsonpath='{.data.token}' | base64 -d)
echo "仪表板令牌: $DASHBOARD_TOKEN"
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








