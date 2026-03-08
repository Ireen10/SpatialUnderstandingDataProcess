@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ==========================================
echo   SpatialUnderstandingDataProcess
echo ==========================================
echo.

REM Get script directory
cd /d "%~dp0"
set SCRIPT_DIR=%cd%

REM Create directories
if not exist logs mkdir logs
if not exist data mkdir data

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%
if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

REM Check Python
echo Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM Check Node.js
echo.
echo Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo [WARN] Node.js not found, frontend will not start
    echo Download from https://nodejs.org/
) else (
    for /f "tokens=*" %%i in ('node -v') do echo [OK] Node.js %%i
)

REM Backend setup
echo.
echo ==========================================
echo   Backend Setup
echo ==========================================

cd /d "%SCRIPT_DIR%\backend"

REM Create virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
if exist requirements.txt (
    echo Installing Python dependencies...
    pip install -r requirements.txt -q
)

REM Start backend
echo.
echo Starting backend service...
set DATABASE_URL=sqlite+aiosqlite:///./data/app.db
set DATA_STORAGE_PATH=.\data

start "Backend" /min cmd /c "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080"

timeout /t 3 /nobreak >nul

REM Frontend setup
echo.
echo ==========================================
echo   Frontend Setup
echo ==========================================

cd /d "%SCRIPT_DIR%\frontend"

if exist node_modules (
    echo [OK] Dependencies installed
) else (
    if exist package.json (
        echo Installing npm dependencies...
        call npm install --silent
    )
)

REM Start frontend
echo.
echo Starting frontend service...
start "Frontend" /min cmd /c "npm run dev -- --host 0.0.0.0"

timeout /t 5 /nobreak >nul

REM Show info
echo.
echo ==========================================
echo   Services Started!
echo ==========================================
echo.
echo Access URLs:
echo   Frontend: http://%LOCAL_IP%:5173
echo   Backend:  http://%LOCAL_IP%:8080
echo   API Docs: http://%LOCAL_IP%:8080/docs
echo.
echo First time? Visit the frontend URL to complete setup.
echo.
echo To stop: run stop.bat
echo.
echo Press any key to close this window (services will keep running)
pause >nul