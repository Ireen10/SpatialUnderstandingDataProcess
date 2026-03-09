@echo off
REM 数据库迁移脚本 - 添加 split 字段

echo 🔧 开始数据库迁移...
echo.

REM 激活虚拟环境
call venv\Scripts\activate

REM 运行迁移脚本
python migrate_add_split_column.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo ✅ 迁移完成！请重启后端: .\start.bat
) else (
    echo ❌ 迁移失败，请检查错误信息
)

pause
