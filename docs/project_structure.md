# 專案結構說明

## 目錄結構

```
mouse-power-analyzer/
├── src/                                    # 原始碼目錄
│   └── mouse_power_analyzer/               # 主要套件
│       ├── __init__.py                     # 套件初始化，定義公開API
│       ├── analyzer.py                     # 核心分析功能
│       ├── visualizer.py                   # 視覺化圖表生成
│       ├── gui.py                          # GUI圖形化介面
│       ├── cli.py                          # 命令列介面
│       └── utils.py                        # 工具函數和設定
│
├── tests/                                  # 測試檔案
│   ├── __init__.py                         # 測試套件初始化
│   └── test_analyzer.py                    # 分析器測試
│
├── scripts/                                # 執行腳本
│   ├── quick_start.py                      # 快速啟動分析
│   ├── run_gui.py                          # GUI啟動腳本
│   └── start_analysis.bat                  # Windows批次檔
│
├── examples/                               # 使用範例
│   └── example_usage.py                    # 使用範例程式碼
│
├── docs/                                   # 文檔目錄
│   ├── 使用指南.md                         # 中文使用指南
│   └── project_structure.md                # 專案結構說明
│
├── database/                               # 資料檔案目錄
│   ├── MD103 Breath 2025-10-02 0.csv      # 呼吸燈模式資料
│   ├── MD103 Color cycle 2025-10-02 0.csv # 彩色循環模式資料
│   ├── MD103 Flash 2025-10-02 0.csv       # 閃爍模式資料
│   └── MD103 No light 2025-10-02 0.csv    # 無燈光模式資料
│
├── analysis_results/                       # 分析結果輸出目錄
│   ├── comprehensive_comparison.png        # 綜合比較圖表
│   ├── Breath_detailed_analysis.png        # 呼吸燈詳細分析
│   ├── Colorcycle_detailed_analysis.png    # 彩色循環詳細分析
│   ├── Flash_detailed_analysis.png         # 閃爍詳細分析
│   └── Nolight_detailed_analysis.png       # 無燈光詳細分析
│
├── .gitignore                              # Git忽略檔案配置
├── CHANGELOG.md                            # 更新日誌
├── LICENSE                                 # MIT授權條款
├── Makefile                                # 建置和開發工具
├── MANIFEST.in                             # 套件包含檔案配置
├── pyproject.toml                          # 現代Python專案配置
├── README.md                               # 專案說明文件
├── requirements.txt                        # Python依賴套件
└── setup.py                                # 傳統安裝腳本
```

## 模組說明

### 核心模組

#### `analyzer.py`
- **MousePowerAnalyzer**: 主要分析類別
- 功能：CSV檔案載入、資料處理、統計計算
- 方法：
  - `load_csv_file()`: 載入和清理CSV資料
  - `calculate_statistics()`: 計算統計數據
  - `analyze_files()`: 批次分析多個檔案

#### `visualizer.py`
- **PowerVisualizer**: 視覺化工具類別
- 功能：生成各種分析圖表
- 方法：
  - `create_single_analysis()`: 單檔詳細分析圖表
  - `create_comparison_analysis()`: 多檔比較圖表

#### `utils.py`
- 工具函數集合
- 功能：字體設定、模式識別、電池計算
- 主要函數：
  - `setup_matplotlib()`: 設定中文字體
  - `detect_mode_from_filename()`: 自動識別模式
  - `calculate_battery_life()`: 電池續航估算

### 介面模組

#### `gui.py`
- **MousePowerGUI**: GUI主類別
- 功能：圖形化使用者介面
- 特色：檔案管理、即時分析、報告匯出

#### `cli.py`
- 命令列介面實作
- 功能：批次處理、參數配置
- 支援：單檔/多檔分析、自訂輸出

## 配置檔案

### `pyproject.toml`
現代Python專案配置檔案，包含：
- 專案元資料
- 依賴管理
- 建置設定
- 開發工具配置

### `setup.py`
傳統安裝腳本，提供向後相容性

### `requirements.txt`
Python套件依賴清單

### `Makefile`
開發和建置工具，提供常用命令：
- `make install`: 安裝套件
- `make test`: 執行測試
- `make quick`: 快速分析
- `make run-gui`: 啟動GUI

## 資料流程

1. **資料輸入**: CSV檔案 → `analyzer.load_csv_file()`
2. **資料處理**: 清理和標準化 → `analyzer.calculate_statistics()`
3. **視覺化**: 統計數據 → `visualizer.create_*_analysis()`
4. **輸出**: PNG圖表 + 統計報告

## 擴展性設計

### 新增分析功能
1. 在 `analyzer.py` 中添加新的分析方法
2. 在 `visualizer.py` 中添加對應的視覺化
3. 更新 `cli.py` 和 `gui.py` 的介面

### 新增資料格式支援
1. 在 `utils.py` 中添加新的載入函數
2. 更新 `analyzer.py` 的資料處理邏輯

### 新增輸出格式
1. 在 `visualizer.py` 中添加新的匯出方法
2. 更新GUI和CLI的選項

## 測試策略

- **單元測試**: `tests/test_analyzer.py`
- **整合測試**: 透過 `scripts/quick_start.py`
- **GUI測試**: 手動測試GUI功能
- **覆蓋率**: 使用 `make test-cov` 檢查

## 部署方式

### 開發安裝
```bash
pip install -e .
```

### 生產安裝
```bash
pip install mouse-power-analyzer
```

### 打包發布
```bash
make build
make upload
```

這個結構遵循Python社群的最佳實踐，提供了良好的可維護性和擴展性。