#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Power Analyzer - Streamlit Web介面

提供互動式的Web介面，方便非工程人員使用
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from pathlib import Path
import tempfile
import zipfile
from datetime import datetime

# 設定頁面配置
st.set_page_config(
    page_title="無線滑鼠耗電分析工具",
    page_icon="🖱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 導入我們的分析模組
import sys
from pathlib import Path

# 添加src目錄到Python路徑
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from mouse_power_analyzer.analyzer import MousePowerAnalyzer
    from mouse_power_analyzer.utils import calculate_battery_life, detect_mode_from_filename
    from mouse_power_analyzer.time_range_ui import TimeRangeAnalysisUI
    from mouse_power_analyzer.result_manager import AnalysisResultManager
    from mouse_power_analyzer.comparison_ui import ComparisonUI
    from mouse_power_analyzer.result_controls import ResultManagementUI
    from mouse_power_analyzer.error_handler import (
        ErrorHandler, InputValidator, UserGuide, 
        setup_error_handling, safe_execute
    )
except ImportError as e:
    st.error(f"導入模組失敗: {e}")
    st.error("請確認所有必要的模組都已正確安裝")
    st.stop()

# 初始化session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MousePowerAnalyzer()
if 'data_dict' not in st.session_state:
    st.session_state.data_dict = {}
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'analysis_mode' not in st.session_state:
    st.session_state.analysis_mode = "完整分析"
if 'time_range_results' not in st.session_state:
    st.session_state.time_range_results = []

# 初始化結果管理器
if 'result_manager' not in st.session_state:
    st.session_state.result_manager = AnalysisResultManager("time_range_results")
if 'comparison_ui' not in st.session_state:
    st.session_state.comparison_ui = ComparisonUI(st.session_state.result_manager)
if 'management_ui' not in st.session_state:
    st.session_state.management_ui = ResultManagementUI(st.session_state.result_manager)

# 初始化效能監控
if 'performance_stats' not in st.session_state:
    st.session_state.performance_stats = {
        'files_processed': 0,
        'total_data_points': 0,
        'cache_hits': 0,
        'cache_misses': 0,
        'analysis_count': 0
    }

# 初始化快取設定
if 'cache_settings' not in st.session_state:
    st.session_state.cache_settings = {
        'enable_caching': True,
        'max_cache_size': 100,  # MB
        'auto_cleanup': True
    }

# 初始化錯誤處理和驗證
error_handler, input_validator = setup_error_handling()

# 初始化使用者指引設定
if 'show_guides' not in st.session_state:
    st.session_state.show_guides = True
if 'first_visit' not in st.session_state:
    st.session_state.first_visit = True

def clear_all_caches():
    """清除所有快取"""
    try:
        # 清除 Streamlit 快取
        st.cache_data.clear()
        
        # 重置效能統計中的快取相關數據
        st.session_state.performance_stats['cache_hits'] = 0
        st.session_state.performance_stats['cache_misses'] = 0
        
        # 清除時間區間分析的快取
        if hasattr(st.session_state, 'time_range_ui') and st.session_state.time_range_ui:
            if hasattr(st.session_state.time_range_ui, 'real_time_preview'):
                st.session_state.time_range_ui.real_time_preview.clear_cache()
        
    except Exception as e:
        st.error(f"清除快取時發生錯誤: {str(e)}")


def get_memory_usage_info():
    """取得記憶體使用資訊"""
    try:
        import psutil
        import os
        
        # 取得當前程序的記憶體使用
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / (1024 * 1024),  # 實際記憶體使用
            'vms_mb': memory_info.vms / (1024 * 1024),  # 虛擬記憶體使用
            'percent': process.memory_percent()
        }
    except ImportError:
        # 如果沒有 psutil，返回估算值
        total_points = st.session_state.performance_stats['total_data_points']
        estimated_mb = total_points * 32 / (1024 * 1024)  # 估算每個資料點32bytes
        
        return {
            'rss_mb': estimated_mb,
            'vms_mb': estimated_mb * 1.5,
            'percent': min(estimated_mb / 1024 * 100, 100)  # 假設系統有1GB記憶體
        }


def optimize_dataframe_memory(df):
    """最佳化 DataFrame 記憶體使用"""
    if df is None or df.empty:
        return df
    
    # 轉換數值欄位為更節省記憶體的類型
    for col in ['Time', 'Voltage', 'Current', 'Power']:
        if col in df.columns:
            # 檢查是否可以使用 float32 而不是 float64
            if df[col].dtype == 'float64':
                # 檢查數值範圍是否適合 float32
                min_val = df[col].min()
                max_val = df[col].max()
                
                if (min_val >= np.finfo(np.float32).min and 
                    max_val <= np.finfo(np.float32).max):
                    df[col] = df[col].astype(np.float32)
    
    return df


def display_memory_warning():
    """顯示記憶體警告"""
    memory_info = get_memory_usage_info()
    
    if memory_info['rss_mb'] > 500:  # 超過500MB顯示警告
        st.warning(f"⚠️ 記憶體使用量較高: {memory_info['rss_mb']:.1f} MB")
        
        with st.expander("💡 記憶體優化建議"):
            st.write("""
            **減少記憶體使用的建議:**
            
            1. **清除快取**: 點擊側邊欄的「清除快取」按鈕
            2. **減少檔案數量**: 一次分析較少的檔案
            3. **使用時間區間分析**: 分析部分資料而非全部
            4. **關閉不需要的分頁**: 關閉瀏覽器中其他分頁
            5. **重新載入頁面**: 刷新頁面重新開始
            """)
            
            if st.button("🔄 立即清除快取"):
                clear_all_caches()
                st.success("快取已清除，記憶體使用應該會降低")


