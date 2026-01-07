# -*- coding: utf-8 -*-
"""
최적화 가중치 설정 창
사용자가 핵심 메트릭 가중치와 페널티 값을 조절할 수 있음
GridLayout을 사용하여 깔끔한 배치
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QDoubleSpinBox, QPushButton, QGridLayout,
    QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from logic.settings import get_settings


# 기본값 정의
DEFAULT_OPTIMIZATION_SETTINGS = {
    # 핵심 5개 메트릭 가중치
    "snr": 2.0,
    "noise_std_mad": 1.0,
    "edge_sharpness": 5.0,
    "linewise_h": 1.0,
    "abnormal_lines_count": 1.0,
    # 페널티 설정
    "negative_penalty_factor": 5.0,
    "critical_penalty_factor": 20.0,
    "negative_count_penalty": 50.0
}


class OptimizationSettingsWindow(QDialog):
    """최적화 가중치 설정 창"""
    
    # 설정 변경 시그널
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self._spinboxes = {}  # 스핀박스 참조 저장
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("Optimization Settings")
        self.setFixedSize(500, 650)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #3a3a5a;
                border-radius: 10px;
                margin-top: 15px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #1a1a2e;
            }
            QLabel {
                color: #e0e0e0;
            }
            QDoubleSpinBox {
                background-color: #252540;
                color: #ffffff;
                border: 2px solid #3a3a5a;
                border-radius: 5px;
                padding: 5px 8px;
                min-width: 100px;
                font-size: 14px;
                font-weight: bold;
            }
            QDoubleSpinBox:hover {
                border-color: #4ecca3;
            }
            QDoubleSpinBox:focus {
                border-color: #4ecca3;
                background-color: #303050;
            }
            QPushButton {
                background-color: #3a3a5a;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4a4a6a;
            }
            QPushButton#saveBtn {
                background-color: #4ecca3;
                color: #1a1a2e;
                font-weight: bold;
            }
            QPushButton#saveBtn:hover {
                background-color: #3dbb92;
            }
            QPushButton#resetBtn {
                background-color: #e74c3c;
            }
            QPushButton#resetBtn:hover {
                background-color: #c0392b;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 제목
        title = QLabel("⚙️ Optimization Weight Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4ecca3;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 메트릭 가중치 그룹
        weights_group = QGroupBox("📊 Metric Weights")
        weights_group.setStyleSheet(weights_group.styleSheet() + "QGroupBox { color: #3498db; }")
        weights_grid = QGridLayout(weights_group)
        weights_grid.setContentsMargins(15, 25, 15, 15)
        weights_grid.setHorizontalSpacing(20)
        weights_grid.setVerticalSpacing(12)
        
        # 핵심 5개 메트릭 가중치
        row = 0
        row = self._add_grid_row(weights_grid, row, "snr", "SNR", 0.0, 10.0, 0.5)
        row = self._add_grid_row(weights_grid, row, "noise_std_mad", "Noise σ (MAD)", 0.0, 10.0, 0.5)
        row = self._add_grid_row(weights_grid, row, "edge_sharpness", "Edge Sharpness", 0.0, 20.0, 1.0)
        row = self._add_grid_row(weights_grid, row, "linewise_h", "Line σ (H)", 0.0, 10.0, 0.5)
        row = self._add_grid_row(weights_grid, row, "abnormal_lines_count", "Abnormal Lines", 0.0, 10.0, 0.5)
        
        # 오른쪽 여백 추가
        weights_grid.setColumnStretch(2, 1)
        
        layout.addWidget(weights_group)
        
        # 페널티 설정 그룹
        penalty_group = QGroupBox("⚠️ Penalty Settings")
        penalty_group.setStyleSheet(penalty_group.styleSheet() + "QGroupBox { color: #e74c3c; }")
        penalty_grid = QGridLayout(penalty_group)
        penalty_grid.setContentsMargins(15, 25, 15, 15)
        penalty_grid.setHorizontalSpacing(20)
        penalty_grid.setVerticalSpacing(12)
        
        row = 0
        row = self._add_grid_row(penalty_grid, row, "negative_penalty_factor", "General Negative Penalty", 1.0, 50.0, 1.0)
        row = self._add_grid_row(penalty_grid, row, "critical_penalty_factor", "Critical Metric Penalty", 1.0, 100.0, 5.0)
        row = self._add_grid_row(penalty_grid, row, "negative_count_penalty", "Per-Negative Penalty", 0.0, 200.0, 10.0)
        
        # 오른쪽 여백 추가
        penalty_grid.setColumnStretch(2, 1)
        
        layout.addWidget(penalty_group)
        
        # 설명 라벨
        info_label = QLabel(
            "💡 Higher weights = more influence on optimization score.\n"
            "   Higher penalties = stronger avoidance of degradation."
        )
        info_label.setStyleSheet("color: #a0a0b0; font-size: 13px; padding: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self._reset_to_defaults)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _add_grid_row(self, grid: QGridLayout, row: int, key: str, label: str,
                      min_val: float, max_val: float, step: float) -> int:
        """그리드에 라벨과 스핀박스 행 추가"""
        # 라벨
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 14px;")
        label_widget.setMinimumWidth(180)
        label_widget.setFixedHeight(32)
        grid.addWidget(label_widget, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        
        # 스핀박스
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setSingleStep(step)
        spinbox.setDecimals(1)
        spinbox.setFixedSize(110, 32)
        grid.addWidget(spinbox, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
        
        self._spinboxes[key] = spinbox
        
        return row + 1
    
    def _load_settings(self):
        """저장된 설정 불러오기"""
        opt_settings = self.settings.get("optimization_weights", {})
        
        for key, spinbox in self._spinboxes.items():
            value = opt_settings.get(key, DEFAULT_OPTIMIZATION_SETTINGS.get(key, 1.0))
            spinbox.setValue(value)
    
    def _save_settings(self):
        """설정 저장 (창은 닫지 않음)"""
        opt_settings = {}
        for key, spinbox in self._spinboxes.items():
            opt_settings[key] = spinbox.value()
        
        self.settings.set("optimization_weights", opt_settings)
        self.settings.save()
        
        self.settings_changed.emit()
        
        QMessageBox.information(self, "Saved", 
                               "Optimization settings saved successfully.\n"
                               "Changes will apply to future optimizations.")
    
    def _reset_to_defaults(self):
        """기본값으로 리셋"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all optimization settings to default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for key, spinbox in self._spinboxes.items():
                default_val = DEFAULT_OPTIMIZATION_SETTINGS.get(key, 1.0)
                spinbox.setValue(default_val)
    
    def get_current_settings(self) -> dict:
        """현재 설정 반환"""
        return {key: spinbox.value() for key, spinbox in self._spinboxes.items()}
    
    def showEvent(self, event):
        """창이 표시될 때 위치 설정"""
        super().showEvent(event)
        # 화면 오른쪽 상단에 배치
        if self.parent():
            parent_geom = self.parent().geometry()
            # 부모 창 오른쪽에 배치
            x = parent_geom.x() + parent_geom.width() - 800
            y = parent_geom.y()
            self.move(x, y)
        else:
            # 부모가 없으면 화면 오른쪽에 배치
            from PySide6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            x = screen.width() - self.width() - 50
            y = 100
            self.move(x, y)
