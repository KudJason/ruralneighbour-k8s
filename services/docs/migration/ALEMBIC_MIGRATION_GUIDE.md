# Alembic 数据库迁移指南

## 概述

所有微服务现在都使用 Alembic 进行数据库迁移管理，而不是 SQLAlchemy 的 `Base.metadata.create_all()`。

## 已完成的设置

### ✅ 1. Alembic 配置文件

每个服务现在都有:

- `alembic.ini` - Alembic 配置文件
- `alembic/env.py` - Alembic 环境配置
- `alembic/script.py.mako` - 迁移脚本模板
- `alembic/versions/` - 迁移脚本目录

### ✅ 2. 移除了 create_all() 调用

所有服务的 `app/main.py` 中的 `Base.metadata.create_all()` 已被移除。

### ✅ 3. Docker Entrypoint

创建了 `docker-entrypoint.sh`，在服务启动前自动运行 Alembic 迁移。

## 服务列表及状态

| 服务                 | 数据库          | 初始迁移                       | 状态               |
| -------------------- | --------------- | ------------------------------ | ------------------ |
| auth-service         | auth_db         | ✅ 0001_create_users_table.py  | 已完成             |
| user-service         | user_db         | ⚠️ 0001_initial_migration.py   | 需要生成           |
| location-service     | location_db     | ⚠️ 0001_initial_migration.py   | 需要生成 + PostGIS |
| content-service      | content_db      | ⚠️ 0001_initial_migration.py   | 需要生成           |
| request-service      | request_db      | ⚠️ 0001_initial_migration.py   | 需要生成           |
| notification-service | notification_db | ⚠️ 0001_initial_migration.py   | 需要生成           |
| payment-service      | payment_db      | ⚠️ 0001_initial_migration.py   | 需要生成           |
| safety-service       | safety_db       | ⚠️ 0001_initial_migration.py   | 需要生成           |
| rating-service       | rating_db       | ✅ 001_create_ratings_table.py | 已完成             |
| investment-service   | investment_db   | ⚠️ 使用 SQLite                 | 特殊处理           |

## 生成完整迁移的步骤

对于每个标记为 "需要生成" 的服务，执行以下步骤：

### 方法 1: 使用 autogenerate（推荐）

```bash
cd /path/to/service
export DATABASE_URL="postgresql://neighbor:password@localhost:5432/<db_name>"
alembic revision --autogenerate -m "Initial migration"
```

### 方法 2: 手动编写迁移

编辑 `alembic/versions/0001_initial_migration.py`，在 `upgrade()` 函数中添加表创建语句。

参考 `auth-service/alembic/versions/0001_create_users_table.py` 作为示例。

## 特殊情况

### location-service (需要 PostGIS)

在迁移中需要启用 PostGIS 扩展：

```python
def upgrade() -> None:
    # 启用 PostGIS 扩展
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')

    # 然后创建表...
```

### investment-service (使用 SQLite)

此服务使用 SQLite，不需要远程 PostgreSQL 数据库。可以继续使用现有方式或为其配置 SQLite 的 Alembic。

## Docker 集成

### 在 Dockerfile 中添加 entrypoint

每个服务的 Dockerfile 需要：

```dockerfile
# 复制 entrypoint 脚本
COPY services/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 设置 entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### entrypoint 脚本功能

`docker-entrypoint.sh` 会自动：

1. 等待数据库就绪
2. 运行 `alembic upgrade head`
3. 启动应用

## 运行迁移

### 开发环境

```bash
cd service-name
alembic upgrade head
```

### 生产环境 (Kubernetes)

服务 Pod 启动时会自动运行迁移（通过 docker-entrypoint.sh）。

## 创建新迁移

当模型发生变化时：

```bash
cd service-name
alembic revision --autogenerate -m "Description of changes"
# 检查生成的迁移文件
alembic upgrade head
```

## 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade <revision_id>

# 回滚所有
alembic downgrade base
```

## 查看迁移状态

```bash
# 查看当前版本
alembic current

# 查看历史
alembic history

# 查看待执行的迁移
alembic heads
```

## CloudNativePG 集成

PostgreSQL HA 集群配置 (`ms-backend/k8s/_shared/postgres-ha-cluster.yaml`) 只负责：

1. 创建空数据库
2. 为 location_db 启用 PostGIS 扩展
3. 创建 `neighbor` 用户

**表结构完全由各服务的 Alembic 迁移管理。**

## 故障排除

### 迁移失败

```bash
# 检查数据库连接
echo $DATABASE_URL
psql $DATABASE_URL -c "SELECT version();"

# 检查 Alembic 版本表
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# 手动标记当前版本（谨慎使用）
alembic stamp head
```

### 生成的迁移为空

确保：

1. 所有模型都已导入到 `alembic/env.py`
2. `Base.metadata` 包含所有模型
3. 数据库连接正确

## 下一步

1. ✅ 所有服务已配置 Alembic
2. ⚠️ 需要为每个服务生成完整的初始迁移
3. ⚠️ 需要更新所有 Dockerfile 使用 docker-entrypoint.sh
4. ⚠️ 需要测试所有迁移在 Kubernetes 环境中的执行

## 相关文件

- `/ms-backend/services/setup_alembic_all.sh` - Alembic 配置脚本
- `/ms-backend/services/docker-entrypoint.sh` - Docker entrypoint 脚本
- `/ms-backend/services/remove_create_all.sh` - 清理 create_all() 的脚本
- `/ms-backend/services/create_all_initial_migrations.py` - 创建初始迁移模板的脚本
