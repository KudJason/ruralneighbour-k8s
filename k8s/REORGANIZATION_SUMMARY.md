# k8s/ 目录重组总结

## 重组前的问题

1. **文件混乱**：所有脚本、文档、配置文件都混在一起
2. **环境管理困难**：没有清晰的环境分离
3. **部署脚本重复**：多个相似的部署脚本
4. **缺乏统一管理**：没有统一的部署和清理流程

## 重组后的结构

```
k8s/
├── README.md                    # 主要文档
├── QUICKSTART.md               # 快速开始指南
├── kustomization.yaml          # 基础配置
├── _shared/                     # 共享资源
├── overlays/                    # 环境覆盖层
│   ├── development/            # 开发环境
│   ├── staging/                # 测试环境
│   └── production/             # 生产环境
├── scripts/                     # 所有脚本
├── docs/                       # 文档
├── services/                   # 各服务配置
└── tests/                      # 测试配置
```

## 主要改进

### 1. 环境管理

- **开发环境**：`overlays/development/` - 单副本，小资源
- **测试环境**：`overlays/staging/` - 中等配置
- **生产环境**：`overlays/production/` - 高可用，大资源

### 2. 统一脚本

- **`scripts/deploy.sh`**：统一部署脚本，支持多环境
- **`scripts/cleanup.sh`**：统一清理脚本
- **其他脚本**：整理到 `scripts/` 目录

### 3. 配置管理

- **Kustomize 覆盖层**：每个环境有独立的配置
- **补丁文件**：环境特定的配置修改
- **环境变量模板**：`env.example` 文件

### 4. 文档完善

- **README.md**：完整的目录结构说明
- **QUICKSTART.md**：快速开始指南
- **环境特定文档**：每个环境的配置说明

## 使用方法

### 部署

```bash
# 开发环境
./scripts/deploy.sh --environment development

# 测试环境
./scripts/deploy.sh --environment staging

# 生产环境
./scripts/deploy.sh --environment production
```

### 清理

```bash
# 清理开发环境
./scripts/cleanup.sh --environment development

# 强制清理
./scripts/cleanup.sh --environment production --force
```

### 手动部署

```bash
# 使用 Kustomize
kubectl apply -k overlays/development
microk8s kubectl apply -k overlays/development
```

## 环境配置

### 开发环境

- 命名空间：`default`
- 副本数：1
- 资源限制：较小
- 用途：本地开发

### 测试环境

- 命名空间：`ruralneighbour-staging`
- 副本数：1-2
- 资源限制：中等
- 用途：集成测试

### 生产环境

- 命名空间：`ruralneighbour`
- 副本数：3-5
- 资源限制：较大
- 用途：生产环境

## 文件移动记录

### 移动到 scripts/

- `*.sh` 文件 → `scripts/`

### 移动到 docs/

- `*.md` 文件 → `docs/`

### 环境覆盖层

- `overlays/microk8s/` → `overlays/development/`
- 新增 `overlays/staging/`
- 新增 `overlays/production/`

## 新增文件

### 脚本

- `scripts/deploy.sh` - 统一部署脚本
- `scripts/cleanup.sh` - 统一清理脚本

### 配置

- `overlays/development/patches/replicas-one.yaml`
- `overlays/development/patches/use-app-secrets.yaml`
- `overlays/staging/kustomization.yaml`
- `overlays/production/kustomization.yaml`

### 文档

- `README.md` - 主要文档
- `QUICKSTART.md` - 快速开始指南
- `overlays/development/env.example` - 环境变量模板

## 兼容性

### GitHub Actions

- 更新了工作流文件以使用新的目录结构
- 保持向后兼容性

### 现有脚本

- 所有现有脚本都保留在 `scripts/` 目录
- 可以继续使用现有的部署方式

## 最佳实践

1. **环境隔离**：使用不同的命名空间和配置
2. **配置管理**：使用 Kustomize 管理环境配置
3. **统一部署**：使用统一的部署脚本
4. **文档完善**：保持文档更新
5. **版本控制**：不要提交 `.env` 文件

## 后续改进

1. **添加更多环境**：如 `preview`、`hotfix` 等
2. **自动化测试**：集成更多自动化测试
3. **监控集成**：添加监控和告警
4. **安全加固**：增强安全配置
5. **性能优化**：优化资源配置和部署策略

