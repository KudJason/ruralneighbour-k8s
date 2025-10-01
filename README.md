# RuralNeighbour 微服务后端

## 📁 项目结构

```
ms-backend/
├── README.md                     # 主要说明文档
├── docs/                        # 文档目录
│   ├── api/                     # API 相关文档
│   │   └── API_COMPATIBILITY_FIXES.md
│   ├── deployment/              # 部署相关文档
│   │   └── DEPLOYMENT.md
│   ├── testing/                 # 测试相关文档
│   └── SPRINT8_COMPLETION_SUMMARY.md
├── scripts/                     # 脚本目录
│   ├── deployment/              # 部署脚本和配置
│   │   ├── docker-compose.yaml
│   │   └── requirements.txt
│   ├── testing/                # 测试脚本
│   │   └── api_compatibility_test.py
│   ├── auto-deploy-production.sh
│   ├── auto-deploy-test.sh
│   ├── check-services.sh
│   ├── init-databases.sh
│   ├── manage-secrets.sh
│   ├── restart-failed-services.sh
│   └── smart-deploy.sh
├── services/                    # 微服务目录
│   ├── auth-service/
│   ├── user-service/
│   ├── location-service/
│   ├── content-service/
│   ├── request-service/
│   ├── notification-service/
│   ├── payment-service/
│   ├── safety-service/
│   ├── rating-service/
│   └── investment-service/
├── k8s/                        # Kubernetes 配置
└── shared/                     # 共享资源
```

## 🚀 快速开始

### 1. 本地开发

```bash
# 启动所有服务（Docker Compose）
cd scripts/deployment
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 2. Kubernetes 部署

```bash
# 部署到 K8s 集群
cd k8s
./scripts/deploy.sh --environment development
```

### 3. 运行测试

```bash
# API 兼容性测试
cd scripts/testing
python api_compatibility_test.py
```

## 📚 文档导航

### API 文档

- **[API 兼容性修复](docs/api/API_COMPATIBILITY_FIXES.md)** - 前后端 API 兼容性修复总结

### 部署文档

- **[部署指南](docs/deployment/DEPLOYMENT.md)** - 完整的部署说明
- **[Sprint 8 完成总结](docs/SPRINT8_COMPLETION_SUMMARY.md)** - 项目完成情况

### 微服务文档

- **[微服务迁移指南](services/README.md)** - Alembic 数据库迁移指南

## 🛠️ 脚本说明

### 部署脚本

- **`scripts/deployment/docker-compose.yaml`** - 本地开发环境配置
- **`scripts/deployment/requirements.txt`** - Python 依赖列表
- **`scripts/auto-deploy-production.sh`** - 生产环境自动部署
- **`scripts/auto-deploy-test.sh`** - 测试环境自动部署
- **`scripts/smart-deploy.sh`** - 智能部署脚本

### 测试脚本

- **`scripts/testing/api_compatibility_test.py`** - API 兼容性测试

### 管理脚本

- **`scripts/check-services.sh`** - 检查服务状态
- **`scripts/init-databases.sh`** - 初始化数据库
- **`scripts/manage-secrets.sh`** - 管理密钥
- **`scripts/restart-failed-services.sh`** - 重启失败的服务

## 🔧 服务状态

### 微服务列表

| 服务                 | 端口 | 状态    | 功能     |
| -------------------- | ---- | ------- | -------- |
| auth-service         | 8001 | ✅ 运行 | 用户认证 |
| user-service         | 8002 | ✅ 运行 | 用户管理 |
| location-service     | 8003 | ✅ 运行 | 位置服务 |
| content-service      | 8004 | ✅ 运行 | 内容管理 |
| request-service      | 8005 | ✅ 运行 | 服务请求 |
| notification-service | 8006 | ✅ 运行 | 通知服务 |
| payment-service      | 8007 | ✅ 运行 | 支付服务 |
| safety-service       | 8008 | ✅ 运行 | 安全服务 |
| rating-service       | 8009 | ✅ 运行 | 评分服务 |
| investment-service   | 8010 | ✅ 运行 | 投资服务 |

### 数据库迁移状态

所有服务都已配置完整的 Alembic 迁移：

| 服务                 | 迁移状态 | 主要表                                                                         |
| -------------------- | -------- | ------------------------------------------------------------------------------ |
| auth-service         | ✅ 完成  | users                                                                          |
| user-service         | ✅ 完成  | user_profiles, provider_profile                                                |
| location-service     | ✅ 完成  | user_addresses, saved_locations (PostGIS)                                      |
| content-service      | ✅ 完成  | news_articles, videos, system_settings                                         |
| request-service      | ✅ 完成  | service_requests, service_assignments, ratings                                 |
| notification-service | ✅ 完成  | notifications, messages                                                        |
| payment-service      | ✅ 完成  | payments, payment_history, refunds, user_payment_methods, payment_method_usage |
| safety-service       | ✅ 完成  | safety_reports, disputes, platform_metrics                                     |
| rating-service       | ✅ 完成  | ratings                                                                        |

## 🔍 测试和验证

### API 兼容性测试

```bash
cd scripts/testing
python api_compatibility_test.py
```

### 服务健康检查

```bash
./scripts/check-services.sh
```

### 数据库迁移验证

```bash
cd services
./scripts/verify_migrations.sh
```

## 🚨 故障排除

### 常见问题

1. **服务启动失败**

   - 检查数据库连接
   - 验证环境变量配置
   - 查看服务日志

2. **API 兼容性问题**

   - 运行兼容性测试
   - 检查字段映射
   - 验证端点路径

3. **数据库迁移问题**
   - 检查 Alembic 配置
   - 验证数据库连接
   - 查看迁移日志

### 调试命令

```bash
# 查看服务日志
docker-compose logs -f [service-name]

# 检查 K8s Pod 状态
kubectl get pods -n default

# 查看数据库迁移状态
cd services/[service-name]
alembic current
```

## 📞 支持

如有问题，请查看：

1. **[部署指南](docs/deployment/DEPLOYMENT.md)** - 部署相关问题
2. **[API 兼容性修复](docs/api/API_COMPATIBILITY_FIXES.md)** - API 相关问题
3. **[微服务迁移指南](services/README.md)** - 数据库迁移问题
4. **[Sprint 8 完成总结](docs/SPRINT8_COMPLETION_SUMMARY.md)** - 项目整体情况

## 🔄 更新日志

- **Sprint 8**: 完成 K8s 部署优化和 CI/CD 配置
- **API 兼容性**: 修复前后端 API 兼容性问题
- **数据库迁移**: 完成所有服务的 Alembic 迁移配置
- **文档整理**: 重新组织项目文档结构


