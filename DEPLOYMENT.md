# RuralNeighbour 后端部署指南

## 概述

本项目使用 GitHub Actions 进行自动化构建和部署，支持以下部署方式：

1. **GitHub Actions 自动部署**（推荐）
2. **本地脚本部署**
3. **手动部署**

## GitHub Actions 部署

### 设置

1. **配置 GitHub Secrets**：

   - 进入仓库设置 → Secrets and variables → Actions
   - 添加 `SSH_PRIVATE_KEY`：远程服务器的 SSH 私钥

2. **生成 SSH 密钥**：
   ```bash
   ssh-keygen -t rsa -b 4096 -C "github-actions@ruralneighbour" -f ~/.ssh/github_actions_key
   ssh-copy-id -i ~/.ssh/github_actions_key.pub masterjia@home.worthwolf.top
   ```

### 工作流

- **自动触发**：推送到 `main` 或 `develop` 分支
- **手动触发**：在 GitHub Actions 页面手动运行
- **快速部署**：仅同步代码，不重新构建镜像
- **回滚**：回滚到上一个版本

## 本地脚本部署

### 完整部署

```bash
# 构建镜像并部署
./scripts/deploy.sh
```

### 快速部署

```bash
# 仅同步代码并重新部署
./scripts/deploy.sh quick
```

## 手动部署

### 1. 同步代码

```bash
rsync -avz --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='*.log' \
  ./ masterjia@home.worthwolf.top:/home/masterjia/ruralneighbour/ms-backend/
```

### 2. 远程构建和部署

```bash
ssh masterjia@home.worthwolf.top << 'EOF'
cd /home/masterjia/ruralneighbour/ms-backend

# 构建镜像
cd services
./export_requirements.bash
for service in auth-service user-service location-service request-service payment-service notification-service content-service safety-service; do
  cd $service
  docker build -t neighbor-connect/$service:latest .
  microk8s ctr images import - < $(docker save neighbor-connect/$service:latest)
  cd ..
done

# 部署
cd ../k8s
microk8s kubectl apply -k overlays/microk8s/
EOF
```

## 监控和管理

### 查看服务状态

```bash
ssh masterjia@home.worthwolf.top
cd /home/masterjia/ruralneighbour/ms-backend/k8s
microk8s kubectl get pods -n ruralneighbour
microk8s kubectl get services -n ruralneighbour
microk8s kubectl get ingress -n ruralneighbour
```

### 查看日志

```bash
# 查看特定服务日志
microk8s kubectl logs -l app=auth-service -n ruralneighbour -f

# 查看所有服务日志
microk8s kubectl logs -l tier=backend -n ruralneighbour -f
```

### 重启服务

```bash
microk8s kubectl rollout restart deployment/auth-service -n ruralneighbour
microk8s kubectl rollout restart deployment/user-service -n ruralneighbour
```

### 回滚服务

```bash
microk8s kubectl rollout undo deployment/auth-service -n ruralneighbour
microk8s kubectl rollout undo deployment/user-service -n ruralneighbour
```

## 故障排除

### 常见问题

1. **SSH 连接失败**

   - 检查 SSH 密钥配置
   - 确认远程服务器可访问

2. **构建失败**

   - 检查 Docker 镜像构建日志
   - 确认依赖文件是否正确

3. **部署失败**

   - 检查 MicroK8s 状态
   - 查看 Pod 事件和日志

4. **服务无法访问**
   - 检查 Ingress 配置
   - 确认服务端口配置

### 调试命令

```bash
# 查看 Pod 事件
microk8s kubectl get events --sort-by=.lastTimestamp -n ruralneighbour

# 查看 Pod 详细信息
microk8s kubectl describe pod <pod-name> -n ruralneighbour

# 查看服务配置
microk8s kubectl get svc -n ruralneighbour -o yaml

# 查看 Ingress 配置
microk8s kubectl get ingress -n ruralneighbour -o yaml
```

## 环境配置

### 环境变量

在 `k8s/overlays/microk8s/.env` 中配置：

```bash
# 数据库连接
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=your_host
POSTGRES_PORT=5432

# Redis 连接
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# JWT 密钥
JWT_SECRET_KEY=your_jwt_secret
SECRET_KEY=your_secret_key
```

### 服务配置

各服务的配置在对应的 `k8s/*/deployment.yaml` 中：

- 资源限制
- 环境变量
- 健康检查
- 端口配置

## 扩展和自定义

### 添加新服务

1. 在 `services/` 目录下创建新服务
2. 在 `k8s/` 目录下创建对应的 Kubernetes 配置
3. 更新 `k8s/kustomization.yaml`
4. 更新部署脚本中的服务列表

### 修改部署策略

1. 编辑 `.github/workflows/build-and-deploy.yml`
2. 修改 `scripts/deploy.sh`
3. 更新 Kustomize 配置

## 安全注意事项

1. **密钥管理**：使用 Kubernetes Secrets 存储敏感信息
2. **网络安全**：配置适当的网络策略
3. **访问控制**：限制对部署脚本的访问权限
4. **日志安全**：避免在日志中输出敏感信息

## 性能优化

1. **资源限制**：为每个服务设置适当的资源限制
2. **水平扩缩**：配置 HPA 自动扩缩
3. **镜像优化**：使用多阶段构建减小镜像大小
4. **缓存策略**：配置适当的缓存策略

## 备份和恢复

1. **配置备份**：定期备份 Kubernetes 配置
2. **数据备份**：配置数据库和 Redis 备份
3. **灾难恢复**：制定灾难恢复计划
4. **版本管理**：使用 Git 标签管理版本

