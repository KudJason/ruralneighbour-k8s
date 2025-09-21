#!/bin/bash
# ms-backend/k8s/combine_api_docs.sh
# 最简单的 API 文档合并脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取 Minikube IP
MINIKUBE_IP=$(minikube ip)
BASE_URL="http://$MINIKUBE_IP"
API_BASE="$BASE_URL/api/v1"

echo -e "${BLUE}📚 合并所有 API 文档${NC}"
echo "================================"

# 服务映射
declare -A SERVICES=(
    ["auth"]="auth-service"
    ["users"]="user-service" 
    ["locations"]="location-service"
    ["requests"]="request-service"
    ["payments"]="payment-service"
    ["notifications"]="notification-service"
    ["content"]="content-service"
    ["safety"]="safety-service"
)

# 创建临时目录
TEMP_DIR="/tmp/openapi-specs-$$"
mkdir -p "$TEMP_DIR"

echo -e "${YELLOW}📥 下载各服务的 OpenAPI 规范...${NC}"

# 下载所有服务的 OpenAPI 规范
for path in "${!SERVICES[@]}"; do
    service_name="${SERVICES[$path]}"
    echo -n "  下载 $service_name ... "
    
    if curl -s -f "$API_BASE/$path/openapi.json" -o "$TEMP_DIR/$service_name.json" 2>/dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        echo "    警告: 无法获取 $service_name 的 OpenAPI 规范"
    fi
done

echo ""
echo -e "${YELLOW}🔧 创建统一文档页面...${NC}"

# 创建简单的 HTML 文档页面
cat > "$TEMP_DIR/combined-docs.html" << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Rural Neighbor Connect - 统一 API 文档</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        .swagger-ui .topbar { display: none; }
        .swagger-ui .info { margin: 20px 0; }
        .service-link { 
            display: inline-block; 
            margin: 5px 10px; 
            padding: 8px 15px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px; 
        }
        .service-link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div style="padding: 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;">
        <h1>Rural Neighbor Connect - 统一 API 文档</h1>
        <p>选择要查看的服务文档：</p>
        <div>
            <a href="#auth" class="service-link">认证服务</a>
            <a href="#users" class="service-link">用户服务</a>
            <a href="#locations" class="service-link">位置服务</a>
            <a href="#requests" class="service-link">请求服务</a>
            <a href="#payments" class="service-link">支付服务</a>
            <a href="#notifications" class="service-link">通知服务</a>
            <a href="#content" class="service-link">内容服务</a>
            <a href="#safety" class="service-link">安全服务</a>
        </div>
    </div>
    
    <div id="swagger-ui"></div>
    
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script>
        // 服务配置
        const services = {
            "auth": { name: "认证服务", url: "$API_BASE/auth/openapi.json" },
            "users": { name: "用户服务", url: "$API_BASE/users/openapi.json" },
            "locations": { name: "位置服务", url: "$API_BASE/locations/openapi.json" },
            "requests": { name: "请求服务", url: "$API_BASE/requests/openapi.json" },
            "payments": { name: "支付服务", url: "$API_BASE/payments/openapi.json" },
            "notifications": { name: "通知服务", url: "$API_BASE/notifications/openapi.json" },
            "content": { name: "内容服务", url: "$API_BASE/content/openapi.json" },
            "safety": { name: "安全服务", url: "$API_BASE/safety/openapi.json" }
        };
        
        let currentService = 'auth';
        
        // 加载指定服务的文档
        function loadService(serviceKey) {
            const service = services[serviceKey];
            if (!service) return;
            
            currentService = serviceKey;
            document.title = service.name + ' - API 文档';
            
            // 更新页面标题
            document.querySelector('h1').textContent = service.name + ' - API 文档';
            
            // 加载 OpenAPI 规范
            fetch(service.url)
                .then(response => response.json())
                .then(spec => {
                    // 更新服务器 URL
                    spec.servers = [{ url: "$API_BASE/" + serviceKey, description: "API 服务" }];
                    
                    // 初始化 Swagger UI
                    SwaggerUIBundle({
                        spec: spec,
                        dom_id: '#swagger-ui',
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIBundle.presets.standalone
                        ],
                        layout: "StandaloneLayout",
                        deepLinking: true,
                        showExtensions: true,
                        showCommonExtensions: true
                    });
                })
                .catch(error => {
                    console.error('加载服务文档失败:', error);
                    document.getElementById('swagger-ui').innerHTML = 
                        '<div style="padding: 20px; color: red;">无法加载 ' + service.name + ' 的 API 文档</div>';
                });
        }
        
        // 绑定服务链接点击事件
        document.querySelectorAll('.service-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const serviceKey = this.getAttribute('href').substring(1);
                loadService(serviceKey);
            });
        });
        
        // 默认加载认证服务
        loadService('auth');
    </script>
</body>
</html>
EOL

# 复制到项目目录
OUTPUT_DIR="/home/masterjia/ruralneighbour/ms-backend/k8s"
cp "$TEMP_DIR/combined-docs.html" "$OUTPUT_DIR/combined-api-docs.html"

echo ""
echo -e "${GREEN}✅ 合并完成！${NC}"
echo ""
echo -e "${BLUE}📄 生成的文件：${NC}"
echo "  - 统一文档页面: $OUTPUT_DIR/combined-api-docs.html"
echo ""
echo -e "${YELLOW}🌐 访问方式：${NC}"
echo "  1. 在浏览器中打开: file://$OUTPUT_DIR/combined-api-docs.html"
echo "  2. 或者通过 HTTP 服务器:"
echo "     cd $OUTPUT_DIR"
echo "     python3 -m http.server 8080"
echo "     然后访问: http://localhost:8080/combined-api-docs.html"
echo ""
echo -e "${BLUE}📊 各服务状态：${NC}"
for path in "${!SERVICES[@]}"; do
    service_name="${SERVICES[$path]}"
    if curl -s -f "$API_BASE/$path/health" > /dev/null 2>&1; then
        echo "  ✅ $service_name ($path) - 运行中"
    else
        echo "  ❌ $service_name ($path) - 离线"
    fi
done

# 清理临时文件
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}🎉 完成！现在您可以在一个页面查看所有 API 文档了！${NC}"








