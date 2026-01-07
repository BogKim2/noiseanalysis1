# -*- coding: utf-8 -*-
"""
노이즈 분석 윈도우
Simple 탭: 핵심 메트릭만 표시
Complete 탭: 모든 메트릭을 섹션별로 표시
"""
import numpy as np
from typing import Optional, List, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QDialog, QTableWidget, QTableWidgetItem, QPushButton,
    QCheckBox, QHeaderView, QAbstractItemView, QFrame,
    QScrollArea, QGroupBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont

# calnoise 모듈 임포트
import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from calnoise import NoiseAnalyzer, NoiseMetrics


class SimpleMetricTable(QWidget):
    """Simple 탭용 간단한 테이블"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 설명
        desc = QLabel("📊 Key noise metrics at a glance")
        desc.setStyleSheet("color: #3498db; font-size: 14px; font-weight: bold;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Metric", "Original", "Processed", "Change (Δ%)"])
        
        # Simple 메트릭 정의
        self._metrics = [
            ("SNR", "snr", "Signal-to-Noise Ratio (↑ higher = better)", True),
            ("Noise σ", "noise_std_laplacian", "Laplacian-based noise estimate (↓ lower = better)", False),
            ("Line σ (H)", "linewise_h", "Horizontal line variation (↓ lower = better)", False),
            ("Line σ (V)", "linewise_v", "Vertical line variation (↓ lower = better)", False),
            ("Edge σ", "edge_noise", "Edge region noise (↓ lower = better)", False),
        ]
        
        self.table.setRowCount(len(self._metrics))
        
        # 테이블 스타일
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                gridline-color: #404050;
                color: #e0e0e0;
                font-size: 16px;
                border: 1px solid #404050;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #303040;
            }
            QTableWidget::item:selected {
                background-color: #2980b9;
            }
            QHeaderView::section {
                background-color: #16213e;
                color: #3498db;
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #3498db;
            }
        """)
        
        # 헤더 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(1, 120)
        header.resizeSection(2, 120)
        header.resizeSection(3, 100)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 행 초기화
        for row, (display_name, key, tooltip, higher_is_better) in enumerate(self._metrics):
            name_item = QTableWidgetItem(display_name)
            name_item.setToolTip(tooltip)
            name_item.setFont(QFont("", 14, QFont.Bold))
            self.table.setItem(row, 0, name_item)
            
            for col in range(1, 4):
                item = QTableWidgetItem("--")
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("", 14))
                self.table.setItem(row, col, item)
            
            self.table.setRowHeight(row, 55)
        
        layout.addWidget(self.table)
        
        # 설명
        legend = QLabel(
            "💡 <span style='color:#27ae60'>Green</span> = Improved | "
            "<span style='color:#e74c3c'>Red</span> = Degraded | "
            "<b>SNR</b>: ↑ Better, <b>Others</b>: ↓ Better"
        )
        legend.setStyleSheet("color: #808080; font-size: 12px; padding: 10px;")
        legend.setAlignment(Qt.AlignCenter)
        layout.addWidget(legend)
        
        layout.addStretch()
    
    def update_values(self, orig_dict: dict, proc_dict: dict, improvement: dict):
        """값 업데이트"""
        for row, (display_name, key, tooltip, higher_is_better) in enumerate(self._metrics):
            # Original
            orig_val = orig_dict.get(key)
            orig_item = self.table.item(row, 1)
            if orig_val is not None:
                orig_item.setText(f"{orig_val:.2f}")
                orig_item.setForeground(QColor("#e0e0e0"))
            else:
                orig_item.setText("--")
            
            # Processed
            proc_val = proc_dict.get(key)
            proc_item = self.table.item(row, 2)
            if proc_val is not None:
                proc_item.setText(f"{proc_val:.2f}")
                proc_item.setForeground(QColor("#e0e0e0"))
            else:
                proc_item.setText("--")
            
            # Delta
            delta_item = self.table.item(row, 3)
            if improvement and key in improvement:
                delta = improvement[key]
                if delta > 0:
                    delta_item.setText(f"+{delta:.1f}%")
                    delta_item.setForeground(QColor("#27ae60"))
                elif delta < 0:
                    delta_item.setText(f"{delta:.1f}%")
                    delta_item.setForeground(QColor("#e74c3c"))
                else:
                    delta_item.setText("0.0%")
                    delta_item.setForeground(QColor("#808080"))
            else:
                delta_item.setText("--")
                delta_item.setForeground(QColor("#808080"))
    
    def clear_values(self):
        """값 초기화"""
        for row in range(self.table.rowCount()):
            for col in range(1, 4):
                item = self.table.item(row, col)
                if item:
                    item.setText("--")
                    item.setForeground(QColor("#808080"))


