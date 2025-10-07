#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Power Analyzer - 命令列介面

提供命令列操作功能
"""

import argparse
import sys
from pathlib import Path
from typing import List

from .analyzer import MousePowerAnalyzer
from .visualizer import PowerVisualizer


def main():
    """命令列主函數"""
    
    parser = argparse.ArgumentParser(
        description='無線滑鼠耗電分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s file1.csv file2.csv                    # 分析指定檔案
  %(prog)s -d ./database -o ./results             # 分析目錄中的所有CSV檔案
  %(prog)s --quick                                # 快速分析database目錄
  %(prog)s --version                              # 顯示版本資訊
        """
    )
    
    # 基本參數
    parser.add_argument('files', nargs='*', help='CSV檔案路徑')
    parser.add_argument('-d', '--directory', help='包含CSV檔案的目錄')
    parser.add_argument('-o', '--output', default='./analysis_results', help='輸出目錄 (預設: ./analysis_results)')
    
    # 分析選項
    parser.add_argument('--no-charts', action='store_true', help='不生成圖表')
    parser.add_argument('--single-only', action='store_true', help='只進行單檔分析')
    parser.add_argument('--comparison-only', action='store_true', help='只進行比較分析')
    
    # 便利選項
    parser.add_argument('--quick', action='store_true', help='快速分析database目錄')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    # 進階選項
    parser.add_argument('--battery-capacity', type=int, default=1000, help='電池容量 (mAh, 預設: 1000)')
    parser.add_argument('--battery-voltage', type=float, default=3.7, help='電池電壓 (V, 預設: 3.7)')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    # 處理快速分析
    if args.quick:
        args.directory = './database'
        args.output = './analysis_results'
    
    # 收集檔案路徑
    file_paths = collect_file_paths(args)
    
    if not file_paths:
        print("錯誤：沒有找到CSV檔案")
        print("使用 --help 查看使用說明")
        sys.exit(1)
    
    # 執行分析
    try:
        run_analysis(file_paths, args)
    except KeyboardInterrupt:
        print("\n分析被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"分析過程中發生錯誤: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def collect_file_paths(args) -> List[Path]:
    """收集要分析的檔案路徑"""
    
    file_paths = []
    
    # 從目錄載入
    if args.directory:
        directory = Path(args.directory)
        if not directory.exists():
            print(f"錯誤：目錄不存在 - {args.directory}")
            sys.exit(1)
        
        csv_files = list(directory.glob("*.csv"))
        if csv_files:
            file_paths.extend(csv_files)
            if args.verbose:
                print(f"從目錄 {directory} 找到 {len(csv_files)} 個CSV檔案")
        else:
            print(f"警告：目錄 {directory} 中沒有找到CSV檔案")
    
    # 從命令列參數載入
    if args.files:
        for filepath in args.files:
            path = Path(filepath)
            if path.exists():
                file_paths.append(path)
            else:
                print(f"警告：檔案不存在 - {filepath}")
    
    # 如果沒有指定檔案，嘗試預設目錄
    if not file_paths and not args.directory and not args.files:
        database_dir = Path("./database")
        if database_dir.exists():
            csv_files = list(database_dir.glob("*.csv"))
            if csv_files:
                file_paths.extend(csv_files)
                print(f"使用預設目錄：{database_dir}")
            else:
                print("預設目錄中沒有找到CSV檔案")
    
    return file_paths


def run_analysis(file_paths: List[Path], args):
    """執行分析"""
    
    print("=== 無線滑鼠耗電分析工具 ===")
    
    if args.verbose:
        print(f"分析檔案數量: {len(file_paths)}")
        print(f"輸出目錄: {args.output}")
        print(f"電池規格: {args.battery_capacity}mAh, {args.battery_voltage}V")
    
    # 建立分析器
    analyzer = MousePowerAnalyzer()
    
    # 載入和分析資料
    data_dict, _ = analyzer.analyze_files([str(f) for f in file_paths], args.output)
    
    if not data_dict:
        print("分析失敗：沒有成功載入任何資料")
        sys.exit(1)
    
    generated_files = []
    
    # 生成圖表
    if not args.no_charts:
        visualizer = PowerVisualizer()
        
        # 單檔分析
        if not args.comparison_only and (len(data_dict) == 1 or not args.single_only):
            if args.verbose:
                print("生成單檔分析圖表...")
            
            for mode, df in data_dict.items():
                chart_file = visualizer.create_single_analysis(df, args.output)
                generated_files.append(chart_file)
        
        # 比較分析
        if not args.single_only and len(data_dict) > 1:
            if args.verbose:
                print("生成比較分析圖表...")
            
            chart_file = visualizer.create_comparison_analysis(data_dict, args.output)
            generated_files.append(chart_file)
    
    # 輸出結果摘要
    print_analysis_summary(data_dict, args)
    
    if generated_files:
        print(f"\n✅ 分析完成！")
        print(f"📊 生成了 {len(generated_files)} 個圖表檔案")
        print(f"📁 結果儲存在：{Path(args.output).absolute()}")
        
        if args.verbose:
            print("\n生成的檔案:")
            for file in generated_files:
                print(f"  - {file}")


def print_analysis_summary(data_dict, args):
    """輸出分析摘要"""
    
    from .utils import calculate_battery_life
    
    print("\n=== 分析結果摘要 ===")
    
    # 按功率排序
    sorted_modes = sorted(data_dict.items(), 
                         key=lambda x: x[1]['Power'].mean(), 
                         reverse=True)
    
    for mode, df in sorted_modes:
        stats = {
            'avg_power_W': df['Power'].mean(),
            'avg_power_mW': df['Power'].mean() * 1000,
            'duration_s': df['Time'].max() - df['Time'].min(),
            'data_points': len(df)
        }
        
        battery_life = calculate_battery_life(
            stats['avg_power_W'], 
            args.battery_capacity, 
            args.battery_voltage
        )
        
        mode_cn = df['Mode_CN'].iloc[0]
        
        print(f"\n{mode_cn}：")
        print(f"  平均功率：{stats['avg_power_mW']:.2f} mW")
        print(f"  測量時間：{stats['duration_s']:.1f} 秒")
        print(f"  資料點數：{stats['data_points']} 筆")
        print(f"  預估續航：{battery_life['hours']:.1f} 小時 ({battery_life['days']:.1f} 天)")
    
    # 比較分析
    if len(data_dict) > 1:
        powers = [df['Power'].mean() * 1000 for df in data_dict.values()]
        modes = [df['Mode_CN'].iloc[0] for df in data_dict.values()]
        
        max_idx = powers.index(max(powers))
        min_idx = powers.index(min(powers))
        
        print(f"\n比較摘要:")
        print(f"  最高功耗：{modes[max_idx]} ({powers[max_idx]:.2f} mW)")
        print(f"  最低功耗：{modes[min_idx]} ({powers[min_idx]:.2f} mW)")
        print(f"  功耗差異：{max(powers) - min(powers):.2f} mW ({((max(powers) - min(powers))/min(powers)*100):.1f}%)")


if __name__ == "__main__":
    main()