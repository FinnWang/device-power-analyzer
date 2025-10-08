#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Result Controls - 結果管理控制項

提供結果管理的使用者介面控制項，包括新增、刪除、清除和匯出功能
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import io
import zipfile

from .result_manager import AnalysisResultManager, TimeRangeAnalysisResult, ResultStorageManager


class NewAnalysisController:
    """新分析控制器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化新分析控制器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def render_new_analysis_button(self, key: str = "new_analysis") -> bool:
        """
        渲染「選擇新的時間區間」按鈕
        
        Args:
            key: Streamlit 元件的 key
            
        Returns:
            是否點擊了按鈕
        """
        return st.button(
            "🆕 選擇新的時間區間",
            key=key,
            type="primary",
            help="開始新的時間區間分析",
            use_container_width=True
        )
    
    def render_analysis_mode_selector(self, key: str = "analysis_mode") -> str:
        """
        渲染分析模式選擇器
        
        Args:
            key: Streamlit 元件的 key
            
        Returns:
            選擇的分析模式
        """
        return st.selectbox(
            "選擇分析模式",
            ["時間區間分析", "完整分析"],
            index=0,
            key=key,
            help="選擇要進行的分析類型"
        )
    
    def render_quick_actions(self) -> Dict[str, bool]:
        """
        渲染快速操作按鈕
        
        Returns:
            操作狀態字典
        """
        st.subheader("⚡ 快速操作")
        
        col1, col2, col3 = st.columns(3)
        
        actions = {}
        
        with col1:
            actions['new_analysis'] = st.button(
                "🆕 新分析",
                help="開始新的時間區間分析",
                use_container_width=True
            )
        
        with col2:
            actions['duplicate_last'] = st.button(
                "📋 複製上次設定",
                help="使用上次分析的設定",
                use_container_width=True,
                disabled=not self.result_manager.has_results()
            )
        
        with col3:
            actions['batch_analysis'] = st.button(
                "📊 批次分析",
                help="對多個時間區間進行批次分析",
                use_container_width=True
            )
        
        return actions
    
    def get_last_analysis_settings(self) -> Optional[Dict[str, Any]]:
        """
        取得上次分析的設定
        
        Returns:
            上次分析的設定，如果沒有則返回 None
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            return None
        
        # 取得最新的結果
        last_result = max(results, key=lambda r: r.timestamp)
        
        return {
            'filename': last_result.filename,
            'mode_cn': last_result.mode_cn,
            'duration': last_result.duration,
            'chart_theme': last_result.chart_theme
        }
    
    def render_batch_analysis_config(self) -> Optional[Dict[str, Any]]:
        """
        渲染批次分析配置
        
        Returns:
            批次分析配置，如果取消則返回 None
        """
        st.subheader("📊 批次分析配置")
        
        # 時間區間配置
        st.write("**時間區間設定**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            interval_type = st.selectbox(
                "區間類型",
                ["固定長度", "百分比分割", "自定義區間"],
                help="選擇如何劃分時間區間"
            )
        
        with col2:
            if interval_type == "固定長度":
                interval_length = st.number_input(
                    "區間長度 (秒)",
                    min_value=1.0,
                    max_value=3600.0,
                    value=60.0,
                    step=1.0
                )
                overlap_ratio = st.slider(
                    "重疊比例 (%)",
                    min_value=0,
                    max_value=50,
                    value=0,
                    help="相鄰區間的重疊百分比"
                )
            
            elif interval_type == "百分比分割":
                num_segments = st.number_input(
                    "分割數量",
                    min_value=2,
                    max_value=20,
                    value=5,
                    step=1
                )
                interval_length = None
                overlap_ratio = 0
            
            else:  # 自定義區間
                st.write("請在下方定義自定義區間")
                interval_length = None
                overlap_ratio = 0
                num_segments = None
        
        # 標籤配置
        st.write("**標籤設定**")
        
        label_prefix = st.text_input(
            "標籤前綴",
            value="批次分析",
            help="所有批次結果的標籤前綴"
        )
        
        auto_label = st.checkbox(
            "自動生成標籤",
            value=True,
            help="根據時間範圍自動生成標籤"
        )
        
        # 確認按鈕
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 開始批次分析", type="primary"):
                config = {
                    'interval_type': interval_type,
                    'interval_length': interval_length,
                    'overlap_ratio': overlap_ratio,
                    'num_segments': num_segments if interval_type == "百分比分割" else None,
                    'label_prefix': label_prefix,
                    'auto_label': auto_label
                }
                return config
        
        with col2:
            if st.button("❌ 取消"):
                return None
        
        return None


