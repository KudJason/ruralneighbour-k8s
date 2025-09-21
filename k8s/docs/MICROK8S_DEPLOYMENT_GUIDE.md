# MicroK8s 部署指南 - home.worthwolf.top

由于 MicroK8s 部署的复杂性，请按照以下步骤手动部署：

## 1. SSH 连接到服务器

```bash
ssh masterjia@home.worthwolf.top
```

## 2. 安装和配置 MicroK8s

```bash
# 安装 MicroK8s
sudo snap install microk8s --classic

# 将用户添加到 microk8s 组
sudo usermod -a -G microk8s masterjia

# 重新登录以应用组权限
exit
ssh masterjia@home.worthwolf.top

# 启动 MicroK8s
microk8s start

# 启用必要的插件
microk8s enable dns
microk8s enable storage
microk8s enable ingress
microk8s enable dashboard
```

## 3. 进入项目目录

```bash
cd /home/masterjia/ruralneighbour/ms-backend/k8s
```

## 4. 创建命名空间

```bash
microk8s kubectl create namespace ruralneighbour
```

## 5. 部署共享基础设施

```bash
# 创建 ConfigMaps
cat > postgres-config.yaml << 'EOF'
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
EOF

cat > redis-config.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: ruralneighbour
data:
  user-lifecycle-stream: "user_lifecycle"
  payment-stream: "payment_events"
  notification-stream: "notification_events"
EOF

microk8s kubectl apply -f postgres-config.yaml
microk8s kubectl apply -f redis-config.yaml

# 部署数据库和缓存
microk8s kubectl apply -f _shared/postgres-secrets.yaml -n ruralneighbour
microk8s kubectl apply -f _shared/redis-secrets.yaml -n ruralneighbour
microk8s kubectl apply -f _shared/postgres-deployment.yaml -n ruralneighbour
microk8s kubectl apply -f _shared/redis-deployment.yaml -n ruralneighbour
```

## 6. 等待基础设施启动

```bash
# 等待数据库和缓存启动
microk8s kubectl wait --for=condition=ready pod -l app=postgres-service --timeout=300s -n ruralneighbour
microk8s kubectl wait --for=condition=ready pod -l app=redis-service --timeout=300s -n ruralneighbour
```

## 7. 构建和导入 Docker 镜像

```bash
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
```

## 8. 修改部署文件以使用正确的命名空间

```bash
cd /home/masterjia/ruralneighbour/ms-backend/k8s

# 为每个服务创建修改后的部署文件
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
    echo "修改 $service 部署文件..."
    # 修改部署文件中的命名空间
    sed 's/namespace: default/namespace: ruralneighbour/g' $service/deployment.yaml > $service/deployment-ruralneighbour.yaml
    # 修改服务文件中的命名空间
    sed 's/namespace: default/namespace: ruralneighbour/g' $service/service.yaml > $service/service-ruralneighbour.yaml
done
```

## 9. 部署微服务

```bash
# 部署所有微服务
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
    echo "部署 $service..."
    microk8s kubectl apply -f $service/deployment-ruralneighbour.yaml
    microk8s kubectl apply -f $service/service-ruralneighbour.yaml
done
```

## 10. 部署 Ingress

```bash
# 修改 Ingress 文件以使用正确的命名空间
sed 's/namespace: default/namespace: ruralneighbour/g' _shared/ingress.yaml > _shared/ingress-ruralneighbour.yaml
microk8s kubectl apply -f _shared/ingress-ruralneighbour.yaml
```

## 11. 检查部署状态

```bash
# 查看所有资源
microk8s kubectl get all -n ruralneighbour

# 查看 Pod 状态
microk8s kubectl get pods -n ruralneighbour

# 查看服务状态
microk8s kubectl get services -n ruralneighbour

# 查看 Ingress 状态
microk8s kubectl get ingress -n ruralneighbour
```

## 12. 获取访问信息

