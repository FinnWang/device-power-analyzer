#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Result Manager - 分析結果管理系統

提供多個時間區間分析結果的儲存、管理和比較功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import uuid


@dataclass
class TimeRangeAnalysisResult:
    """時間區間分析結果資料結構"""
    id: str                          # 唯一識別碼
    label: str                       # 使用者自定義標籤
    filename: str                    # 原始檔案名稱
    mode_cn: str                     # 模式中文名稱
    start_time: float                # 開始時間
    end_time: float                  # 結束時間
    duration: float                  # 持續時間
    stats: Dict[str, Any]            # 分析統計資料
    battery_life: Dict[str, float]   # 電池續航資訊
    timestamp: datetime              # 分析時間戳
    chart_theme: str                 # 圖表主題
    metadata: Dict[str, Any]         # 額外元資料
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = asdict(self)
        # 處理 datetime 序列化
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeRangeAnalysisResult':
        """從字典建立物件"""
        # 處理 datetime 反序列化
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def get_summary_text(self) -> str:
        """取得摘要文字"""
        return f"{self.label} - {self.mode_cn} ({self.start_time:.3f}s-{self.end_time:.3f}s)"
    
    def get_power_info(self) -> Dict[str, float]:
        """取得功率相關資訊"""
        return {
            'avg_power_mW': self.stats.get('avg_power_mW', 0.0),
            'max_power_mW': self.stats.get('max_power_mW', 0.0),
            'avg_current_mA': self.stats.get('avg_current_mA', 0.0),
            'battery_hours': self.battery_life.get('hours', 0.0)
        }


