# Makefile for Mouse Power Analyzer

.PHONY: help install install-dev test lint format clean build upload quick run-gui run-web

help:  ## 顯示幫助訊息
	@echo "可用的命令："
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安裝套件
	pip install -r requirements.txt
	pip install -e .

install-dev:  ## 安裝開發環境
	pip install -r requirements.txt
	pip install -e ".[dev,web]"
	pip install pytest pytest-cov black flake8 mypy

test:  ## 執行測試
	python -m pytest tests/ -v --cov=src/mouse_power_analyzer --cov-report=html --cov-report=term

lint:  ## 程式碼檢查
	flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	mypy src/mouse_power_analyzer --ignore-missing-imports

format:  ## 格式化程式碼
	black src/ tests/ scripts/ --line-length=88
	isort src/ tests/ scripts/ --profile=black

clean:  ## 清理暫存檔案
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/

build:  ## 建置套件
	python -m build

upload:  ## 上傳到PyPI (需要先設定token)
	python -m twine upload dist/*

quick:  ## 快速分析
	python scripts/quick_start.py

run-gui:  ## 啟動GUI介面
	python scripts/run_gui.py

run-web:  ## 啟動Web介面
	streamlit run src/mouse_power_analyzer/streamlit_app.py

demo:  ## 執行示範
	@echo "=== 無線滑鼠耗電分析工具示範 ==="
	@echo "1. 快速分析..."
	python scripts/quick_start.py
	@echo "2. 啟動Web介面..."
	@echo "請在瀏覽器中開啟 http://localhost:8501"
	streamlit run src/mouse_power_analyzer/streamlit_app.py

check:  ## 檢查專案狀態
	@echo "=== 專案檢查 ==="
	@echo "Python版本:"
	@python --version
	@echo "套件狀態:"
	@pip list | grep -E "(pandas|numpy|matplotlib|streamlit)"
	@echo "檔案結構:"
	@find . -name "*.py" | head -10
	@echo "測試檔案:"
	@find tests/ -name "*.py" 2>/dev/null || echo "無測試檔案"