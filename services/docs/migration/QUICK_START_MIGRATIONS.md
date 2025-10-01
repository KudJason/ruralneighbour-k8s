# 🚀 Alembic 迁移快速开始指南

## 一键执行迁移

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
./execute_migrations.sh
```

## 一键验证结果

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
./verify_migrations.sh
```

## 如果遇到问题

### 1. 检查服务状态

```bash
kubectl get pods -l app=auth-service
kubectl get pods -l app=user-service
# ... 检查其他服务
```

### 2. 查看服务日志

```bash
kubectl logs -l app=auth-service
kubectl logs -l app=user-service
# ... 查看其他服务日志
```

### 3. 手动运行单个服务迁移

```bash
# 获取 Pod 名称
POD=$(kubectl get pod -l app=auth-service -o jsonpath='{.items[0].metadata.name}')

# 运行迁移
kubectl exec -it $POD -- alembic upgrade head

# 检查状态
kubectl exec $POD -- alembic current
```

### 4. 重启服务（如果自动迁移失败）

```bash
kubectl rollout restart deployment/auth-service
kubectl rollout restart deployment/user-service
kubectl rollout restart deployment/location-service
kubectl rollout restart deployment/content-service
kubectl rollout restart deployment/request-service
kubectl rollout restart deployment/notification-service
kubectl rollout restart deployment/payment-service
kubectl rollout restart deployment/safety-service
kubectl rollout restart deployment/rating-service
```

## 预期结果

迁移成功后，你应该看到：

- ✅ 所有服务 Pod 状态为 Running
- ✅ 所有服务显示正确的迁移版本
- ✅ 数据库连接正常
- ✅ 表结构创建成功

## 需要帮助？

如果遇到问题，请检查：

1. Kubernetes 集群连接是否正常
2. 所有服务 Pod 是否在运行
3. DATABASE_URL 环境变量是否正确配置
4. 数据库是否可访问
5. PostGIS 扩展是否已安装（location-service 需要）
