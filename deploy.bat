@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   SpatialUnderstandingDataProcess
echo   生产环境部署
echo ==========================================
echo.

REM 获取脚本所在目录
cd /d "%~dp0"
set SCRIPT_DIR=%cd%

REM 检查 Docker
echo 检查 Docker...
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] Docker 未安装
    echo 请安装 Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker 已安装

REM 检查 Docker Compose
docker compose version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [警告] Docker Compose 不可用，请确保 Docker Desktop 版本支持
)

REM 创建必要目录
if not exist logs mkdir logs
if not exist data mkdir data

REM 创建环境文件
if not exist .env (
    echo.
    echo 创建环境配置...
    
    REM 生成随机密钥（简化版）
    set SECRET_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%
    
    (
        echo # 生产环境配置
        echo SECRET_KEY=!SECRET_KEY!
        echo DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/sudp
        echo REDIS_URL=redis://redis:6379/0
        echo DATA_STORAGE_PATH=/data
        echo.
        echo # API 配置（可选）
        echo OPENROUTER_API_KEY=
        echo OPENROUTER_MODEL=z-ai/glm-5
        echo.
        echo # 服务端口
        echo BACKEND_PORT=8080
        echo FRONTEND_PORT=80
    ) > .env
    
    echo [OK] 已创建 .env 文件
) else (
    echo [OK] .env 文件已存在
)

REM 构建前端
echo.
echo 构建前端...
cd /d "%SCRIPT_DIR%\frontend"

if exist node_modules (
    echo [OK] 依赖已安装
) else (
    if exist package.json (
        echo 安装依赖...
        call npm install --silent
    )
)

if exist package.json (
    echo 构建生产版本...
    call npm run build
    echo [OK] 前端构建完成
)

cd /d "%SCRIPT_DIR%"

REM 启动服务
echo.
echo 启动 Docker 服务...
docker compose up -d --build

REM 等待服务就绪
echo.
echo 等待服务启动...
timeout /t 10 /nobreak >nul

REM 获取本机IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%
if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

REM 显示信息
echo.
echo ==========================================
echo   部署完成！
echo ==========================================
echo.
echo 访问地址:
echo   应用:    http://%LOCAL_IP%
echo   API文档: http://%LOCAL_IP%:8080/docs
echo.
echo 默认配置:
echo   数据存储: .\data
echo   日志目录: .\logs
echo.
echo 管理命令:
echo   停止服务: deploy.bat stop
echo   查看日志: docker compose logs -f
echo   重启服务: docker compose restart
echo.
pause