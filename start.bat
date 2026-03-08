@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ==========================================
echo   SpatialUnderstandingDataProcess
echo ==========================================
echo.

cd /d "%~dp0"
set SCRIPT_DIR=%cd%

if not exist logs mkdir logs
if not exist data mkdir data

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :got_ip
)
:got_ip
set LOCAL_IP=%LOCAL_IP: =%
if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

echo Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

echo.
echo Checking Node.js...
where node >nul 2>&1
if errorlevel 1 (
    echo [WARN] Node.js not found
) else (
    for /f "tokens=*" %%i in ('node -v') do echo [OK] Node.js %%i
)

echo.
echo ==========================================
echo   Starting Backend
echo ==========================================

cd /d "%SCRIPT_DIR%\backend"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt -q
)

echo Starting backend on port 8080...
set DATABASE_URL=sqlite+aiosqlite:///./data/app.db
set DATA_STORAGE_PATH=.\data

start "SpatialDataProcess-Backend" python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo   Starting Frontend
echo ==========================================

cd /d "%SCRIPT_DIR%\frontend"

if not exist node_modules (
    if exist package.json (
        echo Installing npm dependencies...
        call npm install --silent
    )
)

echo Starting frontend on port 5173...
start "SpatialDataProcess-Frontend" npm run dev -- --host 0.0.0.0

timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo   Services Started!
echo ==========================================
echo.
echo   Frontend: http://%LOCAL_IP%:5173
echo   Backend:  http://%LOCAL_IP%:8080
echo   API Docs: http://%LOCAL_IP%:8080/docs
echo.
echo   To stop: run stop.bat
echo.
echo   Close this window? (services will keep running)
pause