#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Time Range UI Components - 時間區間選擇介面元件

提供 Streamlit 時間區間選擇的使用者介面元件
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Any
from .time_range_analyzer import TimeRangeAnalyzer


class TimeRangeSelector:
    """時間區間選擇器"""
    
    def __init__(self, key_prefix: str = "time_range"):
        """
        初始化時間區間選擇器
        
        Args:
            key_prefix: Streamlit 元件的 key 前綴，用於避免衝突
        """
        self.key_prefix = key_prefix
        self.analyzer = None
        self.time_info = None
    
    def setup_analyzer(self, df: pd.DataFrame) -> bool:
        """
        設定時間分析器
        
        Args:
            df: 包含時間資料的 DataFrame
            
        Returns:
            是否成功設定
        """
        try:
            self.analyzer = TimeRangeAnalyzer(df)
            self.time_info = self.analyzer.get_time_range_info()
            return True
        except Exception as e:
            st.error(f"設定時間分析器失敗: {str(e)}")
            return False
    
    def format_time_display(self, time_value: float) -> str:
        """
        格式化時間顯示
        
        Args:
            time_value: 時間值（秒）
            
        Returns:
            格式化的時間字串
        """
        if time_value < 60:
            return f"{time_value:.3f}s"
        elif time_value < 3600:
            minutes = int(time_value // 60)
            seconds = time_value % 60
            return f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(time_value // 3600)
            minutes = int((time_value % 3600) // 60)
            seconds = time_value % 60
            return f"{hours}h {minutes}m {seconds:.1f}s"
    
    def render_time_info_panel(self) -> None:
        """渲染時間資訊面板"""
        if not self.time_info:
            st.warning("請先載入資料")
            return
        
        st.subheader("📊 資料時間範圍資訊")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "開始時間", 
                self.format_time_display(self.time_info['min_time']),
                help=f"原始值: {self.time_info['min_time']:.6f}s"
            )
        
        with col2:
            st.metric(
                "結束時間", 
                self.format_time_display(self.time_info['max_time']),
                help=f"原始值: {self.time_info['max_time']:.6f}s"
            )
        
        with col3:
            st.metric(
                "總持續時間", 
                self.format_time_display(self.time_info['total_duration']),
                help=f"原始值: {self.time_info['total_duration']:.6f}s"
            )
        
        with col4:
            st.metric(
                "資料點數", 
                f"{self.time_info['data_points']:,}",
                help=f"時間解析度: {self.time_info['time_resolution']:.6f}s"
            )
    
    def render_slider_selector(self) -> Tuple[float, float]:
        """
        渲染滑桿選擇器
        
        Returns:
            (開始時間, 結束時間)
        """
        if not self.time_info:
            st.error("時間資訊未載入")
            return 0.0, 0.0
        
        st.subheader("🎚️ 時間範圍選擇")
        
        # 使用雙滑桿選擇時間範圍
        time_range = st.slider(
            "選擇時間範圍",
            min_value=self.time_info['min_time'],
            max_value=self.time_info['max_time'],
            value=(self.time_info['min_time'], self.time_info['max_time']),
            step=self.time_info['time_resolution'],
            format="%.3f",
            key=f"{self.key_prefix}_slider",
            help="拖動滑桿選擇分析的時間範圍"
        )
        
        start_time, end_time = time_range
        
        # 顯示選擇的時間範圍資訊
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**開始時間**: {self.format_time_display(start_time)}")
        
        with col2:
            st.info(f"**結束時間**: {self.format_time_display(end_time)}")
        
        with col3:
            duration = end_time - start_time
            st.info(f"**選擇長度**: {self.format_time_display(duration)}")
        
        return start_time, end_time
    
    def render_number_input_selector(self, current_start: float, current_end: float) -> Tuple[float, float]:
        """
        渲染數值輸入選擇器
        
        Args:
            current_start: 當前開始時間
            current_end: 當前結束時間
            
        Returns:
            (開始時間, 結束時間)
        """
        if not self.time_info:
            st.error("時間資訊未載入")
            return current_start, current_end
        
        st.subheader("🔢 精確時間輸入")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_time = st.number_input(
                "開始時間 (秒)",
                min_value=self.time_info['min_time'],
                max_value=self.time_info['max_time'],
                value=current_start,
                step=self.time_info['time_resolution'],
                format="%.6f",
                key=f"{self.key_prefix}_start_input",
                help=f"範圍: {self.time_info['min_time']:.3f}s ~ {self.time_info['max_time']:.3f}s"
            )
        
        with col2:
            end_time = st.number_input(
                "結束時間 (秒)",
                min_value=self.time_info['min_time'],
                max_value=self.time_info['max_time'],
                value=current_end,
                step=self.time_info['time_resolution'],
                format="%.6f",
                key=f"{self.key_prefix}_end_input",
                help=f"範圍: {self.time_info['min_time']:.3f}s ~ {self.time_info['max_time']:.3f}s"
            )
        
        # 驗證時間範圍
        if self.analyzer:
            is_valid, error_msg = self.analyzer.validate_time_range(start_time, end_time)
            if not is_valid:
                st.error(f"❌ 時間範圍無效: {error_msg}")
            else:
                st.success("✅ 時間範圍有效")
        
        return start_time, end_time
    
    def render_preset_buttons(self) -> Optional[Tuple[float, float]]:
        """
        渲染預設時間範圍按鈕
        
        Returns:
            選擇的時間範圍，如果沒有選擇則返回 None
        """
        if not self.time_info:
            return None
        
        st.subheader("⚡ 快速選擇")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_duration = self.time_info['total_duration']
        min_time = self.time_info['min_time']
        max_time = self.time_info['max_time']
        
        selected_range = None
        
        with col1:
            if st.button("前 25%", key=f"{self.key_prefix}_preset_25", help="選擇前 25% 的時間範圍"):
                end_time = min_time + total_duration * 0.25
                selected_range = (min_time, end_time)
        
        with col2:
            if st.button("前 50%", key=f"{self.key_prefix}_preset_50", help="選擇前 50% 的時間範圍"):
                end_time = min_time + total_duration * 0.5
                selected_range = (min_time, end_time)
        
        with col3:
            if st.button("後 50%", key=f"{self.key_prefix}_preset_back_50", help="選擇後 50% 的時間範圍"):
                start_time = min_time + total_duration * 0.5
                selected_range = (start_time, max_time)
        
        with col4:
            if st.button("全部", key=f"{self.key_prefix}_preset_all", help="選擇全部時間範圍"):
                selected_range = (min_time, max_time)
        
        # 第二行按鈕
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            if st.button("中間 50%", key=f"{self.key_prefix}_preset_middle_50", help="選擇中間 50% 的時間範圍"):
                start_time = min_time + total_duration * 0.25
                end_time = min_time + total_duration * 0.75
                selected_range = (start_time, end_time)
        
        with col6:
            if st.button("前 10%", key=f"{self.key_prefix}_preset_10", help="選擇前 10% 的時間範圍"):
                end_time = min_time + total_duration * 0.1
                selected_range = (min_time, end_time)
        
        with col7:
            if st.button("後 10%", key=f"{self.key_prefix}_preset_back_10", help="選擇後 10% 的時間範圍"):
                start_time = min_time + total_duration * 0.9
                selected_range = (start_time, max_time)
        
        with col8:
            if st.button("重置", key=f"{self.key_prefix}_preset_reset", help="重置為全部範圍"):
                selected_range = (min_time, max_time)
        
        return selected_range
    
    def render_complete_selector(self, df: pd.DataFrame) -> Tuple[float, float, bool]:
        """
        渲染完整的時間選擇器介面
        
        Args:
            df: 包含時間資料的 DataFrame
            
        Returns:
            (開始時間, 結束時間, 是否有效)
        """
        # 設定分析器
        if not self.setup_analyzer(df):
            return 0.0, 0.0, False
        
        # 渲染時間資訊面板
        self.render_time_info_panel()
        
        st.divider()
        
        # 檢查是否有預設選擇
        preset_range = self.render_preset_buttons()
        
        st.divider()
        
        # 如果有預設選擇，更新 session state
        if preset_range:
            st.session_state[f"{self.key_prefix}_current_start"] = preset_range[0]
            st.session_state[f"{self.key_prefix}_current_end"] = preset_range[1]
        
        # 獲取當前時間範圍
        current_start = st.session_state.get(f"{self.key_prefix}_current_start", self.time_info['min_time'])
        current_end = st.session_state.get(f"{self.key_prefix}_current_end", self.time_info['max_time'])
        
        # 渲染滑桿選擇器
        slider_start, slider_end = self.render_slider_selector()
        
        st.divider()
        
        # 渲染數值輸入選擇器
        input_start, input_end = self.render_number_input_selector(slider_start, slider_end)
        
        # 使用數值輸入的結果作為最終結果（優先級更高）
        final_start = input_start
        final_end = input_end
        
        # 更新 session state
        st.session_state[f"{self.key_prefix}_current_start"] = final_start
        st.session_state[f"{self.key_prefix}_current_end"] = final_end
        
        # 驗證最終結果
        is_valid = True
        if self.analyzer:
            is_valid, _ = self.analyzer.validate_time_range(final_start, final_end)
        
        return final_start, final_end, is_valid


class TimeRangePreview:
    """時間區間預覽器"""
    
    def __init__(self, analyzer: TimeRangeAnalyzer):
        """
        初始化時間區間預覽器
        
        Args:
            analyzer: 時間區間分析器
        """
        self.analyzer = analyzer
    
    def render_preview_stats(self, start_time: float, end_time: float) -> None:
        """
        渲染預覽統計資訊
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
        """
        try:
            # 獲取預覽統計
            stats = self.analyzer.get_preview_stats(start_time, end_time)
            
            st.subheader("📋 選擇區間預覽")
            
            # 時間範圍資訊
            time_info = stats['time_range']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("開始時間", time_info['start_time_formatted'])
            
            with col2:
                st.metric("結束時間", time_info['end_time_formatted'])
            
            with col3:
                st.metric("持續時間", time_info['duration_formatted'])
            
            # 資料資訊
            data_info = stats['data_info']
            col4, col5, col6 = st.columns(3)
            
            with col4:
                st.metric("資料點數", f"{data_info['data_points']:,}")
            
            with col5:
                st.metric("總資料點數", f"{data_info['total_data_points']:,}")
            
            with col6:
                st.metric("資料比例", f"{data_info['data_percentage']:.1f}%")
            
            # 功率統計（如果有）
            if 'power_stats' in stats:
                st.subheader("⚡ 功率統計")
                power_stats = stats['power_stats']
                
                col7, col8, col9, col10 = st.columns(4)
                
                with col7:
                    st.metric("平均功率", f"{power_stats['mean_mW']:.2f} mW")
                
                with col8:
                    st.metric("最大功率", f"{power_stats['max_mW']:.2f} mW")
                
                with col9:
                    st.metric("最小功率", f"{power_stats['min_mW']:.2f} mW")
                
                with col10:
                    st.metric("功率標準差", f"{power_stats['std_mW']:.2f} mW")
            
            # 電流統計（如果有）
            if 'current_stats' in stats:
                st.subheader("🔌 電流統計")
                current_stats = stats['current_stats']
                
                col11, col12, col13, col14 = st.columns(4)
                
                with col11:
                    st.metric("平均電流", f"{current_stats['mean_mA']:.2f} mA")
                
                with col12:
                    st.metric("最大電流", f"{current_stats['max_mA']:.2f} mA")
                
                with col13:
                    st.metric("最小電流", f"{current_stats['min_mA']:.2f} mA")
                
                with col14:
                    st.metric("電流標準差", f"{current_stats['std_mA']:.2f} mA")
            
            # 電壓統計（如果有）
            if 'voltage_stats' in stats:
                st.subheader("🔋 電壓統計")
                voltage_stats = stats['voltage_stats']
                
                col15, col16, col17, col18 = st.columns(4)
                
                with col15:
                    st.metric("平均電壓", f"{voltage_stats['mean_V']:.3f} V")
                
                with col16:
                    st.metric("最大電壓", f"{voltage_stats['max_V']:.3f} V")
                
                with col17:
                    st.metric("最小電壓", f"{voltage_stats['min_V']:.3f} V")
                
                with col18:
                    st.metric("電壓標準差", f"{voltage_stats['std_V']:.3f} V")
            
        except Exception as e:
            st.error(f"無法生成預覽統計: {str(e)}")
    
    def render_validation_status(self, start_time: float, end_time: float) -> bool:
        """
        渲染驗證狀態
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            是否通過驗證
        """
        is_valid, error_msg = self.analyzer.validate_time_range(start_time, end_time)
        
        if is_valid:
            st.success("✅ 時間範圍驗證通過，可以進行分析")
        else:
            st.error(f"❌ 時間範圍驗證失敗: {error_msg}")
        
        return is_valid


class RealTimePreview:
    """即時預覽功能"""
    
    def __init__(self, analyzer: TimeRangeAnalyzer, key_prefix: str = "preview"):
        """
        初始化即時預覽
        
        Args:
            analyzer: 時間區間分析器
            key_prefix: Streamlit 元件的 key 前綴
        """
        self.analyzer = analyzer
        self.key_prefix = key_prefix
        self.preview_cache = {}
    
    def _get_cache_key(self, start_time: float, end_time: float) -> str:
        """
        生成快取鍵值
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            快取鍵值
        """
        return f"{start_time:.6f}_{end_time:.6f}"
    
    def _calculate_preview_data(self, start_time: float, end_time: float) -> Dict:
        """
        計算預覽資料
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            預覽資料字典
        """
        cache_key = self._get_cache_key(start_time, end_time)
        
        # 檢查快取
        if cache_key in self.preview_cache:
            return self.preview_cache[cache_key]
        
        try:
            # 計算統計資料
            stats = self.analyzer.get_preview_stats(start_time, end_time)
            
            # 獲取過濾後的資料用於圖表
            filtered_df = self.analyzer.filter_by_time_range(start_time, end_time)
            
            preview_data = {
                'stats': stats,
                'filtered_df': filtered_df,
                'is_valid': True,
                'error_msg': None
            }
            
            # 快取結果
            self.preview_cache[cache_key] = preview_data
            
            return preview_data
            
        except Exception as e:
            error_data = {
                'stats': None,
                'filtered_df': None,
                'is_valid': False,
                'error_msg': str(e)
            }
            return error_data
    
    def render_instant_stats(self, start_time: float, end_time: float) -> None:
        """
        渲染即時統計資訊
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
        """
        preview_data = self._calculate_preview_data(start_time, end_time)
        
        if not preview_data['is_valid']:
            st.error(f"無法計算預覽統計: {preview_data['error_msg']}")
            return
        
        stats = preview_data['stats']
        
        # 建立即時更新的統計面板
        with st.container():
            st.subheader("⚡ 即時預覽統計")
            
            # 基本資訊
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                duration = stats['time_range']['duration']
                st.metric(
                    "選擇長度",
                    f"{duration:.3f}s",
                    delta=f"{duration/stats['time_range']['duration']*100:.1f}% of total" if duration > 0 else None
                )
            
            with col2:
                data_points = stats['data_info']['data_points']
                st.metric(
                    "資料點數",
                    f"{data_points:,}",
                    delta=f"{stats['data_info']['data_percentage']:.1f}%"
                )
            
            with col3:
                if 'power_stats' in stats:
                    avg_power = stats['power_stats']['mean_mW']
                    st.metric("平均功率", f"{avg_power:.2f} mW")
                else:
                    st.metric("平均功率", "N/A")
            
            with col4:
                if 'current_stats' in stats:
                    avg_current = stats['current_stats']['mean_mA']
                    st.metric("平均電流", f"{avg_current:.2f} mA")
                else:
                    st.metric("平均電流", "N/A")
    
    def render_mini_chart(self, start_time: float, end_time: float) -> None:
        """
        渲染迷你圖表預覽
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
        """
        preview_data = self._calculate_preview_data(start_time, end_time)
        
        if not preview_data['is_valid']:
            st.warning("無法生成預覽圖表")
            return
        
        filtered_df = preview_data['filtered_df']
        
        if filtered_df is None or filtered_df.empty:
            st.warning("選擇的時間範圍內沒有資料")
            return
        
        # 建立迷你圖表
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 只顯示功率圖表作為預覽
        if 'Power' in filtered_df.columns:
            fig = go.Figure()
            
            fig.add_trace(
                go.Scatter(
                    x=filtered_df['Time'],
                    y=filtered_df['Power'] * 1000,  # 轉換為 mW
                    mode='lines',
                    name='功率',
                    line=dict(color='blue', width=1)
                )
            )
            
            fig.update_layout(
                title="功率預覽",
                xaxis_title="時間 (s)",
                yaxis_title="功率 (mW)",
                height=200,
                margin=dict(l=50, r=50, t=50, b=50),
                showlegend=False
            )
            
            # 標註選擇範圍
            fig.add_vline(x=start_time, line_dash="dash", line_color="red", annotation_text="開始")
            fig.add_vline(x=end_time, line_dash="dash", line_color="red", annotation_text="結束")
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_data_quality_check(self, start_time: float, end_time: float) -> None:
        """
        渲染資料品質檢查
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
        """
        preview_data = self._calculate_preview_data(start_time, end_time)
        
        if not preview_data['is_valid']:
            st.error("❌ 資料品質檢查失敗")
            st.error(preview_data['error_msg'])
            return
        
        filtered_df = preview_data['filtered_df']
        stats = preview_data['stats']
        
        # 資料品質指標
        quality_checks = []
        
        # 檢查資料點數量
        data_points = len(filtered_df)
        if data_points < 10:
            quality_checks.append(("⚠️", "資料點數量較少", f"只有 {data_points} 個資料點"))
        elif data_points < 100:
            quality_checks.append(("⚠️", "資料點數量適中", f"有 {data_points} 個資料點"))
        else:
            quality_checks.append(("✅", "資料點數量充足", f"有 {data_points} 個資料點"))
        
        # 檢查時間範圍
        duration = stats['time_range']['duration']
        if duration < 1.0:
            quality_checks.append(("⚠️", "時間範圍較短", f"持續時間 {duration:.3f}s"))
        elif duration < 10.0:
            quality_checks.append(("✅", "時間範圍適中", f"持續時間 {duration:.3f}s"))
        else:
            quality_checks.append(("✅", "時間範圍充足", f"持續時間 {duration:.3f}s"))
        
        # 檢查資料完整性
        if 'Power' in filtered_df.columns:
            power_na_count = filtered_df['Power'].isna().sum()
            if power_na_count == 0:
                quality_checks.append(("✅", "功率資料完整", "無缺失值"))
            else:
                quality_checks.append(("⚠️", "功率資料有缺失", f"{power_na_count} 個缺失值"))
        
        # 顯示品質檢查結果
        st.subheader("🔍 資料品質檢查")
        
        for icon, title, description in quality_checks:
            st.write(f"{icon} **{title}**: {description}")
    
    def render_comparison_with_full_data(self, start_time: float, end_time: float) -> None:
        """
        渲染與完整資料的比較
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
        """
        preview_data = self._calculate_preview_data(start_time, end_time)
        
        if not preview_data['is_valid']:
            return
        
        stats = preview_data['stats']
        
        # 計算完整資料的統計
        full_time_info = self.analyzer.get_time_range_info()
        full_stats = self.analyzer.get_preview_stats(
            full_time_info['min_time'], 
            full_time_info['max_time']
        )
        
        st.subheader("📊 與完整資料比較")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**選擇區間**")
            if 'power_stats' in stats:
                st.write(f"平均功率: {stats['power_stats']['mean_mW']:.2f} mW")
                st.write(f"最大功率: {stats['power_stats']['max_mW']:.2f} mW")
            st.write(f"資料點數: {stats['data_info']['data_points']:,}")
            st.write(f"持續時間: {stats['time_range']['duration']:.3f}s")
        
        with col2:
            st.write("**完整資料**")
            if 'power_stats' in full_stats:
                st.write(f"平均功率: {full_stats['power_stats']['mean_mW']:.2f} mW")
                st.write(f"最大功率: {full_stats['power_stats']['max_mW']:.2f} mW")
            st.write(f"資料點數: {full_stats['data_info']['data_points']:,}")
            st.write(f"持續時間: {full_stats['time_range']['duration']:.3f}s")
        
        # 計算差異百分比
        if 'power_stats' in stats and 'power_stats' in full_stats:
            power_diff = ((stats['power_stats']['mean_mW'] - full_stats['power_stats']['mean_mW']) / 
                         full_stats['power_stats']['mean_mW'] * 100)
            
            if abs(power_diff) < 5:
                st.success(f"✅ 平均功率差異很小: {power_diff:+.1f}%")
            elif abs(power_diff) < 20:
                st.warning(f"⚠️ 平均功率有一定差異: {power_diff:+.1f}%")
            else:
                st.error(f"❌ 平均功率差異較大: {power_diff:+.1f}%")
    
    def render_complete_preview(self, start_time: float, end_time: float) -> bool:
        """
        渲染完整的即時預覽
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            是否可以進行分析
        """
        # 驗證時間範圍
        is_valid, error_msg = self.analyzer.validate_time_range(start_time, end_time)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return False
        
        # 渲染各個預覽元件
        self.render_instant_stats(start_time, end_time)
        
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_mini_chart(start_time, end_time)
        
        with col2:
            self.render_data_quality_check(start_time, end_time)
        
        st.divider()
        
        self.render_comparison_with_full_data(start_time, end_time)
        
        return True
    
    def clear_cache(self) -> None:
        """清除預覽快取"""
        self.preview_cache.clear()


class TimeRangeAnalysisUI:
    """時間區間分析完整介面"""
    
    def __init__(self, key_prefix: str = "time_analysis"):
        """
        初始化時間區間分析介面
        
        Args:
            key_prefix: Streamlit 元件的 key 前綴
        """
        self.key_prefix = key_prefix
        self.selector = TimeRangeSelector(f"{key_prefix}_selector")
        self.preview = None
        self.real_time_preview = None
    
    def render_complete_interface(self, df: pd.DataFrame) -> Tuple[float, float, bool, Optional[pd.DataFrame]]:
        """
        渲染完整的時間區間分析介面
        
        Args:
            df: 包含時間資料的 DataFrame
            
        Returns:
            (開始時間, 結束時間, 是否有效, 過濾後的資料)
        """
        st.header("🕒 時間區間分析")
        
        # 設定選擇器
        if not self.selector.setup_analyzer(df):
            return 0.0, 0.0, False, None
        
        # 初始化預覽器
        if self.preview is None:
            self.preview = TimeRangePreview(self.selector.analyzer)
        
        if self.real_time_preview is None:
            self.real_time_preview = RealTimePreview(self.selector.analyzer, f"{self.key_prefix}_preview")
        
        # 渲染時間選擇器
        start_time, end_time, is_valid = self.selector.render_complete_selector(df)
        
        st.divider()
        
        # 如果時間範圍有效，顯示即時預覽
        if is_valid:
            can_analyze = self.real_time_preview.render_complete_preview(start_time, end_time)
            
            if can_analyze:
                # 提供確認分析按鈕
                st.divider()
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    if st.button(
                        "🚀 確認並開始分析", 
                        key=f"{self.key_prefix}_confirm_analysis",
                        type="primary",
                        use_container_width=True,
                        help="使用選擇的時間範圍進行完整分析"
                    ):
                        # 獲取過濾後的資料
                        try:
                            filtered_df = self.selector.analyzer.filter_by_time_range(start_time, end_time)
                            st.success("✅ 時間範圍確認，開始分析...")
                            return start_time, end_time, True, filtered_df
                        except Exception as e:
                            st.error(f"獲取過濾資料失敗: {str(e)}")
                            return start_time, end_time, False, None
            
            return start_time, end_time, is_valid, None
        else:
            st.warning("請選擇有效的時間範圍")
            return start_time, end_time, False, None