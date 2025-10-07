@echo off
chcp 65001 >nul
echo ========================================
echo 無線滑鼠耗電分析工具
echo ========================================
echo.

echo 檢查Python環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤：找不到Python，請先安裝Python 3.7或更高版本
    pause
    exit /b 1
)

echo Python環境正常
echo.

echo 選擇執行模式：
echo 1. 快速分析（自動分析database目錄）
echo 2. 啟動GUI介面
echo 3. 安裝必要套件
echo 4. 退出
echo.

set /p choice=請輸入選項 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 執行快速分析...
    python quick_start.py
) else if "%choice%"=="2" (
    echo.
    echo 啟動GUI介面...
    python run_gui.py
) else if "%choice%"=="3" (
    echo.
    echo 安裝必要套件...
    pip install -r requirements.txt
    echo 套件安裝完成
) else if "%choice%"=="4" (
    echo 再見！
    exit /b 0
) else (
    echo 無效的選項
)

echo.
pause