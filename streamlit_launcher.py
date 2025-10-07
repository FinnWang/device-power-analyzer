#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit應用啟動器 - 解決模組導入問題
"""

import sys
import os
from pathlib import Path

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 設定環境變數
os.environ['PYTHONPATH'] = str(src_dir)

# 現在導入Streamlit應用
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import tempfile
import zipfile
from datetime import datetime

# 導入我們的分析模組
from mouse_power_analyzer.analyzer import MousePowerAnalyzer
from mouse_power_analyzer.utils import calculate_battery_life, detect_mode_from_filename

# 設定頁面配置
st.set_page_config(
    page_title="無線滑鼠耗電分析工具",
    page_icon="🖱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MousePowerAnalyzer()
if 'data_dict' not in st.session_state:
    st.session_state.data_dict = {}
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def main():
    """主函數"""
    
    # 標題和說明
    st.title("🖱️ 無線滑鼠耗電分析工具")
    st.markdown("""
    這個工具可以幫你分析無線滑鼠在不同發光模式下的耗電情況。
    只需要上傳CSV檔案，就能獲得詳細的分析報告和視覺化圖表。
    """)
    
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
    
    # 主要內容區域
    if uploaded_files:
        # 處理上傳的檔案
        process_uploaded_files(uploaded_files, battery_capacity, battery_voltage)
        
        if st.session_state.analysis_complete:
            # 顯示分析結果
            display_analysis_results(chart_theme, show_statistics, show_comparison)
    else:
        # 顯示範例和說明
        display_welcome_page()

def process_uploaded_files(uploaded_files, battery_capacity, battery_voltage):
    """處理上傳的檔案"""
    
    with st.spinner("正在處理檔案..."):
        data_dict = {}
        
        for uploaded_file in uploaded_files:
            try:
                # 讀取CSV檔案
                df = pd.read_csv(uploaded_file)
                
                # 檢查檔案格式
                if len(df.columns) >= 4:
                    df.columns = ['Time', 'Voltage', 'Current', 'Power']
                else:
                    st.error(f"檔案 {uploaded_file.name} 格式不正確，需要至少4個欄位")
                    continue
                
                # 推測模式
                mode_name = detect_mode_from_filename(uploaded_file.name)
                
                # 資料清理
                df = df.dropna()
                df = df[df['Power'] >= 0]
                df['Mode'] = mode_name
                df['Mode_CN'] = st.session_state.analyzer.mode_names.get(mode_name, mode_name)
                
                data_dict[uploaded_file.name] = df
                
            except Exception as e:
                st.error(f"處理檔案 {uploaded_file.name} 時發生錯誤：{str(e)}")
        
        if data_dict:
            st.session_state.data_dict = data_dict
            st.session_state.analysis_complete = True
            st.success(f"成功載入 {len(data_dict)} 個檔案！")
        else:
            st.error("沒有成功載入任何檔案")

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
2. **視覺效果**: 如需發光效果，選擇功耗較低的模式
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

def display_welcome_page():
    """顯示歡迎頁面"""
    
    st.header("👋 歡迎使用無線滑鼠耗電分析工具")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 快速開始
        
        1. **上傳檔案**: 在左側邊欄選擇一個或多個CSV檔案
        2. **設定參數**: 調整電池容量和電壓設定
        3. **查看結果**: 系統會自動分析並顯示結果
        
        ### 📊 功能特色
        
        - **自動模式識別**: 自動識別無燈光、呼吸燈、彩色循環、閃爍模式
        - **互動式圖表**: 使用Plotly提供豐富的互動體驗
        - **即時分析**: 上傳檔案後立即獲得分析結果
        - **比較分析**: 支援多檔案同時比較
        - **報告匯出**: 可下載詳細的分析報告
        
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
        """)
        
        st.success("""
        ✅ **支援的模式**
        
        - 無燈光 (Nolight)
        - 呼吸燈 (Breath)  
        - 彩色循環 (Colorcycle)
        - 閃爍 (Flash)
        """)

if __name__ == "__main__":
    main()