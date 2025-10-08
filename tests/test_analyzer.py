#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 MousePowerAnalyzer 類別
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# 添加src目錄到路徑
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mouse_power_analyzer import MousePowerAnalyzer
from mouse_power_analyzer.utils import detect_mode_from_filename, calculate_battery_life


class TestMousePowerAnalyzer(unittest.TestCase):
    """測試 MousePowerAnalyzer 類別"""
    
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
        
        # 建立臨時檔案
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_nolight.csv")
        self.test_data.to_csv(self.test_file, index=False)
    
    def tearDown(self):
        """清理測試環境"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_csv_file(self):
        """測試CSV檔案載入"""
        df = self.analyzer.load_csv_file(self.test_file)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 100)
        self.assertIn('Time', df.columns)
        self.assertIn('Power', df.columns)
    
    def test_calculate_statistics(self):
        """測試統計計算"""
        stats = self.analyzer.calculate_statistics(self.test_data)
        
        self.assertIn('avg_power_mW', stats)
        self.assertIn('duration_s', stats)
        self.assertIn('data_points', stats)
        
        # 檢查數值合理性
        self.assertGreater(stats['avg_power_mW'], 0)
        self.assertEqual(stats['data_points'], 100)
        self.assertAlmostEqual(stats['duration_s'], 10, places=1)
    
    def test_detect_mode_from_filename(self):
        """測試模式檢測"""
        test_cases = [
            ("MD103 No light 2025-10-02 0.csv", "無燈光"),
            ("MD103 Breath 2025-10-02 0.csv", "呼吸燈"),
            ("MD103 Color cycle 2025-10-02 0.csv", "彩色循環"),
            ("MD103 Flash 2025-10-02 0.csv", "閃爍"),
            ("unknown_file.csv", "未知")
        ]
        
        for filename, expected_mode in test_cases:
            with self.subTest(filename=filename):
                mode = detect_mode_from_filename(filename)
                self.assertEqual(mode, expected_mode)
    
    def test_calculate_battery_life(self):
        """測試電池續航計算"""
        avg_power_W = 0.074  # 74mW
        battery_hours = calculate_battery_life(avg_power_W)
        
        self.assertIsInstance(battery_hours, float)
        self.assertGreater(battery_hours, 0)
        self.assertLess(battery_hours, 1000)  # 合理範圍
    
    def test_analyze_files(self):
        """測試檔案分析"""
        data_dict, summary = self.analyzer.analyze_files([self.test_file])
        
        self.assertIsInstance(data_dict, dict)
        self.assertIsInstance(summary, dict)
        self.assertEqual(len(data_dict), 1)
        
        # 檢查資料結構
        file_key = list(data_dict.keys())[0]
        self.assertIn(file_key, data_dict)
        self.assertIsInstance(data_dict[file_key], pd.DataFrame)


class TestUtilityFunctions(unittest.TestCase):
    """測試工具函數"""
    
    def test_calculate_battery_life_edge_cases(self):
        """測試電池續航計算的邊界情況"""
        # 零功率
        self.assertEqual(calculate_battery_life(0), float('inf'))
        
        # 負功率
        self.assertEqual(calculate_battery_life(-0.01), float('inf'))
        
        # 極小功率
        result = calculate_battery_life(0.001)  # 1mW
        self.assertGreater(result, 1000)  # 應該超過1000小時
    
    def test_detect_mode_case_insensitive(self):
        """測試模式檢測的大小寫不敏感"""
        test_cases = [
            ("test_NOLIGHT.csv", "無燈光"),
            ("test_breath.csv", "呼吸燈"),
            ("test_COLORCYCLE.csv", "彩色循環"),
            ("test_flash.csv", "閃爍")
        ]
        
        for filename, expected_mode in test_cases:
            with self.subTest(filename=filename):
                mode = detect_mode_from_filename(filename)
                self.assertEqual(mode, expected_mode)


if __name__ == '__main__':
    unittest.main()