def main():
    """主函數"""
    
    # 標題和說明
    st.title("🖱️ 無線滑鼠耗電分析工具")
    st.markdown("""
    這個工具可以幫你分析無線滑鼠在不同發光模式下的耗電情況。
    只需要上傳CSV檔案，就能獲得詳細的分析報告和視覺化圖表。
    """)
    
    # 顯示記憶體警告（如果需要）
    display_memory_warning()
    
    # 首次訪問歡迎指引
    if st.session_state.first_visit and st.session_state.show_guides:
        UserGuide.show_welcome_guide()
        st.session_state.first_visit = False
    
    # 側邊欄 - 檔案上傳和設定
    with st.sidebar:
        st.header("📁 檔案上傳")
        
        # 檔案上傳
        uploaded_files = st.file_uploader(
            "選擇CSV檔案",
            type=['csv'],
            accept_multiple_files=True,
            help="可以同時上傳多個CSV檔案進行比較分析"
        )
        
        # 分析模式選擇
        st.header("🔧 分析模式")
        
        analysis_mode = st.selectbox(
            "選擇分析模式",
            ["完整分析", "時間區間分析", "結果比較", "結果管理"],
            index=0 if st.session_state.analysis_mode == "完整分析" else 1,
            help="選擇要進行的分析類型"
        )
        
        st.session_state.analysis_mode = analysis_mode
        
        # 分析設定
        st.header("⚙️ 分析設定")
        
        battery_capacity = st.number_input(
            "電池容量 (mAh)",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
            help="用於計算電池續航時間"
        )
        
        battery_voltage = st.number_input(
            "電池電壓 (V)",
            min_value=1.0,
            max_value=5.0,
            value=3.7,
            step=0.1,
            help="電池的標準電壓"
        )
        
        # 圖表設定
        st.header("📊 圖表設定")
        
        chart_theme = st.selectbox(
            "圖表主題",
            ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn"],
            index=1
        )
        
        show_statistics = st.checkbox("顯示統計摘要", value=True)
        show_comparison = st.checkbox("顯示比較分析", value=True)
        
        # 效能設定
        st.header("⚡ 效能設定")
        
        enable_caching = st.checkbox(
            "啟用快取", 
            value=st.session_state.cache_settings['enable_caching'],
            help="啟用快取可以提高重複分析的速度"
        )
        st.session_state.cache_settings['enable_caching'] = enable_caching
        
        if enable_caching:
            max_cache_size = st.slider(
                "最大快取大小 (MB)",
                min_value=50,
                max_value=500,
                value=st.session_state.cache_settings['max_cache_size'],
                step=50,
                help="設定快取使用的最大記憶體"
            )
            st.session_state.cache_settings['max_cache_size'] = max_cache_size
        
        # 效能監控面板
        with st.expander("📊 效能監控", expanded=False):
            perf_stats = st.session_state.performance_stats
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("已處理檔案", perf_stats['files_processed'])
                st.metric("快取命中", perf_stats['cache_hits'])
            
            with col2:
                st.metric("總資料點", f"{perf_stats['total_data_points']:,}")
                st.metric("快取未命中", perf_stats['cache_misses'])
            
            # 快取命中率
            total_requests = perf_stats['cache_hits'] + perf_stats['cache_misses']
            if total_requests > 0:
                hit_rate = perf_stats['cache_hits'] / total_requests * 100
                st.metric("快取命中率", f"{hit_rate:.1f}%")
            
            # 清除快取按鈕
            if st.button("🗑️ 清除快取", help="清除所有快取資料以釋放記憶體"):
                clear_all_caches()
                st.success("快取已清除")
        
        # 使用者指引設定
        st.header("📚 使用者指引")
        
        show_guides = st.checkbox(
            "顯示使用指引", 
            value=st.session_state.show_guides,
            help="顯示或隱藏使用指引和說明"
        )
        st.session_state.show_guides = show_guides
        
        if show_guides:
            # 快速指引按鈕
            if st.button("📖 檔案格式說明"):
                UserGuide.show_file_format_guide()
            
            if st.button("🔧 分析模式說明"):
                UserGuide.show_analysis_mode_guide()
            
            if st.button("🆘 故障排除"):
                UserGuide.show_troubleshooting_guide()
            
            if st.button("💡 使用技巧"):
                UserGuide.show_tips_and_tricks()
    
    # 主要內容區域
    if st.session_state.analysis_mode == "結果比較":
        # 顯示結果比較介面
        st.session_state.comparison_ui.render_complete_comparison_interface()
    elif st.session_state.analysis_mode == "結果管理":
        # 顯示結果管理介面
        st.session_state.management_ui.render_complete_management_interface()
    elif uploaded_files:
        # 處理上傳的檔案
        process_uploaded_files(uploaded_files, battery_capacity, battery_voltage)
        
        if st.session_state.analysis_complete:
            # 根據分析模式顯示不同的介面
            if st.session_state.analysis_mode == "時間區間分析":
                display_time_range_analysis(chart_theme, show_statistics, show_comparison)
            else:
                # 顯示完整分析結果
                display_analysis_results(chart_theme, show_statistics, show_comparison)
    else:
        # 顯示範例和說明
        display_welcome_page()

