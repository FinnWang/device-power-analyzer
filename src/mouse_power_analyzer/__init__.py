#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Power Analyzer - 無線滑鼠耗電分析工具

這個套件提供了完整的無線滑鼠耗電分析功能，包括：
- 資料載入和處理
- 統計分析
- 視覺化圖表生成
- GUI介面
- 報告匯出

主要模組：
- analyzer: 核心分析功能
- gui: 圖形化使用者介面
- visualizer: 視覺化工具
- utils: 工具函數
- cli: 命令列介面
"""

__version__ = "1.0.0"
__author__ = "Mouse Power Analysis Team"
__email__ = ""
__description__ = "無線滑鼠耗電分析工具"

# 匯入主要類別
from .analyzer import MousePowerAnalyzer
from .visualizer import PowerVisualizer
from .time_range_analyzer import TimeRangeAnalyzer, TimeRangeInfo
from .utils import load_csv_file, calculate_battery_life

# 定義公開的API
__all__ = [
    "MousePowerAnalyzer",
    "PowerVisualizer",
    "TimeRangeAnalyzer",
    "TimeRangeInfo",
    "load_csv_file",
    "calculate_battery_life",
    "__version__",
]

# 版本資訊
VERSION_INFO = {
    "major": 1,
    "minor": 0,
    "patch": 0,
    "release": "stable"
}

def get_version():
    """取得版本資訊"""
    return __version__

def get_info():
    """取得套件資訊"""
    return {
        "name": "mouse-power-analyzer",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "python_requires": ">=3.7"
    }