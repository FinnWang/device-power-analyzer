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
    
    def calculate_statistics(self, df: pd.DataFrame, time_range: Optional[Tuple[float, float]] = None) -> Dict:
        """
        計算統計數據
        
        Args:
            df: 資料DataFrame
            time_range: 時間範圍 (start_time, end_time)，如果為None則分析整個資料集
            
        Returns:
            統計結果字典
        """
        # 如果指定了時間範圍，先過濾資料
        if time_range is not None:
            start_time, end_time = time_range
            df_filtered = df[(df['Time'] >= start_time) & (df['Time'] <= end_time)].copy()
            
            # 檢查過濾後是否還有資料
            if len(df_filtered) == 0:
                raise ValueError(f"指定的時間範圍 [{start_time}, {end_time}] 內沒有資料")
            
            analysis_df = df_filtered
        else:
            analysis_df = df
        
        duration = analysis_df['Time'].max() - analysis_df['Time'].min()
        total_energy = np.trapz(analysis_df['Power'], analysis_df['Time'])
        
        stats = {
            'mode': analysis_df['Mode'].iloc[0],
            'mode_cn': analysis_df['Mode_CN'].iloc[0],
            'duration_s': duration,
            'data_points': len(analysis_df),
            'avg_voltage_V': analysis_df['Voltage'].mean(),
            'avg_current_A': analysis_df['Current'].mean(),
            'avg_current_mA': analysis_df['Current'].mean() * 1000,
            'avg_power_W': analysis_df['Power'].mean(),
            'avg_power_mW': analysis_df['Power'].mean() * 1000,
            'max_power_W': analysis_df['Power'].max(),
            'max_power_mW': analysis_df['Power'].max() * 1000,
            'min_power_W': analysis_df['Power'].min(),
            'min_power_mW': analysis_df['Power'].min() * 1000,
            'std_power_W': analysis_df['Power'].std(),
            'std_power_mW': analysis_df['Power'].std() * 1000,
            'total_energy_J': total_energy,
            'cv_power': analysis_df['Power'].std() / analysis_df['Power'].mean() if analysis_df['Power'].mean() > 0 else 0
        }
        
        # 添加時間範圍資訊
        if time_range is not None:
            stats['time_range'] = {
                'start_time': start_time,
                'end_time': end_time,
                'selected_duration': end_time - start_time,
                'actual_start_time': analysis_df['Time'].min(),
                'actual_end_time': analysis_df['Time'].max(),
                'is_partial_analysis': True
            }
        else:
            stats['time_range'] = {
                'start_time': analysis_df['Time'].min(),
                'end_time': analysis_df['Time'].max(),
                'selected_duration': duration,
                'actual_start_time': analysis_df['Time'].min(),
                'actual_end_time': analysis_df['Time'].max(),
                'is_partial_analysis': False
            }
        
        # 計算電池續航時間並添加到統計結果中
        battery_life = calculate_battery_life(stats['avg_power_W'], time_range_info=stats['time_range'])
        stats['battery_life'] = battery_life
        
        return stats
    
    def analyze_files(self, file_paths: List[Union[str, Path]], output_dir: Union[str, Path] = './analysis_results', time_range: Optional[Tuple[float, float]] = None) -> Tuple[Dict, List[str]]:
        """
        主要分析函數
        
        Args:
            file_paths: CSV檔案路徑列表
            output_dir: 輸出目錄
            time_range: 時間範圍 (start_time, end_time)，如果為None則分析整個資料集
            
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
        if time_range is not None:
            print(f"時間範圍分析：{time_range[0]:.2f}s - {time_range[1]:.2f}s")
        
        for mode, df in data_dict.items():
            stats = self.calculate_statistics(df, time_range)
            battery_life = calculate_battery_life(stats['avg_power_W'], time_range_info=stats['time_range'])
            
            print(f"{stats['mode_cn']}：")
            print(f"  平均功率：{stats['avg_power_mW']:.2f} mW")
            print(f"  測量時間：{stats['duration_s']:.1f} 秒")
            print(f"  資料點數：{stats['data_points']} 筆")
            print(f"  預估續航：{battery_life['hours']:.1f} 小時")
            if time_range is not None:
                print(f"  時間範圍：{stats['time_range']['actual_start_time']:.2f}s - {stats['time_range']['actual_end_time']:.2f}s")
                if 'analysis_note' in battery_life:
                    print(f"  註記：{battery_life['analysis_note']}")
        
        return data_dict, []
    
    def get_comparison_statistics(self, data_dict: Dict[str, pd.DataFrame], time_range: Optional[Tuple[float, float]] = None) -> Dict:
        """
        計算多檔比較統計
        
        Args:
            data_dict: 資料字典
            time_range: 時間範圍 (start_time, end_time)，如果為None則分析整個資料集
            
        Returns:
            比較統計結果
        """
        comparison_stats = {}
        
        # 計算每個檔案的統計數據
        for mode, df in data_dict.items():
            comparison_stats[mode] = self.calculate_statistics(df, time_range)
        
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
    
    def get_enhanced_analysis_result(self, df: pd.DataFrame, time_range: Optional[Tuple[float, float]] = None) -> Dict:
        """
        取得增強的分析結果，包含完整的元資料
        
        Args:
            df: 資料DataFrame
            time_range: 時間範圍 (start_time, end_time)
            
        Returns:
            增強的分析結果字典
        """
        stats = self.calculate_statistics(df, time_range)
        
        # 添加原始資料資訊
        original_time_range = {
            'original_start_time': df['Time'].min(),
            'original_end_time': df['Time'].max(),
            'original_duration': df['Time'].max() - df['Time'].min(),
            'original_data_points': len(df)
        }
        
        # 建立完整的分析結果
        enhanced_result = {
            'statistics': stats,
            'original_data_info': original_time_range,
            'analysis_metadata': {
                'analysis_type': 'time_range' if time_range is not None else 'full_dataset',
                'timestamp': pd.Timestamp.now().isoformat(),
                'mode': stats['mode'],
                'mode_cn': stats['mode_cn']
            }
        }
        
        # 如果是時間範圍分析，添加額外的比較資訊
        if time_range is not None:
            coverage_percent = (stats['time_range']['selected_duration'] / original_time_range['original_duration']) * 100
            enhanced_result['analysis_metadata']['coverage_percent'] = coverage_percent
            enhanced_result['analysis_metadata']['data_reduction_ratio'] = stats['data_points'] / original_time_range['original_data_points']
        
        return enhanced_result