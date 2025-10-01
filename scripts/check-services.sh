#!/bin/bash

# Rural Neighbour 服務狀態檢查腳本

REMOTE_HOST="home.worthwolf.top"
NAMESPACE="ruralneighbour-dev"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "🔍 Rural Neighbour 服務狀態檢查"
echo "=========================================="
echo "服務器: $REMOTE_HOST"
echo "命名空間: $NAMESPACE"
echo "時間: $(date)"
echo ""

echo "📋 Pod 狀態:"
ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --no-headers" | while read line; do
    name=$(echo $line | awk '{print $1}')
    ready=$(echo $line | awk '{print $2}')
    status=$(echo $line | awk '{print $3}')
    restarts=$(echo $line | awk '{print $4}')
    
    if [ "$status" = "Running" ]; then
        echo -e "  ${GREEN}✅${NC} $name - $status (重啟: $restarts)"
    elif [ "$status" = "Pending" ]; then
        echo -e "  ${YELLOW}⏳${NC} $name - $status (重啟: $restarts)"
    elif [ "$status" = "Completed" ]; then
        echo -e "  ${BLUE}✅${NC} $name - $status (重啟: $restarts)"
    else
        echo -e "  ${RED}❌${NC} $name - $status (重啟: $restarts)"
    fi
done

echo ""
echo "🔗 服務狀態:"
ssh $REMOTE_HOST "microk8s kubectl get svc -n $NAMESPACE --no-headers" | while read line; do
    echo "  📡 $line"
done

echo ""
echo "🌐 Ingress 狀態:"
ssh $REMOTE_HOST "microk8s kubectl get ingress -n $NAMESPACE --no-headers" | while read line; do
    echo "  🌍 $line"
done

echo ""
echo "📊 統計信息:"
TOTAL_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --no-headers | wc -l")
RUNNING_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers | wc -l")
FAILED_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed --no-headers | wc -l")
PENDING_PODS=$(ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase=Pending --no-headers | wc -l")

echo "  總 Pod 數: $TOTAL_PODS"
echo "  運行中: $RUNNING_PODS"
echo "  失敗: $FAILED_PODS"
echo "  等待中: $PENDING_PODS"

if [ $RUNNING_PODS -gt 0 ]; then
    PERCENTAGE=$((RUNNING_PODS * 100 / TOTAL_PODS))
    echo "  運行率: $PERCENTAGE%"
fi

echo ""
echo "🔍 API 端點測試:"
INGRESS_IP=$(ssh $REMOTE_HOST "microk8s kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'" 2>/dev/null || echo "192.168.1.183")

if [ ! -z "$INGRESS_IP" ]; then
    echo "  主入口: http://$INGRESS_IP"
    echo "  API 文檔: http://$INGRESS_IP/api-docs"
    echo "  健康檢查: http://$INGRESS_IP/health"
    
    echo ""
    echo "  測試健康檢查..."
    HEALTH_STATUS=$(ssh $REMOTE_HOST "curl -s -o /dev/null -w '%{http_code}' http://$INGRESS_IP/health" 2>/dev/null || echo "000")
    if [ "$HEALTH_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✅ 健康檢查正常${NC}"
    else
        echo -e "  ${RED}❌ 健康檢查失敗 (HTTP $HEALTH_STATUS)${NC}"
    fi
fi

echo ""
echo "⚠️  有問題的 Pod:"
ssh $REMOTE_HOST "microk8s kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers" | while read line; do
    if [ ! -z "$line" ]; then
        echo -e "  ${RED}❌ $line${NC}"
    fi
done

echo ""
echo "=========================================="
echo "檢查完成"
echo "=========================================="