class ResultDeleteController:
    """結果刪除控制器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化結果刪除控制器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
    
    def render_delete_single_button(self, result_id: str, key: str) -> bool:
        """
        渲染單個結果刪除按鈕
        
        Args:
            result_id: 結果 ID
            key: Streamlit 元件的 key
            
        Returns:
            是否確認刪除
        """
        if st.button("🗑️ 刪除", key=key, help="刪除此結果"):
            # 顯示確認對話框
            result = self.result_manager.get_result_by_id(result_id)
            if result:
                st.warning(f"確定要刪除結果「{result.label}」嗎？")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ 確認刪除", key=f"{key}_confirm"):
                        return True
                
                with col2:
                    if st.button("❌ 取消", key=f"{key}_cancel"):
                        return False
        
        return False
    
    def render_delete_multiple_interface(self) -> Optional[List[str]]:
        """
        渲染多選刪除介面
        
        Returns:
            要刪除的結果 ID 列表，如果取消則返回 None
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            st.info("沒有可刪除的結果")
            return None
        
        st.subheader("🗑️ 批次刪除結果")
        
        # 選擇要刪除的結果
        selected_for_deletion = []
        
        st.write("**選擇要刪除的結果:**")
        
        for i, result in enumerate(results):
            col_check, col_info, col_details = st.columns([0.1, 0.6, 0.3])
            
            with col_check:
                if st.checkbox("", key=f"delete_select_{i}", label_visibility="collapsed"):
                    selected_for_deletion.append(result.id)
            
            with col_info:
                st.write(f"**{result.label}**")
                st.caption(f"{result.mode_cn} | {result.start_time:.3f}s-{result.end_time:.3f}s")
            
            with col_details:
                power_info = result.get_power_info()
                st.caption(f"{power_info['avg_power_mW']:.2f} mW")
                st.caption(f"{result.timestamp.strftime('%m-%d %H:%M')}")
        
        if not selected_for_deletion:
            st.info("請選擇要刪除的結果")
            return None
        
        # 確認刪除
        st.warning(f"將刪除 {len(selected_for_deletion)} 個結果，此操作無法復原！")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 確認刪除", type="primary", key="confirm_batch_delete"):
                return selected_for_deletion
        
        with col2:
            if st.button("❌ 取消", key="cancel_batch_delete"):
                return None
        
        return None
    
    def render_clear_all_interface(self) -> bool:
        """
        渲染清除所有結果介面
        
        Returns:
            是否確認清除所有結果
        """
        result_count = self.result_manager.get_result_count()
        
        if result_count == 0:
            st.info("沒有可清除的結果")
            return False
        
        st.subheader("🗑️ 清除所有結果")
        
        st.warning(f"將清除全部 {result_count} 個分析結果，此操作無法復原！")
        
        # 顯示將被清除的結果摘要
        with st.expander("📋 查看將被清除的結果"):
            summary = self.result_manager.get_results_summary()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**涉及的模式:**")
                for mode in summary['modes']:
                    st.write(f"- {mode}")
            
            with col2:
                st.write("**涉及的檔案:**")
                for file in summary['files']:
                    st.write(f"- {file}")
        
        # 確認清除
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ 確認清除全部", type="primary", key="confirm_clear_all"):
                return True
        
        with col2:
            if st.button("❌ 取消", key="cancel_clear_all"):
                return False
        
        return False
    
    def render_selective_clear_interface(self) -> Optional[Dict[str, Any]]:
        """
        渲染選擇性清除介面
        
        Returns:
            清除條件字典，如果取消則返回 None
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            st.info("沒有可清除的結果")
            return None
        
        st.subheader("🎯 選擇性清除")
        
        # 收集可用的選項
        all_modes = list(set(result.mode_cn for result in results))
        all_files = list(set(result.filename for result in results))
        
        # 清除條件
        st.write("**清除條件 (符合任一條件的結果將被清除):**")
        
        clear_by_mode = st.multiselect(
            "按模式清除",
            options=all_modes,
            help="選擇要清除的模式"
        )
        
        clear_by_file = st.multiselect(
            "按檔案清除",
            options=all_files,
            help="選擇要清除的檔案"
        )
        
        # 按時間清除
        clear_by_time = st.checkbox("按分析時間清除")
        
        if clear_by_time:
            time_threshold = st.date_input(
                "清除此日期之前的結果",
                value=datetime.now().date(),
                help="選擇日期，此日期之前的分析結果將被清除"
            )
        else:
            time_threshold = None
        
        # 預覽將被清除的結果
        matching_results = []
        
        for result in results:
            should_clear = False
            
            if clear_by_mode and result.mode_cn in clear_by_mode:
                should_clear = True
            
            if clear_by_file and result.filename in clear_by_file:
                should_clear = True
            
            if clear_by_time and time_threshold:
                if result.timestamp.date() < time_threshold:
                    should_clear = True
            
            if should_clear:
                matching_results.append(result)
        
        if matching_results:
            st.warning(f"將清除 {len(matching_results)} 個結果")
            
            with st.expander("📋 預覽將被清除的結果"):
                for result in matching_results:
                    st.write(f"- {result.label} ({result.mode_cn}, {result.timestamp.strftime('%Y-%m-%d %H:%M')})")
            
            # 確認清除
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 確認選擇性清除", type="primary", key="confirm_selective_clear"):
                    return {
                        'modes': clear_by_mode,
                        'files': clear_by_file,
                        'time_threshold': time_threshold
                    }
            
            with col2:
                if st.button("❌ 取消", key="cancel_selective_clear"):
                    return None
        
        else:
            st.info("沒有符合條件的結果")
        
        return None


class ResultExportController:
    """結果匯出控制器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化結果匯出控制器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
        self.storage_manager = ResultStorageManager(result_manager)
    
    def render_export_options(self) -> Dict[str, bool]:
        """
        渲染匯出選項
        
        Returns:
            匯出選項字典
        """
        if not self.result_manager.has_results():
            st.info("沒有可匯出的結果")
            return {}
        
        st.subheader("📥 匯出選項")
        
        col1, col2, col3 = st.columns(3)
        
        export_options = {}
        
        with col1:
            export_options['json'] = st.button(
                "📄 匯出 JSON",
                help="匯出為 JSON 格式，可重新匯入",
                use_container_width=True
            )
        
        with col2:
            export_options['csv'] = st.button(
                "📊 匯出 CSV",
                help="匯出為 CSV 表格格式",
                use_container_width=True
            )
        
        with col3:
            export_options['markdown'] = st.button(
                "📝 匯出報告",
                help="匯出為 Markdown 報告",
                use_container_width=True
            )
        
        return export_options
    
    def render_selective_export_interface(self) -> Optional[Tuple[List[str], str]]:
        """
        渲染選擇性匯出介面
        
        Returns:
            (選中的結果 ID 列表, 匯出格式)，如果取消則返回 None
        """
        results = self.result_manager.get_all_results()
        
        if not results:
            st.info("沒有可匯出的結果")
            return None
        
        st.subheader("🎯 選擇性匯出")
        
        # 選擇要匯出的結果
        selected_for_export = []
        
        st.write("**選擇要匯出的結果:**")
        
        # 全選/全不選按鈕
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("全選", key="export_select_all"):
                for i in range(len(results)):
                    st.session_state[f"export_select_{i}"] = True
        
        with col2:
            if st.button("全不選", key="export_deselect_all"):
                for i in range(len(results)):
                    st.session_state[f"export_select_{i}"] = False
        
        # 結果選擇列表
        for i, result in enumerate(results):
            col_check, col_info, col_details = st.columns([0.1, 0.6, 0.3])
            
            with col_check:
                if st.checkbox("", key=f"export_select_{i}", label_visibility="collapsed"):
                    selected_for_export.append(result.id)
            
            with col_info:
                st.write(f"**{result.label}**")
                st.caption(f"{result.mode_cn} | {result.start_time:.3f}s-{result.end_time:.3f}s")
            
            with col_details:
                power_info = result.get_power_info()
                st.caption(f"{power_info['avg_power_mW']:.2f} mW")
                st.caption(f"{result.timestamp.strftime('%m-%d %H:%M')}")
        
        if not selected_for_export:
            st.info("請選擇要匯出的結果")
            return None
        
        # 選擇匯出格式
        export_format = st.selectbox(
            "選擇匯出格式",
            ["JSON", "CSV", "Markdown"],
            help="選擇匯出的檔案格式"
        )
        
        # 確認匯出
        if st.button("📥 匯出選中結果", type="primary", key="confirm_selective_export"):
            return selected_for_export, export_format.lower()
        
        return None
    
    def generate_export_data(self, result_ids: Optional[List[str]] = None, format_type: str = "json") -> Tuple[str, str, str]:
        """
        生成匯出資料
        
        Args:
            result_ids: 要匯出的結果 ID 列表，None 表示匯出全部
            format_type: 匯出格式 ("json", "csv", "markdown")
            
        Returns:
            (資料內容, 檔案名稱, MIME 類型)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == "json":
            if result_ids is None:
                # 匯出全部結果
                data = self.storage_manager.save_to_json()
                filename = f"mouse_power_analysis_results_{timestamp}.json"
            else:
                # 匯出選中結果
                # 暫時修改結果管理器以只包含選中的結果
                original_results = self.result_manager.get_all_results()
                selected_results = [r for r in original_results if r.id in result_ids]
                
                # 建立臨時的匯出資料
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'result_count': len(selected_results),
                    'results': [result.to_dict() for result in selected_results]
                }
                
                data = json.dumps(export_data, ensure_ascii=False, indent=2)
                filename = f"mouse_power_analysis_selected_{timestamp}.json"
            
            mime_type = "application/json"
        
        elif format_type == "csv":
            if result_ids is None:
                data = self.storage_manager.generate_csv_report()
                filename = f"mouse_power_analysis_report_{timestamp}.csv"
            else:
                # 生成選中結果的 CSV
                selected_results = [self.result_manager.get_result_by_id(rid) for rid in result_ids if self.result_manager.get_result_by_id(rid)]
                
                csv_data = []
                for result in selected_results:
                    power_info = result.get_power_info()
                    csv_data.append({
                        '標籤': result.label,
                        '模式': result.mode_cn,
                        '檔案': result.filename,
                        '開始時間 (s)': f"{result.start_time:.3f}",
                        '結束時間 (s)': f"{result.end_time:.3f}",
                        '持續時間 (s)': f"{result.duration:.3f}",
                        '平均功率 (mW)': f"{power_info['avg_power_mW']:.2f}",
                        '最大功率 (mW)': f"{power_info['max_power_mW']:.2f}",
                        '平均電流 (mA)': f"{power_info['avg_current_mA']:.2f}",
                        '預估續航 (小時)': f"{power_info['battery_hours']:.1f}",
                        '分析時間': result.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                df = pd.DataFrame(csv_data)
                data = df.to_csv(index=False, encoding='utf-8-sig')
                filename = f"mouse_power_analysis_selected_{timestamp}.csv"
            
            mime_type = "text/csv"
        
        elif format_type == "markdown":
            if result_ids is None:
                data = self.storage_manager.generate_markdown_report()
                filename = f"mouse_power_analysis_report_{timestamp}.md"
            else:
                # 生成選中結果的 Markdown 報告
                selected_results = [self.result_manager.get_result_by_id(rid) for rid in result_ids if self.result_manager.get_result_by_id(rid)]
                
                report = f"""# 時間區間分析報告 (選中結果)

