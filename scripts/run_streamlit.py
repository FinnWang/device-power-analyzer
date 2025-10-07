#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動Streamlit Web介面
"""

import subprocess
import sys
from pathlib import Path
import webbrowser
import time
import threading

def check_streamlit():
    """檢查Streamlit是否已安裝"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_streamlit():
    """安裝Streamlit和相關依賴"""
    print("正在安裝Streamlit和相關依賴...")
    
    packages = [
        "streamlit>=1.28.0",
        "plotly>=5.0.0",
        "streamlit-option-menu>=0.3.0"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ 成功安裝 {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 安裝 {package} 失敗: {e}")
            return False
    
    return True

def open_browser_delayed(url, delay=3):
    """延遲開啟瀏覽器"""
    time.sleep(delay)
    webbrowser.open(url)

def main():
    """主函數"""
    
    print("=== 無線滑鼠耗電分析工具 - Streamlit Web介面 ===")
    
    # 檢查Streamlit
    if not check_streamlit():
        print("未找到Streamlit，正在安裝...")
        if not install_streamlit():
            print("❌ 安裝失敗，請手動執行：pip install streamlit plotly")
            return
    
    # 找到Streamlit應用檔案
    app_file = Path(__file__).parent.parent / "streamlit_launcher.py"
    
    if not app_file.exists():
        print(f"❌ 找不到應用檔案：{app_file}")
        return
    
    print("🚀 啟動Streamlit應用...")
    print("📱 Web介面將在瀏覽器中開啟")
    print("🛑 按 Ctrl+C 停止服務")
    print()
    
    # 延遲開啟瀏覽器
    browser_thread = threading.Thread(
        target=open_browser_delayed, 
        args=("http://localhost:8502", 3)
    )
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # 啟動Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--server.port", "8502",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit應用已停止")
    except Exception as e:
        print(f"❌ 啟動失敗：{e}")

if __name__ == "__main__":
    main()