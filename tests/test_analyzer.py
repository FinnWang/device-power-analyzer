#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試分析器功能
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# 假設我們已經安裝了套件
try:
    from mouse_power_analyzer import MousePowerAnalyzer
    from mouse_power_analyzer.utils import detect_mode_from_filename, calculate_battery_life
except ImportError:
    # 如果還沒安裝，從本地導入
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from mouse_power_analyzer import MousePowerAnalyzer
    from mouse_power_analyzer.utils import detect_mode_from_filename, calculate_battery_life


class TestMousePowerAnalyzer(unittest.TestCase):
    """測試MousePowerAnalyzer類別"""
    
    def setUp(self):
        """設定測試環境"""
        self.analyzer = MousePowerAnalyzer()
        
        # 建立測試資料
        self.test_data = pd.DataFrame({
            'Time': np.linspace(0, 10, 100),
            'Voltage': np.full(100, 3.7) + np.random.normal(0, 0.01, 100),
            'Current': np.full(100, 0.02) + np.random.normal(0, 0.001, 100),
            'Power': np.full(100, 0.074) + np.random.normal(0, 0.005, 100)
        })
        
        # 建立臨時CSV檔案
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = Path(self.temp_dir) / "test_breath.csv"
        self.test_data.to_csv(self.test_csv, index=False)
    
    def tearDown(self):
        """清理測試環境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_csv_file(self):
        """測試CSV檔案載入"""
        df = self.analyzer.load_csv_file(self.test_csv)
        
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 100)
        self.assertIn('Mode', df.columns)
        self.assertIn('Mode_CN', df.columns)
        self.assertEqual(df['Mode'].iloc[0], 'Breath')
    
    def test_calculate_statistics(self):
        """測試統計計算"""
        df = self.analyzer.load_csv_file(self.test_csv)
        stats = self.analyzer.calculate_statistics(df)
        
        self.assertIn('avg_power_mW', stats)
        self.assertIn('duration_s', stats)
        self.assertIn('data_points', stats)
        self.assertEqual(stats['data_points'], 100)
        self.assertGreater(stats['avg_power_mW'], 0)
    
    def test_mode_detection(self):
        """測試模式識別"""
        test_cases = [
            ("MD103_Nolight_test.csv", "Nolight"),
            ("breath_mode.csv", "Breath"),
            ("color_cycle_data.csv", "Colorcycle"),
            ("flash_test.csv", "Flash"),
            ("unknown_file.csv", "Unknown")
        ]
        
        for filename, expected_mode in test_cases:
            detected_mode = detect_mode_from_filename(filename)
            self.assertEqual(detected_mode, expected_mode)
    
    def test_battery_life_calculation(self):
        """測試電池續航計算"""
        # 測試正常功率
        battery_life = calculate_battery_life(0.074)  # 74mW
        self.assertGreater(battery_life['hours'], 0)
        self.assertGreater(battery_life['days'], 0)
        
        # 測試零功率
        battery_life_zero = calculate_battery_life(0)
        self.assertEqual(battery_life_zero['hours'], float('inf'))
        
        # 測試自訂電池規格
        battery_life_custom = calculate_battery_life(0.074, 2000, 3.8)
        self.assertGreater(battery_life_custom['hours'], battery_life['hours'])


class TestUtilityFunctions(unittest.TestCase):
    """測試工具函數"""
    
    def test_mode_detection_edge_cases(self):
        """測試模式識別的邊界情況"""
        test_cases = [
            ("", "Unknown"),
            ("MD103 No light 2025.csv", "Nolight"),
            ("MD103 Color cycle test.csv", "Colorcycle"),
            ("呼吸燈模式.csv", "Breath"),
            ("閃爍效果.csv", "Flash")
        ]
        
        for filename, expected in test_cases:
            result = detect_mode_from_filename(filename)
            self.assertEqual(result, expected)
    
    def test_battery_calculation_edge_cases(self):
        """測試電池計算的邊界情況"""
        # 測試負功率
        result = calculate_battery_life(-0.01)
        self.assertEqual(result['hours'], float('inf'))
        
        # 測試極小功率
        result = calculate_battery_life(0.001)
        self.assertGreater(result['hours'], 1000)
        
        # 測試極大功率
        result = calculate_battery_life(10)
        self.assertLess(result['hours'], 1)


if __name__ == '__main__':
    unittest.main()