```bash
# 获取 MicroK8s 节点 IP
MICROK8S_IP=$(microk8s kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo "MicroK8s IP: $MICROK8S_IP"

# 显示访问地址
echo "API 访问地址："
echo "  - 认证服务: http://$MICROK8S_IP/api/v1/auth/docs"
echo "  - 用户服务: http://$MICROK8S_IP/api/v1/users/docs"
echo "  - 位置服务: http://$MICROK8S_IP/api/v1/locations/docs"
echo "  - 请求服务: http://$MICROK8S_IP/api/v1/requests/docs"
echo "  - 支付服务: http://$MICROK8S_IP/api/v1/payments/docs"
echo "  - 通知服务: http://$MICROK8S_IP/api/v1/notifications/docs"
echo "  - 内容服务: http://$MICROK8S_IP/api/v1/content/docs"
echo "  - 安全服务: http://$MICROK8S_IP/api/v1/safety/docs"
```

## 13. 创建统一文档页面

```bash
# 创建统一文档页面
cat > combined-api-docs.html << EOF
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
                </div>
            </div>

            <div class="service-card">
                <h3>👤 用户服务 (User Service)</h3>
                <p>管理用户信息、个人资料和用户数据</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/users/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/users/redoc" target="_blank">ReDoc</a>
                </div>
            </div>

            <div class="service-card">
                <h3>📍 位置服务 (Location Service)</h3>
                <p>处理地理位置、地址管理和位置验证</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/locations/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/locations/redoc" target="_blank">ReDoc</a>
                </div>
            </div>

            <div class="service-card">
                <h3>📋 请求服务 (Request Service)</h3>
                <p>管理服务请求、任务分配和请求状态</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/requests/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/requests/redoc" target="_blank">ReDoc</a>
                </div>
            </div>

            <div class="service-card">
                <h3>💳 支付服务 (Payment Service)</h3>
                <p>处理支付、交易和支付方式管理</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/payments/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/payments/redoc" target="_blank">ReDoc</a>
                </div>
            </div>

            <div class="service-card">
                <h3>🔔 通知服务 (Notification Service)</h3>
                <p>发送通知、消息和事件处理</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/notifications/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/notifications/redoc" target="_blank">ReDoc</a>
                </div>
            </div>

            <div class="service-card">
                <h3>📰 内容服务 (Content Service)</h3>
                <p>管理新闻、文章和内容发布</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/content/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/content/redoc" target="_blank">ReDoc</a>
                </div>
            </div>

            <div class="service-card">
                <h3>🛡️ 安全服务 (Safety Service)</h3>
                <p>处理安全报告、争议和指标统计</p>
                <div class="service-links">
                    <a href="http://$MICROK8S_IP/api/v1/safety/docs" target="_blank">Swagger UI</a>
                    <a href="http://$MICROK8S_IP/api/v1/safety/redoc" target="_blank">ReDoc</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF

# 启动文档服务器
python3 -m http.server 8080 &
```

## 14. 管理命令

```bash
# 查看服务状态
microk8s kubectl get pods -n ruralneighbour

# 查看服务日志
microk8s kubectl logs -l app=auth-service -n ruralneighbour

# 重启服务
microk8s kubectl rollout restart deployment/auth-service -n ruralneighbour

# 删除服务
microk8s kubectl delete deployment auth-service -n ruralneighbour

# 删除整个命名空间
microk8s kubectl delete namespace ruralneighbour

# 查看 MicroK8s 状态
microk8s status

# 停止 MicroK8s
microk8s stop

# 启动 MicroK8s
microk8s start
```

## 15. 故障排除

### 如果 Pod 无法启动：

```bash
# 查看 Pod 详细信息
microk8s kubectl describe pod <pod-name> -n ruralneighbour

# 查看 Pod 日志
microk8s kubectl logs <pod-name> -n ruralneighbour

# 检查事件
microk8s kubectl get events -n ruralneighbour
```

### 如果服务无法访问：

```bash
# 检查 Ingress 状态
microk8s kubectl get ingress -n ruralneighbour

# 检查服务状态
microk8s kubectl get services -n ruralneighbour

# 检查端口转发
microk8s kubectl port-forward service/auth-service 8001:80 -n ruralneighbour
```

完成这些步骤后，您的所有微服务将在 MicroK8s 上运行，并且可以通过统一的文档页面访问所有 API 文档。








