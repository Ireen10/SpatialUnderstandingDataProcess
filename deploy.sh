#!/bin/bash

# 生产环境一键部署脚本
# 适用于 Linux/Mac

set -e

echo "=========================================="
echo "  SpatialUnderstandingDataProcess"
echo "  生产环境部署"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN"
esac

# 获取本机IP
get_local_ip() {
    case "$MACHINE" in
        Linux)
            hostname -I | awk '{print $1}'
            ;;
        Mac)
            ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1
            ;;
        *)
            ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "127.0.0.1"
            ;;
    esac
}

LOCAL_IP=$(get_local_ip)
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

# 检查 Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Docker 未安装，正在安装...${NC}"
        
        if [ "$MACHINE" = "Mac" ]; then
            echo "请手动安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
            exit 1
        elif [ "$MACHINE" = "Linux" ]; then
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker $USER
            echo -e "${GREEN}Docker 安装完成，请重新登录后运行此脚本${NC}"
            exit 0
        fi
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${YELLOW}Docker Compose 未安装，正在安装...${NC}"
        if [ "$MACHINE" = "Linux" ]; then
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    fi
    
    echo -e "${GREEN}✓ Docker 已安装${NC}"
}

# 检查 Node.js（可选，用于本地构建）
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"
        return 0
    else
        echo -e "${YELLOW}! Node.js 未安装，将使用 Docker 构建${NC}"
        return 1
    fi
}

# 创建环境文件
create_env() {
    if [ ! -f ".env" ]; then
        echo ""
        echo -e "${BLUE}创建环境配置...${NC}"
        
        # 生成随机密钥
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | xxd -p)
        
        cat > .env << EOF
# 生产环境配置
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/sudp
REDIS_URL=redis://redis:6379/0
DATA_STORAGE_PATH=/data

# API 配置（可选）
OPENROUTER_API_KEY=
OPENROUTER_MODEL=z-ai/glm-5

# 服务端口
BACKEND_PORT=8080
FRONTEND_PORT=80
EOF
        
        echo -e "${GREEN}✓ 已创建 .env 文件${NC}"
    else
        echo -e "${GREEN}✓ .env 文件已存在${NC}"
    fi
}

# 创建必要目录
create_dirs() {
    mkdir -p logs
    mkdir -p data
    mkdir -p docker/nginx
}

# 构建前端
build_frontend() {
    echo ""
    echo -e "${BLUE}构建前端...${NC}"
    
    cd "$SCRIPT_DIR/frontend"
    
    if command -v npm &> /dev/null; then
        npm install --silent 2>/dev/null || npm install
        npm run build
        echo -e "${GREEN}✓ 前端构建完成${NC}"
    else
        echo -e "${YELLOW}! npm 未安装，跳过本地构建${NC}"
    fi
    
    cd "$SCRIPT_DIR"
}

# 启动服务
start_services() {
    echo ""
    echo -e "${BLUE}启动 Docker 服务...${NC}"
    
    # 使用 docker-compose
    if docker compose version &> /dev/null; then
        docker compose up -d --build
    else
        docker-compose up -d --build
    fi
    
    echo -e "${GREEN}✓ 服务已启动${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo ""
    echo -e "${BLUE}等待服务启动...${NC}"
    
    for i in {1..30}; do
        if curl -s "http://localhost:8080/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 后端服务已就绪${NC}"
            break
        fi
        sleep 1
    done
}

# 显示信息
show_info() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ 部署完成！${NC}"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo -e "  ${GREEN}应用:${NC}    http://${LOCAL_IP}"
    echo -e "  ${GREEN}API文档:${NC} http://${LOCAL_IP}:8080/docs"
    echo ""
    echo "默认配置:"
    echo "  数据存储: ./data"
    echo "  日志目录: ./logs"
    echo ""
    echo "管理命令:"
    echo "  停止服务: ./deploy.sh stop"
    echo "  查看日志: docker compose logs -f"
    echo "  重启服务: docker compose restart"
    echo ""
}

# 停止服务
stop_services() {
    echo "停止服务..."
    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi
    echo "服务已停止"
}

# 主函数
main() {
    case "${1:-start}" in
        start)
            create_dirs
            check_docker
            check_node
            create_env
            build_frontend
            start_services
            wait_for_services
            show_info
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            start_services
            wait_for_services
            show_info
            ;;
        *)
            echo "用法: $0 {start|stop|restart}"
            exit 1
            ;;
    esac
}

main "$@"