# Rating Service

评分服务微服务，支持用户对服务提供者进行评分和评论。

## 功能特性

- 评分 CRUD 操作
- 评分摘要统计
- 评分权限验证
- 字段映射兼容性（rating→rating_score，category→data.category）

## API 端点

- `GET /api/v1/ratings` - 获取评分列表
- `POST /api/v1/ratings/` - 创建评分
- `GET /api/v1/ratings/{ratingId}` - 获取特定评分
- `PATCH /api/v1/ratings/{ratingId}` - 更新评分
- `DELETE /api/v1/ratings/{ratingId}` - 删除评分
- `GET /api/v1/ratings/users/{userId}/summary` - 获取用户评分摘要
- `GET /api/v1/ratings/can_rate/{ratedUserId}/{serviceRequestId}` - 检查评分权限

## 运行服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 测试

```bash
pytest tests/
```