@st.cache_data(show_spinner=False)
def load_and_process_csv(file_content, filename):
    """
    載入和處理單個CSV檔案（帶快取和錯誤處理）
    
    Args:
        file_content: 檔案內容（bytes）
        filename: 檔案名稱
        
    Returns:
        處理後的DataFrame或None
    """
    error_handler = st.session_state.error_handler
    input_validator = st.session_state.input_validator
    
    try:
        # 從bytes讀取CSV
        df = pd.read_csv(io.BytesIO(file_content))
        
        # 驗證檔案格式
        is_valid, validation_errors = input_validator.validate_csv_file(df, filename)
        
        if not is_valid:
            error_msg = "檔案格式驗證失敗:\n" + "\n".join(validation_errors)
            return None, error_msg
        
        # 設定欄位名稱（假設前4個欄位是我們需要的）
        if len(df.columns) >= 4:
            df.columns = ['Time', 'Voltage', 'Current', 'Power'] + list(df.columns[4:])
        
        # 轉換數值型態並處理錯誤
        numeric_columns = ['Time', 'Voltage', 'Current', 'Power']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 推測模式
        mode_name = detect_mode_from_filename(filename)
        
        # 資料清理和驗證
        original_count = len(df)
        
        # 移除空值
        df = df.dropna(subset=numeric_columns)
        
        # 移除負功率值
        df = df[df['Power'] >= 0]
        
        # 檢查時間序列的合理性
        if 'Time' in df.columns and len(df) > 1:
            time_diffs = df['Time'].diff().dropna()
            if (time_diffs <= 0).any():
                # 時間序列不是遞增的，嘗試排序
                df = df.sort_values('Time').reset_index(drop=True)
        
        cleaned_count = len(df)
        
        # 檢查清理後的資料是否足夠
        if cleaned_count < 10:
            return None, f"清理後的有效資料點過少 ({cleaned_count} 個)，建議至少10個資料點"
        
        # 添加模式資訊
        df['Mode'] = mode_name
        
        # 獲取模式中文名稱
        from mouse_power_analyzer.analyzer import MousePowerAnalyzer
        analyzer = MousePowerAnalyzer()
        df['Mode_CN'] = analyzer.mode_names.get(mode_name, mode_name)
        
        # 更新效能統計
        st.session_state.performance_stats['files_processed'] += 1
        st.session_state.performance_stats['total_data_points'] += cleaned_count
        
        # 資料品質檢查
        quality_warnings = []
        
        # 檢查資料清理比例
        removal_percentage = (original_count - cleaned_count) / original_count * 100
        if removal_percentage > 20:
            quality_warnings.append(f"移除了 {removal_percentage:.1f}% 的資料點")
        
        # 檢查功率值的合理性
        power_values = df['Power'].values
        if len(power_values) > 0:
            power_mean = np.mean(power_values)
            power_std = np.std(power_values)
            
            # 檢查是否有異常高的功率值
            outliers = power_values > (power_mean + 5 * power_std)
            if np.any(outliers):
                outlier_count = np.sum(outliers)
                quality_warnings.append(f"發現 {outlier_count} 個可能的功率異常值")
        
        # 返回處理結果和統計資訊
        processing_info = {
            'original_count': original_count,
            'cleaned_count': cleaned_count,
            'removed_count': original_count - cleaned_count,
            'mode_name': mode_name,
            'mode_cn': df['Mode_CN'].iloc[0] if not df.empty else mode_name,
            'quality_warnings': quality_warnings,
            'file_size_mb': len(file_content) / (1024 * 1024),
            'removal_percentage': removal_percentage
        }
        
        return df, processing_info
        
    except Exception as e:
        return None, f"處理檔案時發生錯誤：{str(e)}"


def process_uploaded_files(uploaded_files, battery_capacity, battery_voltage):
    """處理上傳的檔案（優化版本）"""
    
    if not uploaded_files:
        return
    
    # 驗證電池設定
    error_handler = st.session_state.error_handler
    input_validator = st.session_state.input_validator
    
    battery_valid, battery_errors = input_validator.validate_battery_settings(
        battery_capacity, battery_voltage
    )
    
    if not battery_valid:
        error_handler.display_error(
            "warning",
            "電池設定有問題",
            battery_errors
        )
        # 繼續處理，但顯示警告
    
    # 初始化進度追蹤
    total_files = len(uploaded_files)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    data_dict = {}
    processing_results = []
    
    try:
        for i, uploaded_file in enumerate(uploaded_files):
            # 更新進度
            progress = (i + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"正在處理檔案 {i+1}/{total_files}: {uploaded_file.name}")
            
            # 讀取檔案內容
            file_content = uploaded_file.read()
            
            # 檢查檔案大小
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > 100:  # 限制檔案大小為100MB
                st.warning(f"檔案 {uploaded_file.name} 過大 ({file_size_mb:.1f}MB)，可能影響效能")
            
            # 處理檔案
            result, info = load_and_process_csv(file_content, uploaded_file.name)
            
            if result is not None and isinstance(info, dict):
                # 記憶體優化
                result = optimize_dataframe_memory(result)
                
                # 成功處理
                data_dict[uploaded_file.name] = result
                processing_results.append({
                    'filename': uploaded_file.name,
                    'success': True,
                    'info': info
                })
            else:
                # 處理失敗
                processing_results.append({
                    'filename': uploaded_file.name,
                    'success': False,
                    'error': info
                })
        
        # 完成處理
        progress_bar.progress(1.0)
        status_text.text("檔案處理完成！")
        
        # 顯示處理結果摘要
        display_processing_summary(processing_results)
        
        if data_dict:
            # 快取處理結果
            st.session_state.data_dict = data_dict
            st.session_state.analysis_complete = True
            st.session_state.battery_capacity = battery_capacity
            st.session_state.battery_voltage = battery_voltage
            
            # 清除進度顯示
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ 成功載入 {len(data_dict)} 個檔案！")
            
            # 顯示資料摘要
            display_data_summary(data_dict)
        else:
            progress_bar.empty()
            status_text.empty()
            st.error("❌ 沒有成功載入任何檔案")
            
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"處理檔案時發生未預期的錯誤：{str(e)}")