**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**選中結果數量**: {len(selected_results)}

## 分析摘要

"""
                
                for i, result in enumerate(selected_results, 1):
                    power_info = result.get_power_info()
                    
                    report += f"""
### {i}. {result.label}

- **模式**: {result.mode_cn}
- **檔案**: {result.filename}
- **時間範圍**: {result.start_time:.3f}s - {result.end_time:.3f}s
- **持續時間**: {result.duration:.3f}s
- **平均功率**: {power_info['avg_power_mW']:.2f} mW
- **最大功率**: {power_info['max_power_mW']:.2f} mW
- **平均電流**: {power_info['avg_current_mA']:.2f} mA
- **預估續航**: {power_info['battery_hours']:.1f} 小時
- **分析時間**: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

"""
                
                data = report
                filename = f"mouse_power_analysis_selected_{timestamp}.md"
            
            mime_type = "text/markdown"
        
        else:
            raise ValueError(f"不支援的匯出格式: {format_type}")
        
        return data, filename, mime_type
    
    def render_download_buttons(self) -> None:
        """渲染下載按鈕"""
        if not self.result_manager.has_results():
            return
        
        st.subheader("📥 快速下載")
        
        col1, col2, col3 = st.columns(3)
        
        # JSON 下載
        with col1:
            json_data, json_filename, json_mime = self.generate_export_data(format_type="json")
            st.download_button(
                label="📄 下載 JSON",
                data=json_data,
                file_name=json_filename,
                mime=json_mime,
                help="下載完整的 JSON 格式資料",
                use_container_width=True
            )
        
        # CSV 下載
        with col2:
            csv_data, csv_filename, csv_mime = self.generate_export_data(format_type="csv")
            st.download_button(
                label="📊 下載 CSV",
                data=csv_data,
                file_name=csv_filename,
                mime=csv_mime,
                help="下載 CSV 表格格式資料",
                use_container_width=True
            )
        
        # Markdown 下載
        with col3:
            md_data, md_filename, md_mime = self.generate_export_data(format_type="markdown")
            st.download_button(
                label="📝 下載報告",
                data=md_data,
                file_name=md_filename,
                mime=md_mime,
                help="下載 Markdown 格式報告",
                use_container_width=True
            )


class ResultImportController:
    """結果匯入控制器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化結果匯入控制器
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
        self.storage_manager = ResultStorageManager(result_manager)
    
    def render_import_interface(self) -> Optional[int]:
        """
        渲染匯入介面
        
        Returns:
            匯入的結果數量，如果沒有匯入則返回 None
        """
        st.subheader("📤 匯入分析結果")
        
        # 檔案上傳
        uploaded_file = st.file_uploader(
            "選擇要匯入的 JSON 檔案",
            type=['json'],
            help="選擇之前匯出的 JSON 格式分析結果檔案"
        )
        
        if uploaded_file is not None:
            try:
                # 讀取檔案內容
                content = uploaded_file.read().decode('utf-8')
                
                # 預覽匯入資料
                import_data = json.loads(content)
                
                if 'results' not in import_data:
                    st.error("檔案格式不正確，缺少 'results' 欄位")
                    return None
                
                result_count = len(import_data['results'])
                export_timestamp = import_data.get('export_timestamp', '未知')
                
                st.info(f"檔案包含 {result_count} 個分析結果")
                st.caption(f"匯出時間: {export_timestamp}")
                
                # 預覽將要匯入的結果
                with st.expander("📋 預覽匯入資料"):
                    for i, result_data in enumerate(import_data['results'][:5]):  # 只顯示前5個
                        st.write(f"**{i+1}. {result_data.get('label', 'N/A')}**")
                        st.caption(f"模式: {result_data.get('mode_cn', 'N/A')} | "
                                 f"時間: {result_data.get('start_time', 0):.3f}s-{result_data.get('end_time', 0):.3f}s")
                    
                    if result_count > 5:
                        st.caption(f"... 還有 {result_count - 5} 個結果")
                
                # 匯入選項
                col1, col2 = st.columns(2)
                
                with col1:
                    merge_mode = st.selectbox(
                        "匯入模式",
                        ["合併", "覆蓋"],
                        help="合併: 添加到現有結果；覆蓋: 清除現有結果後匯入"
                    )
                
                with col2:
                    handle_duplicates = st.selectbox(
                        "重複處理",
                        ["跳過", "重新命名", "覆蓋"],
                        help="處理標籤重複的結果"
                    )
                
                # 確認匯入
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ 確認匯入", type="primary", key="confirm_import"):
                        # 處理匯入
                        if merge_mode == "覆蓋":
                            self.result_manager.clear_all_results()
                        
                        # 處理重複標籤
                        if handle_duplicates == "跳過":
                            existing_labels = [r.label for r in self.result_manager.get_all_results()]
                            filtered_results = []
                            
                            for result_data in import_data['results']:
                                if result_data.get('label') not in existing_labels:
                                    filtered_results.append(result_data)
                            
                            import_data['results'] = filtered_results
                        
                        elif handle_duplicates == "重新命名":
                            existing_labels = [r.label for r in self.result_manager.get_all_results()]
                            
                            for result_data in import_data['results']:
                                original_label = result_data.get('label', '未命名')
                                new_label = original_label
                                counter = 1
                                
                                while new_label in existing_labels:
                                    new_label = f"{original_label} ({counter})"
                                    counter += 1
                                
                                result_data['label'] = new_label
                                existing_labels.append(new_label)
                        
                        # 執行匯入
                        imported_count = self.storage_manager.load_from_json(json.dumps(import_data))
                        
                        return imported_count
                
                with col2:
                    if st.button("❌ 取消", key="cancel_import"):
                        return None
            
            except json.JSONDecodeError as e:
                st.error(f"JSON 格式錯誤: {str(e)}")
            except Exception as e:
                st.error(f"匯入失敗: {str(e)}")
        
        return None