class MetricSection(QGroupBox):
    """Complete 탭용 메트릭 섹션"""
    
    def __init__(self, title: str, color: str, metrics: List[Tuple], parent=None):
        super().__init__(title, parent)
        self.metrics = metrics
        self.color = color
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                color: {self.color};
                border: 2px solid {self.color};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 5px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background-color: #1a1a2e;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 15, 8, 8)
        layout.setSpacing(0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Metric", "Original", "Processed", "Δ%"])
        self.table.setRowCount(len(self.metrics))
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #12121f;
                gridline-color: #303040;
                color: #e0e0e0;
                font-size: 12px;
                border: none;
            }}
            QTableWidget::item {{
                padding: 4px;
                border-bottom: 1px solid #252535;
            }}
            QHeaderView::section {{
                background-color: #1a1a2e;
                color: #808090;
                font-size: 10px;
                padding: 5px;
                border: none;
                border-bottom: 1px solid {self.color};
            }}
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.resizeSection(1, 90)
        header.resizeSection(2, 90)
        header.resizeSection(3, 70)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        for row, (display_name, key, tooltip, higher_is_better) in enumerate(self.metrics):
            name_item = QTableWidgetItem(display_name)
            name_item.setToolTip(tooltip)
            name_item.setFont(QFont("", -1, QFont.Bold))
            self.table.setItem(row, 0, name_item)
            
            for col in range(1, 4):
                item = QTableWidgetItem("--")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            
            self.table.setRowHeight(row, 28)
        
        total_height = self.table.horizontalHeader().height() + 4
        for row in range(self.table.rowCount()):
            total_height += self.table.rowHeight(row)
        self.table.setFixedHeight(total_height)
        
        layout.addWidget(self.table)
    
    def update_values(self, orig_dict: dict, proc_dict: dict, improvement: dict):
        for row, (display_name, key, tooltip, higher_is_better) in enumerate(self.metrics):
            orig_val = orig_dict.get(key)
            orig_item = self.table.item(row, 1)
            if orig_val is not None:
                orig_item.setText(self._format_value(orig_val))
                orig_item.setForeground(QColor("#e0e0e0"))
            else:
                orig_item.setText("--")
            
            proc_val = proc_dict.get(key)
            proc_item = self.table.item(row, 2)
            if proc_val is not None:
                proc_item.setText(self._format_value(proc_val))
                proc_item.setForeground(QColor("#e0e0e0"))
            else:
                proc_item.setText("--")
            
            delta_item = self.table.item(row, 3)
            if improvement and key in improvement:
                delta = improvement[key]
                if delta > 0:
                    delta_item.setText(f"+{delta:.1f}%")
                    delta_item.setForeground(QColor("#27ae60"))
                elif delta < 0:
                    delta_item.setText(f"{delta:.1f}%")
                    delta_item.setForeground(QColor("#e74c3c"))
                else:
                    delta_item.setText("0.0%")
                    delta_item.setForeground(QColor("#808080"))
            else:
                delta_item.setText("--")
                delta_item.setForeground(QColor("#808080"))
    
    def _format_value(self, val: float) -> str:
        if abs(val) >= 1e7:
            return f"{val:.2e}"
        elif abs(val) >= 1000:
            return f"{val:.1f}"
        elif abs(val) >= 10:
            return f"{val:.2f}"
        else:
            return f"{val:.3f}"
    
    def clear_values(self):
        for row in range(self.table.rowCount()):
            for col in range(1, 4):
                item = self.table.item(row, col)
                if item:
                    item.setText("--")
                    item.setForeground(QColor("#808080"))


