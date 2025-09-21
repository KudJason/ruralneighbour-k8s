# 手动部署指南 - home.worthwolf.top

由于权限问题，请按照以下步骤在服务器上手动部署：

## 1. SSH 连接到服务器

```bash
ssh masterjia@home.worthwolf.top
```

## 2. 配置 Docker 权限

```bash
# 将用户添加到 docker 组
sudo usermod -aG docker masterjia

# 重启 Docker 服务
sudo systemctl restart docker

# 重新登录以应用组权限
exit
ssh masterjia@home.worthwolf.top
```

## 3. 进入项目目录

```bash
cd /home/masterjia/ruralneighbour/ms-backend
```

## 4. 启动服务

```bash
# 停止现有服务（如果有）
docker-compose down

# 启动所有服务
docker-compose up -d --build
```

## 5. 检查服务状态

```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs auth-service
```

## 6. 访问 API 文档

服务启动后，您可以通过以下地址访问各服务的 API 文档：

- **认证服务**: http://home.worthwolf.top:8001/docs
- **用户服务**: http://home.worthwolf.top:8002/docs
- **位置服务**: http://home.worthwolf.top:8003/docs
- **请求服务**: http://home.worthwolf.top:8004/docs
- **支付服务**: http://home.worthwolf.top:8005/docs
- **通知服务**: http://home.worthwolf.top:8006/docs
- **内容服务**: http://home.worthwolf.top:8007/docs
- **安全服务**: http://home.worthwolf.top:8008/docs

## 7. 启动统一文档服务器

```bash
# 启动文档服务器
cd /home/masterjia/ruralneighbour/ms-backend
python3 -m http.server 8080 &

# 访问统一文档
# http://home.worthwolf.top:8080/combined-docs.html
```

## 8. 管理命令

```bash
# 重启特定服务
docker-compose restart auth-service

# 重启所有服务
docker-compose restart

# 停止所有服务
docker-compose down

# 查看服务资源使用情况
docker stats

# 进入服务容器
docker-compose exec auth-service bash
```

## 9. 故障排除

### 如果服务无法启动：

```bash
# 查看详细日志
docker-compose logs --tail=50 auth-service

# 检查端口占用
netstat -tlnp | grep :8001

# 检查 Docker 状态
docker ps -a
```

### 如果权限问题：

```bash
# 检查用户组
groups

# 重新应用组权限
newgrp docker

# 或者使用 sudo 运行
sudo docker-compose up -d
```

## 10. 服务端口映射

| 服务                 | 端口 | 描述     |
| -------------------- | ---- | -------- |
| auth-service         | 8001 | 认证服务 |
| user-service         | 8002 | 用户服务 |
| location-service     | 8003 | 位置服务 |
| request-service      | 8004 | 请求服务 |
| payment-service      | 8005 | 支付服务 |
| notification-service | 8006 | 通知服务 |
| content-service      | 8007 | 内容服务 |
| safety-service       | 8008 | 安全服务 |
| postgres             | 5432 | 数据库   |
| redis                | 6379 | 缓存     |

## 11. 健康检查

```bash
# 检查服务健康状态
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
curl http://localhost:8006/health
curl http://localhost:8007/health
curl http://localhost:8008/health
```

## 12. 备份和恢复

```bash
# 备份数据库
docker-compose exec postgres pg_dump -U postgres ruralneighbour > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U postgres ruralneighbour < backup.sql
```

完成这些步骤后，您的所有微服务将在 home.worthwolf.top 上运行，并且可以通过统一的文档页面访问所有 API 文档。








