#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handler - 錯誤處理和驗證模組

提供全面的錯誤處理、輸入驗證和使用者指引功能
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import traceback
import logging
from datetime import datetime
from pathlib import Path


class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        """初始化錯誤處理器"""
        self.error_log = []
        self.setup_logging()
    
    def setup_logging(self):
        """設定日誌記錄"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """
        記錄錯誤
        
        Args:
            error_type: 錯誤類型
            message: 錯誤訊息
            details: 錯誤詳情
        """
        error_entry = {
            'timestamp': datetime.now(),
            'type': error_type,
            'message': message,
            'details': details or {},
            'traceback': traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        self.logger.error(f"{error_type}: {message}")
    
    def display_error(self, error_type: str, message: str, 
                     suggestions: Optional[List[str]] = None,
                     show_details: bool = False):
        """
        顯示使用者友善的錯誤訊息
        
        Args:
            error_type: 錯誤類型
            message: 錯誤訊息
            suggestions: 解決建議
            show_details: 是否顯示詳細資訊
        """
        # 根據錯誤類型選擇圖示和顏色
        if error_type == "warning":
            st.warning(f"⚠️ {message}")
        elif error_type == "info":
            st.info(f"ℹ️ {message}")
        else:
            st.error(f"❌ {message}")
        
        # 顯示解決建議
        if suggestions:
            with st.expander("💡 解決建議"):
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
        
        # 顯示詳細資訊
        if show_details and self.error_log:
            with st.expander("🔧 技術詳情"):
                latest_error = self.error_log[-1]
                st.write(f"**錯誤時間:** {latest_error['timestamp']}")
                st.write(f"**錯誤類型:** {latest_error['type']}")
                if latest_error['details']:
                    st.write("**詳細資訊:**")
                    st.json(latest_error['details'])
    
    def handle_file_error(self, filename: str, error: Exception):
        """
        處理檔案相關錯誤
        
        Args:
            filename: 檔案名稱
            error: 錯誤物件
        """
        error_msg = str(error)
        suggestions = []
        
        if "UnicodeDecodeError" in error_msg:
            suggestions = [
                "檢查檔案編碼，建議使用 UTF-8 編碼",
                "嘗試用文字編輯器重新保存檔案",
                "確認檔案沒有損壞"
            ]
        elif "ParserError" in error_msg or "CSV" in error_msg:
            suggestions = [
                "檢查CSV檔案格式是否正確",
                "確認檔案有正確的欄位分隔符號（逗號）",
                "檢查是否有缺少的欄位或額外的空行",
                "嘗試用Excel或其他工具檢查檔案內容"
            ]
        elif "PermissionError" in error_msg:
            suggestions = [
                "檢查檔案是否被其他程式開啟",
                "確認有足夠的檔案存取權限",
                "嘗試關閉可能使用該檔案的程式"
            ]
        else:
            suggestions = [
                "檢查檔案是否存在且可讀取",
                "確認檔案格式符合要求",
                "嘗試重新上傳檔案"
            ]
        
        self.log_error("file_error", f"處理檔案 {filename} 時發生錯誤: {error_msg}")
        self.display_error(
            "error",
            f"無法處理檔案 '{filename}': {error_msg}",
            suggestions,
            show_details=True
        )
    
    def handle_data_error(self, operation: str, error: Exception, data_info: Optional[Dict] = None):
        """
        處理資料相關錯誤
        
        Args:
            operation: 操作名稱
            error: 錯誤物件
            data_info: 資料資訊
        """
        error_msg = str(error)
        suggestions = []
        
        if "empty" in error_msg.lower():
            suggestions = [
                "檢查資料是否包含有效的數值",
                "確認時間範圍選擇是否正確",
                "檢查資料過濾條件是否過於嚴格"
            ]
        elif "memory" in error_msg.lower():
            suggestions = [
                "嘗試分析較小的時間範圍",
                "清除瀏覽器快取",
                "重新載入頁面",
                "考慮分批處理大型檔案"
            ]
        elif "calculation" in error_msg.lower() or "math" in error_msg.lower():
            suggestions = [
                "檢查資料中是否有異常值",
                "確認數值範圍是否合理",
                "檢查是否有除零或無效運算"
            ]
        else:
            suggestions = [
                "檢查資料格式是否正確",
                "確認所有必要欄位都存在",
                "嘗試重新載入資料"
            ]
        
        details = {"operation": operation}
        if data_info:
            details.update(data_info)
        
        self.log_error("data_error", f"{operation} 時發生錯誤: {error_msg}", details)
        self.display_error(
            "error",
            f"資料處理錯誤 ({operation}): {error_msg}",
            suggestions,
            show_details=True
        )


class InputValidator:
    """輸入驗證器"""
    
    @staticmethod
    def validate_csv_file(df: pd.DataFrame, filename: str) -> Tuple[bool, List[str]]:
        """
        驗證CSV檔案格式
        
        Args:
            df: DataFrame
            filename: 檔案名稱
            
        Returns:
            (是否有效, 錯誤訊息列表)
        """
        errors = []
        
        # 檢查是否為空
        if df is None or df.empty:
            errors.append("檔案為空或無法讀取")
            return False, errors
        
        # 檢查欄位數量
        if len(df.columns) < 4:
            errors.append(f"欄位數量不足，需要至少4個欄位，目前只有{len(df.columns)}個")
        
        # 檢查必要欄位
        expected_columns = ['Time', 'Voltage', 'Current', 'Power']
        if len(df.columns) >= 4:
            # 假設前4個欄位是我們需要的
            df_temp = df.copy()
            df_temp.columns = expected_columns[:len(df_temp.columns)]
            
            for col in expected_columns:
                if col not in df_temp.columns:
                    continue
                
                # 檢查是否為數值型態
                try:
                    pd.to_numeric(df_temp[col], errors='coerce')
                except:
                    errors.append(f"欄位 '{col}' 包含非數值資料")
                
                # 檢查是否有過多的空值
                null_percentage = df_temp[col].isnull().sum() / len(df_temp) * 100
                if null_percentage > 50:
                    errors.append(f"欄位 '{col}' 有過多空值 ({null_percentage:.1f}%)")
        
        # 檢查資料點數量
        if len(df) < 10:
            errors.append(f"資料點數量過少 ({len(df)} 個)，建議至少有10個資料點")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_time_range(start_time: float, end_time: float, 
                          min_time: float, max_time: float) -> Tuple[bool, str]:
        """
        驗證時間範圍
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            min_time: 最小時間
            max_time: 最大時間
            
        Returns:
            (是否有效, 錯誤訊息)
        """
        if start_time >= end_time:
            return False, "開始時間必須小於結束時間"
        
        if start_time < min_time:
            return False, f"開始時間 ({start_time:.3f}s) 不能小於資料最小時間 ({min_time:.3f}s)"
        
        if end_time > max_time:
            return False, f"結束時間 ({end_time:.3f}s) 不能大於資料最大時間 ({max_time:.3f}s)"
        
        duration = end_time - start_time
        if duration < 0.001:  # 1毫秒
            return False, "時間範圍太小，最小範圍應為0.001秒"
        
        return True, ""
    
    @staticmethod
    def validate_battery_settings(capacity: float, voltage: float) -> Tuple[bool, List[str]]:
        """
        驗證電池設定
        
        Args:
            capacity: 電池容量 (mAh)
            voltage: 電池電壓 (V)
            
        Returns:
            (是否有效, 錯誤訊息列表)
        """
        errors = []
        
        if capacity <= 0:
            errors.append("電池容量必須大於0")
        elif capacity < 100:
            errors.append("電池容量過小，建議至少100mAh")
        elif capacity > 10000:
            errors.append("電池容量過大，請檢查數值是否正確")
        
        if voltage <= 0:
            errors.append("電池電壓必須大於0")
        elif voltage < 1.0:
            errors.append("電池電壓過低，建議至少1.0V")
        elif voltage > 12.0:
            errors.append("電池電壓過高，請檢查數值是否正確")
        
        return len(errors) == 0, errors


class UserGuide:
    """使用者指引"""
    
    @staticmethod
    def show_welcome_guide():
        """顯示歡迎指引"""
        st.info("""
        👋 **歡迎使用無線滑鼠耗電分析工具！**
        
        這是您第一次使用嗎？讓我們快速了解如何開始：
        
        1. **上傳檔案** - 在左側邊欄選擇CSV檔案
        2. **選擇模式** - 選擇分析類型（完整分析或時間區間分析）
        3. **設定參數** - 調整電池容量和電壓
        4. **查看結果** - 獲得詳細的分析報告
        """)
    
    @staticmethod
    def show_file_format_guide():
        """顯示檔案格式指引"""
        with st.expander("📁 CSV檔案格式要求", expanded=False):
            st.markdown("""
            **必要欄位（按順序）：**
            
            1. **Time** - 時間戳記（秒）
            2. **Voltage** - 電壓（伏特）
            3. **Current** - 電流（安培）
            4. **Power** - 功率（瓦特）
            
            **檔案要求：**
            - 檔案格式：CSV（逗號分隔）
            - 編碼：UTF-8（建議）
            - 大小限制：100MB以下
            - 資料點：建議至少10個
            
            **範例格式：**
            ```
            Time,Voltage,Current,Power
            0.000,3.700,0.020,0.074
            0.001,3.699,0.021,0.077
            0.002,3.698,0.019,0.070
            ...
            ```
            """)
    
    @staticmethod
    def show_analysis_mode_guide():
        """顯示分析模式指引"""
        with st.expander("🔧 分析模式說明", expanded=False):
            st.markdown("""
            **完整分析模式：**
            - 分析整個CSV檔案的所有資料
            - 提供完整的統計報告和視覺化圖表
            - 適合全面了解滑鼠耗電特性
            
            **時間區間分析模式：**
            - 選擇特定時間範圍進行分析
            - 即時預覽選擇區間的統計資訊
            - 支援多個時間區間結果比較
            - 適合分析特定時段的耗電行為
            
            **結果比較模式：**
            - 比較多個時間區間分析結果
            - 提供詳細的比較圖表和統計
            - 適合深入比較不同條件下的表現
            
            **結果管理模式：**
            - 管理所有已保存的分析結果
            - 支援結果標籤編輯和刪除
            - 提供多種格式的匯出功能
            """)
    
    @staticmethod
    def show_troubleshooting_guide():
        """顯示故障排除指引"""
        with st.expander("🔧 常見問題解決", expanded=False):
            st.markdown("""
            **檔案上傳問題：**
            - 檢查檔案格式是否為CSV
            - 確認檔案大小不超過100MB
            - 檢查檔案是否被其他程式開啟
            
            **資料格式問題：**
            - 確認CSV檔案有正確的欄位分隔符號
            - 檢查是否有缺少的欄位或額外的空行
            - 確認數值欄位不包含文字
            
            **效能問題：**
            - 清除瀏覽器快取
            - 關閉不需要的瀏覽器分頁
            - 嘗試分析較小的檔案或時間範圍
            
            **分析錯誤：**
            - 檢查選擇的時間範圍是否包含資料
            - 確認電池設定值是否合理
            - 嘗試重新載入頁面
            """)
    
    @staticmethod
    def show_tips_and_tricks():
        """顯示使用技巧"""
        with st.expander("💡 使用技巧", expanded=False):
            st.markdown("""
            **提高分析效率：**
            - 啟用快取功能以加速重複分析
            - 使用時間區間分析專注於感興趣的時段
            - 利用預設時間範圍快速選擇
            
            **獲得更好的結果：**
            - 確保資料品質良好，避免異常值
            - 選擇合適的時間範圍，避免過短或過長
            - 使用多個檔案進行比較分析
            
            **管理分析結果：**
            - 為分析結果添加有意義的標籤
            - 定期匯出重要的分析結果
            - 使用比較功能找出最佳設定
            """)


def setup_error_handling():
    """設定全域錯誤處理"""
    if 'error_handler' not in st.session_state:
        st.session_state.error_handler = ErrorHandler()
    
    if 'input_validator' not in st.session_state:
        st.session_state.input_validator = InputValidator()
    
    return st.session_state.error_handler, st.session_state.input_validator


def safe_execute(func, *args, error_handler: ErrorHandler = None, 
                operation_name: str = "操作", **kwargs):
    """
    安全執行函數，自動處理錯誤
    
    Args:
        func: 要執行的函數
        *args: 函數參數
        error_handler: 錯誤處理器
        operation_name: 操作名稱
        **kwargs: 函數關鍵字參數
        
    Returns:
        函數執行結果或None（如果發生錯誤）
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.handle_data_error(operation_name, e)
        else:
            st.error(f"執行 {operation_name} 時發生錯誤: {str(e)}")
        return None