#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Time Range Analyzer - 時間區間分析模組

提供時間範圍分析和資料過濾功能
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimeRangeInfo:
    """時間範圍資訊"""
    min_time: float          # 最小時間
    max_time: float          # 最大時間
    total_duration: float    # 總持續時間
    data_points: int         # 總資料點數
    time_resolution: float   # 時間解析度


class TimeRangeAnalyzer:
    """時間區間分析器"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化時間區間分析器
        
        Args:
            df: 包含時間資料的 DataFrame，必須有 'Time' 欄位
            
        Raises:
            ValueError: 當 DataFrame 不包含 'Time' 欄位或資料為空時
        """
        if df is None or df.empty:
            raise ValueError("DataFrame 不能為空")
            
        if 'Time' not in df.columns:
            raise ValueError("DataFrame 必須包含 'Time' 欄位")
            
        # 清理和驗證時間資料
        self.df = self._clean_time_data(df.copy())
        
        if self.df.empty:
            raise ValueError("清理後的資料為空")
            
        # 計算時間範圍資訊
        self._time_range_info = self._calculate_time_range_info()
    
    def _clean_time_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理時間資料
        
        Args:
            df: 原始 DataFrame
            
        Returns:
            清理後的 DataFrame
        """
        # 移除 Time 欄位中的 NaN 值
        df = df.dropna(subset=['Time'])
        
        # 確保 Time 欄位是數值型態
        try:
            df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
            df = df.dropna(subset=['Time'])
        except Exception:
            raise ValueError("Time 欄位包含無法轉換為數值的資料")
        
        # 移除負數時間值
        df = df[df['Time'] >= 0]
        
        # 按時間排序
        df = df.sort_values('Time').reset_index(drop=True)
        
        return df
    
    def _calculate_time_range_info(self) -> TimeRangeInfo:
        """
        計算時間範圍資訊
        
        Returns:
            TimeRangeInfo 物件
        """
        time_values = self.df['Time'].values
        
        min_time = float(time_values.min())
        max_time = float(time_values.max())
        total_duration = max_time - min_time
        data_points = len(time_values)
        
        # 計算時間解析度（平均時間間隔）
        if data_points > 1:
            time_diffs = np.diff(time_values)
            time_resolution = float(np.mean(time_diffs[time_diffs > 0]))
        else:
            time_resolution = 0.0
        
        return TimeRangeInfo(
            min_time=min_time,
            max_time=max_time,
            total_duration=total_duration,
            data_points=data_points,
            time_resolution=time_resolution
        )
    
    def get_time_range_info(self) -> Dict:
        """
        取得時間範圍的基本資訊
        
        Returns:
            包含時間範圍資訊的字典
        """
        info = self._time_range_info
        
        return {
            'min_time': info.min_time,
            'max_time': info.max_time,
            'total_duration': info.total_duration,
            'data_points': info.data_points,
            'time_resolution': info.time_resolution,
            'start_time_formatted': f"{info.min_time:.3f}s",
            'end_time_formatted': f"{info.max_time:.3f}s",
            'duration_formatted': f"{info.total_duration:.3f}s",
            'time_resolution_formatted': f"{info.time_resolution:.6f}s"
        }
    
    def validate_time_range(self, start_time: float, end_time: float) -> Tuple[bool, str]:
        """
        驗證時間範圍的有效性
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            (是否有效, 錯誤訊息)
        """
        info = self._time_range_info
        
        # 檢查時間範圍順序
        if start_time >= end_time:
            return False, "開始時間必須小於結束時間"
        
        # 檢查時間範圍是否在資料範圍內
        if start_time < info.min_time:
            return False, f"開始時間 ({start_time:.3f}s) 不能小於資料最小時間 ({info.min_time:.3f}s)"
        
        if end_time > info.max_time:
            return False, f"結束時間 ({end_time:.3f}s) 不能大於資料最大時間 ({info.max_time:.3f}s)"
        
        # 檢查時間範圍是否太小
        min_duration = info.time_resolution * 2  # 至少需要2個資料點的時間間隔
        if (end_time - start_time) < min_duration:
            return False, f"時間範圍太小，最小範圍應為 {min_duration:.6f}s"
        
        return True, ""
    
    def filter_by_time_range(self, start_time: float, end_time: float) -> pd.DataFrame:
        """
        根據時間範圍過濾資料
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            過濾後的 DataFrame
            
        Raises:
            ValueError: 當時間範圍無效時
        """
        # 驗證時間範圍
        is_valid, error_msg = self.validate_time_range(start_time, end_time)
        if not is_valid:
            raise ValueError(f"無效的時間範圍: {error_msg}")
        
        # 過濾資料
        mask = (self.df['Time'] >= start_time) & (self.df['Time'] <= end_time)
        filtered_df = self.df[mask].copy()
        
        # 檢查過濾後是否有資料
        if filtered_df.empty:
            raise ValueError(f"在時間範圍 [{start_time:.3f}s, {end_time:.3f}s] 內沒有找到資料")
        
        # 重置索引
        filtered_df = filtered_df.reset_index(drop=True)
        
        return filtered_df    

    def get_preview_stats(self, start_time: float, end_time: float) -> Dict:
        """
        取得預覽統計資訊
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            包含預覽統計資訊的字典
            
        Raises:
            ValueError: 當時間範圍無效時
        """
        # 驗證時間範圍
        is_valid, error_msg = self.validate_time_range(start_time, end_time)
        if not is_valid:
            raise ValueError(f"無效的時間範圍: {error_msg}")
        
        # 過濾資料
        try:
            filtered_df = self.filter_by_time_range(start_time, end_time)
        except ValueError as e:
            raise ValueError(f"無法取得預覽統計: {str(e)}")
        
        # 計算基本統計資訊
        stats = {
            'time_range': {
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'start_time_formatted': f"{start_time:.3f}s",
                'end_time_formatted': f"{end_time:.3f}s",
                'duration_formatted': f"{end_time - start_time:.3f}s"
            },
            'data_info': {
                'data_points': len(filtered_df),
                'total_data_points': len(self.df),
                'data_percentage': (len(filtered_df) / len(self.df)) * 100
            }
        }
        
        # 如果有功率資料，計算功率統計
        if 'Power' in filtered_df.columns:
            power_values = filtered_df['Power'].dropna()
            if not power_values.empty:
                stats['power_stats'] = {
                    'mean_W': float(power_values.mean()),
                    'mean_mW': float(power_values.mean() * 1000),
                    'max_W': float(power_values.max()),
                    'max_mW': float(power_values.max() * 1000),
                    'min_W': float(power_values.min()),
                    'min_mW': float(power_values.min() * 1000),
                    'std_W': float(power_values.std()),
                    'std_mW': float(power_values.std() * 1000)
                }
        
        # 如果有電壓資料，計算電壓統計
        if 'Voltage' in filtered_df.columns:
            voltage_values = filtered_df['Voltage'].dropna()
            if not voltage_values.empty:
                stats['voltage_stats'] = {
                    'mean_V': float(voltage_values.mean()),
                    'max_V': float(voltage_values.max()),
                    'min_V': float(voltage_values.min()),
                    'std_V': float(voltage_values.std())
                }
        
        # 如果有電流資料，計算電流統計
        if 'Current' in filtered_df.columns:
            current_values = filtered_df['Current'].dropna()
            if not current_values.empty:
                stats['current_stats'] = {
                    'mean_A': float(current_values.mean()),
                    'mean_mA': float(current_values.mean() * 1000),
                    'max_A': float(current_values.max()),
                    'max_mA': float(current_values.max() * 1000),
                    'min_A': float(current_values.min()),
                    'min_mA': float(current_values.min() * 1000),
                    'std_A': float(current_values.std()),
                    'std_mA': float(current_values.std() * 1000)
                }
        
        return stats