class AnalysisResultManager:
    """分析結果管理器"""
    
    def __init__(self, session_key: str = "time_range_results"):
        """
        初始化結果管理器
        
        Args:
            session_key: 在 session_state 中儲存結果的鍵值
        """
        self.session_key = session_key
        self._ensure_session_state()
    
    def _ensure_session_state(self) -> None:
        """確保 session_state 中有結果列表"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = []
    
    def add_result(self, 
                   filename: str,
                   mode_cn: str,
                   start_time: float,
                   end_time: float,
                   stats: Dict[str, Any],
                   battery_life: Dict[str, float],
                   chart_theme: str = "plotly_white",
                   label: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加分析結果
        
        Args:
            filename: 檔案名稱
            mode_cn: 模式中文名稱
            start_time: 開始時間
            end_time: 結束時間
            stats: 統計資料
            battery_life: 電池續航資訊
            chart_theme: 圖表主題
            label: 自定義標籤
            metadata: 額外元資料
            
        Returns:
            結果的唯一識別碼
        """
        # 生成唯一識別碼
        result_id = str(uuid.uuid4())
        
        # 生成預設標籤
        if label is None:
            result_count = len(st.session_state[self.session_key]) + 1
            label = f"結果 {result_count}"
        
        # 建立結果物件
        result = TimeRangeAnalysisResult(
            id=result_id,
            label=label,
            filename=filename,
            mode_cn=mode_cn,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            stats=stats,
            battery_life=battery_life,
            timestamp=datetime.now(),
            chart_theme=chart_theme,
            metadata=metadata or {}
        )
        
        # 添加到 session_state
        st.session_state[self.session_key].append(result)
        
        return result_id
    
    def get_all_results(self) -> List[TimeRangeAnalysisResult]:
        """取得所有結果"""
        return st.session_state[self.session_key].copy()
    
    def get_result_by_id(self, result_id: str) -> Optional[TimeRangeAnalysisResult]:
        """根據 ID 取得結果"""
        for result in st.session_state[self.session_key]:
            if result.id == result_id:
                return result
        return None
    
    def get_result_by_index(self, index: int) -> Optional[TimeRangeAnalysisResult]:
        """根據索引取得結果"""
        results = st.session_state[self.session_key]
        if 0 <= index < len(results):
            return results[index]
        return None
    
    def update_result_label(self, result_id: str, new_label: str) -> bool:
        """
        更新結果標籤
        
        Args:
            result_id: 結果 ID
            new_label: 新標籤
            
        Returns:
            是否成功更新
        """
        for result in st.session_state[self.session_key]:
            if result.id == result_id:
                result.label = new_label
                return True
        return False
    
    def delete_result(self, result_id: str) -> bool:
        """
        刪除結果
        
        Args:
            result_id: 結果 ID
            
        Returns:
            是否成功刪除
        """
        results = st.session_state[self.session_key]
        for i, result in enumerate(results):
            if result.id == result_id:
                del results[i]
                return True
        return False
    
    def delete_result_by_index(self, index: int) -> bool:
        """
        根據索引刪除結果
        
        Args:
            index: 結果索引
            
        Returns:
            是否成功刪除
        """
        results = st.session_state[self.session_key]
        if 0 <= index < len(results):
            del results[index]
            return True
        return False
    
    def clear_all_results(self) -> int:
        """
        清除所有結果
        
        Returns:
            清除的結果數量
        """
        count = len(st.session_state[self.session_key])
        st.session_state[self.session_key] = []
        return count
    
    def get_result_count(self) -> int:
        """取得結果數量"""
        return len(st.session_state[self.session_key])
    
    def has_results(self) -> bool:
        """檢查是否有結果"""
        return len(st.session_state[self.session_key]) > 0
    
    def get_results_summary(self) -> Dict[str, Any]:
        """
        取得結果摘要統計
        
        Returns:
            包含摘要統計的字典
        """
        results = st.session_state[self.session_key]
        
        if not results:
            return {
                'count': 0,
                'modes': [],
                'files': [],
                'power_range': {'min': 0, 'max': 0},
                'time_range': {'min': 0, 'max': 0}
            }
        
        # 收集統計資料
        modes = set()
        files = set()
        powers = []
        start_times = []
        end_times = []
        
        for result in results:
            modes.add(result.mode_cn)
            files.add(result.filename)
            power_info = result.get_power_info()
            powers.append(power_info['avg_power_mW'])
            start_times.append(result.start_time)
            end_times.append(result.end_time)
        
        return {
            'count': len(results),
            'modes': list(modes),
            'files': list(files),
            'power_range': {
                'min': min(powers) if powers else 0,
                'max': max(powers) if powers else 0
            },
            'time_range': {
                'min': min(start_times) if start_times else 0,
                'max': max(end_times) if end_times else 0
            }
        }
    
    def export_results_to_dict(self) -> Dict[str, Any]:
        """
        匯出結果為字典格式
        
        Returns:
            包含所有結果的字典
        """
        results = st.session_state[self.session_key]
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'result_count': len(results),
            'results': [result.to_dict() for result in results]
        }
    
    def import_results_from_dict(self, data: Dict[str, Any]) -> int:
        """
        從字典匯入結果
        
        Args:
            data: 包含結果資料的字典
            
        Returns:
            匯入的結果數量
        """
        if 'results' not in data:
            return 0
        
        imported_count = 0
        
        for result_data in data['results']:
            try:
                result = TimeRangeAnalysisResult.from_dict(result_data)
                st.session_state[self.session_key].append(result)
                imported_count += 1
            except Exception as e:
                st.warning(f"匯入結果時發生錯誤: {str(e)}")
        
        return imported_count
    
    def get_comparison_data(self) -> pd.DataFrame:
        """
        取得比較分析用的資料表
        
        Returns:
            包含比較資料的 DataFrame
        """
        results = st.session_state[self.session_key]
        
        if not results:
            return pd.DataFrame()
        
        comparison_data = []
        
        for i, result in enumerate(results):
            power_info = result.get_power_info()
            
            comparison_data.append({
                'ID': result.id,
                '標籤': result.label,
                '模式': result.mode_cn,
                '檔案': result.filename,
                '開始時間 (s)': result.start_time,
                '結束時間 (s)': result.end_time,
                '持續時間 (s)': result.duration,
                '平均功率 (mW)': power_info['avg_power_mW'],
                '最大功率 (mW)': power_info['max_power_mW'],
                '平均電流 (mA)': power_info['avg_current_mA'],
                '預估續航 (小時)': power_info['battery_hours'],
                '分析時間': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return pd.DataFrame(comparison_data)
    
    def find_results_by_mode(self, mode_cn: str) -> List[TimeRangeAnalysisResult]:
        """
        根據模式尋找結果
        
        Args:
            mode_cn: 模式中文名稱
            
        Returns:
            符合條件的結果列表
        """
        results = st.session_state[self.session_key]
        return [result for result in results if result.mode_cn == mode_cn]
    
    def find_results_by_file(self, filename: str) -> List[TimeRangeAnalysisResult]:
        """
        根據檔案名稱尋找結果
        
        Args:
            filename: 檔案名稱
            
        Returns:
            符合條件的結果列表
        """
        results = st.session_state[self.session_key]
        return [result for result in results if result.filename == filename]
    
    def get_power_statistics(self) -> Dict[str, float]:
        """
        取得功率統計資訊
        
        Returns:
            功率統計字典
        """
        results = st.session_state[self.session_key]
        
        if not results:
            return {}
        
        powers = []
        for result in results:
            power_info = result.get_power_info()
            powers.append(power_info['avg_power_mW'])
        
        return {
            'min_power': min(powers),
            'max_power': max(powers),
            'avg_power': np.mean(powers),
            'std_power': np.std(powers),
            'power_range': max(powers) - min(powers)
        }


class ResultLabelManager:
    """結果標籤管理器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化標籤管理器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def generate_auto_label(self, result: TimeRangeAnalysisResult) -> str:
        """
        生成自動標籤
        
        Args:
            result: 分析結果
            
        Returns:
            自動生成的標籤
        """
        # 基於模式和時間範圍生成標籤
        duration_str = f"{result.duration:.1f}s"
        
        if result.duration < 10:
            time_desc = "短時"
        elif result.duration < 60:
            time_desc = "中時"
        else:
            time_desc = "長時"
        
        return f"{result.mode_cn}-{time_desc}({duration_str})"
    
    def suggest_labels(self, result: TimeRangeAnalysisResult) -> List[str]:
        """
        建議標籤選項
        
        Args:
            result: 分析結果
            
        Returns:
            建議的標籤列表
        """
        suggestions = []
        
        # 基於時間範圍的建議
        if result.duration < 5:
            suggestions.append(f"{result.mode_cn}-啟動階段")
        elif result.duration < 30:
            suggestions.append(f"{result.mode_cn}-短期測試")
        elif result.duration < 300:
            suggestions.append(f"{result.mode_cn}-標準測試")
        else:
            suggestions.append(f"{result.mode_cn}-長期測試")
        
        # 基於功率水平的建議
        power_info = result.get_power_info()
        avg_power = power_info['avg_power_mW']
        
        if avg_power < 50:
            suggestions.append(f"{result.mode_cn}-低功耗")
        elif avg_power < 100:
            suggestions.append(f"{result.mode_cn}-中功耗")
        else:
            suggestions.append(f"{result.mode_cn}-高功耗")
        
        # 基於時間位置的建議
        start_ratio = result.start_time / (result.start_time + result.duration) if result.duration > 0 else 0
        
        if start_ratio < 0.1:
            suggestions.append(f"{result.mode_cn}-開始段")
        elif start_ratio > 0.8:
            suggestions.append(f"{result.mode_cn}-結束段")
        else:
            suggestions.append(f"{result.mode_cn}-中間段")
        
        return suggestions
    
    def validate_label(self, label: str) -> Tuple[bool, str]:
        """
        驗證標籤有效性
        
        Args:
            label: 要驗證的標籤
            
        Returns:
            (是否有效, 錯誤訊息)
        """
        if not label or not label.strip():
            return False, "標籤不能為空"
        
        if len(label.strip()) > 50:
            return False, "標籤長度不能超過50個字元"
        
        # 檢查是否有重複標籤
        existing_labels = [result.label for result in self.result_manager.get_all_results()]
        if label.strip() in existing_labels:
            return False, "標籤已存在，請使用不同的標籤"
        
        return True, ""
    
    def get_unique_label(self, base_label: str) -> str:
        """
        取得唯一標籤（如果重複會自動加上數字後綴）
        
        Args:
            base_label: 基礎標籤
            
        Returns:
            唯一的標籤
        """
        existing_labels = [result.label for result in self.result_manager.get_all_results()]
        
        if base_label not in existing_labels:
            return base_label
        
        # 尋找可用的數字後綴
        counter = 1
        while f"{base_label} ({counter})" in existing_labels:
            counter += 1
        
        return f"{base_label} ({counter})"


class ResultStorageManager:
    """結果儲存管理器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化儲存管理器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def save_to_json(self) -> str:
        """
        儲存結果為 JSON 格式
        
        Returns:
            JSON 字串
        """
        data = self.result_manager.export_results_to_dict()
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def load_from_json(self, json_str: str) -> int:
        """
        從 JSON 字串載入結果
        
        Args:
            json_str: JSON 字串
            
        Returns:
            載入的結果數量
        """
        try:
            data = json.loads(json_str)
            return self.result_manager.import_results_from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 格式錯誤: {str(e)}")
    
    def generate_csv_report(self) -> str:
        """
        生成 CSV 格式的報告
        
        Returns:
            CSV 字串
        """
        df = self.result_manager.get_comparison_data()
        
        if df.empty:
            return "沒有可匯出的資料"
        
        # 移除 ID 欄位（內部使用）
        if 'ID' in df.columns:
            df = df.drop('ID', axis=1)
        
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    def generate_markdown_report(self) -> str:
        """
        生成 Markdown 格式的報告
        
        Returns:
            Markdown 字串
        """
        results = self.result_manager.get_all_results()
        summary = self.result_manager.get_results_summary()
        
        if not results:
            return "# 時間區間分析報告\n\n沒有分析結果。"
        
        report = f"""# 時間區間分析報告

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析結果數量**: {summary['count']}  
**涉及模式**: {', '.join(summary['modes'])}  
**涉及檔案**: {', '.join(summary['files'])}

## 分析摘要

"""
        
        # 添加每個結果的詳細資訊
        for i, result in enumerate(results, 1):
            power_info = result.get_power_info()
            
            report += f"""
### {i}. {result.label}

- **模式**: {result.mode_cn}
- **檔案**: {result.filename}
- **時間範圍**: {result.start_time:.3f}s - {result.end_time:.3f}s
- **持續時間**: {result.duration:.3f}s
- **平均功率**: {power_info['avg_power_mW']:.2f} mW
- **最大功率**: {power_info['max_power_mW']:.2f} mW
- **平均電流**: {power_info['avg_current_mA']:.2f} mA
- **預估續航**: {power_info['battery_hours']:.1f} 小時
- **分析時間**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # 添加比較分析
        if len(results) > 1:
            power_stats = self.result_manager.get_power_statistics()
            
            report += f"""
## 比較分析

- **最高平均功率**: {power_stats['max_power']:.2f} mW
- **最低平均功率**: {power_stats['min_power']:.2f} mW
- **功率差異**: {power_stats['power_range']:.2f} mW
- **平均功率**: {power_stats['avg_power']:.2f} mW
- **功率標準差**: {power_stats['std_power']:.2f} mW

## 建議

基於分析結果，建議：

1. **最佳效能模式**: 選擇平均功率最低的時間區間設定
2. **功率管理**: 注意功率變化較大的時間段
3. **使用策略**: 根據不同使用場景選擇合適的模式和時間設定
"""
        
        return report