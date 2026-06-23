@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 Super SP v3.0 广告全景分析系统
echo ============================================================
echo.

REM 检查数据目录
if not exist "data" (
    echo ❌ 错误：data 文件夹不存在
    echo 请确保 data 文件夹中有亚马逊广告报告文件
    pause
    exit /b 1
)

REM 检查是否有报告文件
dir /b data\*.xlsx >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：data 文件夹中没有 .xlsx 报告文件
    echo 请将亚马逊广告报告放入 data 文件夹
    pause
    exit /b 1
)

echo 📂 检测到的报告文件：
dir /b data\*.xlsx
echo.

REM 使用 Hermes Python 环境运行分析
echo ▶️  开始分析...
echo.
"C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" generate.py

if errorlevel 1 (
    echo.
    echo ❌ 分析失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ 分析完成！
echo ============================================================
echo.
echo 📂 输出文件：
echo   - output\dashboard.html (可视化面板)
echo   - output\report.xlsx (Excel 报告)
echo   - output\analysis.json (JSON 数据)
echo   - output\negatives.json (否定关键词数据)
echo.

REM 自动打开可视化面板
if exist "output\dashboard.html" (
    echo 🌐 正在打开可视化面板...
    start output\dashboard.html
)

echo.
echo 按任意键退出...
pause >nul
