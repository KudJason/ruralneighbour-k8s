#!/bin/bash
# 为所有微服务生成初始迁移

set -e

echo "=================================================="
echo "为所有微服务生成初始 Alembic 迁移..."
echo "=================================================="
echo ""

# 临时使用本地数据库 URL 进行迁移生成
export DATABASE_URL="sqlite:///temp.db"

SERVICES=(
    "auth-service"
    "user-service"
    "location-service"
    "content-service"
    "request-service"
    "notification-service"
    "payment-service"
    "safety-service"
)

for SERVICE in "${SERVICES[@]}"; do
    echo "------------------------------------------------"
    echo "处理: $SERVICE"
    echo "------------------------------------------------"
    
    cd "$SERVICE"
    
    # 检查是否已有迁移
    if ls alembic/versions/*.py 2>/dev/null | grep -v __pycache__ | head -1 > /dev/null; then
        echo "✓ $SERVICE 已有迁移文件，跳过"
    else
        echo "生成初始迁移..."
        alembic revision --autogenerate -m "Initial migration" || echo "⚠️ 自动生成失败，需要手动创建"
    fi
    
    cd ..
    echo ""
done

echo "=================================================="
echo "迁移生成完成！"
echo "=================================================="
echo ""
echo "请检查生成的迁移文件并根据需要调整。"
