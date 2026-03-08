@echo off
echo Stopping services...

REM Kill Python processes for backend
taskkill /f /fi "WINDOWTITLE eq Backend*" >nul 2>&1

REM Kill Node processes for frontend
taskkill /f /fi "WINDOWTITLE eq Frontend*" >nul 2>&1

echo All services stopped.
pause