#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的Streamlit測試應用
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 設定頁面配置
st.set_page_config(
    page_title="無線滑鼠耗電分析工具",
    page_icon="🖱️",
    layout="wide"
)

def main():
    st.title("🖱️ 無線滑鼠耗電分析工具")
    st.markdown("這是一個互動式的Web介面，用於分析無線滑鼠的耗電情況。")
    
    # 側邊欄
    with st.sidebar:
        st.header("📁 檔案上傳")
        uploaded_files = st.file_uploader(
            "選擇CSV檔案",
            type=['csv'],
            accept_multiple_files=True
        )
        
        st.header("⚙️ 設定")
        battery_capacity = st.number_input("電池容量 (mAh)", value=1000)
        battery_voltage = st.number_input("電池電壓 (V)", value=3.7)
    
    if uploaded_files:
        st.success(f"已上傳 {len(uploaded_files)} 個檔案")
        
        # 處理檔案
        data_dict = {}
        for uploaded_file in uploaded_files:
            try:
                df = pd.read_csv(uploaded_file)
                if len(df.columns) >= 4:
                    df.columns = ['Time', 'Voltage', 'Current', 'Power']
                    df = df.dropna()
                    df = df[df['Power'] >= 0]
                    
                    # 簡單的模式識別
                    filename = uploaded_file.name.lower()
                    if 'nolight' in filename or 'no light' in filename:
                        mode = '無燈光'
                    elif 'breath' in filename:
                        mode = '呼吸燈'
                    elif 'color' in filename:
                        mode = '彩色循環'
                    elif 'flash' in filename:
                        mode = '閃爍'
                    else:
                        mode = '未知模式'
                    
                    df['Mode'] = mode
                    data_dict[uploaded_file.name] = df
                    
            except Exception as e:
                st.error(f"處理檔案 {uploaded_file.name} 時發生錯誤：{str(e)}")
        
        if data_dict:
            # 顯示分析結果
            tab1, tab2 = st.tabs(["📊 總覽", "📈 詳細分析"])
            
            with tab1:
                st.header("分析總覽")
                
                # 統計表格
                stats_data = []
                for filename, df in data_dict.items():
                    avg_power_mw = df['Power'].mean() * 1000
                    max_power_mw = df['Power'].max() * 1000
                    avg_current_ma = df['Current'].mean() * 1000
                    duration = df['Time'].max() - df['Time'].min()
                    
                    # 電池續航估算
                    battery_energy_j = battery_capacity * battery_voltage * 3.6
                    hours = battery_energy_j / (df['Power'].mean() * 3600) if df['Power'].mean() > 0 else 0
                    
                    stats_data.append({
                        '檔案名稱': filename,
                        '模式': df['Mode'].iloc[0],
                        '平均功率 (mW)': f"{avg_power_mw:.2f}",
                        '最大功率 (mW)': f"{max_power_mw:.2f}",
                        '平均電流 (mA)': f"{avg_current_ma:.2f}",
                        '測量時間 (秒)': f"{duration:.1f}",
                        '預估續航 (小時)': f"{hours:.1f}"
                    })
                
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True)
                
                # 功率比較圖
                if len(data_dict) > 1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_power = px.bar(
                            stats_df,
                            x='模式',
                            y='平均功率 (mW)',
                            title='平均功率比較',
                            color='模式'
                        )
                        st.plotly_chart(fig_power, use_container_width=True)
                    
                    with col2:
                        fig_battery = px.bar(
                            stats_df,
                            x='模式',
                            y='預估續航 (小時)',
                            title='預估電池續航比較',
                            color='模式'
                        )
                        st.plotly_chart(fig_battery, use_container_width=True)
            
            with tab2:
                st.header("詳細分析")
                
                selected_file = st.selectbox("選擇檔案", list(data_dict.keys()))
                
                if selected_file:
                    df = data_dict[selected_file]
                    mode = df['Mode'].iloc[0]
                    
                    st.subheader(f"{mode} 模式詳細分析")
                    
                    # 功率時間序列圖
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['Time'],
                        y=df['Power'] * 1000,
                        mode='lines',
                        name='功率',
                        line=dict(color='blue')
                    ))
                    fig.update_layout(
                        title='功率時間序列',
                        xaxis_title='時間 (秒)',
                        yaxis_title='功率 (mW)',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 統計指標
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("平均功率", f"{df['Power'].mean()*1000:.2f} mW")
                    with col2:
                        st.metric("最大功率", f"{df['Power'].max()*1000:.2f} mW")
                    with col3:
                        st.metric("平均電流", f"{df['Current'].mean()*1000:.2f} mA")
                    with col4:
                        st.metric("測量時間", f"{df['Time'].max()-df['Time'].min():.1f} 秒")
    
    else:
        st.info("請在左側邊欄上傳CSV檔案開始分析")
        
        st.markdown("""
        ### 📁 檔案格式要求
        
        CSV檔案應包含以下欄位：
        - Time: 時間戳記（秒）
        - Voltage: 電壓（伏特）
        - Current: 電流（安培）
        - Power: 功率（瓦特）
        
        ### 🚀 功能特色
        
        - 自動模式識別
        - 互動式圖表
        - 即時分析
        - 比較分析
        - 電池續航估算
        """)

if __name__ == "__main__":
    main()