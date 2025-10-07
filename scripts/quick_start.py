#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
無線滑鼠耗電分析工具 - 快速啟動腳本
自動分析database目錄中的所有CSV檔案
"""

import os
import sys
from pathlib import Path

def main():
    """快速啟動分析"""
    
    print("=== 無線滑鼠耗電分析工具 - 快速啟動 ===")
    
    # 檢查database目錄
    database_dir = Path("./database")
    if not database_dir.exists():
        print("錯誤：找不到database目錄")
        print("請確認database目錄存在且包含CSV檔案")
        return
    
    # 尋找CSV檔案
    csv_files = list(database_dir.glob("*.csv"))
    if not csv_files:
        print("錯誤：database目錄中沒有CSV檔案")
        return
    
    print(f"找到 {len(csv_files)} 個CSV檔案：")
    for file in csv_files:
        print(f"  - {file.name}")
    
    # 建立輸出目錄
    output_dir = Path("./analysis_results")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n開始分析，結果將儲存至：{output_dir}")
    
    try:
        # 導入並執行分析
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from mouse_power_analyzer import MousePowerAnalyzer
        from mouse_power_analyzer.visualizer import PowerVisualizer
        
        analyzer = MousePowerAnalyzer()
        visualizer = PowerVisualizer()
        
        # 執行分析
        data_dict, _ = analyzer.analyze_files([str(f) for f in csv_files], str(output_dir))
        
        # 生成圖表
        generated_files = []
        if data_dict:
            if len(data_dict) > 1:
                chart_file = visualizer.create_comparison_analysis(data_dict, str(output_dir))
                generated_files.append(chart_file)
            
            for mode, df in data_dict.items():
                chart_file = visualizer.create_single_analysis(df, str(output_dir))
                generated_files.append(chart_file)
        
        if data_dict and generated_files:
            print(f"\n✅ 分析完成！")
            print(f"📊 生成了 {len(generated_files)} 個圖表檔案")
            print(f"📁 結果儲存在：{output_dir.absolute()}")
            
            # 詢問是否開啟結果目錄
            try:
                response = input("\n是否要開啟結果目錄？(y/n): ").lower().strip()
                if response in ['y', 'yes', '是']:
                    if sys.platform == "win32":
                        os.startfile(str(output_dir))
                    elif sys.platform == "darwin":
                        os.system(f"open '{output_dir}'")
                    else:
                        os.system(f"xdg-open '{output_dir}'")
            except KeyboardInterrupt:
                print("\n程式結束")
        else:
            print("❌ 分析失敗")
            
    except ImportError as e:
        print(f"❌ 導入錯誤：{e}")
        print("請確認integrated_analyzer.py檔案存在")
    except Exception as e:
        print(f"❌ 執行錯誤：{e}")

if __name__ == "__main__":
    main()