# RuralNeighbour Kubernetes 配置

本目录包含 RuralNeighbour 项目的所有 Kubernetes 配置文件和部署脚本。

## 目录结构

```
k8s/
├── README.md                    # 本文档
├── kustomization.yaml          # 基础 Kustomize 配置
├── _shared/                     # 共享资源
│   ├── ingress.yaml            # Ingress 配置
│   ├── postgres-*.yaml         # PostgreSQL 相关配置
│   └── redis-*.yaml            # Redis 相关配置
├── overlays/                    # 环境覆盖层
│   ├── development/            # 开发环境
│   │   ├── kustomization.yaml
│   │   ├── .env               # 环境变量（不提交到版本控制）
│   │   └── patches/           # 补丁文件
│   │       ├── replicas-one.yaml
│   │       └── use-app-secrets.yaml
│   ├── staging/                # 测试环境
│   │   ├── kustomization.yaml
│   │   └── .env
│   └── production/             # 生产环境
│       ├── kustomization.yaml
│       └── .env
├── scripts/                     # 部署脚本
│   ├── deploy.sh              # 统一部署脚本
│   ├── cleanup.sh             # 清理脚本
│   ├── test_deployment.sh     # 部署测试
│   └── ...                    # 其他脚本
├── docs/                       # 文档
│   ├── MANUAL_DEPLOYMENT_GUIDE.md
│   └── MICROK8S_DEPLOYMENT_GUIDE.md
├── services/                   # 各服务配置
│   ├── auth-service/
│   ├── user-service/
│   └── ...
└── tests/                      # 测试配置
    └── auth-health-job.yaml
```

## 环境配置

### 开发环境 (development)

- 命名空间: `default`
- 副本数: 1
- 资源限制: 较小
- 用途: 本地开发和测试

### 测试环境 (staging)

- 命名空间: `ruralneighbour-staging`
- 副本数: 1-2
- 资源限制: 中等
- 用途: 集成测试和预发布测试

### 生产环境 (production)

- 命名空间: `ruralneighbour`
- 副本数: 3-5
- 资源限制: 较大
- 用途: 生产环境

## 使用方法

### 部署应用

```bash
# 部署到开发环境
./scripts/deploy.sh --environment development

# 部署到测试环境
./scripts/deploy.sh --environment staging

# 部署到生产环境
./scripts/deploy.sh --environment production

# 干运行模式（仅显示命令，不执行）
./scripts/deploy.sh --environment production --dry-run
```

### 清理部署

```bash
# 清理开发环境
./scripts/cleanup.sh --environment development

# 强制清理（不询问确认）
./scripts/cleanup.sh --environment production --force
```

### 手动部署

```bash
# 使用 Kustomize 直接部署
kubectl apply -k overlays/development
microk8s kubectl apply -k overlays/development

# 查看部署状态
kubectl get pods -n default
microk8s kubectl get pods -n default
```

## 环境变量配置

每个环境都需要在对应的 `.env` 文件中配置环境变量：

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

# 其他服务特定配置...
```

## 服务配置

每个服务都有自己的目录，包含：

- `deployment.yaml` - 部署配置
- `service.yaml` - 服务配置
- `secrets.yaml` - 密钥配置（可选）

## 共享资源

`_shared/` 目录包含所有服务共享的资源：

- Ingress 配置
- 数据库配置
- 缓存配置
- 其他基础设施配置

## 补丁文件

`overlays/*/patches/` 目录包含环境特定的补丁文件：

- `replicas-one.yaml` - 设置副本数为 1
- `use-app-secrets.yaml` - 使用统一的密钥配置

## 测试

### 运行部署测试

```bash
./scripts/test_deployment.sh
```

### 运行 API 测试

```bash
./scripts/test_apis.sh
```

## 故障排除

### 查看日志

```bash
# 查看特定服务日志
kubectl logs -l app=auth-service -n default -f
microk8s kubectl logs -l app=auth-service -n default -f

# 查看所有服务日志
kubectl logs -l tier=backend -n default -f
```

### 查看事件

```bash
kubectl get events --sort-by=.lastTimestamp -n default
microk8s kubectl get events --sort-by=.lastTimestamp -n default
```

### 调试 Pod

```bash
kubectl describe pod <pod-name> -n default
microk8s kubectl describe pod <pod-name> -n default
```

## 最佳实践

1. **环境隔离**: 使用不同的命名空间隔离不同环境
2. **配置管理**: 使用 Kustomize 管理不同环境的配置
3. **密钥管理**: 使用 Kubernetes Secrets 存储敏感信息
4. **资源限制**: 为每个服务设置适当的资源限制
5. **健康检查**: 配置适当的健康检查和就绪检查
6. **监控**: 配置适当的监控和日志收集

## 扩展

### 添加新服务

1. 在根目录创建服务配置目录
2. 在 `kustomization.yaml` 中添加服务引用
3. 在环境覆盖层中添加必要的补丁

### 添加新环境

1. 在 `overlays/` 目录下创建新环境目录
2. 创建 `kustomization.yaml` 配置文件
3. 添加环境特定的补丁文件
4. 更新部署脚本以支持新环境






