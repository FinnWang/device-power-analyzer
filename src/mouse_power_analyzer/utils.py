#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Power Analyzer - 工具函數模組

提供通用的工具函數和設定
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from typing import Dict, Union


def setup_matplotlib():
    """設定matplotlib中文字體"""
    
    # 嘗試不同的中文字體
    chinese_fonts = [
        'Microsoft JhengHei',  # Windows
        'PingFang TC',         # macOS
        'Noto Sans CJK TC',    # Linux
        'SimHei',              # 備用
        'DejaVu Sans'          # 英文備用
    ]
    
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    for font in chinese_fonts:
        if font in available_fonts:
            plt.rcParams['font.family'] = [font]
            break
    else:
        plt.rcParams['font.family'] = ['DejaVu Sans']
    
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['font.size'] = 10


def detect_mode_from_filename(filename: str) -> str:
    """
    從檔名推測模式
    
    Args:
        filename: 檔案名稱
        
    Returns:
        推測的模式名稱
    """
    filename_lower = filename.lower()
    
    if 'nolight' in filename_lower or 'no light' in filename_lower or '無燈' in filename_lower:
        return 'Nolight'
    elif 'breath' in filename_lower or '呼吸' in filename_lower:
        return 'Breath'
    elif 'colorcycle' in filename_lower or 'color cycle' in filename_lower or 'color' in filename_lower or '彩色' in filename_lower:
        return 'Colorcycle'
    elif 'flash' in filename_lower or '閃爍' in filename_lower:
        return 'Flash'
    else:
        return 'Unknown'


def calculate_battery_life(avg_power_W: float, battery_capacity_mAh: int = 1000, voltage: float = 3.7, time_range_info: Dict = None) -> Dict:
    """
    估算電池續航時間
    
    Args:
        avg_power_W: 平均功率 (瓦特)
        battery_capacity_mAh: 電池容量 (毫安時)
        voltage: 電池電壓 (伏特)
        time_range_info: 時間範圍資訊字典
        
    Returns:
        續航時間估算字典
    """
    battery_energy_J = battery_capacity_mAh * voltage * 3.6
    
    if avg_power_W > 0:
        hours = battery_energy_J / (avg_power_W * 3600)
        days = hours / 24
        
        result = {
            'hours': hours,
            'days': days,
            'battery_capacity_mAh': battery_capacity_mAh,
            'voltage': voltage,
            'avg_power_W': avg_power_W
        }
        
        # 添加時間範圍相關資訊
        if time_range_info is not None:
            result['time_range_analysis'] = {
                'is_partial_analysis': time_range_info.get('is_partial_analysis', False),
                'analysis_duration': time_range_info.get('selected_duration', 0),
                'start_time': time_range_info.get('start_time', 0),
                'end_time': time_range_info.get('end_time', 0)
            }
            
            # 如果是部分分析，添加警告說明
            if time_range_info.get('is_partial_analysis', False):
                result['analysis_note'] = f"基於 {time_range_info.get('selected_duration', 0):.1f} 秒時間區間的分析結果"
        
        return result
    else:
        return {
            'hours': float('inf'), 
            'days': float('inf'),
            'battery_capacity_mAh': battery_capacity_mAh,
            'voltage': voltage,
            'avg_power_W': avg_power_W
        }


def load_csv_file(filepath: Union[str, Path], mode_name: str = None):
    """
    載入CSV檔案的便利函數
    
    Args:
        filepath: CSV檔案路徑
        mode_name: 模式名稱
        
    Returns:
        處理後的DataFrame
    """
    try:
        from .analyzer import MousePowerAnalyzer
    except ImportError:
        from analyzer import MousePowerAnalyzer
    
    analyzer = MousePowerAnalyzer()
    return analyzer.load_csv_file(filepath, mode_name)


def get_default_colors() -> Dict[str, str]:
    """取得預設顏色配置"""
    return {
        'Nolight': '#2E8B57',      # 海綠色
        'Breath': '#4169E1',       # 皇家藍
        'Colorcycle': '#FF6347',   # 番茄紅
        'Flash': '#FFD700',        # 金色
        'Unknown': '#808080'       # 灰色
    }


def get_mode_names() -> Dict[str, str]:
    """取得模式名稱對應"""
    return {
        'Nolight': '無燈光',
        'Breath': '呼吸燈',
        'Colorcycle': '彩色循環',
        'Flash': '閃爍',
        'Unknown': '未知模式'
    }


def validate_csv_format(filepath: Union[str, Path]) -> bool:
    """
    驗證CSV檔案格式
    
    Args:
        filepath: CSV檔案路徑
        
    Returns:
        是否為有效格式
    """
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        
        # 檢查欄位數量
        if len(df.columns) < 4:
            return False
            
        # 檢查是否有數值資料
        if len(df) == 0:
            return False
            
        return True
        
    except Exception:
        return False


def format_power_value(power_W: float, unit: str = 'auto') -> str:
    """
    格式化功率值顯示
    
    Args:
        power_W: 功率值（瓦特）
        unit: 單位 ('W', 'mW', 'auto')
        
    Returns:
        格式化的功率字串
    """
    if unit == 'auto':
        if power_W >= 1:
            return f"{power_W:.3f} W"
        else:
            return f"{power_W * 1000:.2f} mW"
    elif unit == 'W':
        return f"{power_W:.3f} W"
    elif unit == 'mW':
        return f"{power_W * 1000:.2f} mW"
    else:
        return f"{power_W:.6f}"


def format_time_duration(seconds: float) -> str:
    """
    格式化時間長度顯示
    
    Args:
        seconds: 秒數
        
    Returns:
        格式化的時間字串
    """
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} 分鐘"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} 小時"
    else:
        days = seconds / 86400
        return f"{days:.1f} 天"