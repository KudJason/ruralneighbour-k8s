#!/bin/bash
# 在 K8s 环境中为所有服务运行 Alembic 迁移的简单脚本

set -e

echo "=================================================="
echo "K8s 服务 Alembic 迁移运行指南"
echo "=================================================="
echo ""

SERVICES=(
    "auth-service"
    "user-service"
    "location-service"
    "content-service"
    "request-service"
    "notification-service"
    "payment-service"
    "safety-service"
    "rating-service"
)

echo "以下服务需要运行迁移："
for service in "${SERVICES[@]}"; do
    echo "  - $service"
done

echo ""
echo "=================================================="
echo "方法 1: 在每个服务 Pod 中手动运行迁移"
echo "=================================================="
echo ""

for service in "${SERVICES[@]}"; do
    echo "# $service"
    echo "kubectl exec -it \$(kubectl get pod -l app=$service -o jsonpath='{.items[0].metadata.name}') -- alembic upgrade head"
    echo ""
done

echo "=================================================="
echo "方法 2: 重启所有服务让 docker-entrypoint.sh 自动运行"
echo "=================================================="
echo ""
echo "所有服务的 docker-entrypoint.sh 会在启动时自动运行 'alembic upgrade head'"
echo ""

for service in "${SERVICES[@]}"; do
    echo "kubectl rollout restart deployment/$service"
done

echo ""
echo "=================================================="
echo "方法 3: 使用批量脚本（推荐）"
echo "=================================================="
echo ""
echo "运行以下命令批量执行迁移："
echo ""
echo "for service in auth-service user-service location-service content-service request-service notification-service payment-service safety-service rating-service; do"
echo "  echo \"=== Running migration for \$service ===\";"
echo "  POD=\$(kubectl get pod -l app=\$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null);"
echo "  if [ -n \"\$POD\" ]; then"
echo "    kubectl exec -it \$POD -- alembic upgrade head || echo \"Failed: \$service\";"
echo "  else"
echo "    echo \"Pod not found for \$service\";"
echo "  fi;"
echo "  echo \"\";"
echo "done"

echo ""
echo "=================================================="
echo "验证迁移状态"
echo "=================================================="
echo ""
echo "检查每个服务的迁移版本："
echo ""
echo "for service in auth-service user-service location-service content-service request-service notification-service payment-service safety-service rating-service; do"
echo "  echo \"=== \$service migration status ===\";"
echo "  POD=\$(kubectl get pod -l app=\$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null);"
echo "  if [ -n \"\$POD\" ]; then"
echo "    kubectl exec \$POD -- alembic current 2>/dev/null || echo \"No migration applied\";"
echo "  fi;"
echo "  echo \"\";"
echo "done"

echo ""
echo "=================================================="
echo "注意事项"
echo "=================================================="
echo ""
echo "1. 确保所有服务的 Pod 都在运行"
echo "2. 确保 DATABASE_URL 环境变量已正确配置"
echo "3. location-service 需要 PostGIS 扩展"
echo "4. 建议先在测试环境验证迁移"
echo ""
