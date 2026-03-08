#!/bin/bash

# 停止服务脚本

echo "停止服务..."

# 停止后端
if [ -f logs/backend.pid ]; then
    PID=$(cat logs/backend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✓ 后端服务已停止"
    fi
    rm -f logs/backend.pid
fi

# 停止前端
if [ -f logs/frontend.pid ]; then
    PID=$(cat logs/frontend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✓ 前端服务已停止"
    fi
    rm -f logs/frontend.pid
fi

# 额外清理
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "所有服务已停止"