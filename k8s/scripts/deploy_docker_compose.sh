#!/bin/bash
# ms-backend/k8s/deploy_docker_compose.sh
# 使用 Docker Compose 的简单部署方案

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 服务器配置
REMOTE_HOST="home.worthwolf.top"
REMOTE_USER="masterjia"
REMOTE_PATH="/home/masterjia/ruralneighbour"
LOCAL_PATH="/Users/jasonjia/codebase/ruralneighbour"

echo -e "${BLUE}🚀 使用 Docker Compose 部署到 home.worthwolf.top${NC}"
echo "=============================================="

# 检查 SSH 连接
echo -e "${YELLOW}🔍 检查服务器连接...${NC}"
if ! ssh -o ConnectTimeout=10 $REMOTE_USER@$REMOTE_HOST "echo '连接成功'" 2>/dev/null; then
    echo -e "${RED}❌ 无法连接到服务器 $REMOTE_HOST${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 服务器连接正常${NC}"

# 同步代码到远程服务器
echo -e "${YELLOW}📤 同步代码到远程服务器...${NC}"
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='dist' \
    --exclude='build' \
    $LOCAL_PATH/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

echo -e "${GREEN}✅ 代码同步完成${NC}"

# 在远程服务器上执行部署
echo -e "${YELLOW}🔧 在远程服务器上执行部署...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd /home/masterjia/ruralneighbour/ms-backend

echo "🔧 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker 安装完成"
else
    echo "✅ Docker 已安装"
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，正在安装..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose 安装完成"
else
    echo "✅ Docker Compose 已安装"
fi

# 确保用户有 Docker 权限
echo "🔐 配置 Docker 权限..."
sudo usermod -aG docker $USER

echo "🚀 启动服务..."
# 停止现有服务
docker-compose down 2>/dev/null || true

# 启动服务
docker-compose up -d --build

echo "⏳ 等待服务启动..."
sleep 30

echo "📊 服务状态："
docker-compose ps

echo "🔗 访问地址："
echo "  - 认证服务: http://localhost:8001/docs"
echo "  - 用户服务: http://localhost:8002/docs"
echo "  - 位置服务: http://localhost:8003/docs"
echo "  - 请求服务: http://localhost:8004/docs"
echo "  - 支付服务: http://localhost:8005/docs"
echo "  - 通知服务: http://localhost:8006/docs"
echo "  - 内容服务: http://localhost:8007/docs"
echo "  - 安全服务: http://localhost:8008/docs"

# 创建简单的文档聚合页面
echo "📚 创建统一 API 文档..."
cat > /home/masterjia/ruralneighbour/ms-backend/combined-docs.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>Rural Neighbor Connect - 统一 API 文档</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .service-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: #fafafa; }
        .service-card h3 { color: #007bff; margin-top: 0; }
        .service-card p { color: #666; margin: 10px 0; }
        .service-links { margin-top: 15px; }
        .service-links a { display: inline-block; margin: 5px 10px 5px 0; padding: 8px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 14px; }
        .service-links a:hover { background: #0056b3; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status.running { background: #d4edda; color: #155724; }
        .status.stopped { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Rural Neighbor Connect - 统一 API 文档</h1>
        <p style="text-align: center; color: #666;">所有微服务的 API 文档入口</p>
        
        <div class="service-grid">
            <div class="service-card">
                <h3>🔐 认证服务 (Auth Service)</h3>
                <p>处理用户认证、登录、注册和令牌管理</p>
                <div class="service-links">
                    <a href="http://localhost:8001/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8001/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8001/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>👤 用户服务 (User Service)</h3>
                <p>管理用户信息、个人资料和用户数据</p>
                <div class="service-links">
                    <a href="http://localhost:8002/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8002/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8002/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>📍 位置服务 (Location Service)</h3>
                <p>处理地理位置、地址管理和位置验证</p>
                <div class="service-links">
                    <a href="http://localhost:8003/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8003/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8003/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>📋 请求服务 (Request Service)</h3>
                <p>管理服务请求、任务分配和请求状态</p>
                <div class="service-links">
                    <a href="http://localhost:8004/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8004/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8004/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>💳 支付服务 (Payment Service)</h3>
                <p>处理支付、交易和支付方式管理</p>
                <div class="service-links">
                    <a href="http://localhost:8005/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8005/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8005/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>🔔 通知服务 (Notification Service)</h3>
                <p>发送通知、消息和事件处理</p>
                <div class="service-links">
                    <a href="http://localhost:8006/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8006/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8006/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>📰 内容服务 (Content Service)</h3>
                <p>管理新闻、文章和内容发布</p>
                <div class="service-links">
                    <a href="http://localhost:8007/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8007/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8007/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
            
            <div class="service-card">
                <h3>🛡️ 安全服务 (Safety Service)</h3>
                <p>处理安全报告、争议和指标统计</p>
                <div class="service-links">
                    <a href="http://localhost:8008/docs" target="_blank">Swagger UI</a>
                    <a href="http://localhost:8008/redoc" target="_blank">ReDoc</a>
                    <a href="http://localhost:8008/openapi.json" target="_blank">OpenAPI JSON</a>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>📊 服务状态</h3>
            <p>要查看服务状态，请在服务器上运行：</p>
            <code>docker-compose ps</code>
        </div>
    </div>
</body>
</html>
EOL

# 启动文档服务器
echo "🌐 启动文档服务器..."
nohup python3 -m http.server 8080 > /dev/null 2>&1 &
echo "文档服务器已启动在端口 8080"

EOF

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo -e "${BLUE}🌐 访问信息：${NC}"
echo "  - 服务器: $REMOTE_HOST"
echo "  - 统一文档: http://$REMOTE_HOST:8080/combined-docs.html"
echo ""
echo -e "${YELLOW}🔧 管理命令：${NC}"
echo "1. SSH 连接到服务器:"
echo "   ssh $REMOTE_USER@$REMOTE_HOST"
echo ""
echo "2. 进入项目目录:"
echo "   cd $REMOTE_PATH/ms-backend"
echo ""
echo "3. 查看服务状态:"
echo "   docker-compose ps"
echo ""
echo "4. 查看服务日志:"
echo "   docker-compose logs [service-name]"
echo ""
echo "5. 重启服务:"
echo "   docker-compose restart [service-name]"
echo ""
echo "6. 停止所有服务:"
echo "   docker-compose down"








