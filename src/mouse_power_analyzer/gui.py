#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
無線滑鼠耗電分析 GUI 工具
整合所有分析功能的圖形化介面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from pathlib import Path
import threading
import queue
import os
import sys
from datetime import datetime

# 導入現有的分析模組
try:
    from mouse_power_analyzer import MousePowerAnalyzer
except ImportError:
    print("警告：無法導入 mouse_power_analyzer，將使用內建分析功能")
    MousePowerAnalyzer = None

class MousePowerGUI:
    """無線滑鼠耗電分析 GUI 主類別"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("無線滑鼠耗電分析工具 v1.0")
        self.root.geometry("1200x800")
        
        # 初始化變數
        self.analyzer = MousePowerAnalyzer() if MousePowerAnalyzer else None
        self.loaded_files = {}
        self.analysis_results = {}
        self.output_dir = "./gui_analysis_results"
        
        # 建立輸出目錄
        Path(self.output_dir).mkdir(exist_ok=True)
        
        # 設定樣式
        self.setup_styles()
        
        # 建立GUI元件
        self.create_widgets()
        
        # 初始化狀態
        self.update_status("就緒 - 請載入CSV檔案開始分析")
    
    def setup_styles(self):
        """設定GUI樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自訂樣式
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
    
    def create_widgets(self):
        """建立GUI元件"""
        
        # 主標題
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(title_frame, text="無線滑鼠耗電分析工具", 
                 style='Title.TLabel').pack()
        
        # 建立筆記本（分頁）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 分頁1: 檔案載入與基本資訊
        self.create_file_tab()
        
        # 分頁2: 單檔分析
        self.create_single_analysis_tab()
        
        # 分頁3: 多檔比較
        self.create_comparison_tab()
        
        # 分頁4: 報告生成
        self.create_report_tab()
        
        # 狀態列
        self.create_status_bar()
    
    def create_file_tab(self):
        """建立檔案載入分頁"""
        
        file_frame = ttk.Frame(self.notebook)
        self.notebook.add(file_frame, text="檔案管理")
        
        # 檔案載入區域
        load_frame = ttk.LabelFrame(file_frame, text="檔案載入", padding=10)
        load_frame.pack(fill='x', padx=10, pady=5)
        
        # 按鈕區域
        btn_frame = ttk.Frame(load_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="載入單一檔案", 
                  command=self.load_single_file).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="載入多個檔案", 
                  command=self.load_multiple_files).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="載入資料夾", 
                  command=self.load_folder).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清除所有檔案", 
                  command=self.clear_files).pack(side='left', padx=5)
        
        # 已載入檔案列表
        list_frame = ttk.LabelFrame(file_frame, text="已載入檔案", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 建立樹狀檢視
        columns = ('檔案名稱', '模式', '資料點數', '時間範圍', '平均功率')
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=120)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 檔案操作按鈕
        file_btn_frame = ttk.Frame(list_frame)
        file_btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(file_btn_frame, text="檢視資料", 
                  command=self.view_data).pack(side='left', padx=5)
        ttk.Button(file_btn_frame, text="移除選中", 
                  command=self.remove_selected).pack(side='left', padx=5)
    
    def create_single_analysis_tab(self):
        """建立單檔分析分頁"""
        
        single_frame = ttk.Frame(self.notebook)
        self.notebook.add(single_frame, text="單檔分析")
        
        # 檔案選擇
        select_frame = ttk.LabelFrame(single_frame, text="選擇分析檔案", padding=10)
        select_frame.pack(fill='x', padx=10, pady=5)
        
        self.single_file_var = tk.StringVar()
        self.single_file_combo = ttk.Combobox(select_frame, textvariable=self.single_file_var, 
                                             state='readonly', width=50)
        self.single_file_combo.pack(side='left', padx=5)
        
        ttk.Button(select_frame, text="開始分析", 
                  command=self.run_single_analysis).pack(side='left', padx=5)
        
        # 分析選項
        options_frame = ttk.LabelFrame(single_frame, text="分析選項", padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        self.include_detailed = tk.BooleanVar(value=True)
        self.include_statistics = tk.BooleanVar(value=True)
        self.include_battery = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="詳細分析圖表", 
                       variable=self.include_detailed).pack(side='left', padx=10)
        ttk.Checkbutton(options_frame, text="統計摘要", 
                       variable=self.include_statistics).pack(side='left', padx=10)
        ttk.Checkbutton(options_frame, text="電池續航估算", 
                       variable=self.include_battery).pack(side='left', padx=10)
        
        # 結果顯示區域
        result_frame = ttk.LabelFrame(single_frame, text="分析結果", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.single_result_text = scrolledtext.ScrolledText(result_frame, height=15)
        self.single_result_text.pack(fill='both', expand=True)
    
    def create_comparison_tab(self):
        """建立多檔比較分頁"""
        
        comp_frame = ttk.Frame(self.notebook)
        self.notebook.add(comp_frame, text="多檔比較")
        
        # 檔案選擇
        select_frame = ttk.LabelFrame(comp_frame, text="選擇比較檔案", padding=10)
        select_frame.pack(fill='x', padx=10, pady=5)
        
        # 可選檔案列表
        self.comparison_listbox = tk.Listbox(select_frame, selectmode='multiple', height=6)
        self.comparison_listbox.pack(fill='x', pady=5)
        
        btn_frame = ttk.Frame(select_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="全選", 
                  command=self.select_all_files).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="清除選擇", 
                  command=self.clear_selection).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="開始比較分析", 
                  command=self.run_comparison_analysis).pack(side='left', padx=5)
        
        # 比較選項
        comp_options_frame = ttk.LabelFrame(comp_frame, text="比較選項", padding=10)
        comp_options_frame.pack(fill='x', padx=10, pady=5)
        
        self.include_power_comparison = tk.BooleanVar(value=True)
        self.include_efficiency = tk.BooleanVar(value=True)
        self.include_battery_comparison = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(comp_options_frame, text="功率比較", 
                       variable=self.include_power_comparison).pack(side='left', padx=10)
        ttk.Checkbutton(comp_options_frame, text="效率分析", 
                       variable=self.include_efficiency).pack(side='left', padx=10)
        ttk.Checkbutton(comp_options_frame, text="續航比較", 
                       variable=self.include_battery_comparison).pack(side='left', padx=10)
        
        # 結果顯示
        comp_result_frame = ttk.LabelFrame(comp_frame, text="比較結果", padding=10)
        comp_result_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.comp_result_text = scrolledtext.ScrolledText(comp_result_frame, height=15)
        self.comp_result_text.pack(fill='both', expand=True)
    
    def create_report_tab(self):
        """建立報告生成分頁"""
        
        report_frame = ttk.Frame(self.notebook)
        self.notebook.add(report_frame, text="報告生成")
        
        # 報告設定
        settings_frame = ttk.LabelFrame(report_frame, text="報告設定", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # 輸出目錄選擇
        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill='x', pady=5)
        
        ttk.Label(dir_frame, text="輸出目錄:").pack(side='left')
        self.output_dir_var = tk.StringVar(value=self.output_dir)
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=40).pack(side='left', padx=5)
        ttk.Button(dir_frame, text="瀏覽", 
                  command=self.select_output_dir).pack(side='left', padx=5)
        
        # 報告格式選項
        format_frame = ttk.Frame(settings_frame)
        format_frame.pack(fill='x', pady=5)
        
        ttk.Label(format_frame, text="報告格式:").pack(side='left')
        
        self.export_png = tk.BooleanVar(value=True)
        self.export_pdf = tk.BooleanVar(value=False)
        self.export_excel = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(format_frame, text="PNG圖片", 
                       variable=self.export_png).pack(side='left', padx=10)
        ttk.Checkbutton(format_frame, text="PDF報告", 
                       variable=self.export_pdf).pack(side='left', padx=10)
        ttk.Checkbutton(format_frame, text="Excel統計", 
                       variable=self.export_excel).pack(side='left', padx=10)
        
        # 生成按鈕
        generate_frame = ttk.Frame(settings_frame)
        generate_frame.pack(fill='x', pady=10)
        
        ttk.Button(generate_frame, text="生成完整報告", 
                  command=self.generate_full_report).pack(side='left', padx=5)
        ttk.Button(generate_frame, text="開啟輸出目錄", 
                  command=self.open_output_dir).pack(side='left', padx=5)
        
        # 報告預覽
        preview_frame = ttk.LabelFrame(report_frame, text="報告預覽", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.report_text = scrolledtext.ScrolledText(preview_frame, height=15)
        self.report_text.pack(fill='both', expand=True)
    
    def create_status_bar(self):
        """建立狀態列"""
        
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # 進度條
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate')
        self.progress.pack(side='right', padx=10, pady=5)
    
    def update_status(self, message):
        """更新狀態列"""
        self.status_var.set(f"狀態: {message}")
        self.root.update_idletasks()
    
    def start_progress(self):
        """開始進度條動畫"""
        self.progress.start()
    
    def stop_progress(self):
        """停止進度條動畫"""
        self.progress.stop()
    
    def load_single_file(self):
        """載入單一檔案"""
        
        file_path = filedialog.askopenfilename(
            title="選擇CSV檔案",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_multiple_files(self):
        """載入多個檔案"""
        
        file_paths = filedialog.askopenfilenames(
            title="選擇多個CSV檔案",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        for file_path in file_paths:
            self.load_file(file_path)
    
    def load_folder(self):
        """載入資料夾中的所有CSV檔案"""
        
        folder_path = filedialog.askdirectory(title="選擇包含CSV檔案的資料夾")
        
        if folder_path:
            csv_files = list(Path(folder_path).glob("*.csv"))
            
            if csv_files:
                for file_path in csv_files:
                    self.load_file(str(file_path))
                
                messagebox.showinfo("載入完成", f"成功載入 {len(csv_files)} 個CSV檔案")
            else:
                messagebox.showwarning("警告", "選擇的資料夾中沒有找到CSV檔案")
    
    def load_file(self, file_path):
        """載入單一檔案的核心函數"""
        
        try:
            self.update_status(f"載入檔案: {Path(file_path).name}")
            
            # 讀取CSV檔案
            df = pd.read_csv(file_path)
            
            # 檢查欄位
            if len(df.columns) >= 4:
                df.columns = ['Time', 'Voltage', 'Current', 'Power']
            else:
                raise ValueError("CSV檔案格式不正確，需要至少4個欄位")
            
            # 推測模式名稱
            filename = Path(file_path).stem
            mode_name = self.detect_mode_from_filename(filename)
            
            # 資料清理
            df = df.dropna()
            df = df[df['Power'] >= 0]
            df['Mode'] = mode_name
            
            # 儲存到已載入檔案字典
            file_key = Path(file_path).name
            self.loaded_files[file_key] = {
                'path': file_path,
                'data': df,
                'mode': mode_name
            }
            
            # 更新檔案列表顯示
            self.update_file_list()
            
            # 更新下拉選單
            self.update_combo_boxes()
            
            self.update_status(f"成功載入: {file_key}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入檔案失敗: {str(e)}")
            self.update_status("載入失敗")
    
    def detect_mode_from_filename(self, filename):
        """從檔名推測模式"""
        
        filename_lower = filename.lower()
        
        if 'nolight' in filename_lower or 'no light' in filename_lower or '無燈' in filename_lower:
            return '無燈光'
        elif 'breath' in filename_lower or '呼吸' in filename_lower:
            return '呼吸燈'
        elif 'colorcycle' in filename_lower or 'color cycle' in filename_lower or 'color' in filename_lower or '彩色' in filename_lower:
            return '彩色循環'
        elif 'flash' in filename_lower or '閃爍' in filename_lower:
            return '閃爍'
        else:
            return '未知模式'
    
    def update_file_list(self):
        """更新檔案列表顯示"""
        
        # 清除現有項目
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # 添加已載入的檔案
        for file_key, file_info in self.loaded_files.items():
            df = file_info['data']
            
            # 計算統計資訊
            time_range = f"{df['Time'].min():.1f} - {df['Time'].max():.1f}s"
            avg_power = f"{df['Power'].mean()*1000:.2f} mW"
            
            self.file_tree.insert('', 'end', values=(
                file_key,
                file_info['mode'],
                len(df),
                time_range,
                avg_power
            ))
    
    def update_combo_boxes(self):
        """更新下拉選單和列表框"""
        
        file_names = list(self.loaded_files.keys())
        
        # 更新單檔分析下拉選單
        self.single_file_combo['values'] = file_names
        if file_names and not self.single_file_var.get():
            self.single_file_var.set(file_names[0])
        
        # 更新比較分析列表框
        self.comparison_listbox.delete(0, tk.END)
        for name in file_names:
            self.comparison_listbox.insert(tk.END, name)
    
    def clear_files(self):
        """清除所有已載入的檔案"""
        
        if messagebox.askyesno("確認", "確定要清除所有已載入的檔案嗎？"):
            self.loaded_files.clear()
            self.update_file_list()
            self.update_combo_boxes()
            self.update_status("已清除所有檔案")
    
    def remove_selected(self):
        """移除選中的檔案"""
        
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "請先選擇要移除的檔案")
            return
        
        for item in selected_items:
            file_name = self.file_tree.item(item)['values'][0]
            if file_name in self.loaded_files:
                del self.loaded_files[file_name]
        
        self.update_file_list()
        self.update_combo_boxes()
        self.update_status(f"已移除 {len(selected_items)} 個檔案")
    
    def view_data(self):
        """檢視選中檔案的資料"""
        
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "請先選擇要檢視的檔案")
            return
        
        item = selected_items[0]
        file_name = self.file_tree.item(item)['values'][0]
        
        if file_name in self.loaded_files:
            df = self.loaded_files[file_name]['data']
            
            # 建立新視窗顯示資料
            data_window = tk.Toplevel(self.root)
            data_window.title(f"資料檢視 - {file_name}")
            data_window.geometry("800x600")
            
            # 建立文字區域顯示資料摘要
            text_area = scrolledtext.ScrolledText(data_window)
            text_area.pack(fill='both', expand=True, padx=10, pady=10)
            
            # 顯示資料摘要
            summary = f"""檔案: {file_name}
模式: {self.loaded_files[file_name]['mode']}
資料點數: {len(df)}
時間範圍: {df['Time'].min():.2f} - {df['Time'].max():.2f} 秒

統計摘要:
平均電壓: {df['Voltage'].mean():.3f} V
平均電流: {df['Current'].mean()*1000:.2f} mA  
平均功率: {df['Power'].mean()*1000:.2f} mW
最大功率: {df['Power'].max()*1000:.2f} mW
最小功率: {df['Power'].min()*1000:.2f} mW

前10筆資料:
{df.head(10).to_string()}
"""
            
            text_area.insert('1.0', summary)
            text_area.config(state='disabled')

def main():
    """主函數"""
    
    # 建立主視窗
    root = tk.Tk()
    
    # 建立GUI應用程式
    app = MousePowerGUI(root)
    
    # 啟動GUI
    root.mainloop()

if __name__ == "__main__":
    main()
