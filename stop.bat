@echo off
echo ==========================================
echo   Stopping Services
echo ==========================================
echo.

echo Stopping backend (port 8080)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080.*LISTENING" 2^>nul') do (
    echo Killing PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

echo Stopping frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    echo Killing PID %%a
    taskkill /f /pid %%a >nul 2>&1
)

REM Also kill by window title
taskkill /f /fi "WINDOWTITLE eq SpatialDataProcess-Backend*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq SpatialDataProcess-Frontend*" >nul 2>&1

echo.
echo All services stopped.
echo.
pause