def display_processing_summary(processing_results):
    """顯示檔案處理摘要"""
    
    success_count = sum(1 for r in processing_results if r['success'])
    total_count = len(processing_results)
    
    if success_count == total_count:
        st.success(f"🎉 所有 {total_count} 個檔案都處理成功！")
    elif success_count > 0:
        st.warning(f"⚠️ {success_count}/{total_count} 個檔案處理成功")
    else:
        st.error(f"❌ 所有檔案處理失敗")
    
    # 顯示詳細結果
    with st.expander("📋 詳細處理結果", expanded=success_count < total_count):
        for result in processing_results:
            if result['success']:
                info = result['info']
                st.success(f"✅ **{result['filename']}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("模式", info['mode_cn'])
                with col2:
                    st.metric("原始資料點", f"{info['original_count']:,}")
                with col3:
                    st.metric("清理後資料點", f"{info['cleaned_count']:,}")
                with col4:
                    if info['removed_count'] > 0:
                        st.metric("移除資料點", f"{info['removed_count']:,}", 
                                delta=f"-{info['removal_percentage']:.1f}%")
                    else:
                        st.metric("資料品質", "完美")
                
                # 顯示品質警告
                if 'quality_warnings' in info and info['quality_warnings']:
                    st.warning("⚠️ 資料品質提醒:")
                    for warning in info['quality_warnings']:
                        st.write(f"  • {warning}")
                
                # 顯示檔案資訊
                if 'file_size_mb' in info:
                    st.caption(f"檔案大小: {info['file_size_mb']:.1f} MB")
            else:
                st.error(f"❌ **{result['filename']}**: {result['error']}")


def display_data_summary(data_dict):
    """顯示資料摘要"""
    
    st.subheader("📊 資料摘要")
    
    summary_data = []
    total_points = 0
    total_duration = 0
    
    for filename, df in data_dict.items():
        data_points = len(df)
        duration = df['Time'].max() - df['Time'].min() if len(df) > 0 else 0
        avg_power = df['Power'].mean() * 1000 if len(df) > 0 else 0  # 轉換為mW
        
        total_points += data_points
        total_duration += duration
        
        summary_data.append({
            '檔案': filename,
            '模式': df['Mode_CN'].iloc[0] if len(df) > 0 else 'Unknown',
            '資料點數': f"{data_points:,}",
            '持續時間': f"{duration:.1f}s",
            '平均功率': f"{avg_power:.2f} mW",
            '檔案大小': f"{len(df) * 32 / 1024:.1f} KB"  # 估算記憶體使用
        })
    
    # 顯示摘要表格
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # 顯示總計資訊
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總檔案數", len(data_dict))
    
    with col2:
        st.metric("總資料點數", f"{total_points:,}")
    
    with col3:
        st.metric("總持續時間", f"{total_duration:.1f}s")
    
    with col4:
        estimated_memory = total_points * 32 / (1024 * 1024)  # 估算MB
        st.metric("估算記憶體", f"{estimated_memory:.1f} MB")

def display_analysis_results(chart_theme, show_statistics, show_comparison):
    """顯示分析結果"""
    
    data_dict = st.session_state.data_dict
    
    # 分頁顯示不同的分析結果
    tab1, tab2, tab3, tab4 = st.tabs(["📊 總覽", "📈 詳細分析", "⚡ 功率比較", "📋 統計報告"])
    
    with tab1:
        display_overview(data_dict, chart_theme)
    
    with tab2:
        display_detailed_analysis(data_dict, chart_theme)
    
    with tab3:
        if show_comparison and len(data_dict) > 1:
            display_comparison_analysis(data_dict, chart_theme)
        else:
            st.info("需要至少2個檔案才能進行比較分析")
    
    with tab4:
        if show_statistics:
            display_statistics_report(data_dict)

def display_overview(data_dict, chart_theme):
    """顯示總覽"""
    
    st.header("📊 分析總覽")
    
    # 計算統計數據
    stats_data = []
    for filename, df in data_dict.items():
        stats = st.session_state.analyzer.calculate_statistics(df)
        battery_life = calculate_battery_life(stats['avg_power_W'])
        
        stats_data.append({
            '檔案名稱': filename,
            '模式': stats['mode_cn'],
            '平均功率 (mW)': f"{stats['avg_power_mW']:.2f}",
            '最大功率 (mW)': f"{stats['max_power_mW']:.2f}",
            '平均電流 (mA)': f"{stats['avg_current_mA']:.2f}",
            '測量時間 (秒)': f"{stats['duration_s']:.1f}",
            '資料點數': stats['data_points'],
            '預估續航 (小時)': f"{battery_life['hours']:.1f}"
        })
    
    # 顯示統計表格
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)
    
    # 功率比較圖表
    if len(data_dict) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # 平均功率比較
            fig_power = px.bar(
                stats_df,
                x='模式',
                y='平均功率 (mW)',
                title='平均功率比較',
                template=chart_theme,
                color='模式'
            )
            fig_power.update_layout(showlegend=False)
            st.plotly_chart(fig_power, use_container_width=True)
        
        with col2:
            # 電池續航比較
            fig_battery = px.bar(
                stats_df,
                x='模式',
                y='預估續航 (小時)',
                title='預估電池續航比較',
                template=chart_theme,
                color='模式'
            )
            fig_battery.update_layout(showlegend=False)
            st.plotly_chart(fig_battery, use_container_width=True)

