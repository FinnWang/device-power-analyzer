# 🖱️ 無線滑鼠耗電分析工具

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)](https://streamlit.io/)

這是一個專門用於分析無線滑鼠在不同發光模式下耗電情況的Python工具集，提供完整的GUI和Web介面。

## 功能特色

### 🖥️ GUI圖形化介面
- 直觀的檔案管理介面
- 即時的分析結果顯示
- 多種視覺化圖表生成
- 完整的報告匯出功能

### 📊 分析功能
- **單檔分析**：詳細分析單一模式的耗電特性
- **多檔比較**：比較不同發光模式的功耗差異
- **統計計算**：平均功率、電流、電壓等統計數據
- **電池續航估算**：基於實測數據預估電池使用時間

### 📈 視覺化圖表
- 功率時間序列圖
- 電流變化圖
- 功率分布直方圖
- 累積能量消耗圖
- 多模式比較圖
- 電池續航比較圖

## 安裝需求

### Python版本
- Python 3.7 或更高版本

### 必要套件
```bash
pip install -r requirements.txt
```

主要套件包括：
- pandas：資料處理
- numpy：數值計算
- matplotlib：圖表繪製
- seaborn：統計視覺化
- tkinter：GUI介面（通常內建）
- openpyxl：Excel報告匯出

## 🚀 快速開始

### 最簡單的方式
```bash
# 1. 克隆專案
git clone https://github.com/your-username/mouse-power-analyzer.git
cd mouse-power-analyzer

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 快速分析（自動分析database目錄中的所有檔案）
python scripts/quick_start.py

# 4. 啟動Web介面
streamlit run src/mouse_power_analyzer/streamlit_app.py
```

## 使用方法

### 1. 套件安裝（推薦）

```bash
# 安裝套件
pip install -e .

# 使用命令列工具
mouse-analyzer --quick

# 啟動GUI介面
mouse-analyzer-gui
```

### 2. 直接執行腳本

```bash
# GUI介面
python scripts/run_gui.py

# 快速分析
python scripts/quick_start.py
```

#### GUI使用步驟：
1. **檔案管理**分頁：載入CSV資料檔案
2. **單檔分析**分頁：選擇單一檔案進行詳細分析
3. **多檔比較**分頁：選擇多個檔案進行比較分析
4. **報告生成**分頁：匯出完整的分析報告

### 3. 命令列介面

#### 分析單一檔案
```bash
mouse-analyzer database/MD103\ Flash\ 2025-10-02\ 0.csv
```

#### 分析多個檔案
```bash
mouse-analyzer database/*.csv
```

#### 分析整個目錄
```bash
mouse-analyzer -d database -o results
```

#### 快速分析
```bash
mouse-analyzer --quick
```

### 4. 作為Python模組使用

```python
from mouse_power_analyzer import MousePowerAnalyzer, PowerVisualizer

# 建立分析器
analyzer = MousePowerAnalyzer()
visualizer = PowerVisualizer()

# 分析檔案
file_paths = ['file1.csv', 'file2.csv']
data_dict, _ = analyzer.analyze_files(file_paths)

# 生成圖表
chart_file = visualizer.create_comparison_analysis(data_dict, './output')
```

### 5. 使用Makefile（開發者）

```bash
# 安裝開發環境
make install-dev

# 執行測試
make test

# 快速分析
make quick

# 啟動GUI
make run-gui
```

## 資料格式

CSV檔案應包含以下欄位：
- **Time**：時間戳記（秒）
- **Voltage**：電壓（伏特）
- **Current**：電流（安培）
- **Power**：功率（瓦特）

範例：
```csv
Time,Active Instrument A Channel 1 Voltage Avg,Active Instrument A Channel 1 Current Avg,Active Instrument A Channel 1 Power Avg
0,3.900197029,0.01335064,0.052070128
0.1000038,3.900190592,0.00857474,0.03344312
```

## 支援的發光模式

工具會自動從檔名識別以下模式：
- **無燈光**（Nolight）：省電模式
- **呼吸燈**（Breath）：緩慢明暗變化
- **彩色循環**（Colorcycle）：多色循環顯示
- **閃爍**（Flash）：快速閃爍效果

## 輸出結果

### 圖表檔案
- `{模式}_detailed_analysis.png`：單模式詳細分析
- `comprehensive_comparison.png`：多模式比較分析
- `detailed_statistics.png`：統計摘要表

### 報告檔案
- Excel統計報告（.xlsx）
- 文字摘要報告

### 統計數據
- 平均功率、最大功率、最小功率
- 平均電流、電壓
- 功率穩定性指標
- 總能量消耗
- 電池續航估算

## 專案結構

```
mouse-power-analyzer/
├── src/                        # 原始碼
│   └── mouse_power_analyzer/   # 主要套件
│       ├── __init__.py         # 套件初始化
│       ├── analyzer.py         # 核心分析功能
│       ├── visualizer.py       # 視覺化工具
│       ├── gui.py              # GUI介面
│       ├── cli.py              # 命令列介面
│       └── utils.py            # 工具函數
├── tests/                      # 測試檔案
│   ├── __init__.py
│   └── test_analyzer.py
├── scripts/                    # 執行腳本
│   ├── quick_start.py          # 快速啟動
│   ├── run_gui.py              # GUI啟動
│   └── start_analysis.bat      # Windows批次檔
├── examples/                   # 使用範例
│   └── example_usage.py
├── docs/                       # 文檔
│   └── 使用指南.md
├── database/                   # 資料檔案
│   ├── MD103 Breath 2025-10-02 0.csv
│   ├── MD103 Color cycle 2025-10-02 0.csv
│   ├── MD103 Flash 2025-10-02 0.csv
│   └── MD103 No light 2025-10-02 0.csv
├── requirements.txt            # 套件需求
├── pyproject.toml              # 專案配置
├── setup.py                    # 安裝腳本
├── Makefile                    # 建置工具
└── README.md                   # 說明文件
```

## 故障排除

### 常見問題

1. **中文字體顯示問題**
   - Windows：確保系統有Microsoft JhengHei字體
   - macOS：使用PingFang TC字體
   - Linux：安裝Noto Sans CJK TC字體

2. **GUI無法啟動**
   - 確認tkinter已安裝：`python -c "import tkinter"`
   - 確認系統支援GUI顯示

3. **套件安裝問題**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **記憶體不足**
   - 大檔案分析時可能需要較多記憶體
   - 建議分批處理大量檔案

### 效能優化

- 使用SSD儲存可提升檔案讀取速度
- 增加系統記憶體可處理更大的資料集
- 關閉不必要的背景程式

## 開發資訊

### 版本歷史
- v1.0：初始版本，包含基本分析功能
- v1.1：新增GUI介面
- v1.2：整合所有分析工具

### 技術架構
- **資料處理**：pandas + numpy
- **視覺化**：matplotlib + seaborn
- **GUI框架**：tkinter
- **報告匯出**：openpyxl

### 貢獻指南
歡迎提交Issue和Pull Request來改善這個工具。

## 授權條款

本專案採用MIT授權條款。

## 聯絡資訊

如有問題或建議，請透過GitHub Issues聯絡。