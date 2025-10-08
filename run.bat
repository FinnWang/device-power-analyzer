@echo off
REM Windows批次檔 - 無線滑鼠耗電分析工具

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="test" goto test
if "%1"=="quick" goto quick
if "%1"=="gui" goto gui
if "%1"=="web" goto web
if "%1"=="clean" goto clean
if "%1"=="check" goto check
goto help

:help
echo.
echo 無線滑鼠耗電分析工具 - Windows 執行腳本
echo.
echo 可用命令:
echo   run.bat install    - 安裝套件
echo   run.bat test       - 執行測試
echo   run.bat quick      - 快速分析
echo   run.bat gui        - 啟動GUI介面
echo   run.bat web        - 啟動Web介面
echo   run.bat clean      - 清理暫存檔案
echo   run.bat check      - 檢查專案狀態
echo   run.bat help       - 顯示此幫助訊息
echo.
goto end

:install
echo 安裝套件...
pip install -r requirements.txt
pip install -e .
echo 安裝完成!
goto end

:test
echo 執行測試...
python -m pytest tests/ -v
goto end

:quick
echo 執行快速分析...
python scripts/quick_start.py
goto end

:gui
echo 啟動GUI介面...
python scripts/run_gui.py
goto end

:web
echo 啟動Web介面...
echo 請在瀏覽器中開啟 http://localhost:8501
streamlit run src/mouse_power_analyzer/streamlit_app.py
goto end

:clean
echo 清理暫存檔案...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f"
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.egg-info rd /s /q *.egg-info
echo 清理完成!
goto end

:check
echo === 專案檢查 ===
echo Python版本:
python --version
echo.
echo 套件狀態:
pip list | findstr "pandas numpy matplotlib streamlit"
echo.
echo 主要檔案:
if exist "src\mouse_power_analyzer\__init__.py" echo ✓ 主程式存在
if exist "database\" echo ✓ 資料目錄存在
if exist "scripts\quick_start.py" echo ✓ 快速啟動腳本存在
if exist "src\mouse_power_analyzer\streamlit_app.py" echo ✓ Web介面存在
echo.
goto end

:end