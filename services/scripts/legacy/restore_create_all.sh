#!/bin/bash
# 临时恢复 create_all() 以便快速部署测试

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
echo "临时恢复 create_all() 调用..."
echo "=================================================="

for SERVICE in "${SERVICES[@]}"; do
    MAIN_FILE="$SERVICE/app/main.py"
    BACKUP_FILE="$MAIN_FILE.bak"
    
    if [ -f "$BACKUP_FILE" ]; then
        echo "恢复: $SERVICE/app/main.py"
        cp "$BACKUP_FILE" "$MAIN_FILE"
        echo "✓ $SERVICE 已恢复"
    else
        echo "⚠️  $BACKUP_FILE 不存在，跳过"
    fi
done

echo "=================================================="
echo"完成！已恢复 create_all() 调用"
echo "=================================================="
