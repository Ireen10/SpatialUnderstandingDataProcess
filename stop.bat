@echo off
chcp 65001 >nul
echo 停止服务...

REM 停止后端
taskkill /f /im "python.exe" /fi "WINDOWTITLE eq Backend*" >nul 2>&1

REM 停止前端
taskkill /f /im "node.exe" /fi "WINDOWTITLE eq Frontend*" >nul 2>&1

echo 所有服务已停止
pause