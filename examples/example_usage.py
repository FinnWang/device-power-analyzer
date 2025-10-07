#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
無線滑鼠耗電分析工具 - 使用範例

這個腳本展示了如何使用 MousePowerAnalyzer 進行各種分析
"""

from mouse_power_analyzer import MousePowerAnalyzer
import os

def example_single_file_analysis():
    """範例1: 單檔分析"""
    print("=== 範例1: 單檔分析 ===")
    
    analyzer = MousePowerAnalyzer()
    
    # 載入單一檔案
    file_path = '../sample_data/MD103Flash2025-10-020.csv'
    if os.path.exists(file_path):
        df = analyzer.load_csv_file(file_path)
        
        if df is not None:
            # 計算統計數據
            stats = analyzer.calculate_statistics(df)
            
            print(f"模式: {stats['mode_cn']}")
            print(f"平均功率: {stats['avg_power_mW']:.2f} mW")
            print(f"測量時間: {stats['duration_s']:.1f} 秒")
            print(f"資料點數: {stats['data_points']} 筆")
            
            # 估算電池續航
            battery_life = analyzer.estimate_battery_life(stats['avg_power_W'])
            print(f"預估續航: {battery_life['hours']:.1f} 小時")
            
            # 建立分析圖表
            output_file = analyzer.create_single_analysis(df, '../results_example1')
            print(f"圖表已儲存: {output_file}")
        else:
            print("檔案載入失敗")
    else:
        print(f"檔案不存在: {file_path}")

def example_multi_file_comparison():
    """範例2: 多檔比較分析"""
    print("\n=== 範例2: 多檔比較分析 ===")
    
    analyzer = MousePowerAnalyzer()
    
    # 多個檔案路徑
    file_paths = [
        '../sample_data/MD103Nolight2025-10-020.csv',
        '../sample_data/MD103Breath2025-10-020.csv',
        '../sample_data/MD103Flash2025-10-020.csv'
    ]
    
    # 檢查檔案是否存在
    existing_files = [f for f in file_paths if os.path.exists(f)]
    
    if len(existing_files) >= 2:
        # 執行比較分析
        data_dict, generated_files = analyzer.analyze_files(existing_files, '../results_example2')
        
        print(f"成功分析 {len(data_dict)} 個模式")
        print(f"生成 {len(generated_files)} 個圖表檔案")
        
        # 顯示比較結果
        print("\n功率比較:")
        for mode, df in data_dict.items():
            stats = analyzer.calculate_statistics(df)
            print(f"  {stats['mode_cn']}: {stats['avg_power_mW']:.2f} mW")
    else:
        print("需要至少2個檔案進行比較分析")

def example_custom_battery_calculation():
    """範例3: 自訂電池規格計算"""
    print("\n=== 範例3: 自訂電池規格計算 ===")
    
    analyzer = MousePowerAnalyzer()
    
    # 不同的功率值
    power_values = [0.005, 0.08, 0.11]  # 瓦特
    mode_names = ['無燈光', '呼吸燈', '閃爍']
    
    # 不同電池規格
    battery_configs = [
        {'capacity': 1000, 'voltage': 3.7, 'name': '標準電池'},
        {'capacity': 2000, 'voltage': 3.8, 'name': '大容量電池'},
        {'capacity': 500, 'voltage': 3.6, 'name': '小型電池'}
    ]
    
    print("不同電池規格的續航比較:")
    print(f"{'模式':<8} {'功率(mW)':<10} {'標準電池':<12} {'大容量電池':<12} {'小型電池':<12}")
    print("-" * 60)
    
    for power, mode in zip(power_values, mode_names):
        row = f"{mode:<8} {power*1000:<10.1f}"
        
        for config in battery_configs:
            battery_life = analyzer.estimate_battery_life(
                power, 
                config['capacity'], 
                config['voltage']
            )
            row += f" {battery_life['hours']:<12.1f}"
        
        print(row)

def example_data_processing():
    """範例4: 資料處理和統計"""
    print("\n=== 範例4: 資料處理和統計 ===")
    
    analyzer = MousePowerAnalyzer()
    
    file_path = '../sample_data/MD103Colorcycle2025-10-020.csv'
    if os.path.exists(file_path):
        df = analyzer.load_csv_file(file_path)
        
        if df is not None:
            print(f"原始資料形狀: {df.shape}")
            print(f"時間範圍: {df['Time'].min():.1f} - {df['Time'].max():.1f} 秒")
            
            # 基本統計
            print(f"\n功率統計 (mW):")
            power_mw = df['Power'] * 1000
            print(f"  平均值: {power_mw.mean():.2f}")
            print(f"  中位數: {power_mw.median():.2f}")
            print(f"  標準差: {power_mw.std():.2f}")
            print(f"  最小值: {power_mw.min():.2f}")
            print(f"  最大值: {power_mw.max():.2f}")
            
            # 百分位數
            percentiles = [25, 50, 75, 90, 95]
            print(f"\n功率百分位數 (mW):")
            for p in percentiles:
                value = power_mw.quantile(p/100)
                print(f"  {p}%: {value:.2f}")
            
            # 計算能量消耗
            import numpy as np
            total_energy = np.trapz(df['Power'], df['Time'])
            print(f"\n總能量消耗: {total_energy:.3f} J")
            print(f"平均功率: {total_energy/(df['Time'].max()-df['Time'].min()):.6f} W")

def example_custom_colors_and_names():
    """範例5: 自訂顏色和名稱"""
    print("\n=== 範例5: 自訂顏色和名稱 ===")
    
    analyzer = MousePowerAnalyzer()
    
    # 自訂顏色主題
    analyzer.colors.update({
        'Nolight': '#2C3E50',     # 深藍灰
        'Breath': '#3498DB',      # 藍色
        'Colorcycle': '#E74C3C',  # 紅色
        'Flash': '#F39C12'        # 橙色
    })
    
    # 自訂模式名稱
    analyzer.mode_names.update({
        'Nolight': '省電模式',
        'Breath': '呼吸效果',
        'Colorcycle': '彩虹循環',
        'Flash': '閃爍效果'
    })
    
    print("已更新顏色主題和模式名稱")
    print("顏色配置:", analyzer.colors)
    print("名稱配置:", analyzer.mode_names)

if __name__ == "__main__":
    print("無線滑鼠耗電分析工具 - 使用範例")
    print("=" * 50)
    
    # 執行所有範例
    try:
        example_single_file_analysis()
        example_multi_file_comparison()
        example_custom_battery_calculation()
        example_data_processing()
        example_custom_colors_and_names()
        
        print("\n所有範例執行完成！")
        
    except Exception as e:
        print(f"執行過程中發生錯誤: {e}")
        print("請確認:")
        print("1. 範例資料檔案存在於 ../sample_data/ 目錄")
        print("2. 已安裝必要的Python套件")
        print("3. 有足夠的磁碟空間儲存結果")