class ResultManagementUI:
    """結果管理介面主控制器"""
    
    def __init__(self, result_manager: AnalysisResultManager):
        """
        初始化結果管理介面
        
        Args:
            result_manager: 結果管理器實例
        """
        self.result_manager = result_manager
        self.new_analysis_controller = NewAnalysisController(result_manager)
        self.delete_controller = ResultDeleteController(result_manager)
        self.export_controller = ResultExportController(result_manager)
        self.import_controller = ResultImportController(result_manager)
    
    def render_management_sidebar(self) -> Dict[str, Any]:
        """
        渲染管理側邊欄
        
        Returns:
            操作結果字典
        """
        st.sidebar.header("🛠️ 結果管理")
        
        actions = {}
        
        # 新分析控制
        if st.sidebar.button("🆕 新的時間區間分析", use_container_width=True):
            actions['new_analysis'] = True
        
        # 結果統計
        result_count = self.result_manager.get_result_count()
        st.sidebar.metric("已保存結果", result_count)
        
        if result_count > 0:
            # 快速操作
            st.sidebar.subheader("⚡ 快速操作")
            
            if st.sidebar.button("📊 查看比較", use_container_width=True):
                actions['show_comparison'] = True
            
            if st.sidebar.button("📥 匯出全部", use_container_width=True):
                actions['export_all'] = True
            
            if st.sidebar.button("🗑️ 清除全部", use_container_width=True):
                actions['clear_all'] = True
        
        # 匯入功能
        st.sidebar.subheader("📤 匯入")
        
        if st.sidebar.button("📤 匯入結果", use_container_width=True):
            actions['import_results'] = True
        
        return actions
    
    def render_management_tabs(self) -> None:
        """渲染管理分頁"""
        if not self.result_manager.has_results():
            st.info("📝 目前沒有分析結果")
            
            # 顯示匯入選項
            st.divider()
            imported_count = self.import_controller.render_import_interface()
            
            if imported_count is not None and imported_count > 0:
                st.success(f"✅ 成功匯入 {imported_count} 個結果！")
                st.rerun()
            
            return
        
        # 建立分頁
        tab1, tab2, tab3, tab4 = st.tabs(["🆕 新增分析", "🗑️ 刪除管理", "📥 匯出下載", "📤 匯入資料"])
        
        with tab1:
            self._render_new_analysis_tab()
        
        with tab2:
            self._render_delete_management_tab()
        
        with tab3:
            self._render_export_tab()
        
        with tab4:
            self._render_import_tab()
    
    def _render_new_analysis_tab(self) -> None:
        """渲染新增分析分頁"""
        # 快速操作
        actions = self.new_analysis_controller.render_quick_actions()
        
        if actions.get('new_analysis'):
            st.success("🆕 準備開始新的時間區間分析")
            st.info("請返回主介面選擇檔案和時間範圍")
        
        if actions.get('duplicate_last'):
            last_settings = self.new_analysis_controller.get_last_analysis_settings()
            if last_settings:
                st.success("📋 已載入上次分析設定")
                st.json(last_settings)
            else:
                st.warning("沒有找到上次分析設定")
        
        if actions.get('batch_analysis'):
            batch_config = self.new_analysis_controller.render_batch_analysis_config()
            if batch_config:
                st.success("📊 批次分析配置已設定")
                st.json(batch_config)
                st.info("請返回主介面選擇檔案並應用批次設定")
    
    def _render_delete_management_tab(self) -> None:
        """渲染刪除管理分頁"""
        # 刪除選項
        delete_mode = st.selectbox(
            "選擇刪除模式",
            ["批次刪除", "清除全部", "選擇性清除"],
            help="選擇不同的刪除方式"
        )
        
        if delete_mode == "批次刪除":
            deleted_ids = self.delete_controller.render_delete_multiple_interface()
            if deleted_ids:
                # 執行刪除
                deleted_count = 0
                for result_id in deleted_ids:
                    if self.result_manager.delete_result(result_id):
                        deleted_count += 1
                
                st.success(f"✅ 成功刪除 {deleted_count} 個結果")
                st.rerun()
        
        elif delete_mode == "清除全部":
            if self.delete_controller.render_clear_all_interface():
                cleared_count = self.result_manager.clear_all_results()
                st.success(f"✅ 成功清除 {cleared_count} 個結果")
                st.rerun()
        
        elif delete_mode == "選擇性清除":
            clear_conditions = self.delete_controller.render_selective_clear_interface()
            if clear_conditions:
                # 執行選擇性清除
                results = self.result_manager.get_all_results()
                cleared_count = 0
                
                for result in results[:]:  # 使用副本避免修改時的問題
                    should_clear = False
                    
                    if clear_conditions.get('modes') and result.mode_cn in clear_conditions['modes']:
                        should_clear = True
                    
                    if clear_conditions.get('files') and result.filename in clear_conditions['files']:
                        should_clear = True
                    
                    if clear_conditions.get('time_threshold'):
                        if result.timestamp.date() < clear_conditions['time_threshold']:
                            should_clear = True
                    
                    if should_clear:
                        if self.result_manager.delete_result(result.id):
                            cleared_count += 1
                
                st.success(f"✅ 成功清除 {cleared_count} 個結果")
                st.rerun()
    
    def _render_export_tab(self) -> None:
        """渲染匯出分頁"""
        # 快速下載按鈕
        self.export_controller.render_download_buttons()
        
        st.divider()
        
        # 選擇性匯出
        export_result = self.export_controller.render_selective_export_interface()
        
        if export_result:
            selected_ids, export_format = export_result
            
            try:
                data, filename, mime_type = self.export_controller.generate_export_data(
                    result_ids=selected_ids,
                    format_type=export_format
                )
                
                st.download_button(
                    label=f"📥 下載 {export_format.upper()} 檔案",
                    data=data,
                    file_name=filename,
                    mime=mime_type,
                    type="primary",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"匯出失敗: {str(e)}")
    
    def _render_import_tab(self) -> None:
        """渲染匯入分頁"""
        imported_count = self.import_controller.render_import_interface()
        
        if imported_count is not None:
            if imported_count > 0:
                st.success(f"✅ 成功匯入 {imported_count} 個結果！")
                st.rerun()
            else:
                st.warning("沒有匯入任何結果")
    
    def render_complete_management_interface(self) -> None:
        """渲染完整的管理介面"""
        st.header("🛠️ 結果管理")
        
        # 渲染管理分頁
        self.render_management_tabs()