class CompleteMetricView(QWidget):
    """Complete 탭용 전체 메트릭 뷰"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sections: List[MetricSection] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { width: 8px; }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(8)
        
        sections_config = [
            ("📈 Signal-to-Noise Ratio", "#3498db", [
                ("SNR (μ/σ)", "snr", "Mean/Std based SNR (↑)", True),
                ("SNR (RMS)", "snr_rms", "RMS based SNR (↑)", True),
            ]),
            ("📉 Noise Standard Deviation", "#9b59b6", [
                ("Noise σ (Std)", "noise_std", "Simple std (↓)", False),
                ("Noise σ (MAD)", "noise_std_mad", "MAD-based (↓)", False),
                ("Noise σ (Laplacian)", "noise_std_laplacian", "Laplacian-based (↓)", False),
            ]),
            ("📏 Line-wise Metrics", "#e67e22", [
                ("Line σ (H)", "linewise_h", "Horizontal scan variation (↓)", False),
                ("Line σ (V)", "linewise_v", "Vertical scan variation (↓)", False),
                ("Line Correlation", "line_correlation", "Adjacent line correlation (↑)", True),
                ("Abnormal Lines", "abnormal_lines_count", "Abnormal scan lines (↓)", False),
            ]),
            ("🔲 Edge Analysis", "#27ae60", [
                ("Edge Noise σ", "edge_noise", "Edge region noise (↓)", False),
                ("Edge Sharpness", "edge_sharpness", "Mean gradient (↑ preserve)", True),
                ("Gradient Var", "gradient_variance", "Gradient variance (↓)", False),
                ("Edge Coherence", "edge_coherence", "Direction coherence (↑)", True),
            ]),
            ("🌊 Spectral Analysis", "#e74c3c", [
                ("Spectral Energy", "total_spectral_energy", "Total frequency energy (↓)", False),
                ("PSD Peaks", "psd_peaks_count", "Periodic noise peaks (↓)", False),
            ]),
        ]
        
        for title, color, metrics in sections_config:
            section = MetricSection(title, color, metrics)
            self._sections.append(section)
            scroll_layout.addWidget(section)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def update_values(self, orig_dict: dict, proc_dict: dict, improvement: dict):
        for section in self._sections:
            section.update_values(orig_dict, proc_dict, improvement)
    
    def clear_values(self):
        for section in self._sections:
            section.clear_values()


class NoiseAnalysisWindow(QDialog):
    """노이즈 분석 윈도우 - Simple/Complete 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._analyzer = NoiseAnalyzer()
        self._original_image: Optional[np.ndarray] = None
        self._processed_image: Optional[np.ndarray] = None
        self._auto_calculate = True
        self._setup_ui()
        self.setWindowTitle("Noise Analysis")
        self.setMinimumSize(550, 550)
        self.resize(600, 650)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 컨트롤 바
        control_bar = QHBoxLayout()
        
        self.auto_calc_check = QCheckBox("Auto Calculate (Real-time)")
        self.auto_calc_check.setChecked(True)
        self.auto_calc_check.toggled.connect(self._on_auto_calc_changed)
        self.auto_calc_check.setStyleSheet("font-size: 12px;")
        control_bar.addWidget(self.auto_calc_check)
        
        control_bar.addStretch()
        
        self.calc_btn = QPushButton("Calculate Now")
        self.calc_btn.setVisible(False)
        self.calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3498db; }
        """)
        self.calc_btn.clicked.connect(self._run_analysis)
        control_bar.addWidget(self.calc_btn)
        
        layout.addLayout(control_bar)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404050;
                border-radius: 5px;
                background: #1a1a2e;
            }
            QTabBar::tab {
                background: #252535;
                color: #808080;
                padding: 10px 30px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: #1a1a2e;
                color: #3498db;
                border-bottom: 2px solid #3498db;
            }
            QTabBar::tab:hover:!selected {
                background: #303040;
                color: #e0e0e0;
            }
        """)
        
        # Simple 탭
        self.simple_view = SimpleMetricTable()
        self.tab_widget.addTab(self.simple_view, "📊 Simple")
        
        # Complete 탭
        self.complete_view = CompleteMetricView()
        self.tab_widget.addTab(self.complete_view, "📋 Complete")
        
        layout.addWidget(self.tab_widget, stretch=1)
        
        # 닫기 버튼
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #404050;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #505060; }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _on_auto_calc_changed(self, checked: bool):
        self._auto_calculate = checked
        self.calc_btn.setVisible(not checked)
        if checked and self._original_image is not None:
            self._run_analysis()
    
    @Slot(object)
    def set_original_image(self, image: Optional[np.ndarray]):
        """원본 이미지 설정 - 시그널로부터 호출됨"""
        self._original_image = image
        self._clear_results()
        if self._auto_calculate and image is not None:
            self._run_analysis()
    
    @Slot(object)
    def set_processed_image(self, image: Optional[np.ndarray]):
        """처리된 이미지 설정 - 시그널로부터 호출됨"""
        self._processed_image = image
        if self._auto_calculate and self._original_image is not None:
            self._run_analysis()
    
    @Slot(object, object)
    def update_images(self, original: Optional[np.ndarray], processed: Optional[np.ndarray]):
        self._original_image = original
        self._processed_image = processed
        if self._auto_calculate and original is not None:
            self._run_analysis()
    
    def _clear_results(self):
        self.simple_view.clear_values()
        self.complete_view.clear_values()
    
    def _run_analysis(self):
        if self._original_image is None:
            return
        
        orig_metrics = self._analyzer.analyze_original(self._original_image)
        orig_dict = orig_metrics.to_dict()
        
        proc_dict = {}
        improvement = {}
        
        if self._processed_image is not None:
            proc_metrics = self._analyzer.analyze_processed(self._processed_image)
            proc_dict = proc_metrics.to_dict()
            improvement = self._analyzer.get_improvement() or {}
        
        # 두 탭 모두 업데이트
        self.simple_view.update_values(orig_dict, proc_dict, improvement)
        self.complete_view.update_values(orig_dict, proc_dict, improvement)
    
    def get_analyzer(self) -> NoiseAnalyzer:
        return self._analyzer


# 하위 호환성
class NoiseAnalysisPanel(QWidget):
    analysis_completed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window = NoiseAnalysisWindow()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        btn = QPushButton("Open Noise Analysis")
        btn.clicked.connect(self._window.show)
        layout.addWidget(btn)
    
    def set_original_image(self, image):
        self._window.set_original_image(image)
    
    def set_processed_image(self, image):
        self._window.set_processed_image(image)
    
    def auto_analyze(self):
        pass


class NoiseMetricRow(QWidget):
    pass
