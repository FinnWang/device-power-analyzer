# Mouse Power Analyzer Makefile

.PHONY: help install install-dev test lint format clean build upload docs run-gui run-cli

# 預設目標
help:
	@echo "Mouse Power Analyzer - 無線滑鼠耗電分析工具"
	@echo ""
	@echo "可用的命令:"
	@echo "  install      安裝套件"
	@echo "  install-dev  安裝開發依賴"
	@echo "  test         執行測試"
	@echo "  lint         程式碼檢查"
	@echo "  format       程式碼格式化"
	@echo "  clean        清理建置檔案"
	@echo "  build        建置套件"
	@echo "  upload       上傳到PyPI"
	@echo "  docs         生成文檔"
	@echo "  run-gui      啟動GUI介面"
	@echo "  run-web      啟動Web介面 (推薦)"
	@echo "  run-cli      執行命令列分析"
	@echo "  quick        快速分析database目錄"

# 安裝
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,gui]"

# 測試
test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=src/mouse_power_analyzer --cov-report=html

# 程式碼品質
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

format-check:
	black --check src/ tests/

# 清理
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 建置和發布
build: clean
	python -m build

upload: build
	python -m twine upload dist/*

upload-test: build
	python -m twine upload --repository testpypi dist/*

# 文檔
docs:
	@echo "生成API文檔..."
	# 這裡可以添加文檔生成命令

# 執行
run-gui:
	python scripts/run_gui.py

run-web:
	python scripts/run_streamlit.py

run-cli:
	python -m mouse_power_analyzer.cli --help

quick:
	python scripts/quick_start.py

# 開發工具
dev-setup: install-dev
	@echo "開發環境設定完成"

check-all: format-check lint test
	@echo "所有檢查通過"

# 範例
example:
	python examples/example_usage.py

# 資料庫分析
analyze-database:
	python -m mouse_power_analyzer.cli -d database -o analysis_results

# 單檔分析範例
analyze-single:
	python -m mouse_power_analyzer.cli database/MD103\ Flash\ 2025-10-02\ 0.csv -o single_analysis

# 安裝系統依賴（Ubuntu/Debian）
install-system-deps:
	sudo apt-get update
	sudo apt-get install python3-tk python3-dev

# 安裝系統依賴（macOS）
install-system-deps-mac:
	brew install python-tk

# 檢查系統需求
check-system:
	@echo "檢查Python版本..."
	python --version
	@echo "檢查套件..."
	python -c "import pandas, numpy, matplotlib; print('核心套件正常')"
	@echo "檢查GUI支援..."
	python -c "import tkinter; print('GUI支援正常')" || echo "警告：GUI不支援"