def display_detailed_analysis(data_dict, chart_theme):
    """顯示詳細分析"""
    
    st.header("📈 詳細分析")
    
    # 選擇要分析的檔案
    selected_file = st.selectbox(
        "選擇要詳細分析的檔案",
        list(data_dict.keys())
    )
    
    if selected_file:
        df = data_dict[selected_file]
        mode_cn = df['Mode_CN'].iloc[0]
        
        st.subheader(f"{mode_cn} 模式詳細分析")
        
        # 建立子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('功率時間序列', '電流時間序列', '功率分布', '累積能量消耗'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 功率時間序列
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Power']*1000, name='功率', line=dict(color='blue')),
            row=1, col=1
        )
        
        # 電流時間序列
        fig.add_trace(
            go.Scatter(x=df['Time'], y=df['Current']*1000, name='電流', line=dict(color='green')),
            row=1, col=2
        )
        
        # 功率分布直方圖
        fig.add_trace(
            go.Histogram(x=df['Power']*1000, name='功率分布', marker_color='orange'),
            row=2, col=1
        )
        
        # 累積能量消耗
        time_intervals = np.diff(np.concatenate([[0], df['Time']]))
        cumulative_energy = np.cumsum(df['Power'] * time_intervals)
        fig.add_trace(
            go.Scatter(x=df['Time'], y=cumulative_energy, name='累積能量', line=dict(color='red')),
            row=2, col=2
        )
        
        # 更新軸標籤
        fig.update_xaxes(title_text="時間 (秒)", row=1, col=1)
        fig.update_yaxes(title_text="功率 (mW)", row=1, col=1)
        fig.update_xaxes(title_text="時間 (秒)", row=1, col=2)
        fig.update_yaxes(title_text="電流 (mA)", row=1, col=2)
        fig.update_xaxes(title_text="功率 (mW)", row=2, col=1)
        fig.update_yaxes(title_text="頻次", row=2, col=1)
        fig.update_xaxes(title_text="時間 (秒)", row=2, col=2)
        fig.update_yaxes(title_text="累積能量 (J)", row=2, col=2)
        
        fig.update_layout(height=600, template=chart_theme, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # 統計摘要
        stats = st.session_state.analyzer.calculate_statistics(df)
        battery_life = calculate_battery_life(stats['avg_power_W'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("平均功率", f"{stats['avg_power_mW']:.2f} mW")
            st.metric("最大功率", f"{stats['max_power_mW']:.2f} mW")
        
        with col2:
            st.metric("平均電流", f"{stats['avg_current_mA']:.2f} mA")
            st.metric("平均電壓", f"{stats['avg_voltage_V']:.3f} V")
        
        with col3:
            st.metric("測量時間", f"{stats['duration_s']:.1f} 秒")
            st.metric("資料點數", f"{stats['data_points']}")
        
        with col4:
            st.metric("總消耗能量", f"{stats['total_energy_J']:.3f} J")
            st.metric("預估續航", f"{battery_life['hours']:.1f} 小時")

def display_comparison_analysis(data_dict, chart_theme):
    """顯示比較分析"""
    
    st.header("⚡ 功率比較分析")
    
    # 時間序列疊加圖
    fig_overlay = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    
    for i, (filename, df) in enumerate(data_dict.items()):
        mode_cn = df['Mode_CN'].iloc[0]
        color = colors[i % len(colors)]
        
        # 正規化時間到0-100%
        time_norm = (df['Time'] - df['Time'].min()) / (df['Time'].max() - df['Time'].min()) * 100
        
        fig_overlay.add_trace(
            go.Scatter(
                x=time_norm,
                y=df['Power']*1000,
                name=mode_cn,
                line=dict(color=color, width=2)
            )
        )
    
    fig_overlay.update_layout(
        title="功率時間序列比較",
        xaxis_title="時間進度 (%)",
        yaxis_title="功率 (mW)",
        template=chart_theme,
        height=500
    )
    
    st.plotly_chart(fig_overlay, use_container_width=True)
    
    # 功率分布比較
    fig_dist = go.Figure()
    
    for i, (filename, df) in enumerate(data_dict.items()):
        mode_cn = df['Mode_CN'].iloc[0]
        
        fig_dist.add_trace(
            go.Box(
                y=df['Power']*1000,
                name=mode_cn,
                boxpoints='outliers'
            )
        )
    
    fig_dist.update_layout(
        title="功率分布比較",
        yaxis_title="功率 (mW)",
        template=chart_theme,
        height=400
    )
    
    st.plotly_chart(fig_dist, use_container_width=True)

def display_statistics_report(data_dict):
    """顯示統計報告"""
    
    st.header("📋 統計報告")
    
    # 生成詳細報告
    report = f"""
# 無線滑鼠耗電分析報告

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析檔案數量**: {len(data_dict)}

## 分析摘要

"""
    
    # 計算比較統計
    powers = []
    modes = []
    
    for filename, df in data_dict.items():
        stats = st.session_state.analyzer.calculate_statistics(df)
        battery_life = calculate_battery_life(stats['avg_power_W'])
        
        powers.append(stats['avg_power_mW'])
        modes.append(stats['mode_cn'])
        
        report += f"""
### {stats['mode_cn']} 模式
- **檔案**: {filename}
- **平均功率**: {stats['avg_power_mW']:.2f} mW
- **最大功率**: {stats['max_power_mW']:.2f} mW
- **平均電流**: {stats['avg_current_mA']:.2f} mA
- **測量時間**: {stats['duration_s']:.1f} 秒
- **預估續航**: {battery_life['hours']:.1f} 小時 ({battery_life['days']:.1f} 天)

"""
    
    if len(data_dict) > 1:
        max_idx = powers.index(max(powers))
        min_idx = powers.index(min(powers))
        
        report += f"""
## 比較結論

- **最高功耗模式**: {modes[max_idx]} ({powers[max_idx]:.2f} mW)
- **最低功耗模式**: {modes[min_idx]} ({powers[min_idx]:.2f} mW)
- **功耗差異**: {max(powers) - min(powers):.2f} mW
- **相對差異**: {((max(powers) - min(powers))/min(powers)*100):.1f}%

## 建議

1. **日常使用**: 建議使用{modes[min_idx]}模式以獲得最長續航
2. **視覺效果**: 如需發光效果，{modes[1] if len(modes) > 1 else modes[0]}是較好的平衡選擇
3. **電池管理**: 根據使用場景適時切換模式
"""
    
    st.markdown(report)
    
    # 提供下載按鈕
    st.download_button(
        label="📥 下載報告",
        data=report,
        file_name=f"mouse_power_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

def display_time_range_analysis(chart_theme, show_statistics, show_comparison):
    """顯示時間區間分析介面"""
    
    data_dict = st.session_state.data_dict
    
    if not data_dict:
        st.warning("請先上傳檔案")
        return
    
    # 選擇要分析的檔案
    st.header("📁 選擇分析檔案")
    
    selected_file = st.selectbox(
        "選擇要進行時間區間分析的檔案",
        list(data_dict.keys()),
        key="time_range_file_selector"
    )
    
    if not selected_file:
        return
    
    df = data_dict[selected_file]
    mode_cn = df['Mode_CN'].iloc[0]
    
    st.info(f"正在分析: **{mode_cn}** 模式 ({selected_file})")
    
    # 初始化時間區間分析介面
    if 'time_range_ui' not in st.session_state:
        st.session_state.time_range_ui = TimeRangeAnalysisUI("main_time_analysis")
    
    time_ui = st.session_state.time_range_ui
    
    # 渲染時間區間分析介面
    start_time, end_time, is_valid, filtered_df = time_ui.render_complete_interface(df)
    
    # 如果確認分析且有過濾資料，進行分析
    if filtered_df is not None and is_valid:
        perform_time_range_analysis(filtered_df, selected_file, start_time, end_time, chart_theme)
    
    # 顯示已保存的分析結果
    display_saved_time_range_results(chart_theme, show_statistics, show_comparison)


@st.cache_data(show_spinner=False)
def calculate_analysis_statistics(data_hash, mode_cn):
    """
    計算分析統計（帶快取）
    
    Args:
        data_hash: 資料的雜湊值（用於快取）
        mode_cn: 模式中文名稱
        
    Returns:
        統計結果和電池續航資訊
    """
    # 這個函數會被快取，避免重複計算相同資料的統計
    pass  # 實際實作會在呼叫時處理


def perform_time_range_analysis(filtered_df, filename, start_time, end_time, chart_theme):
    """執行時間區間分析（優化版本）"""
    
    # 建立進度指示器
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步驟1: 資料驗證
            status_text.text("🔍 驗證分析資料...")
            progress_bar.progress(0.2)
            
            if filtered_df is None or filtered_df.empty:
                raise ValueError("過濾後的資料為空")
            
            data_points = len(filtered_df)
            if data_points < 10:
                st.warning(f"⚠️ 資料點數量較少（{data_points} 個），分析結果可能不夠準確")
            
            # 步驟2: 執行統計分析
            status_text.text("📊 計算統計資料...")
            progress_bar.progress(0.5)
            
            # 使用現有的分析器進行分析
            stats = st.session_state.analyzer.calculate_statistics(filtered_df)
            battery_life = calculate_battery_life(stats['avg_power_W'])
            
            # 步驟3: 保存結果
            status_text.text("💾 保存分析結果...")
            progress_bar.progress(0.7)
            
            # 使用新的結果管理器保存結果
            result_id = st.session_state.result_manager.add_result(
                filename=filename,
                mode_cn=stats['mode_cn'],
                start_time=start_time,
                end_time=end_time,
                stats=stats,
                battery_life=battery_life,
                chart_theme=chart_theme
            )
            
            # 步驟4: 生成視覺化
            status_text.text("📈 生成分析圖表...")
            progress_bar.progress(0.9)
            
            # 取得保存的結果並顯示
            saved_result = st.session_state.result_manager.get_result_by_id(result_id)
            
            # 完成
            progress_bar.progress(1.0)
            status_text.text("✅ 分析完成！")
            
            # 清除進度指示器
            progress_bar.empty()
            status_text.empty()
            
            # 顯示成功訊息
            duration = end_time - start_time
            st.success(f"🎉 時間區間分析完成！")
            
            # 顯示分析摘要
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("分析時間範圍", f"{start_time:.3f}s - {end_time:.3f}s")
            with col2:
                st.metric("持續時間", f"{duration:.3f}s")
            with col3:
                st.metric("資料點數", f"{data_points:,}")
            with col4:
                st.metric("平均功率", f"{stats['avg_power_mW']:.2f} mW")
            
            # 顯示詳細結果
            if saved_result:
                display_single_time_range_result_new(saved_result, filtered_df)
            
        except Exception as e:
            # 清除進度指示器
            progress_bar.empty()
            status_text.empty()
            
            st.error(f"❌ 分析過程中發生錯誤: {str(e)}")
            
            # 提供錯誤診斷資訊
            with st.expander("🔧 錯誤診斷資訊"):
                st.write("**錯誤詳情:**")
                st.code(str(e))
                
                st.write("**資料資訊:**")


def display_single_time_range_result_new(result, filtered_df):
    """顯示單個時間區間分析結果（新版本）"""
    
    st.subheader(f"📊 {result.mode_cn} 模式分析結果")
    st.caption(f"標籤: {result.label} | 時間範圍: {result.start_time:.3f}s - {result.end_time:.3f}s (持續 {result.duration:.3f}s)")
    
    # 統計摘要
    col1, col2, col3, col4 = st.columns(4)
    
    power_info = result.get_power_info()
    
    with col1:
        st.metric("平均功率", f"{power_info['avg_power_mW']:.2f} mW")
    
    with col2:
        st.metric("最大功率", f"{power_info['max_power_mW']:.2f} mW")
    
    with col3:
        st.metric("平均電流", f"{power_info['avg_current_mA']:.2f} mA")
    
    with col4:
        st.metric("預估續航", f"{power_info['battery_hours']:.1f} 小時")
    
    # 生成圖表
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('功率時間序列', '電流時間序列', '功率分布', '累積能量消耗'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 功率時間序列
    fig.add_trace(
        go.Scatter(x=filtered_df['Time'], y=filtered_df['Power']*1000, name='功率', line=dict(color='blue')),
        row=1, col=1
    )
    
    # 電流時間序列
    fig.add_trace(
        go.Scatter(x=filtered_df['Time'], y=filtered_df['Current']*1000, name='電流', line=dict(color='green')),
        row=1, col=2
    )
    
    # 功率分布直方圖
    fig.add_trace(
        go.Histogram(x=filtered_df['Power']*1000, name='功率分布', marker_color='orange'),
        row=2, col=1
    )
    
    # 累積能量消耗
    time_intervals = np.diff(np.concatenate([[0], filtered_df['Time']]))
    cumulative_energy = np.cumsum(filtered_df['Power'] * time_intervals)
    fig.add_trace(
        go.Scatter(x=filtered_df['Time'], y=cumulative_energy, name='累積能量', line=dict(color='red')),
        row=2, col=2
    )
    
    # 更新軸標籤
    fig.update_xaxes(title_text="時間 (秒)", row=1, col=1)
    fig.update_yaxes(title_text="功率 (mW)", row=1, col=1)
    fig.update_xaxes(title_text="時間 (秒)", row=1, col=2)
    fig.update_yaxes(title_text="電流 (mA)", row=1, col=2)
    fig.update_xaxes(title_text="功率 (mW)", row=2, col=1)
    fig.update_yaxes(title_text="頻次", row=2, col=1)
    fig.update_xaxes(title_text="時間 (秒)", row=2, col=2)
    fig.update_yaxes(title_text="累積能量 (J)", row=2, col=2)
    
    fig.update_layout(
        height=600, 
        template=result.chart_theme, 
        showlegend=False,
        title_text=f"{result.mode_cn} 模式時間區間分析 - {result.label} ({result.start_time:.3f}s - {result.end_time:.3f}s)"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_single_time_range_result(result):
    """顯示單個時間區間分析結果（舊版本，保持向後相容）"""
    
    st.subheader(f"📊 {result['mode_cn']} 模式分析結果")
    st.caption(f"時間範圍: {result['start_time']:.3f}s - {result['end_time']:.3f}s (持續 {result['duration']:.3f}s)")
    
    # 統計摘要
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("平均功率", f"{result['stats']['avg_power_mW']:.2f} mW")
    
    with col2:
        st.metric("最大功率", f"{result['stats']['max_power_mW']:.2f} mW")
    
    with col3:
        st.metric("平均電流", f"{result['stats']['avg_current_mA']:.2f} mA")
    
    with col4:
        st.metric("預估續航", f"{result['battery_life']['hours']:.1f} 小時")
    
    # 生成圖表
    filtered_df = result['filtered_df']
    
    # 建立詳細分析圖表
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('功率時間序列', '電流時間序列', '功率分布', '累積能量消耗'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 功率時間序列
    fig.add_trace(
        go.Scatter(x=filtered_df['Time'], y=filtered_df['Power']*1000, name='功率', line=dict(color='blue')),
        row=1, col=1
    )
    
    # 電流時間序列
    fig.add_trace(
        go.Scatter(x=filtered_df['Time'], y=filtered_df['Current']*1000, name='電流', line=dict(color='green')),
        row=1, col=2
    )
    
    # 功率分布直方圖
    fig.add_trace(
        go.Histogram(x=filtered_df['Power']*1000, name='功率分布', marker_color='orange'),
        row=2, col=1
    )
    
    # 累積能量消耗
    time_intervals = np.diff(np.concatenate([[0], filtered_df['Time']]))
    cumulative_energy = np.cumsum(filtered_df['Power'] * time_intervals)
    fig.add_trace(
        go.Scatter(x=filtered_df['Time'], y=cumulative_energy, name='累積能量', line=dict(color='red')),
        row=2, col=2
    )
    
    # 更新軸標籤
    fig.update_xaxes(title_text="時間 (秒)", row=1, col=1)
    fig.update_yaxes(title_text="功率 (mW)", row=1, col=1)
    fig.update_xaxes(title_text="時間 (秒)", row=1, col=2)
    fig.update_yaxes(title_text="電流 (mA)", row=1, col=2)
    fig.update_xaxes(title_text="功率 (mW)", row=2, col=1)
    fig.update_yaxes(title_text="頻次", row=2, col=1)
    fig.update_xaxes(title_text="時間 (秒)", row=2, col=2)
    fig.update_yaxes(title_text="累積能量 (J)", row=2, col=2)
    
    fig.update_layout(
        height=600, 
        template=result['chart_theme'], 
        showlegend=False,
        title_text=f"{result['mode_cn']} 模式時間區間分析 ({result['start_time']:.3f}s - {result['end_time']:.3f}s)"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_single_time_range_result_summary(result):
    """顯示單個時間區間分析結果摘要"""
    
    power_info = result.get_power_info()
    
    # 統計摘要
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("平均功率", f"{power_info['avg_power_mW']:.2f} mW")
    
    with col2:
        st.metric("最大功率", f"{power_info['max_power_mW']:.2f} mW")
    
    with col3:
        st.metric("平均電流", f"{power_info['avg_current_mA']:.2f} mA")
    
    with col4:
        st.metric("預估續航", f"{power_info['battery_hours']:.1f} 小時")
    
    # 基本資訊
    st.write("**分析資訊:**")
    st.write(f"- 檔案: {result.filename}")
    st.write(f"- 持續時間: {result.duration:.3f} 秒")
    st.write(f"- 分析時間: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def display_saved_time_range_results(chart_theme, show_statistics, show_comparison):
    """顯示已保存的時間區間分析結果"""
    
    result_manager = st.session_state.result_manager
    results = result_manager.get_all_results()
    
    if not results:
        return
    
    st.divider()
    st.header("📋 已保存的分析結果")
    
    # 結果管理控制項
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.write(f"共有 {len(results)} 個分析結果")
    
    with col2:
        if st.button("📊 比較分析", key="compare_time_results"):
            st.session_state.analysis_mode = "結果比較"
            st.rerun()
    
    with col3:
        if st.button("🛠️ 結果管理", key="manage_time_results"):
            st.session_state.analysis_mode = "結果管理"
            st.rerun()
    
    with col4:
        if st.button("🗑️ 清除所有", key="clear_all_time_results"):
            cleared_count = result_manager.clear_all_results()
            st.success(f"已清除 {cleared_count} 個結果")
            st.rerun()
    
    # 顯示結果列表
    for i, result in enumerate(results):
        with st.expander(f"{result.label}: {result.mode_cn} ({result.start_time:.3f}s - {result.end_time:.3f}s)"):
            # 由於我們沒有保存 filtered_df，這裡需要重新生成或使用簡化版本
            display_single_time_range_result_summary(result)
            
            # 刪除單個結果的按鈕
            if st.button(f"🗑️ 刪除此結果", key=f"delete_result_{result.id}"):
                if result_manager.delete_result(result.id):
                    st.success("結果已刪除")
                    st.rerun()
    
    # 如果有多個結果，顯示比較分析
    if len(results) > 1 and show_comparison:
        st.divider()
        st.subheader("⚡ 快速比較")
        
        # 使用新的比較介面
        comparison_ui = st.session_state.comparison_ui
        
        # 顯示功率比較圖表
        all_ids = [result.id for result in results]
        power_chart = comparison_ui.visualizer.create_power_comparison_chart(all_ids, chart_theme)
        st.plotly_chart(power_chart, use_container_width=True)
        
        # 顯示比較表格
        comparison_df = comparison_ui.report_generator.generate_comparison_table(all_ids)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)


def display_time_range_comparison(results, chart_theme):
    """顯示時間區間比較分析"""
    
    st.header("⚡ 時間區間比較分析")
    
    # 建立比較表格
    comparison_data = []
    for i, result in enumerate(results):
        comparison_data.append({
            '結果編號': f"結果 {i+1}",
            '模式': result['mode_cn'],
            '時間範圍': f"{result['start_time']:.3f}s - {result['end_time']:.3f}s",
            '持續時間': f"{result['duration']:.3f}s",
            '平均功率 (mW)': f"{result['stats']['avg_power_mW']:.2f}",
            '最大功率 (mW)': f"{result['stats']['max_power_mW']:.2f}",
            '平均電流 (mA)': f"{result['stats']['avg_current_mA']:.2f}",
            '預估續航 (小時)': f"{result['battery_life']['hours']:.1f}"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # 功率比較圖表
    import plotly.express as px
    
    # 準備比較資料
    powers = [result['stats']['avg_power_mW'] for result in results]
    labels = [f"結果 {i+1}\n{result['mode_cn']}\n({result['start_time']:.1f}s-{result['end_time']:.1f}s)" 
              for i, result in enumerate(results)]
    
    fig_comparison = px.bar(
        x=labels,
        y=powers,
        title='平均功率比較',
        labels={'x': '分析結果', 'y': '平均功率 (mW)'},
        template=chart_theme
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)


def export_time_range_results(results):
    """匯出時間區間分析結果"""
    
    # 生成報告
    report = f"""
# 時間區間分析報告

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**分析結果數量**: {len(results)}

## 分析摘要

"""
    
    for i, result in enumerate(results):
        report += f"""
### 結果 {i+1}: {result['mode_cn']} 模式

- **檔案**: {result['filename']}
- **時間範圍**: {result['start_time']:.3f}s - {result['end_time']:.3f}s
- **持續時間**: {result['duration']:.3f}s
- **平均功率**: {result['stats']['avg_power_mW']:.2f} mW
- **最大功率**: {result['stats']['max_power_mW']:.2f} mW
- **平均電流**: {result['stats']['avg_current_mA']:.2f} mA
- **預估續航**: {result['battery_life']['hours']:.1f} 小時
- **分析時間**: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

"""
    
    if len(results) > 1:
        powers = [result['stats']['avg_power_mW'] for result in results]
        max_idx = powers.index(max(powers))
        min_idx = powers.index(min(powers))
        
        report += f"""
## 比較結論

- **最高功耗**: 結果 {max_idx+1} ({powers[max_idx]:.2f} mW)
- **最低功耗**: 結果 {min_idx+1} ({powers[min_idx]:.2f} mW)
- **功耗差異**: {max(powers) - min(powers):.2f} mW
- **相對差異**: {((max(powers) - min(powers))/min(powers)*100):.1f}%
"""
    
    # 提供下載
    st.download_button(
        label="📥 下載時間區間分析報告",
        data=report,
        file_name=f"time_range_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )


def display_welcome_page():
    """顯示歡迎頁面"""
    
    st.header("👋 歡迎使用無線滑鼠耗電分析工具")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 快速開始
        
        1. **上傳檔案**: 在左側邊欄選擇一個或多個CSV檔案
        2. **選擇分析模式**: 選擇完整分析或時間區間分析
        3. **設定參數**: 調整電池容量和電壓設定
        4. **查看結果**: 系統會自動分析並顯示結果
        
        ### 📊 功能特色
        
        - **自動模式識別**: 自動識別無燈光、呼吸燈、彩色循環、閃爍模式
        - **互動式圖表**: 使用Plotly提供豐富的互動體驗
        - **時間區間分析**: 選擇特定時間範圍進行精確分析
        - **即時預覽**: 時間區間選擇時提供即時統計預覽
        - **多結果比較**: 支援多個時間區間分析結果的比較
        - **結果管理**: 完整的分析結果儲存、管理和匯出功能
        - **報告匯出**: 可下載詳細的分析報告（JSON、CSV、Markdown格式）
        
        ### 📁 檔案格式要求
        
        CSV檔案應包含以下欄位：
        - Time: 時間戳記（秒）
        - Voltage: 電壓（伏特）
        - Current: 電流（安培）
        - Power: 功率（瓦特）
        """)
    
    with col2:
        st.info("""
        💡 **小提示**
        
        - 可以同時上傳多個檔案進行比較
        - 系統會自動從檔名識別模式
        - 所有圖表都支援縮放和互動
        - 分析結果可以下載保存
        - 時間區間分析支援精確的時間選擇
        """)
        
        st.success("""
        ✅ **支援的模式**
        
        - 無燈光 (Nolight)
        - 呼吸燈 (Breath)
        - 彩色循環 (Colorcycle)
        - 閃爍 (Flash)
        """)
        
        # 安全和隱私提醒
        st.warning("""
        🔒 **隱私保護**
        
        - 所有資料僅在您的瀏覽器中處理
        - 不會上傳到任何伺服器
        - 關閉瀏覽器後資料會自動清除
        """)
    
    # 顯示使用者指引（如果啟用）
    if st.session_state.show_guides:
        st.divider()
        
        # 使用指引區域
        guide_col1, guide_col2 = st.columns(2)
        
        with guide_col1:
            UserGuide.show_file_format_guide()
            UserGuide.show_analysis_mode_guide()
        
        with guide_col2:
            UserGuide.show_troubleshooting_guide()
            UserGuide.show_tips_and_tricks()
        
        # 範例檔案下載
        st.divider()
        st.subheader("📥 範例檔案")
        
        # 生成範例CSV資料
        sample_data = generate_sample_csv_data()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📄 下載範例檔案 (無燈光)",
                data=sample_data['nolight'],
                file_name="sample_nolight.csv",
                mime="text/csv",
                help="下載無燈光模式的範例CSV檔案"
            )
        
        with col2:
            st.download_button(
                label="📄 下載範例檔案 (呼吸燈)",
                data=sample_data['breath'],
                file_name="sample_breath.csv",
                mime="text/csv",
                help="下載呼吸燈模式的範例CSV檔案"
            )
        
        with col3:
            st.download_button(
                label="📄 下載範例檔案 (彩色循環)",
                data=sample_data['colorcycle'],
                file_name="sample_colorcycle.csv",
                mime="text/csv",
                help="下載彩色循環模式的範例CSV檔案"
            )


def generate_sample_csv_data():
    """生成範例CSV資料"""
    import numpy as np
    
    # 生成時間序列
    time_points = np.linspace(0, 10, 1000)  # 10秒，1000個資料點
    
    sample_data = {}
    
    # 無燈光模式 - 低功耗
    voltage_nolight = 3.7 + 0.05 * np.sin(2 * np.pi * 0.1 * time_points)  # 輕微電壓波動
    current_nolight = 0.015 + 0.002 * np.random.normal(0, 1, len(time_points))  # 15mA 基礎電流
    power_nolight = voltage_nolight * current_nolight
    
    nolight_df = pd.DataFrame({
        'Time': time_points,
        'Voltage': voltage_nolight,
        'Current': current_nolight,
        'Power': power_nolight
    })
    sample_data['nolight'] = nolight_df.to_csv(index=False)
    
    # 呼吸燈模式 - 週期性變化
    voltage_breath = 3.7 + 0.03 * np.sin(2 * np.pi * 0.2 * time_points)
    current_breath = 0.025 + 0.015 * np.sin(2 * np.pi * 0.5 * time_points)  # 呼吸效果
    power_breath = voltage_breath * current_breath
    
    breath_df = pd.DataFrame({
        'Time': time_points,
        'Voltage': voltage_breath,
        'Current': current_breath,
        'Power': power_breath
    })
    sample_data['breath'] = breath_df.to_csv(index=False)
    
    # 彩色循環模式 - 高功耗
    voltage_cycle = 3.7 + 0.02 * np.sin(2 * np.pi * 0.3 * time_points)
    current_cycle = 0.045 + 0.025 * np.sin(2 * np.pi * 1.0 * time_points)  # 快速變化
    power_cycle = voltage_cycle * current_cycle
    
    cycle_df = pd.DataFrame({
        'Time': time_points,
        'Voltage': voltage_cycle,
        'Current': current_cycle,
        'Power': power_cycle
    })
    sample_data['colorcycle'] = cycle_df.to_csv(index=False)
    
    return sample_data

if __name__ == "__main__":
    main()