@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ==========================================
echo   SpatialUnderstandingDataProcess
echo   Production Deployment
echo ==========================================
echo.

REM Get script directory
cd /d "%~dp0"
set SCRIPT_DIR=%cd%

REM Check Docker
echo Checking Docker...
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo [OK] Docker installed

REM Check Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker Compose not available
)

REM Create directories
if not exist logs mkdir logs
if not exist data mkdir data

REM Create .env file
if not exist .env (
    echo.
    echo Creating environment configuration...
    
    REM Generate random secret key
    set SECRET_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%
    
    (
        echo # Production Configuration
        echo SECRET_KEY=!SECRET_KEY!
        echo DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/sudp
        echo REDIS_URL=redis://redis:6379/0
        echo DATA_STORAGE_PATH=/data
        echo.
        echo # API Configuration (optional)
        echo OPENROUTER_API_KEY=
        echo OPENROUTER_MODEL=z-ai/glm-5
        echo.
        echo # Ports
        echo BACKEND_PORT=8080
        echo FRONTEND_PORT=80
    ) > .env
    
    echo [OK] Created .env file
) else (
    echo [OK] .env file exists
)

REM Build frontend
echo.
echo Building frontend...
cd /d "%SCRIPT_DIR%\frontend"

if not exist node_modules (
    if exist package.json (
        echo Installing dependencies...
        call npm install --silent
    )
)

if exist package.json (
    echo Building production version...
    call npm run build
    echo [OK] Frontend built
)

cd /d "%SCRIPT_DIR%"

REM Start services
echo.
echo Starting Docker services...
docker compose up -d --build

REM Wait for services
echo.
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%
if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

REM Show info
echo.
echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo Access URLs:
echo   App:     http://%LOCAL_IP%
echo   API Docs: http://%LOCAL_IP%:8080/docs
echo.
echo Configuration:
echo   Data: .\data
echo   Logs: .\logs
echo.
echo Commands:
echo   Stop:   deploy.bat stop
echo   Logs:   docker compose logs -f
echo   Restart: docker compose restart
echo.
pause