#!/bin/bash
# 从所有服务的 main.py 中移除 Base.metadata.create_all() 调用

set -e

SERVICES=(
    "auth-service"
    "user-service"
    "location-service"
    "content-service"
    "request-service"
    "notification-service"
    "payment-service"
    "safety-service"
    "investment-service"
)

echo "=================================================="
echo "移除所有服务中的 Base.metadata.create_all() 调用..."
echo "=================================================="
echo ""

for SERVICE in "${SERVICES[@]}"; do
    MAIN_FILE="$SERVICE/app/main.py"
    
    if [ -f "$MAIN_FILE" ]; then
        echo "处理: $SERVICE/app/main.py"
        
        # 备份原文件
        cp "$MAIN_FILE" "$MAIN_FILE.bak"
        
        # 移除包含 create_all 的行以及相关的条件判断
        sed -i '' '/Base\.metadata\.create_all/d' "$MAIN_FILE"
        sed -i '' '/if os\.getenv("TESTING") != "true":/d' "$MAIN_FILE"
        
        echo "✓ $SERVICE 已处理"
    else
        echo "⚠️  $MAIN_FILE 不存在，跳过"
    fi
    echo ""
done

echo "=================================================="
echo "完成！所有 create_all() 调用已移除"
echo "=================================================="
echo "备份文件保存为 *.bak"
