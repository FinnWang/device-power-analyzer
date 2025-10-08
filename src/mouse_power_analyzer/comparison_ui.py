#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparison UI - 結果比較介面

提供多個時間區間分析結果的比較和視覺化功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from .result_manager import AnalysisResultManager, TimeRangeAnalysisResult


class ResultListDisplay:
    """結果列表顯示器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化結果列表顯示器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def render_results_table(self, selectable: bool = False) -> Optional[List[str]]:
        """
        渲染結果表格
        
        Args:
            selectable: 是否可選擇結果
            
        Returns:
            如果可選擇，返回選中的結果 ID 列表
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            st.info("📝 目前沒有分析結果")
            return None
        
        # 建立表格資料
        table_data = []
        for i, result in enumerate(results):
            power_info = result.get_power_info()
            
            table_data.append({
                '編號': i + 1,
                '標籤': result.label,
                '模式': result.mode_cn,
                '檔案': result.filename,
                '時間範圍': f"{result.start_time:.3f}s - {result.end_time:.3f}s",
                '持續時間': f"{result.duration:.3f}s",
                '平均功率': f"{power_info['avg_power_mW']:.2f} mW",
                '預估續航': f"{power_info['battery_hours']:.1f} 小時",
                '分析時間': result.timestamp.strftime('%m-%d %H:%M')
            })
        
        df = pd.DataFrame(table_data)
        
        if selectable:
            # 可選擇模式
            st.subheader("📋 選擇要比較的結果")
            
            # 全選/全不選按鈕
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                if st.button("全選", key="select_all_results"):
                    for i in range(len(results)):
                        st.session_state[f"select_result_{i}"] = True
            
            with col2:
                if st.button("全不選", key="deselect_all_results"):
                    for i in range(len(results)):
                        st.session_state[f"select_result_{i}"] = False
            
            # 顯示可選擇的表格
            selected_indices = []
            
            for i, row in df.iterrows():
                col_check, col_data = st.columns([0.1, 0.9])
                
                with col_check:
                    selected = st.checkbox(
                        "",
                        key=f"select_result_{i}",
                        label_visibility="collapsed"
                    )
                    if selected:
                        selected_indices.append(i)
                
                with col_data:
                    # 顯示結果資訊
                    st.write(f"**{row['標籤']}** - {row['模式']}")
                    st.caption(f"{row['時間範圍']} | {row['平均功率']} | {row['預估續航']}")
            
            # 返回選中結果的 ID
            if selected_indices:
                selected_ids = [results[i].id for i in selected_indices]
                return selected_ids
            else:
                return []
        
        else:
            # 只顯示模式
            st.subheader("📋 分析結果列表")
            st.dataframe(df, use_container_width=True, hide_index=True)
            return None
    
    def render_results_cards(self) -> None:
        """渲染結果卡片視圖"""
        results = self.result_manager.get_all_results()
        
        if not results:
            st.info("📝 目前沒有分析結果")
            return
        
        st.subheader("🗂️ 結果卡片視圖")
        
        # 每行顯示3個卡片
        cols_per_row = 3
        
        for i in range(0, len(results), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(results):
                    result = results[idx]
                    power_info = result.get_power_info()
                    
                    with cols[j]:
                        with st.container():
                            st.markdown(f"""
                            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 8px 0;">
                                <h4 style="margin: 0 0 8px 0; color: #1f77b4;">{result.label}</h4>
                                <p style="margin: 4px 0; font-weight: bold;">{result.mode_cn}</p>
                                <p style="margin: 4px 0; font-size: 0.9em; color: #666;">
                                    {result.start_time:.3f}s - {result.end_time:.3f}s
                                </p>
                                <p style="margin: 4px 0;">
                                    <span style="color: #ff6b6b;">⚡ {power_info['avg_power_mW']:.2f} mW</span><br>
                                    <span style="color: #4ecdc4;">🔋 {power_info['battery_hours']:.1f} 小時</span>
                                </p>
                                <p style="margin: 4px 0; font-size: 0.8em; color: #999;">
                                    {result.timestamp.strftime('%m-%d %H:%M')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
    
    def render_results_summary(self) -> None:
        """渲染結果摘要"""
        summary = self.result_manager.get_results_summary()
        
        if summary['count'] == 0:
            return
        
        st.subheader("📊 結果摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總結果數", summary['count'])
        
        with col2:
            st.metric("涉及模式", len(summary['modes']))
        
        with col3:
            st.metric("涉及檔案", len(summary['files']))
        
        with col4:
            power_range = summary['power_range']['max'] - summary['power_range']['min']
            st.metric("功率範圍", f"{power_range:.2f} mW")
        
        # 顯示詳細資訊
        with st.expander("📋 詳細摘要資訊"):
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.write("**涉及的模式:**")
                for mode in summary['modes']:
                    st.write(f"- {mode}")
            
            with col_right:
                st.write("**涉及的檔案:**")
                for file in summary['files']:
                    st.write(f"- {file}")


class ResultSelector:
    """結果選擇器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化結果選擇器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def render_multi_select(self, key: str = "multi_select") -> List[str]:
        """
        渲染多選選擇器
        
        Args:
            key: Streamlit 元件的 key
            
        Returns:
            選中的結果 ID 列表
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            st.warning("沒有可選擇的結果")
            return []
        
        # 建立選項
        options = {}
        for result in results:
            label = f"{result.label} - {result.mode_cn} ({result.start_time:.3f}s-{result.end_time:.3f}s)"
            options[label] = result.id
        
        # 多選框
        selected_labels = st.multiselect(
            "選擇要比較的結果",
            options=list(options.keys()),
            key=key,
            help="可以選擇多個結果進行比較分析"
        )
        
        # 返回選中的 ID
        selected_ids = [options[label] for label in selected_labels]
        
        return selected_ids
    
    def render_single_select(self, key: str = "single_select") -> Optional[str]:
        """
        渲染單選選擇器
        
        Args:
            key: Streamlit 元件的 key
            
        Returns:
            選中的結果 ID，如果沒有選擇則返回 None
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            st.warning("沒有可選擇的結果")
            return None
        
        # 建立選項
        options = ["請選擇..."]
        option_ids = [None]
        
        for result in results:
            label = f"{result.label} - {result.mode_cn} ({result.start_time:.3f}s-{result.end_time:.3f}s)"
            options.append(label)
            option_ids.append(result.id)
        
        # 單選框
        selected_index = st.selectbox(
            "選擇結果",
            range(len(options)),
            format_func=lambda x: options[x],
            key=key
        )
        
        return option_ids[selected_index]
    
    def render_filter_options(self) -> Dict[str, Any]:
        """
        渲染篩選選項
        
        Returns:
            篩選條件字典
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            return {}
        
        st.subheader("🔍 篩選條件")
        
        # 收集所有可用的選項
        all_modes = list(set(result.mode_cn for result in results))
        all_files = list(set(result.filename for result in results))
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 模式篩選
            selected_modes = st.multiselect(
                "篩選模式",
                options=all_modes,
                default=all_modes,
                key="filter_modes"
            )
        
        with col2:
            # 檔案篩選
            selected_files = st.multiselect(
                "篩選檔案",
                options=all_files,
                default=all_files,
                key="filter_files"
            )
        
        # 功率範圍篩選
        powers = [result.get_power_info()['avg_power_mW'] for result in results]
        min_power, max_power = min(powers), max(powers)
        
        if min_power < max_power:
            power_range = st.slider(
                "功率範圍 (mW)",
                min_value=min_power,
                max_value=max_power,
                value=(min_power, max_power),
                step=0.1,
                key="filter_power_range"
            )
        else:
            power_range = (min_power, max_power)
        
        # 時間範圍篩選
        durations = [result.duration for result in results]
        min_duration, max_duration = min(durations), max(durations)
        
        if min_duration < max_duration:
            duration_range = st.slider(
                "持續時間範圍 (秒)",
                min_value=min_duration,
                max_value=max_duration,
                value=(min_duration, max_duration),
                step=0.1,
                key="filter_duration_range"
            )
        else:
            duration_range = (min_duration, max_duration)
        
        return {
            'modes': selected_modes,
            'files': selected_files,
            'power_range': power_range,
            'duration_range': duration_range
        }
    
    def apply_filters(self, filters: Dict[str, Any]) -> List[str]:
        """
        應用篩選條件
        
        Args:
            filters: 篩選條件字典
            
        Returns:
            符合條件的結果 ID 列表
        """
        results = self.result_manager.get_all_results()
        filtered_ids = []
        
        for result in results:
            # 檢查模式篩選
            if result.mode_cn not in filters.get('modes', []):
                continue
            
            # 檢查檔案篩選
            if result.filename not in filters.get('files', []):
                continue
            
            # 檢查功率範圍篩選
            power_info = result.get_power_info()
            power_range = filters.get('power_range', (0, float('inf')))
            if not (power_range[0] <= power_info['avg_power_mW'] <= power_range[1]):
                continue
            
            # 檢查持續時間篩選
            duration_range = filters.get('duration_range', (0, float('inf')))
            if not (duration_range[0] <= result.duration <= duration_range[1]):
                continue
            
            filtered_ids.append(result.id)
        
        return filtered_ids


class ComparisonVisualizer:
    """比較視覺化器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化比較視覺化器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def create_power_comparison_chart(self, result_ids: List[str], chart_theme: str = "plotly_white") -> go.Figure:
        """
        建立功率比較圖表
        
        Args:
            result_ids: 要比較的結果 ID 列表
            chart_theme: 圖表主題
            
        Returns:
            Plotly 圖表物件
        """
        if not result_ids:
            return go.Figure()
        
        # 收集資料
        labels = []
        avg_powers = []
        max_powers = []
        colors = px.colors.qualitative.Set3
        
        for i, result_id in enumerate(result_ids):
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                labels.append(result.label)
                avg_powers.append(power_info['avg_power_mW'])
                max_powers.append(power_info['max_power_mW'])
        
        # 建立圖表
        fig = go.Figure()
        
        # 平均功率
        fig.add_trace(go.Bar(
            name='平均功率',
            x=labels,
            y=avg_powers,
            marker_color=colors[0] if colors else 'blue',
            text=[f"{p:.2f} mW" for p in avg_powers],
            textposition='auto'
        ))
        
        # 最大功率
        fig.add_trace(go.Bar(
            name='最大功率',
            x=labels,
            y=max_powers,
            marker_color=colors[1] if len(colors) > 1 else 'red',
            text=[f"{p:.2f} mW" for p in max_powers],
            textposition='auto'
        ))
        
        fig.update_layout(
            title='功率比較',
            xaxis_title='分析結果',
            yaxis_title='功率 (mW)',
            template=chart_theme,
            barmode='group',
            height=500
        )
        
        return fig
    
    def create_battery_life_comparison_chart(self, result_ids: List[str], chart_theme: str = "plotly_white") -> go.Figure:
        """
        建立電池續航比較圖表
        
        Args:
            result_ids: 要比較的結果 ID 列表
            chart_theme: 圖表主題
            
        Returns:
            Plotly 圖表物件
        """
        if not result_ids:
            return go.Figure()
        
        # 收集資料
        labels = []
        battery_hours = []
        
        for result_id in result_ids:
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                labels.append(result.label)
                battery_hours.append(power_info['battery_hours'])
        
        # 建立圖表
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=labels,
            y=battery_hours,
            marker_color=px.colors.qualitative.Set2,
            text=[f"{h:.1f} 小時" for h in battery_hours],
            textposition='auto'
        ))
        
        fig.update_layout(
            title='電池續航比較',
            xaxis_title='分析結果',
            yaxis_title='預估續航 (小時)',
            template=chart_theme,
            height=400
        )
        
        return fig
    
    def create_time_range_comparison_chart(self, result_ids: List[str], chart_theme: str = "plotly_white") -> go.Figure:
        """
        建立時間範圍比較圖表
        
        Args:
            result_ids: 要比較的結果 ID 列表
            chart_theme: 圖表主題
            
        Returns:
            Plotly 圖表物件
        """
        if not result_ids:
            return go.Figure()
        
        # 收集資料
        data = []
        
        for result_id in result_ids:
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                data.append({
                    'label': result.label,
                    'start_time': result.start_time,
                    'end_time': result.end_time,
                    'duration': result.duration
                })
        
        if not data:
            return go.Figure()
        
        # 建立甘特圖樣式的時間範圍圖
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, item in enumerate(data):
            fig.add_trace(go.Scatter(
                x=[item['start_time'], item['end_time']],
                y=[i, i],
                mode='lines+markers',
                name=item['label'],
                line=dict(width=8, color=colors[i % len(colors)]),
                marker=dict(size=8),
                text=[f"開始: {item['start_time']:.3f}s", f"結束: {item['end_time']:.3f}s"],
                textposition="top center"
            ))
        
        fig.update_layout(
            title='時間範圍比較',
            xaxis_title='時間 (秒)',
            yaxis_title='分析結果',
            yaxis=dict(
                tickmode='array',
                tickvals=list(range(len(data))),
                ticktext=[item['label'] for item in data]
            ),
            template=chart_theme,
            height=max(300, len(data) * 60),
            showlegend=False
        )
        
        return fig
    
    def create_comprehensive_comparison_chart(self, result_ids: List[str], chart_theme: str = "plotly_white") -> go.Figure:
        """
        建立綜合比較圖表
        
        Args:
            result_ids: 要比較的結果 ID 列表
            chart_theme: 圖表主題
            
        Returns:
            Plotly 圖表物件
        """
        if not result_ids:
            return go.Figure()
        
        # 建立子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('平均功率比較', '電池續航比較', '持續時間比較', '功率效率比較'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # 收集資料
        labels = []
        avg_powers = []
        battery_hours = []
        durations = []
        
        for result_id in result_ids:
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                labels.append(result.label)
                avg_powers.append(power_info['avg_power_mW'])
                battery_hours.append(power_info['battery_hours'])
                durations.append(result.duration)
        
        if not labels:
            return go.Figure()
        
        colors = px.colors.qualitative.Set3
        
        # 平均功率比較
        fig.add_trace(
            go.Bar(x=labels, y=avg_powers, name='平均功率', marker_color=colors[0]),
            row=1, col=1
        )
        
        # 電池續航比較
        fig.add_trace(
            go.Bar(x=labels, y=battery_hours, name='電池續航', marker_color=colors[1]),
            row=1, col=2
        )
        
        # 持續時間比較
        fig.add_trace(
            go.Bar(x=labels, y=durations, name='持續時間', marker_color=colors[2]),
            row=2, col=1
        )
        
        # 功率效率散點圖（功率 vs 續航）
        fig.add_trace(
            go.Scatter(
                x=avg_powers, 
                y=battery_hours, 
                mode='markers+text',
                text=labels,
                textposition="top center",
                name='功率效率',
                marker=dict(size=10, color=colors[3])
            ),
            row=2, col=2
        )
        
        # 更新軸標籤
        fig.update_xaxes(title_text="分析結果", row=1, col=1)
        fig.update_yaxes(title_text="功率 (mW)", row=1, col=1)
        fig.update_xaxes(title_text="分析結果", row=1, col=2)
        fig.update_yaxes(title_text="續航 (小時)", row=1, col=2)
        fig.update_xaxes(title_text="分析結果", row=2, col=1)
        fig.update_yaxes(title_text="時間 (秒)", row=2, col=1)
        fig.update_xaxes(title_text="平均功率 (mW)", row=2, col=2)
        fig.update_yaxes(title_text="電池續航 (小時)", row=2, col=2)
        
        fig.update_layout(
            template=chart_theme,
            height=800,
            showlegend=False,
            title_text="綜合比較分析"
        )
        
        return fig
    
    def create_radar_chart(self, result_ids: List[str], chart_theme: str = "plotly_white") -> go.Figure:
        """
        建立雷達圖比較
        
        Args:
            result_ids: 要比較的結果 ID 列表
            chart_theme: 圖表主題
            
        Returns:
            Plotly 圖表物件
        """
        if not result_ids:
            return go.Figure()
        
        # 收集所有結果的資料用於正規化
        all_results = self.result_manager.get_all_results()
        all_powers = [r.get_power_info()['avg_power_mW'] for r in all_results]
        all_batteries = [r.get_power_info()['battery_hours'] for r in all_results]
        all_durations = [r.duration for r in all_results]
        
        # 計算正規化範圍
        power_range = (min(all_powers), max(all_powers))
        battery_range = (min(all_batteries), max(all_batteries))
        duration_range = (min(all_durations), max(all_durations))
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, result_id in enumerate(result_ids):
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                
                # 正規化數值 (0-100)
                power_norm = ((power_info['avg_power_mW'] - power_range[0]) / 
                             (power_range[1] - power_range[0]) * 100) if power_range[1] > power_range[0] else 50
                
                battery_norm = ((power_info['battery_hours'] - battery_range[0]) / 
                               (battery_range[1] - battery_range[0]) * 100) if battery_range[1] > battery_range[0] else 50
                
                duration_norm = ((result.duration - duration_range[0]) / 
                                (duration_range[1] - duration_range[0]) * 100) if duration_range[1] > duration_range[0] else 50
                
                # 效率分數（續航高、功率低為好）
                efficiency_score = (battery_norm + (100 - power_norm)) / 2
                
                fig.add_trace(go.Scatterpolar(
                    r=[power_norm, battery_norm, duration_norm, efficiency_score],
                    theta=['功率水平', '電池續航', '測試時長', '效率分數'],
                    fill='toself',
                    name=result.label,
                    line_color=colors[i % len(colors)]
                ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            template=chart_theme,
            title="多維度比較雷達圖",
            height=600
        )
        
        return fig


class ComparisonReportGenerator:
    """比較報告生成器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化比較報告生成器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def generate_comparison_table(self, result_ids: List[str]) -> pd.DataFrame:
        """
        生成比較表格
        
        Args:
            result_ids: 要比較的結果 ID 列表
            
        Returns:
            比較資料的 DataFrame
        """
        if not result_ids:
            return pd.DataFrame()
        
        comparison_data = []
        
        for result_id in result_ids:
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                
                comparison_data.append({
                    '標籤': result.label,
                    '模式': result.mode_cn,
                    '檔案': result.filename,
                    '開始時間 (s)': f"{result.start_time:.3f}",
                    '結束時間 (s)': f"{result.end_time:.3f}",
                    '持續時間 (s)': f"{result.duration:.3f}",
                    '平均功率 (mW)': f"{power_info['avg_power_mW']:.2f}",
                    '最大功率 (mW)': f"{power_info['max_power_mW']:.2f}",
                    '平均電流 (mA)': f"{power_info['avg_current_mA']:.2f}",
                    '預估續航 (小時)': f"{power_info['battery_hours']:.1f}",
                    '分析時間': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return pd.DataFrame(comparison_data)
    
    def generate_statistical_summary(self, result_ids: List[str]) -> Dict[str, Any]:
        """
        生成統計摘要
        
        Args:
            result_ids: 要比較的結果 ID 列表
            
        Returns:
            統計摘要字典
        """
        if not result_ids:
            return {}
        
        powers = []
        batteries = []
        durations = []
        modes = set()
        files = set()
        
        for result_id in result_ids:
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                powers.append(power_info['avg_power_mW'])
                batteries.append(power_info['battery_hours'])
                durations.append(result.duration)
                modes.add(result.mode_cn)
                files.add(result.filename)
        
        if not powers:
            return {}
        
        return {
            'count': len(result_ids),
            'modes': list(modes),
            'files': list(files),
            'power_stats': {
                'min': min(powers),
                'max': max(powers),
                'mean': np.mean(powers),
                'std': np.std(powers),
                'range': max(powers) - min(powers)
            },
            'battery_stats': {
                'min': min(batteries),
                'max': max(batteries),
                'mean': np.mean(batteries),
                'std': np.std(batteries),
                'range': max(batteries) - min(batteries)
            },
            'duration_stats': {
                'min': min(durations),
                'max': max(durations),
                'mean': np.mean(durations),
                'std': np.std(durations),
                'range': max(durations) - min(durations)
            }
        }
    
    def generate_recommendations(self, result_ids: List[str]) -> List[str]:
        """
        生成建議
        
        Args:
            result_ids: 要比較的結果 ID 列表
            
        Returns:
            建議列表
        """
        if not result_ids or len(result_ids) < 2:
            return ["需要至少兩個結果才能生成比較建議"]
        
        recommendations = []
        
        # 找出最佳和最差的結果
        best_power_result = None
        worst_power_result = None
        best_battery_result = None
        worst_battery_result = None
        
        min_power = float('inf')
        max_power = 0
        max_battery = 0
        min_battery = float('inf')
        
        for result_id in result_ids:
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                power_info = result.get_power_info()
                avg_power = power_info['avg_power_mW']
                battery_hours = power_info['battery_hours']
                
                if avg_power < min_power:
                    min_power = avg_power
                    best_power_result = result
                
                if avg_power > max_power:
                    max_power = avg_power
                    worst_power_result = result
                
                if battery_hours > max_battery:
                    max_battery = battery_hours
                    best_battery_result = result
                
                if battery_hours < min_battery:
                    min_battery = battery_hours
                    worst_battery_result = result
        
        # 生成建議
        if best_power_result:
            recommendations.append(
                f"🏆 最佳功耗表現: {best_power_result.label} ({min_power:.2f} mW)"
            )
        
        if best_battery_result:
            recommendations.append(
                f"🔋 最佳續航表現: {best_battery_result.label} ({max_battery:.1f} 小時)"
            )
        
        if worst_power_result and worst_power_result != best_power_result:
            recommendations.append(
                f"⚠️ 功耗較高: {worst_power_result.label} ({max_power:.2f} mW)"
            )
        
        # 功耗差異分析
        power_diff = max_power - min_power
        power_diff_percent = (power_diff / min_power) * 100 if min_power > 0 else 0
        
        if power_diff_percent > 50:
            recommendations.append(
                f"📊 功耗差異顯著: 最高與最低相差 {power_diff:.2f} mW ({power_diff_percent:.1f}%)"
            )
        elif power_diff_percent > 20:
            recommendations.append(
                f"📊 功耗差異適中: 最高與最低相差 {power_diff:.2f} mW ({power_diff_percent:.1f}%)"
            )
        else:
            recommendations.append(
                f"📊 功耗差異較小: 最高與最低相差 {power_diff:.2f} mW ({power_diff_percent:.1f}%)"
            )
        
        # 使用建議
        if best_power_result and best_battery_result:
            if best_power_result.id == best_battery_result.id:
                recommendations.append(
                    f"💡 建議: {best_power_result.label} 在功耗和續航方面都表現最佳"
                )
            else:
                recommendations.append(
                    f"💡 建議: 根據使用需求選擇 {best_power_result.label}（低功耗）或 {best_battery_result.label}（長續航）"
                )
        
        return recommendations


class ComparisonUI:
    """比較介面主控制器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化比較介面
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
        self.list_display = ResultListDisplay(result_manager)
        self.selector = ResultSelector(result_manager)
        self.visualizer = ComparisonVisualizer(result_manager)
        self.report_generator = ComparisonReportGenerator(result_manager)
    
    def render_complete_comparison_interface(self) -> None:
        """渲染完整的比較介面"""
        if not self.result_manager.has_results():
            st.info("📝 目前沒有分析結果可供比較")
            return
        
        st.header("📊 結果比較分析")
        
        # 顯示結果摘要
        self.list_display.render_results_summary()
        
        st.divider()
        
        # 選擇比較模式
        comparison_mode = st.radio(
            "選擇比較模式",
            ["快速比較", "進階比較", "全部結果比較"],
            horizontal=True,
            help="選擇不同的比較模式來分析結果"
        )
        
        if comparison_mode == "快速比較":
            self._render_quick_comparison()
        elif comparison_mode == "進階比較":
            self._render_advanced_comparison()
        else:
            self._render_all_results_comparison()
    
    def _render_quick_comparison(self) -> None:
        """渲染快速比較"""
        st.subheader("⚡ 快速比較")
        
        # 選擇要比較的結果
        selected_ids = self.selector.render_multi_select("quick_comparison_select")
        
        if len(selected_ids) < 2:
            st.warning("請選擇至少兩個結果進行比較")
            return
        
        # 顯示比較圖表
        col1, col2 = st.columns(2)
        
        with col1:
            power_chart = self.visualizer.create_power_comparison_chart(selected_ids)
            st.plotly_chart(power_chart, use_container_width=True)
        
        with col2:
            battery_chart = self.visualizer.create_battery_life_comparison_chart(selected_ids)
            st.plotly_chart(battery_chart, use_container_width=True)
        
        # 顯示比較表格
        st.subheader("📋 比較表格")
        comparison_df = self.report_generator.generate_comparison_table(selected_ids)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # 顯示建議
        st.subheader("💡 分析建議")
        recommendations = self.report_generator.generate_recommendations(selected_ids)
        for rec in recommendations:
            st.write(f"- {rec}")
    
    def _render_advanced_comparison(self) -> None:
        """渲染進階比較"""
        st.subheader("🔬 進階比較")
        
        # 篩選選項
        filters = self.selector.render_filter_options()
        filtered_ids = self.selector.apply_filters(filters)
        
        if not filtered_ids:
            st.warning("沒有符合篩選條件的結果")
            return
        
        st.info(f"篩選後有 {len(filtered_ids)} 個結果")
        
        # 選擇要比較的結果
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 從篩選結果中選擇
            available_results = [self.result_manager.get_result_by_id(rid) for rid in filtered_ids]
            available_options = {}
            
            for result in available_results:
                if result:
                    label = f"{result.label} - {result.mode_cn} ({result.start_time:.3f}s-{result.end_time:.3f}s)"
                    available_options[label] = result.id
            
            selected_labels = st.multiselect(
                "從篩選結果中選擇要比較的項目",
                options=list(available_options.keys()),
                key="advanced_comparison_select"
            )
            
            selected_ids = [available_options[label] for label in selected_labels]
        
        with col2:
            # 比較選項
            st.write("**比較選項**")
            show_comprehensive = st.checkbox("顯示綜合分析", value=True)
            show_radar = st.checkbox("顯示雷達圖", value=False)
            show_time_range = st.checkbox("顯示時間範圍", value=False)
        
        if len(selected_ids) < 2:
            st.warning("請選擇至少兩個結果進行比較")
            return
        
        # 顯示比較圖表
        if show_comprehensive:
            st.subheader("📊 綜合比較分析")
            comprehensive_chart = self.visualizer.create_comprehensive_comparison_chart(selected_ids)
            st.plotly_chart(comprehensive_chart, use_container_width=True)
        
        if show_radar:
            st.subheader("🎯 雷達圖比較")
            radar_chart = self.visualizer.create_radar_chart(selected_ids)
            st.plotly_chart(radar_chart, use_container_width=True)
        
        if show_time_range:
            st.subheader("⏱️ 時間範圍比較")
            time_chart = self.visualizer.create_time_range_comparison_chart(selected_ids)
            st.plotly_chart(time_chart, use_container_width=True)
        
        # 統計摘要
        st.subheader("📈 統計摘要")
        stats_summary = self.report_generator.generate_statistical_summary(selected_ids)
        
        if stats_summary:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**功率統計**")
                power_stats = stats_summary['power_stats']
                st.write(f"- 最小值: {power_stats['min']:.2f} mW")
                st.write(f"- 最大值: {power_stats['max']:.2f} mW")
                st.write(f"- 平均值: {power_stats['mean']:.2f} mW")
                st.write(f"- 標準差: {power_stats['std']:.2f} mW")
            
            with col2:
                st.write("**續航統計**")
                battery_stats = stats_summary['battery_stats']
                st.write(f"- 最小值: {battery_stats['min']:.1f} 小時")
                st.write(f"- 最大值: {battery_stats['max']:.1f} 小時")
                st.write(f"- 平均值: {battery_stats['mean']:.1f} 小時")
                st.write(f"- 標準差: {battery_stats['std']:.1f} 小時")
            
            with col3:
                st.write("**時間統計**")
                duration_stats = stats_summary['duration_stats']
                st.write(f"- 最小值: {duration_stats['min']:.1f} 秒")
                st.write(f"- 最大值: {duration_stats['max']:.1f} 秒")
                st.write(f"- 平均值: {duration_stats['mean']:.1f} 秒")
                st.write(f"- 標準差: {duration_stats['std']:.1f} 秒")
    
    def _render_all_results_comparison(self) -> None:
        """渲染全部結果比較"""
        st.subheader("🌐 全部結果比較")
        
        all_results = self.result_manager.get_all_results()
        all_ids = [result.id for result in all_results]
        
        if len(all_ids) < 2:
            st.warning("需要至少兩個結果才能進行比較")
            return
        
        # 顯示所有結果的綜合比較
        st.info(f"正在比較全部 {len(all_ids)} 個結果")
        
        # 綜合比較圖表
        comprehensive_chart = self.visualizer.create_comprehensive_comparison_chart(all_ids)
        st.plotly_chart(comprehensive_chart, use_container_width=True)
        
        # 雷達圖（如果結果不太多）
        if len(all_ids) <= 8:
            st.subheader("🎯 全部結果雷達圖")
            radar_chart = self.visualizer.create_radar_chart(all_ids)
            st.plotly_chart(radar_chart, use_container_width=True)
        
        # 完整比較表格
        st.subheader("📋 完整比較表格")
        comparison_df = self.report_generator.generate_comparison_table(all_ids)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # 統計摘要和建議
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 整體統計")
            stats_summary = self.report_generator.generate_statistical_summary(all_ids)
            
            if stats_summary:
                power_stats = stats_summary['power_stats']
                st.write(f"**功率範圍**: {power_stats['min']:.2f} - {power_stats['max']:.2f} mW")
                st.write(f"**平均功率**: {power_stats['mean']:.2f} ± {power_stats['std']:.2f} mW")
                
                battery_stats = stats_summary['battery_stats']
                st.write(f"**續航範圍**: {battery_stats['min']:.1f} - {battery_stats['max']:.1f} 小時")
                st.write(f"**平均續航**: {battery_stats['mean']:.1f} ± {battery_stats['std']:.1f} 小時")
        
        with col2:
            st.subheader("💡 整體建議")
            recommendations = self.report_generator.generate_recommendations(all_ids)
            for rec in recommendations:
                st.write(f"- {rec}")