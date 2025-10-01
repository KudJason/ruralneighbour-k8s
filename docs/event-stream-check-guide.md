# 事件流檢查指南

## 📋 概述

本文檔提供檢查 Rural Neighbour 微服務架構中 Redis 事件流配置和功能的完整指南。

## 🔍 檢查項目清單

### 1. Redis 服務狀態檢查

#### 1.1 基本連接檢查

```bash
# 檢查Redis服務是否運行
ssh home.worthwolf.top "microk8s kubectl get pods -n ruralneighbour-dev | grep redis"

# 測試Redis連接
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli ping"
```

#### 1.2 Redis Streams 檢查

```bash
# 檢查所有Redis Streams
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XINFO STREAMS"

# 檢查特定Stream的長度
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN user_lifecycle"
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN service_lifecycle"
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN payment_lifecycle"
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN safety_lifecycle"
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN investment_lifecycle"
```

### 2. 微服務 Redis 配置檢查

#### 2.1 環境變量檢查

```bash
# 檢查各服務的Redis環境變量
for service in auth-service user-service notification-service payment-service request-service rating-service location-service content-service safety-service investment-service; do
    echo "=== $service Redis配置 ==="
    ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/$service -- env | grep -i redis"
    echo ""
done
```

#### 2.2 連接測試

```bash
# 測試各服務的Redis連接
for service in auth-service user-service notification-service payment-service request-service rating-service location-service content-service safety-service investment-service; do
    echo "=== 測試 $service Redis連接 ==="
    ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/$service -- python -c 'import redis; r = redis.Redis(host=\"redis-service\", port=6379); print(\"$service Redis連接:\", r.ping())'"
    echo ""
done
```

### 3. 事件流配置檢查

#### 3.1 配置映射檢查

```bash
# 檢查Redis配置映射
ssh home.worthwolf.top "microk8s kubectl get configmap redis-config -n ruralneighbour-dev -o yaml"

# 檢查事件流名稱配置
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/auth-service -- env | grep STREAM"
```

#### 3.2 事件發布者檢查

```bash
# 檢查各服務的事件發布者實現
for service in auth-service user-service payment-service request-service; do
    echo "=== $service 事件發布者檢查 ==="
    ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/$service -- python -c 'from app.services.events import EventPublisher; print(\"EventPublisher 可用\")'"
    echo ""
done
```

### 4. 事件流功能測試

#### 4.1 手動事件發布測試

```bash
# 在request-service中發布測試事件
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/request-service -- python -c '
from app.services.events import EventPublisher
import uuid
result = EventPublisher.publish_service_request_created(
    request_id=str(uuid.uuid4()),
    requester_id=str(uuid.uuid4()),
    service_type=\"test_cleaning\",
    location={\"latitude\": 40.7128, \"longitude\": -74.0060}
)
print(\"事件發布結果:\", result)
'"
```

#### 4.2 事件消費測試

```bash
# 檢查payment-service是否能消費事件
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/payment-service -- python -c '
from app.services.events import EventConsumer
print(\"EventConsumer 可用\")
'"
```

#### 4.3 事件流數據檢查

```bash
# 檢查service_lifecycle流中的最新事件
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XREAD STREAMS service_lifecycle 0 COUNT 5"

# 檢查payment_lifecycle流中的最新事件
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XREAD STREAMS payment_lifecycle 0 COUNT 5"
```

### 5. 事件流監控

#### 5.1 實時事件監控

```bash
# 監控所有事件流
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XREAD BLOCK 5000 STREAMS user_lifecycle service_lifecycle payment_lifecycle safety_lifecycle investment_lifecycle \$ \$ \$ \$ \$"
```

#### 5.2 事件統計

```bash
# 統計各事件流的事件數量
for stream in user_lifecycle service_lifecycle payment_lifecycle safety_lifecycle investment_lifecycle; do
    count=$(ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN $stream")
    echo "$stream: $count 個事件"
done
```

### 6. 錯誤檢查

#### 6.1 服務日誌檢查

```bash
# 檢查各服務的Redis相關錯誤
for service in auth-service user-service payment-service request-service; do
    echo "=== $service Redis相關日誌 ==="
    ssh home.worthwolf.top "microk8s kubectl logs -n ruralneighbour-dev deployment/$service --tail=50 | grep -i redis"
    echo ""
done
```

#### 6.2 事件發布錯誤檢查

```bash
# 檢查事件發布錯誤
ssh home.worthwolf.top "microk8s kubectl logs -n ruralneighbour-dev deployment/request-service --tail=100 | grep -i 'event\|redis\|stream'"
```

## 🧪 自動化測試腳本

### 完整檢查腳本

```bash
#!/bin/bash
# event-stream-check.sh

echo "🔍 Rural Neighbour 事件流檢查"
echo "================================"

# 1. Redis服務檢查
echo "1. 檢查Redis服務狀態..."
ssh home.worthwolf.top "microk8s kubectl get pods -n ruralneighbour-dev | grep redis"

# 2. 連接測試
echo "2. 測試Redis連接..."
ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli ping"

# 3. 事件流長度檢查
echo "3. 檢查事件流長度..."
for stream in user_lifecycle service_lifecycle payment_lifecycle safety_lifecycle investment_lifecycle; do
    count=$(ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/redis-service -- redis-cli XLEN $stream")
    echo "  $stream: $count 個事件"
done

# 4. 服務連接測試
echo "4. 測試各服務Redis連接..."
for service in auth-service user-service payment-service request-service; do
    result=$(ssh home.worthwolf.top "microk8s kubectl exec -n ruralneighbour-dev deployment/$service -- python -c 'import redis; r = redis.Redis(host=\"redis-service\", port=6379); print(r.ping())'" 2>/dev/null)
    echo "  $service: $result"
done

echo "檢查完成！"
```

## 📊 預期結果

### 正常狀態指標

- ✅ Redis 服務運行正常
- ✅ 所有微服務能連接到 Redis
- ✅ 事件流配置正確
- ✅ 事件發布和消費功能正常
- ✅ 無 Redis 連接錯誤

### 問題指標

- ❌ Redis 服務無法連接
- ❌ 微服務 Redis 連接失敗
- ❌ 事件流為空或無數據
- ❌ 事件發布失敗
- ❌ 大量 Redis 錯誤日誌

## 🔧 故障排除

### 常見問題

1. **Redis 連接失敗**: 檢查 Redis 服務狀態和網絡配置
2. **事件流為空**: 檢查事件發布者實現和配置
3. **事件消費失敗**: 檢查消費者實現和錯誤處理
4. **配置錯誤**: 檢查環境變量和 ConfigMap 配置

### 修復步驟

1. 重啟有問題的服務
2. 檢查 Redis 配置
3. 驗證事件流實現
4. 檢查服務日誌
5. 重新部署配置

## 📝 檢查報告模板

```
事件流檢查報告
================
檢查時間: [時間]
檢查者: [姓名]

1. Redis服務狀態: [正常/異常]
2. 事件流配置: [完整/不完整]
3. 連接測試: [通過/失敗]
4. 事件發布: [正常/異常]
5. 事件消費: [正常/異常]

問題列表:
- [問題1]
- [問題2]

建議修復:
- [建議1]
- [建議2]
```


