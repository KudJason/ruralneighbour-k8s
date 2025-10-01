# 微服务 Alembic 迁移系统

## 📁 目录结构

```
services/
├── docs/                          # 文档目录
│   └── migration/                 # 迁移相关文档
│       ├── ALEMBIC_MIGRATION_COMPLETE.md    # 完整迁移指南
│       ├── ALEMBIC_MIGRATION_GUIDE.md     # 原始迁移指南
│       └── QUICK_START_MIGRATIONS.md      # 快速开始指南
├── scripts/                      # 脚本目录
│   ├── execute_migrations.sh     # 执行所有迁移（推荐）
│   ├── verify_migrations.sh      # 验证迁移状态
│   ├── run_migrations_k8s.sh     # 显示所有执行方法
│   ├── docker-entrypoint.sh      # Docker 入口脚本
│   ├── export_requirements.bash  # 导出依赖脚本
│   └── legacy/                   # 过时的脚本
│       ├── autogenerate_all_migrations.sh
│       ├── generate_initial_migrations.sh
│       ├── create_all_initial_migrations.py
│       ├── setup_alembic_all.sh
│       ├── remove_create_all.sh
│       └── restore_create_all.sh
├── {service-name}/               # 各个微服务目录
│   ├── alembic/
│   │   ├── env.py
│   │   ├── versions/
│   │   │   └── 0001_*.py
│   │   └── alembic.ini
│   └── app/
└── pyproject.toml               # 项目配置
```

## 🚀 快速开始

### 1. 执行迁移（推荐）

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/services
./scripts/execute_migrations.sh
```

### 2. 验证结果

```bash
./scripts/verify_migrations.sh
```

### 3. 查看所有方法

```bash
./scripts/run_migrations_k8s.sh
```

## 📚 文档

- **[完整迁移指南](docs/migration/ALEMBIC_MIGRATION_COMPLETE.md)** - 详细的迁移说明和故障排除
- **[快速开始](docs/migration/QUICK_START_MIGRATIONS.md)** - 快速执行迁移的步骤
- **[原始指南](docs/migration/ALEMBIC_MIGRATION_GUIDE.md)** - 技术细节和配置说明

## 🛠️ 脚本说明

### 主要脚本

- **`execute_migrations.sh`** - 自动执行所有服务的迁移，包含状态检查和错误处理
- **`verify_migrations.sh`** - 验证所有服务的迁移状态和数据库连接
- **`run_migrations_k8s.sh`** - 显示所有执行迁移的方法和命令
- **`docker-entrypoint.sh`** - Docker 容器启动时自动运行迁移的脚本

### 辅助脚本

- **`export_requirements.bash`** - 为所有服务导出 requirements.txt 文件

### 过时脚本（legacy/）

这些脚本已经不再需要，但保留作为参考：

- `autogenerate_all_migrations.sh` - 自动生成迁移（已手动完成）
- `generate_initial_migrations.sh` - 生成初始迁移（已手动完成）
- `create_all_initial_migrations.py` - 创建迁移模板（已手动完成）
- `setup_alembic_all.sh` - 设置 Alembic（已完成）
- `remove_create_all.sh` - 移除 create_all 调用（已完成）
- `restore_create_all.sh` - 恢复 create_all 调用（不需要）

## 📋 服务状态

所有 9 个服务都已配置完整的 Alembic 迁移：

| 服务                 | 状态    | 主要表                                                                         |
| -------------------- | ------- | ------------------------------------------------------------------------------ |
| auth-service         | ✅ 完成 | users                                                                          |
| user-service         | ✅ 完成 | user_profiles, provider_profile                                                |
| location-service     | ✅ 完成 | user_addresses, saved_locations (PostGIS)                                      |
| content-service      | ✅ 完成 | news_articles, videos, system_settings                                         |
| request-service      | ✅ 完成 | service_requests, service_assignments, ratings                                 |
| notification-service | ✅ 完成 | notifications, messages                                                        |
| payment-service      | ✅ 完成 | payments, payment_history, refunds, user_payment_methods, payment_method_usage |
| safety-service       | ✅ 完成 | safety_reports, disputes, platform_metrics                                     |
| rating-service       | ✅ 完成 | ratings                                                                        |

## 🔧 配置说明

### 环境变量

所有服务都需要 `DATABASE_URL` 环境变量：

```bash
export DATABASE_URL="postgresql://neighbor:password@localhost:5432/{db_name}"
```

### 特殊要求

- **location-service**: 需要 PostGIS 扩展
- **所有服务**: 需要正确的 `DATABASE_URL` 配置

## 🚨 故障排除

如果遇到问题，请查看：

1. **[完整迁移指南](docs/migration/ALEMBIC_MIGRATION_COMPLETE.md)** - 详细的故障排除步骤
2. **[快速开始指南](docs/migration/QUICK_START_MIGRATIONS.md)** - 常见问题解决方案

## 📞 支持

如有问题，请检查：

1. Kubernetes 集群连接
2. 所有服务 Pod 状态
3. 数据库连接配置
4. PostGIS 扩展（location-service）


