#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Power Analyzer - 核心分析模組

提供無線滑鼠耗電分析的核心功能
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

try:
    from .utils import setup_matplotlib, detect_mode_from_filename, calculate_battery_life
except ImportError:
    from utils import setup_matplotlib, detect_mode_from_filename, calculate_battery_life

warnings.filterwarnings('ignore')


class MousePowerAnalyzer:
    """無線滑鼠耗電分析器"""
    
    def __init__(self):
        """初始化分析器"""
        setup_matplotlib()
        
        self.colors = {
            'Nolight': '#2E8B57',      # 海綠色
            'Breath': '#4169E1',       # 皇家藍
            'Colorcycle': '#FF6347',   # 番茄紅
            'Flash': '#FFD700',        # 金色
            'Unknown': '#808080'       # 灰色
        }
        
        self.mode_names = {
            'Nolight': '無燈光',
            'Breath': '呼吸燈',
            'Colorcycle': '彩色循環',
            'Flash': '閃爍',
            'Unknown': '未知模式'
        }
    
    def load_csv_file(self, filepath: Union[str, Path], mode_name: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        載入CSV檔案
        
        Args:
            filepath: CSV檔案路徑
            mode_name: 模式名稱（可選，會自動從檔名推測）
            
        Returns:
            處理後的DataFrame，如果載入失敗則返回None
        """
        try:
            df = pd.read_csv(filepath)
            
            # 檢查欄位數量
            if len(df.columns) >= 4:
                df.columns = ['Time', 'Voltage', 'Current', 'Power']
            else:
                raise ValueError(f"CSV檔案欄位數量不足，需要至少4欄")
            
            # 推測模式名稱
            if mode_name is None:
                mode_name = detect_mode_from_filename(Path(filepath).stem)
            
            df['Mode'] = mode_name
            df['Mode_CN'] = self.mode_names.get(mode_name, mode_name)
            
            # 資料清理
            df = df.dropna()
            df = df[df['Power'] >= 0]
            df = df.sort_values('Time').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"載入檔案 {filepath} 時發生錯誤：{e}")
            return None
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """
        計算統計數據
        
        Args:
            df: 資料DataFrame
            
        Returns:
            統計結果字典
        """
        duration = df['Time'].max() - df['Time'].min()
        total_energy = np.trapz(df['Power'], df['Time'])
        
        stats = {
            'mode': df['Mode'].iloc[0],
            'mode_cn': df['Mode_CN'].iloc[0],
            'duration_s': duration,
            'data_points': len(df),
            'avg_voltage_V': df['Voltage'].mean(),
            'avg_current_A': df['Current'].mean(),
            'avg_current_mA': df['Current'].mean() * 1000,
            'avg_power_W': df['Power'].mean(),
            'avg_power_mW': df['Power'].mean() * 1000,
            'max_power_W': df['Power'].max(),
            'max_power_mW': df['Power'].max() * 1000,
            'min_power_W': df['Power'].min(),
            'min_power_mW': df['Power'].min() * 1000,
            'std_power_W': df['Power'].std(),
            'std_power_mW': df['Power'].std() * 1000,
            'total_energy_J': total_energy,
            'cv_power': df['Power'].std() / df['Power'].mean() if df['Power'].mean() > 0 else 0
        }
        
        return stats
    
    def analyze_files(self, file_paths: List[Union[str, Path]], output_dir: Union[str, Path] = './analysis_results') -> Tuple[Dict, List[str]]:
        """
        主要分析函數
        
        Args:
            file_paths: CSV檔案路徑列表
            output_dir: 輸出目錄
            
        Returns:
            (資料字典, 生成的檔案列表)
        """
        print("=== 無線滑鼠耗電分析工具 ===")
        
        # 建立輸出目錄
        Path(output_dir).mkdir(exist_ok=True)
        
        # 載入資料
        data_dict = {}
        for filepath in file_paths:
            print(f"載入檔案：{filepath}")
            df = self.load_csv_file(filepath)
            if df is not None:
                mode = df['Mode'].iloc[0]
                data_dict[mode] = df
                print(f"  成功載入 {df['Mode_CN'].iloc[0]} 模式，{len(df)} 筆資料")
        
        if not data_dict:
            print("錯誤：沒有成功載入任何檔案")
            return {}, []
        
        # 輸出統計摘要
        print("\n=== 分析結果摘要 ===")
        for mode, df in data_dict.items():
            stats = self.calculate_statistics(df)
            battery_life = calculate_battery_life(stats['avg_power_W'])
            
            print(f"{stats['mode_cn']}：")
            print(f"  平均功率：{stats['avg_power_mW']:.2f} mW")
            print(f"  測量時間：{stats['duration_s']:.1f} 秒")
            print(f"  資料點數：{stats['data_points']} 筆")
            print(f"  預估續航：{battery_life['hours']:.1f} 小時")
        
        return data_dict, []
    
    def get_comparison_statistics(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        計算多檔比較統計
        
        Args:
            data_dict: 資料字典
            
        Returns:
            比較統計結果
        """
        comparison_stats = {}
        
        # 計算每個檔案的統計數據
        for mode, df in data_dict.items():
            comparison_stats[mode] = self.calculate_statistics(df)
        
        # 計算相對比較
        if len(data_dict) > 1:
            # 找出基準功率（通常是無燈光模式或最低功率）
            baseline_power = min(stats['avg_power_W'] for stats in comparison_stats.values())
            
            for mode, stats in comparison_stats.items():
                if baseline_power > 0:
                    stats['power_increase_percent'] = ((stats['avg_power_W'] - baseline_power) / baseline_power * 100)
                else:
                    stats['power_increase_percent'] = 0
        
        return comparison_stats