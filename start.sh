#!/bin/bash

# SpatialUnderstandingDataProcess 一键启动脚本
# 适用于 Linux/Mac

set -e

echo "=========================================="
echo "  SpatialUnderstandingDataProcess"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN"
esac

# 获取本机IP地址
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

# 检查 Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        echo -e "${RED}错误: 未找到 Python${NC}"
        echo "请先安装 Python 3.10+"
        exit 1
    fi
    echo -e "${GREEN}✓ Python: $($PYTHON_CMD --version)${NC}"
}

# 检查 Node.js
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        echo -e "${GREEN}✓ Node.js: $NODE_VERSION${NC}"
    else
        echo -e "${YELLOW}! Node.js 未安装，前端将无法启动${NC}"
        echo "  请安装 Node.js 18+ : https://nodejs.org/"
    fi
}

# 安装后端依赖
install_backend() {
    echo ""
    echo "正在检查后端依赖..."
    
    cd "$SCRIPT_DIR/backend"
    
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate 2>/dev/null || . venv/bin/activate
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        echo "安装 Python 依赖..."
        pip install -r requirements.txt -q
    fi
    
    echo -e "${GREEN}✓ 后端依赖已就绪${NC}"
}

# 安装前端依赖
install_frontend() {
    echo ""
    echo "正在检查前端依赖..."
    
    cd "$SCRIPT_DIR/frontend"
    
    if command -v npm &> /dev/null; then
        if [ ! -d "node_modules" ]; then
            echo "安装 npm 依赖..."
            npm install --silent 2>/dev/null
        fi
        echo -e "${GREEN}✓ 前端依赖已就绪${NC}"
    else
        echo -e "${YELLOW}! 跳过前端依赖安装${NC}"
    fi
}

# 启动后端
start_backend() {
    echo ""
    echo "启动后端服务..."
    
    cd "$SCRIPT_DIR/backend"
    
    # 激活虚拟环境
    source venv/bin/activate 2>/dev/null || . venv/bin/activate
    
    # 检查是否已有实例运行
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo -e "${YELLOW}! 后端服务已在运行${NC}"
        return
    fi
    
    # 设置默认环境变量
    export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/app.db}"
    export DATA_STORAGE_PATH="${DATA_STORAGE_PATH:-./data}"
    
    # 后台启动
    nohup $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    
    sleep 2
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
        cat ../logs/backend.log
        exit 1
    fi
}

# 启动前端
start_frontend() {
    echo ""
    echo "启动前端服务..."
    
    cd "$SCRIPT_DIR/frontend"
    
    if ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}! 跳过前端启动 (Node.js 未安装)${NC}"
        return
    fi
    
    # 检查是否已有实例运行
    if pgrep -f "vite" > /dev/null; then
        echo -e "${YELLOW}! 前端服务已在运行${NC}"
        return
    fi
    
    # 后台启动
    nohup npm run dev -- --host 0.0.0.0 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    sleep 3
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}! 前端服务启动中...${NC}"
    fi
}

# 创建必要目录
create_dirs() {
    mkdir -p "$SCRIPT_DIR/logs"
    mkdir -p "$SCRIPT_DIR/data"
}

# 显示访问信息
show_info() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ 服务启动完成！${NC}"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo -e "  ${GREEN}前端:${NC} http://$LOCAL_IP:5173"
    echo -e "  ${GREEN}后端:${NC} http://$LOCAL_IP:8080"
    echo -e "  ${GREEN}API文档:${NC} http://$LOCAL_IP:8080/docs"
    echo ""
    echo "首次使用请访问前端地址进行初始化配置"
    echo ""
    echo "停止服务: ./stop.sh"
    echo "查看日志: tail -f logs/backend.log"
    echo ""
}

# 主函数
main() {
    create_dirs
    check_python
    check_node
    install_backend
    install_frontend
    start_backend
    start_frontend
    show_info
}

main