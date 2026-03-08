@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ==========================================
echo   SpatialUnderstandingDataProcess
echo ==========================================
echo.

REM 获取脚本所在目录
cd /d "%~dp0"
set SCRIPT_DIR=%cd%

REM 创建必要目录
if not exist logs mkdir logs
if not exist data mkdir data

REM 获取本机IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%
if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

REM 检查 Python
echo 检查 Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM 检查 Node.js
echo.
echo 检查 Node.js...
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [警告] Node.js 未安装，前端将无法启动
    echo 下载地址: https://nodejs.org/
) else (
    for /f "tokens=*" %%i in ('node -v') do echo [OK] Node.js %%i
)

REM 后端设置
echo.
echo ==========================================
echo   后端设置
echo ==========================================

cd /d "%SCRIPT_DIR%\backend"

REM 创建虚拟环境
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
if exist requirements.txt (
    echo 安装 Python 依赖...
    pip install -r requirements.txt -q
)

REM 启动后端
echo.
echo 启动后端服务...
set DATABASE_URL=sqlite+aiosqlite:///./data/app.db
set DATA_STORAGE_PATH=.\data

start "Backend" /min cmd /c "venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080"

timeout /t 3 /nobreak >nul

REM 前端设置
echo.
echo ==========================================
echo   前端设置
echo ==========================================

cd /d "%SCRIPT_DIR%\frontend"

if exist node_modules (
    echo [OK] 依赖已安装
) else (
    if exist package.json (
        echo 安装 npm 依赖...
        call npm install --silent
    )
)

REM 启动前端
echo.
echo 启动前端服务...
start "Frontend" /min cmd /c "npm run dev -- --host 0.0.0.0"

timeout /t 5 /nobreak >nul

REM 显示信息
echo.
echo ==========================================
echo   服务启动完成！
echo ==========================================
echo.
echo 访问地址:
echo   前端:   http://%LOCAL_IP%:5173
echo   后端:   http://%LOCAL_IP%:8080
echo   API文档: http://%LOCAL_IP%:8080/docs
echo.
echo 首次使用请访问前端地址进行初始化配置
echo.
echo 停止服务: 运行 stop.bat
echo 查看日志: logs\backend.log
echo.
echo 按任意键退出此窗口（服务将继续运行）
pause >nul