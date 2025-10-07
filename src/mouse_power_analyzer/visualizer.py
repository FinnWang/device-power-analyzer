#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mouse Power Analyzer - 視覺化模組

提供各種圖表生成功能
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Union

try:
    from .utils import get_default_colors, get_mode_names, calculate_battery_life
except ImportError:
    from utils import get_default_colors, get_mode_names, calculate_battery_life


class PowerVisualizer:
    """功率視覺化工具"""
    
    def __init__(self):
        """初始化視覺化工具"""
        self.colors = get_default_colors()
        self.mode_names = get_mode_names()
    
    def create_single_analysis(self, df: pd.DataFrame, output_dir: Union[str, Path] = './') -> str:
        """
        建立單檔分析圖表
        
        Args:
            df: 資料DataFrame
            output_dir: 輸出目錄
            
        Returns:
            生成的圖表檔案路徑
        """
        mode = df['Mode'].iloc[0]
        mode_cn = df['Mode_CN'].iloc[0]
        color = self.colors.get(mode, '#1f77b4')
        
        Path(output_dir).mkdir(exist_ok=True)
        
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(f'{mode_cn} 模式 - 詳細耗電分析', fontsize=18, fontweight='bold')
        
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. 功率時間序列
        ax1 = fig.add_subplot(gs[0, :2])
        ax1.plot(df['Time'], df['Power']*1000, color=color, linewidth=1.5, alpha=0.8)
        mean_power = df['Power'].mean() * 1000
        ax1.axhline(y=mean_power, color='red', linestyle='--', alpha=0.7, 
                   label=f'平均值: {mean_power:.2f} mW')
        ax1.set_title('功率變化時間序列', fontweight='bold')
        ax1.set_xlabel('時間 (秒)')
        ax1.set_ylabel('功率 (mW)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 統計摘要
        ax2 = fig.add_subplot(gs[0, 2])
        stats = self._calculate_display_stats(df)
        battery_life = calculate_battery_life(stats['avg_power_W'])
        
        stats_text = f"""統計摘要：

平均功率：{stats['avg_power_mW']:.2f} mW
最大功率：{stats['max_power_mW']:.2f} mW
最小功率：{stats['min_power_mW']:.2f} mW
標準差：{stats['std_power_mW']:.2f} mW

平均電流：{stats['avg_current_mA']:.2f} mA
平均電壓：{stats['avg_voltage_V']:.3f} V

測量時間：{stats['duration_s']:.1f} 秒
資料點數：{stats['data_points']} 筆

總消耗能量：{stats['total_energy_J']:.3f} J

預估續航 (1000mAh)：
{battery_life['hours']:.1f} 小時
{battery_life['days']:.1f} 天"""
        
        ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, 
                 fontsize=9, verticalalignment='top', 
                 bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        
        # 3-8. 其他圖表
        self._add_detailed_charts(fig, gs, df, color)
        
        plt.tight_layout()
        filename = f'{output_dir}/{mode}_detailed_analysis.png'
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        plt.close()
        
        return filename
    
    def create_comparison_analysis(self, data_dict: Dict[str, pd.DataFrame], output_dir: Union[str, Path] = './') -> str:
        """
        建立多檔比較分析圖表
        
        Args:
            data_dict: 資料字典
            output_dir: 輸出目錄
            
        Returns:
            生成的圖表檔案路徑
        """
        Path(output_dir).mkdir(exist_ok=True)
        
        fig = plt.figure(figsize=(20, 16))
        fig.suptitle('無線滑鼠不同發光模式耗電分析報告', fontsize=20, fontweight='bold', y=0.98)
        
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        modes = list(data_dict.keys())
        mode_names_cn = [data_dict[mode]['Mode_CN'].iloc[0] for mode in modes]
        colors = [self.colors.get(mode, '#1f77b4') for mode in modes]
        
        # 1. 平均功率比較
        self._create_power_comparison(fig, gs[0, 0], data_dict, modes, mode_names_cn, colors)
        
        # 2. 電池續航估算
        self._create_battery_comparison(fig, gs[0, 1], data_dict, modes, mode_names_cn, colors)
        
        # 3. 功率分布箱型圖
        self._create_power_distribution(fig, gs[0, 2:], data_dict, modes, mode_names_cn, colors)
        
        # 4. 時間序列比較
        self._create_time_series_comparison(fig, gs[1, :], data_dict, modes)
        
        # 5-8. 個別模式圖表
        self._create_individual_mode_charts(fig, gs, data_dict, modes, colors)
        
        plt.tight_layout()
        comparison_file = f'{output_dir}/comprehensive_comparison.png'
        plt.savefig(comparison_file, bbox_inches='tight', dpi=300)
        plt.close()
        
        return comparison_file
    
    def _calculate_display_stats(self, df: pd.DataFrame) -> Dict:
        """計算顯示用的統計數據"""
        duration = df['Time'].max() - df['Time'].min()
        total_energy = np.trapz(df['Power'], df['Time'])
        
        return {
            'duration_s': duration,
            'data_points': len(df),
            'avg_voltage_V': df['Voltage'].mean(),
            'avg_current_mA': df['Current'].mean() * 1000,
            'avg_power_W': df['Power'].mean(),
            'avg_power_mW': df['Power'].mean() * 1000,
            'max_power_mW': df['Power'].max() * 1000,
            'min_power_mW': df['Power'].min() * 1000,
            'std_power_mW': df['Power'].std() * 1000,
            'total_energy_J': total_energy,
        }
    
    def _add_detailed_charts(self, fig, gs, df: pd.DataFrame, color: str):
        """添加詳細圖表"""
        
        # 3. 電流時間序列
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(df['Time'], df['Current']*1000, color=color, linewidth=1.5, alpha=0.8)
        ax3.set_title('電流變化', fontweight='bold')
        ax3.set_xlabel('時間 (秒)')
        ax3.set_ylabel('電流 (mA)')
        ax3.grid(True, alpha=0.3)
        
        # 4. 功率分布直方圖
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.hist(df['Power']*1000, bins=40, color=color, alpha=0.7, edgecolor='black')
        ax4.set_title('功率分布', fontweight='bold')
        ax4.set_xlabel('功率 (mW)')
        ax4.set_ylabel('頻次')
        ax4.grid(True, alpha=0.3)
        
        # 5. 累積能量消耗
        ax5 = fig.add_subplot(gs[1, 2])
        time_intervals = np.diff(np.concatenate([[0], df['Time']]))
        cumulative_energy = np.cumsum(df['Power'] * time_intervals)
        ax5.plot(df['Time'], cumulative_energy, color=color, linewidth=2)
        ax5.set_title('累積能量消耗', fontweight='bold')
        ax5.set_xlabel('時間 (秒)')
        ax5.set_ylabel('累積能量 (J)')
        ax5.grid(True, alpha=0.3)
        
        # 6. 功率變化率
        ax6 = fig.add_subplot(gs[2, 0])
        if len(df) > 1:
            power_diff = np.diff(df['Power'])
            time_diff = np.diff(df['Time'])
            power_rate = power_diff / time_diff
            ax6.plot(df['Time'][1:], power_rate*1000, color=color, alpha=0.7)
        ax6.set_title('功率變化率', fontweight='bold')
        ax6.set_xlabel('時間 (秒)')
        ax6.set_ylabel('功率變化率 (mW/s)')
        ax6.grid(True, alpha=0.3)
        
        # 7. 電壓穩定性
        ax7 = fig.add_subplot(gs[2, 1])
        ax7.plot(df['Time'], df['Voltage'], color=color, linewidth=1.5, alpha=0.8)
        ax7.set_title('電壓穩定性', fontweight='bold')
        ax7.set_xlabel('時間 (秒)')
        ax7.set_ylabel('電壓 (V)')
        ax7.grid(True, alpha=0.3)
        
        # 8. 功率 vs 電流散點圖
        ax8 = fig.add_subplot(gs[2, 2])
        ax8.scatter(df['Current']*1000, df['Power']*1000, color=color, alpha=0.6, s=10)
        ax8.set_title('功率 vs 電流關係', fontweight='bold')
        ax8.set_xlabel('電流 (mA)')
        ax8.set_ylabel('功率 (mW)')
        ax8.grid(True, alpha=0.3)
    
    def _create_power_comparison(self, fig, gs_pos, data_dict, modes, mode_names_cn, colors):
        """建立功率比較圖"""
        ax = fig.add_subplot(gs_pos)
        avg_powers = [data_dict[mode]['Power'].mean()*1000 for mode in modes]
        bars = ax.bar(mode_names_cn, avg_powers, color=colors, alpha=0.8, edgecolor='black')
        ax.set_title('平均功率比較', fontweight='bold')
        ax.set_ylabel('平均功率 (mW)')
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar, power in zip(bars, avg_powers):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{power:.1f}', ha='center', va='bottom', fontweight='bold')
    
    def _create_battery_comparison(self, fig, gs_pos, data_dict, modes, mode_names_cn, colors):
        """建立電池續航比較圖"""
        ax = fig.add_subplot(gs_pos)
        battery_hours = []
        for mode in modes:
            avg_power_W = data_dict[mode]['Power'].mean()
            battery_life = calculate_battery_life(avg_power_W)
            battery_hours.append(battery_life['hours'])
        
        bars = ax.bar(mode_names_cn, battery_hours, color=colors, alpha=0.8, edgecolor='black')
        ax.set_title('預估電池續航 (1000mAh)', fontweight='bold')
        ax.set_ylabel('續航時間 (小時)')
        ax.grid(True, alpha=0.3, axis='y')
        
        for bar, hours in zip(bars, battery_hours):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                    f'{hours:.0f}h', ha='center', va='bottom', fontweight='bold')
    
    def _create_power_distribution(self, fig, gs_pos, data_dict, modes, mode_names_cn, colors):
        """建立功率分布箱型圖"""
        ax = fig.add_subplot(gs_pos)
        power_data = [data_dict[mode]['Power']*1000 for mode in modes]
        bp = ax.boxplot(power_data, labels=mode_names_cn, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_title('功率分布比較', fontweight='bold')
        ax.set_ylabel('功率 (mW)')
        ax.grid(True, alpha=0.3, axis='y')
    
    def _create_time_series_comparison(self, fig, gs_pos, data_dict, modes):
        """建立時間序列比較圖"""
        ax = fig.add_subplot(gs_pos)
        for mode in modes:
            df = data_dict[mode]
            time_norm = (df['Time'] - df['Time'].min()) / (df['Time'].max() - df['Time'].min()) * 100
            ax.plot(time_norm, df['Power']*1000, 
                    color=self.colors.get(mode, '#1f77b4'), 
                    label=df['Mode_CN'].iloc[0], alpha=0.8, linewidth=2)
        
        ax.set_title('功率時間序列比較', fontweight='bold', fontsize=14)
        ax.set_xlabel('時間進度 (%)')
        ax.set_ylabel('功率 (mW)')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
    
    def _create_individual_mode_charts(self, fig, gs, data_dict, modes, colors):
        """建立個別模式圖表"""
        for i, mode in enumerate(modes):
            if i >= 4:  # 最多顯示4個模式
                break
                
            df = data_dict[mode]
            mode_cn = df['Mode_CN'].iloc[0]
            color = colors[i]
            
            # 功率時間序列
            ax = fig.add_subplot(gs[2, i])
            ax.plot(df['Time'], df['Power']*1000, color=color, linewidth=1, alpha=0.8)
            ax.set_title(f'{mode_cn}\n功率變化', fontweight='bold')
            ax.set_xlabel('時間 (秒)')
            ax.set_ylabel('功率 (mW)')
            ax.grid(True, alpha=0.3)
            
            # 功率分布直方圖
            ax = fig.add_subplot(gs[3, i])
            ax.hist(df['Power']*1000, bins=30, color=color, alpha=0.7, edgecolor='black')
            ax.set_title(f'{mode_cn}\n功率分布', fontweight='bold')
            ax.set_xlabel('功率 (mW)')
            ax.set_ylabel('頻次')
            ax.grid(True, alpha=0.3)