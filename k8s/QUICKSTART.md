# RuralNeighbour Kubernetes 快速开始指南

## 快速部署

### 1. 准备环境配置

```bash
# 进入开发环境目录
cd overlays/development

# 复制环境配置模板
cp env.example .env

# 编辑环境配置
nano .env
```

### 2. 部署到开发环境

```bash
# 使用统一部署脚本
./scripts/deploy.sh --environment development

# 或者使用 Kustomize 直接部署
kubectl apply -k overlays/development
# 或者使用 MicroK8s
microk8s kubectl apply -k overlays/development
```

### 3. 验证部署

```bash
# 查看 Pod 状态
kubectl get pods
microk8s kubectl get pods

# 查看服务状态
kubectl get services
microk8s kubectl get services

# 查看 Ingress
kubectl get ingress
microk8s kubectl get ingress
```

### 4. 运行测试

```bash
# 运行部署测试
./scripts/test_deployment.sh

# 运行 API 测试
./scripts/test_apis.sh
```

## 环境管理

### 部署到不同环境

```bash
# 开发环境
./scripts/deploy.sh --environment development

# 测试环境
./scripts/deploy.sh --environment staging

# 生产环境
./scripts/deploy.sh --environment production
```

### 清理环境

```bash
# 清理开发环境
./scripts/cleanup.sh --environment development

# 强制清理（不询问确认）
./scripts/cleanup.sh --environment production --force
```

## 常用命令

### 查看日志

```bash
# 查看特定服务日志
kubectl logs -l app=auth-service -f
microk8s kubectl logs -l app=auth-service -f

# 查看所有服务日志
kubectl logs -l tier=backend -f
microk8s kubectl logs -l tier=backend -f
```

### 重启服务

```bash
# 重启特定服务
kubectl rollout restart deployment/auth-service
microk8s kubectl rollout restart deployment/auth-service

# 重启所有服务
kubectl rollout restart deployment -l tier=backend
microk8s kubectl rollout restart deployment -l tier=backend
```

### 扩缩容

```bash
# 扩展服务副本
kubectl scale deployment auth-service --replicas=3
microk8s kubectl scale deployment auth-service --replicas=3

# 查看副本状态
kubectl get deployment auth-service
microk8s kubectl get deployment auth-service
```

## 故障排除

### 查看事件

```bash
kubectl get events --sort-by=.lastTimestamp
microk8s kubectl get events --sort-by=.lastTimestamp
```

### 调试 Pod

```bash
# 查看 Pod 详细信息
kubectl describe pod <pod-name>
microk8s kubectl describe pod <pod-name>

# 进入 Pod 调试
kubectl exec -it <pod-name> -- /bin/bash
microk8s kubectl exec -it <pod-name> -- /bin/bash
```

### 查看服务配置

```bash
# 查看服务详细信息
kubectl get svc -o yaml
microk8s kubectl get svc -o yaml

# 查看 Ingress 配置
kubectl get ingress -o yaml
microk8s kubectl get ingress -o yaml
```

## 开发工作流

### 1. 本地开发

```bash
# 启动本地服务
cd services/auth-service
python -m uvicorn app.main:app --reload --port 8000
```

### 2. 测试更改

```bash
# 运行单元测试
cd services/auth-service
python -m pytest tests/

# 运行集成测试
cd ../..
./scripts/test_deployment.sh
```

### 3. 部署更改

```bash
# 快速部署（仅同步代码）
./scripts/deploy.sh --environment development

# 完整部署（重新构建镜像）
# 通过 GitHub Actions 或手动构建
```

## 监控和日志

### 查看资源使用

```bash
# 查看 Pod 资源使用
kubectl top pods
microk8s kubectl top pods

# 查看节点资源使用
kubectl top nodes
microk8s kubectl top nodes
```

### 查看服务健康状态

```bash
# 检查服务健康端点
curl http://localhost/api/v1/auth/health
curl http://localhost/api/v1/user/health
```

## 安全注意事项

1. **不要提交 `.env` 文件到版本控制**
2. **使用强密码和密钥**
3. **定期轮换密钥**
4. **限制网络访问**
5. **启用 RBAC**

## 性能优化

1. **设置适当的资源限制**
2. **使用 HPA 自动扩缩容**
3. **优化镜像大小**
4. **配置适当的健康检查**
5. **使用缓存策略**

## 备份和恢复

1. **定期备份数据库**
2. **备份 Kubernetes 配置**
3. **测试恢复流程**
4. **文档化恢复步骤**

