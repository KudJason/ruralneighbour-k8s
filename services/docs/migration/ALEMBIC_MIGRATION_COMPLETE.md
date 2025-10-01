# Alembic 迁移完成总结

## ✅ 已完成的工作

### 1. 为所有服务创建了完整的 Alembic 迁移文件

所有服务的初始迁移文件已手动创建，包含完整的表结构定义：

| 服务                     | 迁移文件                      | 状态    | 主要表                                                                         |
| ------------------------ | ----------------------------- | ------- | ------------------------------------------------------------------------------ |
| **auth-service**         | `0001_create_users_table.py`  | ✅ 完成 | users                                                                          |
| **user-service**         | `0001_initial_migration.py`   | ✅ 完成 | user_profiles, provider_profile                                                |
| **location-service**     | `0001_initial_migration.py`   | ✅ 完成 | user_addresses, saved_locations (PostGIS)                                      |
| **content-service**      | `0001_initial_migration.py`   | ✅ 完成 | news_articles, videos, system_settings                                         |
| **request-service**      | `0001_initial_migration.py`   | ✅ 完成 | service_requests, service_assignments, ratings                                 |
| **notification-service** | `0001_initial_migration.py`   | ✅ 完成 | notifications, messages                                                        |
| **payment-service**      | `0001_initial_migration.py`   | ✅ 完成 | payments, payment_history, refunds, user_payment_methods, payment_method_usage |
| **safety-service**       | `0001_initial_migration.py`   | ✅ 完成 | safety_reports, disputes, platform_metrics                                     |
| **rating-service**       | `001_create_ratings_table.py` | ✅ 完成 | ratings                                                                        |

### 2. 修复了所有服务的 `env.py` 文件

所有服务的 `alembic/env.py` 文件已更新，确保：

- 正确导入所有模型类
- 使用正确的 Base 类（request-service 使用 `base_class.Base`）
- 配置正确的数据库 URL
- 包含必要的 import 语句

### 3. 特殊处理

#### location-service

- ✅ 启用 PostGIS 扩展：`CREATE EXTENSION IF NOT EXISTS postgis`
- ✅ 使用 geoalchemy2 的 Geography 类型

#### user-service

- ✅ 创建 ENUM 类型：`user_mode` ('NIN', 'LAH')

#### request-service

- ✅ 创建多个 ENUM 类型：
  - servicerequestatus
  - assignmentstatus
  - servicetype
  - paymentstatus

#### payment-service

- ✅ 添加 CHECK 约束：`default_must_be_active`

## 📋 在远程 K8s 环境运行迁移

### 方法 1：查看运行指南（推荐）

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
./run_migrations_k8s.sh
```

这个脚本会显示三种运行迁移的方法。

### 方法 2：批量运行（最快）

在你的 K8s 环境中运行以下命令：

```bash
for service in auth-service user-service location-service content-service request-service notification-service payment-service safety-service rating-service; do
  echo "=== Running migration for $service ==="
  POD=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  if [ -n "$POD" ]; then
    kubectl exec -it $POD -- alembic upgrade head || echo "Failed: $service"
  else
    echo "Pod not found for $service"
  fi
  echo ""
done
```

### 方法 3：自动迁移（最简单）

所有服务的 `docker-entrypoint.sh` 都会在启动时自动运行迁移，只需重启服务：

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

## 🔍 验证迁移状态

检查所有服务的迁移版本：

```bash
for service in auth-service user-service location-service content-service request-service notification-service payment-service safety-service rating-service; do
  echo "=== $service migration status ==="
  POD=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  if [ -n "$POD" ]; then
    kubectl exec $POD -- alembic current 2>/dev/null || echo "No migration applied"
  fi
  echo ""
done
```

## 📝 迁移文件详情

### auth-service

- **文件**: `alembic/versions/0001_create_users_table.py`
- **表**: users
- **字段**: user_id, email, password_hash, full_name, is_active, is_verified, created_at, updated_at, last_login, reset_token, reset_token_expires

### user-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: user_profiles, provider_profile
- **ENUM**: user_mode ('NIN', 'LAH')

### location-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: user_addresses, saved_locations
- **特殊**: PostGIS 扩展，Geography 类型

### content-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: news_articles, videos, system_settings

### request-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: service_requests, service_assignments, ratings
- **ENUM**: servicerequestatus, assignmentstatus, servicetype, paymentstatus

### notification-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: notifications, messages

### payment-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: payments, payment_history, refunds, user_payment_methods, payment_method_usage
- **约束**: default_must_be_active CHECK 约束

### safety-service

- **文件**: `alembic/versions/0001_initial_migration.py`
- **表**: safety_reports, disputes, platform_metrics

### rating-service

- **文件**: `alembic/versions/001_create_ratings_table.py`
- **表**: ratings

## ⚠️ 重要注意事项

1. **数据库连接**: 确保所有服务的 `DATABASE_URL` 环境变量已正确配置
2. **PostGIS**: location-service 需要 PostgreSQL 数据库中已启用 PostGIS 扩展
3. **顺序**: 迁移会自动处理依赖关系，按照版本号顺序执行
4. **备份**: 建议在生产环境运行前先备份数据库
5. **测试**: 建议先在测试环境验证所有迁移

## 🚀 执行迁移的三种方法

### 方法 1：自动执行脚本（推荐）

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
./execute_migrations.sh
```

这个脚本会：

- 检查所有服务状态
- 自动运行迁移
- 提供详细的执行报告
- 验证迁移结果

### 方法 2：重启服务（最简单）

由于所有服务都配置了 `docker-entrypoint.sh`，重启服务会自动运行迁移：

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

### 方法 3：手动执行

```bash
for service in auth-service user-service location-service content-service request-service notification-service payment-service safety-service rating-service; do
  echo "=== Running migration for $service ==="
  POD=$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}')
  kubectl exec -it $POD -- alembic upgrade head
done
```

## 🔍 验证迁移结果

运行验证脚本：

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
./verify_migrations.sh
```

这个脚本会：

- 检查所有服务状态
- 验证迁移版本
- 测试数据库连接
- 检查表结构

## 📄 相关文件

- **执行脚本**: `/ms-backend/services/execute_migrations.sh` - 自动执行所有迁移
- **验证脚本**: `/ms-backend/services/verify_migrations.sh` - 验证迁移状态
- **运行指南**: `/ms-backend/services/run_migrations_k8s.sh` - 显示所有方法
- **迁移文件**: `/ms-backend/services/{service-name}/alembic/versions/0001_*.py`
- **环境配置**: `/ms-backend/services/{service-name}/alembic/env.py`
- **Docker Entrypoint**: `/ms-backend/services/docker-entrypoint.sh`
- **原始指南**: `/ms-backend/services/ALEMBIC_MIGRATION_GUIDE.md`
