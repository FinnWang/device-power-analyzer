#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
無線滑鼠耗電分析工具 - 啟動腳本
"""

import sys
import os
from pathlib import Path
from pathlib import Path

def check_requirements():
    """檢查必要套件"""
    
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'tkinter'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("缺少必要套件:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n請執行以下命令安裝:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函數"""
    
    print("=== 無線滑鼠耗電分析工具 ===")
    print("檢查系統需求...")
    
    # 檢查Python版本
    if sys.version_info < (3, 7):
        print("錯誤: 需要Python 3.7或更高版本")
        sys.exit(1)
    
    # 檢查必要套件
    if not check_requirements():
        sys.exit(1)
    
    print("系統需求檢查通過!")
    print("啟動GUI介面...")
    
    # 導入並啟動GUI
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        
        from mouse_power_analyzer.gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"啟動失敗: {e}")
        print("\n請確認:")
        print("1. 所有必要套件已安裝")
        print("2. mouse_power_gui.py 檔案存在")
        print("3. 系統支援GUI顯示")
        sys.exit(1)

if __name__ == "__main__":
    main()