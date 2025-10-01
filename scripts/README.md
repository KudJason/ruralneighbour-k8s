# Rural Neighbour 自動化部署腳本

本目錄包含了用於自動化部署和測試 Rural Neighbour 微服務的腳本。

## 📁 腳本說明

### 1. `auto-deploy-test.sh` - 測試環境自動化部署

**用途**: 完整的自動化部署流程，包括構建、推送、部署和初始化（測試環境 - 單副本）

**功能**:

- ✅ 檢查遠程服務器連接
- ✅ 檢查 Docker 和 MicroK8s 服務
- ✅ 同步代碼到遠程服務器
- ✅ 構建所有服務鏡像
- ✅ 推送鏡像到 registry
- ✅ 部署到 MicroK8s（使用測試環境 overlay）
- ✅ 自動配置單副本和資源限制
- ✅ 初始化數據庫
- ✅ 檢查服務狀態

**使用方法**:

```bash
# 完整部署
./auto-deploy-test.sh

# 清理部署
./auto-deploy-test.sh cleanup
```

### 2. `auto-deploy-production.sh` - 生產環境自動化部署

**用途**: 完整的自動化部署流程，包括構建、推送、部署和初始化（生產環境 - 多副本）

**功能**:

- ✅ 檢查遠程服務器連接
- ✅ 檢查 Docker 和 MicroK8s 服務
- ✅ 同步代碼到遠程服務器
- ✅ 構建所有服務鏡像
- ✅ 推送鏡像到 registry
- ✅ 部署到 MicroK8s（使用生產環境 overlay）
- ✅ 保持多副本和高資源配置
- ✅ 初始化數據庫
- ✅ 檢查服務狀態

**使用方法**:

```bash
# 完整部署
./auto-deploy-production.sh

# 清理部署
./auto-deploy-production.sh cleanup
```

### 3. `quick-deploy.sh` - 快速重新部署

**用途**: 快速重新部署已修改的服務

**功能**:

- ✅ 同步代碼
- ✅ 重新構建指定服務
- ✅ 重新推送鏡像
- ✅ 重新部署服務

**使用方法**:

```bash
# 重新部署單個服務
./quick-deploy.sh auth-service

# 重新部署多個服務
./quick-deploy.sh auth-service user-service

# 重新部署所有服務
./quick-deploy.sh all
```

### 3. `check-services.sh` - 服務狀態檢查

**用途**: 檢查所有服務的運行狀態

**功能**:

- ✅ 顯示 Pod 狀態
- ✅ 顯示服務狀態
- ✅ 顯示 Ingress 狀態
- ✅ 統計信息
- ✅ API 端點測試
- ✅ 健康檢查

**使用方法**:

```bash
./check-services.sh
```

## 🚀 快速開始

### 首次部署（測試環境）

```bash
cd /Users/jasonjia/codebase/ruralneighbour/ms-backend/scripts
./auto-deploy-test.sh
```

> 注意：此腳本會自動將所有服務調整為單副本，適合測試環境使用

### 日常開發

```bash
# 修改代碼後，快速重新部署
./quick-deploy.sh auth-service

# 檢查服務狀態
./check-services.sh
```

## ⚙️ 配置

### 環境變量

腳本使用以下配置（可在腳本中修改）:

- `REMOTE_HOST`: 遠程服務器地址 (`home.worthwolf.top`)
- `REGISTRY_HOST`: Docker registry 地址 (`127.0.0.1:32000`)
- `NAMESPACE`: Kubernetes 命名空間 (`ruralneighbour-dev` 或 `ruralneighbour-prod`)

### Kustomize 配置管理

使用 Kustomize overlays 來管理不同環境的配置：

#### 測試環境 (`overlays/test-environment/`)

- **副本數**: 所有服務設置為 1 個副本
- **資源限制**: 較低的 CPU/內存限制（適合測試）
- **命名空間**: `ruralneighbour-dev`

#### 生產環境 (`overlays/production/`)

- **副本數**: 保持原有的多副本配置
- **資源限制**: 較高的 CPU/內存限制（適合生產）
- **命名空間**: `ruralneighbour-prod`

#### 配置文件結構

```
k8s/
├── base/                    # 基礎配置
├── overlays/
│   ├── test-environment/    # 測試環境 overlay
│   │   ├── kustomization.yaml
│   │   ├── replicas-patch.yaml
│   │   └── resource-limits-patch.yaml
│   └── production/          # 生產環境 overlay
│       └── kustomization.yaml
```

### 服務列表

支持以下微服務:

- `auth-service` - 認證服務
- `user-service` - 用戶服務
- `content-service` - 內容服務
- `request-service` - 請求服務
- `location-service` - 位置服務
- `notification-service` - 通知服務
- `payment-service` - 支付服務
- `rating-service` - 評分服務
- `safety-service` - 安全服務
- `investment-service` - 投資服務

## 🔧 故障排除

### 常見問題

1. **SSH 連接失敗**

   ```bash
   # 檢查 SSH 配置
   ssh home.worthwolf.top "echo 'Connection test'"
   ```

2. **Docker 權限問題**

   ```bash
   # 檢查 Docker 服務
   ssh home.worthwolf.top "docker info"
   ```

3. **MicroK8s 服務異常**

   ```bash
   # 檢查 MicroK8s 狀態
   ssh home.worthwolf.top "microk8s status"
   ```

4. **鏡像構建失敗**

   ```bash
   # 檢查服務代碼
   ssh home.worthwolf.top "ls -la ~/services/"
   ```

5. **Pod 啟動失敗**
   ```bash
   # 查看 Pod 日誌
   ssh home.worthwolf.top "microk8s kubectl logs <pod-name> -n ruralneighbour-dev"
   ```

### 清理和重置

```bash
# 清理所有資源
./auto-deploy-test.sh cleanup

# 手動清理
ssh home.worthwolf.top "microk8s kubectl delete namespace ruralneighbour-dev"
```

## 📊 監控和日誌

### 查看服務日誌

```bash
# 查看特定服務日誌
ssh home.worthwolf.top "microk8s kubectl logs -f deployment/auth-service -n ruralneighbour-dev"

# 查看所有 Pod 日誌
ssh home.worthwolf.top "microk8s kubectl logs -f --all-containers=true -n ruralneighbour-dev"
```

### 監控資源使用

```bash
# 查看資源使用情況
ssh home.worthwolf.top "microk8s kubectl top pods -n ruralneighbour-dev"
```

## 🌐 API 端點

部署完成後，可以通過以下端點訪問服務:

- **主入口**: http://192.168.1.183
- **API 文檔**: http://192.168.1.183/api-docs
- **健康檢查**: http://192.168.1.183/health

## 📝 注意事項

1. **資源要求**: 確保遠程服務器有足夠的 CPU 和內存資源
2. **網絡連接**: 確保本地和遠程服務器之間的網絡連接穩定
3. **權限設置**: 確保 SSH 和 Docker 權限正確配置
4. **鏡像大小**: 注意鏡像大小，避免 registry 存儲空間不足

## 🔄 更新流程

1. 修改代碼
2. 運行 `./quick-deploy.sh <service-name>`
3. 運行 `./check-services.sh` 檢查狀態
4. 如有問題，查看日誌並修復

## 📞 支持

如有問題，請檢查:

1. 腳本日誌輸出
2. Kubernetes 事件: `microk8s kubectl get events -n ruralneighbour-dev`
3. Pod 日誌: `microk8s kubectl logs <pod-name> -n ruralneighbour-dev`
