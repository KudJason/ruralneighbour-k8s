# Investment Service

FastAPI 微服务，提供 `/api/v1/investments` CRUD，用于前端 `InvestmentService`。

本地运行：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8092
```

端点：
- GET /api/v1/investments/
- POST /api/v1/investments/
- GET /api/v1/investments/{id}
- PATCH /api/v1/investments/{id}
- DELETE /api/v1/investments/{id}








