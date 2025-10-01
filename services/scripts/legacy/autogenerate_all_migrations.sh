#!/bin/bash
# 自动为所有服务生成 Alembic 迁移

set -e

echo "=================================================="
echo "为所有微服务自动生成 Alembic 迁移..."
echo "=================================================="
echo ""

# 服务列表（排除 auth-service 和 rating-service，它们已有完整迁移）
SERVICES=(
    "user-service"
    "location-service"
    "content-service"
    "request-service"
    "notification-service"
    "payment-service"
    "safety-service"
)

for SERVICE in "${SERVICES[@]}"; do
    echo "=================================================="
    echo "处理: $SERVICE"
    echo "=================================================="
    
    cd "$SERVICE"
    
    # 删除现有的占位符迁移
    rm -f alembic/versions/0001_initial_migration.py
    
    # 使用临时 SQLite 数据库生成迁移
    echo "生成迁移..."
    export DATABASE_URL="sqlite:///./temp_migration.db"
    
    # 运行 autogenerate
    alembic revision --autogenerate -m "Initial migration" || {
        echo "⚠️  自动生成失败，保留模板"
    }
    
    # 清理临时数据库
    rm -f temp_migration.db
    
    # 检查生成的迁移文件
    MIGRATION_FILE=$(ls -t alembic/versions/*.py 2>/dev/null | head -1)
    if [ -n "$MIGRATION_FILE" ]; then
        echo "✓ 生成迁移: $MIGRATION_FILE"
        echo "内容预览:"
        head -30 "$MIGRATION_FILE"
    fi
    
    cd ..
    echo ""
done

echo "=================================================="
echo "迁移生成完成！"
echo "=================================================="
