# GitHub Actions 工作流说明

本目录包含用于自动构建、测试和部署 RuralNeighbour 后端服务的 GitHub Actions 工作流。

## 工作流文件

### 1. build-and-deploy.yml

**主要构建和部署工作流**

- **触发条件**：

  - 推送到 `main` 或 `develop` 分支
  - 创建 Pull Request 到 `main` 分支
  - 手动触发

- **功能**：
  - 运行 Python 测试
  - 同步代码到远程服务器
  - 在远程服务器上构建 Docker 镜像
  - 部署到 MicroK8s 集群
  - 运行部署测试

### 2. quick-deploy.yml

**快速部署工作流**

- **触发条件**：

  - 手动触发
  - 推送到 `main` 分支且修改了特定文件

- **功能**：
  - 仅同步代码到远程服务器
  - 重新部署现有镜像
  - 重启服务

### 3. rollback.yml

**回滚工作流**

- **触发条件**：

  - 仅手动触发

- **功能**：
  - 回滚所有服务到上一个版本

### 4. test-only.yml

**仅测试工作流**

- **触发条件**：

  - 推送到 `main` 或 `develop` 分支
  - 创建 Pull Request 到 `main` 分支
  - 手动触发

- **功能**：
  - 运行 API 兼容性测试
  - 运行各服务的单元测试
  - 运行集成测试

## 配置要求

### GitHub Secrets

在仓库设置中添加以下 Secrets：

1. `SSH_PRIVATE_KEY`：远程服务器的 SSH 私钥

### 远程服务器配置

- 服务器地址：`home.worthwolf.top`
- 用户名：`masterjia`
- 项目路径：`/home/masterjia/ruralneighbour/ms-backend`

## 使用流程

### 自动部署

```bash
# 1. 开发代码
git add .
git commit -m "feat: 添加新功能"
git push origin main

# 2. GitHub Actions 自动触发构建和部署
# 在 GitHub 仓库的 Actions 页面查看进度
```

### 手动触发

1. 进入 GitHub 仓库的 Actions 页面
2. 选择对应的工作流
3. 点击 "Run workflow" 按钮
4. 选择分支并点击 "Run workflow"

### 快速部署

当只需要同步代码而不重新构建镜像时：

1. 在 GitHub Actions 页面手动触发 "Quick Deploy" 工作流

### 回滚部署

当需要回滚到上一个版本时：

1. 在 GitHub Actions 页面手动触发 "Rollback" 工作流

## 监控和日志

### 查看部署状态

- 在 GitHub Actions 页面查看工作流状态
- 查看详细的构建和部署日志
- 设置通知（邮件、Slack 等）

### 远程服务器管理

```bash
# SSH 到远程服务器
ssh masterjia@home.worthwolf.top

# 进入项目目录
cd /home/masterjia/ruralneighbour/ms-backend

# 查看服务状态
microk8s kubectl get pods -n ruralneighbour
microk8s kubectl get services -n ruralneighbour

# 查看日志
microk8s kubectl logs -l app=auth-service -n ruralneighbour -f
```

## 故障排除

### 常见问题

1. **SSH 连接失败**

   - 检查 SSH 私钥是否正确配置
   - 确认远程服务器可访问

2. **构建失败**

   - 检查 Docker 镜像构建日志
   - 确认依赖文件是否正确生成

3. **部署失败**

   - 检查 MicroK8s 状态
   - 查看 Pod 日志

4. **测试失败**
   - 检查测试环境配置
   - 查看测试日志

### 调试命令

```bash
# 查看工作流日志
# 在 GitHub Actions 页面点击具体的工作流运行

# 远程服务器调试
ssh masterjia@home.worthwolf.top
cd /home/masterjia/ruralneighbour/ms-backend
microk8s kubectl get events --sort-by=.lastTimestamp
microk8s kubectl describe pod <pod-name> -n ruralneighbour
```

## 自定义配置

### 修改远程服务器信息

编辑工作流文件中的环境变量：

```yaml
env:
  REMOTE_HOST: your-server.com
  REMOTE_USER: your-username
  REMOTE_PATH: /path/to/your/project
```

### 添加新的测试

在 `test-only.yml` 中添加新的测试步骤：

```yaml
- name: Run custom tests
  run: |
    # 你的测试命令
```

### 修改部署策略

在 `build-and-deploy.yml` 中修改部署逻辑：

```yaml
- name: Custom deploy step
  run: |
    # 你的部署命令
```






