# -*- coding: utf-8 -*-
"""
필터 탭 위젯 구현
7개의 개별 필터 탭 + 1개의 파이프라인 탭
실시간 미리보기, 설정 저장/불러오기 지원
자동 최적화 기능 포함
"""
from typing import Optional, Type
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QLabel, QSlider, QSpinBox, QDoubleSpinBox,
    QComboBox, QPushButton, QFormLayout, QSizePolicy,
    QMessageBox, QProgressBar, QCheckBox, QScrollArea,
    QFrame, QToolButton
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QThread
from PySide6.QtGui import QIcon

from .compare_view import CompareView
from .styles import get_button_style

from logic import (
    FilterBase, FilterParameter, FilterPipeline,
    BilateralFilter, NLMFilter, WaveletFilter, FourierFilter,
    LinewiseFilter, NotchFilter, AnisotropicFilter,
    get_settings
)
from calnoise import NoiseAnalyzer
from optimize import (
    ScoreFunction, HillClimbingOptimizer, GridSearchOptimizer, OptimizationResult
)

# Step 색상 정의
STEP_COLORS = {
    0: {"bg": "#1a3a5c", "border": "#3498db", "title": "#3498db"},  # Blue
    1: {"bg": "#1a4a3a", "border": "#27ae60", "title": "#27ae60"},  # Green
    2: {"bg": "#4a3a1a", "border": "#e67e22", "title": "#e67e22"},  # Orange
}


class CollapsibleSection(QWidget):
    """접을 수 있는 섹션 위젯"""
    
    def __init__(self, title: str, step_index: int, parent=None):
        super().__init__(parent)
        self.step_index = step_index
        self._is_expanded = True
        self._setup_ui(title)
    
    def _setup_ui(self, title: str) -> None:
        colors = STEP_COLORS.get(self.step_index, STEP_COLORS[0])
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setSpacing(0)
        
        # 헤더 (클릭 가능)
        self.header = QFrame()
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg']};
                border: 2px solid {colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.mousePressEvent = self._toggle_content
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        # 제목
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {colors['title']};
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # 토글 버튼
        self.toggle_btn = QToolButton()
        self.toggle_btn.setText("▼")
        self.toggle_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                color: {colors['title']};
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        self.toggle_btn.clicked.connect(lambda: self._toggle_content(None))
        header_layout.addWidget(self.toggle_btn)
        
        layout.addWidget(self.header)
        
        # 콘텐츠 영역
        self.content = QWidget()
        self.content.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['bg']};
                border: 1px solid {colors['border']};
                border-top: none;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }}
        """)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(5)
        
        layout.addWidget(self.content)
    
    def _toggle_content(self, event) -> None:
        """콘텐츠 접기/펼치기"""
        self._is_expanded = not self._is_expanded
        self.content.setVisible(self._is_expanded)
        self.toggle_btn.setText("▼" if self._is_expanded else "▶")
    
    def expand(self) -> None:
        """펼치기"""
        self._is_expanded = True
        self.content.setVisible(True)
        self.toggle_btn.setText("▼")
    
    def collapse(self) -> None:
        """접기"""
        self._is_expanded = False
        self.content.setVisible(False)
        self.toggle_btn.setText("▶")
    
    def is_expanded(self) -> bool:
        return self._is_expanded
    
    def get_content_layout(self) -> QVBoxLayout:
        return self.content_layout
    
    def set_title(self, title: str) -> None:
        self.title_label.setText(title)


class ParameterWidget(QWidget):
    """필터 파라미터 위젯 생성기 - 라벨 위, 슬라이더 아래 레이아웃"""
    
    value_changed = Signal()
    
    def __init__(self, param: FilterParameter, parent=None):
        super().__init__(parent)
        self.param = param
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI 구성 - 세로 레이아웃 (라벨 위, 컨트롤 아래)"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 10)
        layout.setSpacing(5)
        
        # 라벨 (위)
        label = QLabel(self.param.display_name)
        label.setStyleSheet("font-weight: bold; font-size: 12px; color: #e94560;")
        label.setToolTip(self.param.description)
        layout.addWidget(label)
        
        # 컨트롤 (아래)
        if self.param.param_type == "int":
            self._create_int_widget(layout)
        elif self.param.param_type == "float":
            self._create_float_widget(layout)
        elif self.param.param_type == "choice":
            self._create_choice_widget(layout)
    
    def _create_int_widget(self, layout: QVBoxLayout) -> None:
        """정수 파라미터 위젯 - 전체 너비 슬라이더"""
        # 슬라이더 (전체 너비)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(self.param.min_value))
        self.slider.setMaximum(int(self.param.max_value))
        self.slider.setValue(int(self.param.value))
        self.slider.setSingleStep(int(self.param.step) if self.param.step else 1)
        self.slider.setMinimumHeight(25)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 8px; }
            QSlider::handle:horizontal { width: 20px; margin: -6px 0; }
        """)
        layout.addWidget(self.slider)
        
        # 값 표시 (슬라이더 아래)
        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        
        min_label = QLabel(str(int(self.param.min_value)))
        min_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(int(self.param.min_value))
        self.spinbox.setMaximum(int(self.param.max_value))
        self.spinbox.setValue(int(self.param.value))
        self.spinbox.setFixedWidth(80)
        self.spinbox.setAlignment(Qt.AlignCenter)
        
        max_label = QLabel(str(int(self.param.max_value)))
        max_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        
        value_row.addWidget(min_label)
        value_row.addStretch()
        value_row.addWidget(self.spinbox)
        value_row.addStretch()
        value_row.addWidget(max_label)
        layout.addLayout(value_row)
        
        # 연결
        self.slider.valueChanged.connect(self.spinbox.setValue)
        self.spinbox.valueChanged.connect(self.slider.setValue)
        self.spinbox.valueChanged.connect(lambda: self.value_changed.emit())
    
    def _create_float_widget(self, layout: QVBoxLayout) -> None:
        """실수 파라미터 위젯 - 전체 너비 슬라이더"""
        self.scale = 100
        
        # 슬라이더 (전체 너비)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(int(self.param.min_value * self.scale))
        self.slider.setMaximum(int(self.param.max_value * self.scale))
        self.slider.setValue(int(self.param.value * self.scale))
        self.slider.setMinimumHeight(25)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 8px; }
            QSlider::handle:horizontal { width: 20px; margin: -6px 0; }
        """)
        layout.addWidget(self.slider)
        
        # 값 표시 (슬라이더 아래)
        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        
        min_label = QLabel(f"{self.param.min_value:.1f}")
        min_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self.param.min_value)
        self.spinbox.setMaximum(self.param.max_value)
        self.spinbox.setValue(self.param.value)
        self.spinbox.setSingleStep(self.param.step if self.param.step else 0.1)
        self.spinbox.setDecimals(2)
        self.spinbox.setFixedWidth(90)
        self.spinbox.setAlignment(Qt.AlignCenter)
        
        max_label = QLabel(f"{self.param.max_value:.1f}")
        max_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        
        value_row.addWidget(min_label)
        value_row.addStretch()
        value_row.addWidget(self.spinbox)
        value_row.addStretch()
        value_row.addWidget(max_label)
        layout.addLayout(value_row)
        
        # 연결
        self.slider.valueChanged.connect(
            lambda v: self.spinbox.setValue(v / self.scale)
        )
        self.spinbox.valueChanged.connect(
            lambda v: self.slider.setValue(int(v * self.scale))
        )
        self.spinbox.valueChanged.connect(lambda: self.value_changed.emit())
    
    def _create_choice_widget(self, layout: QVBoxLayout) -> None:
        """선택 파라미터 위젯"""
        self.combo = QComboBox()
        self.combo.setMinimumHeight(30)
        for choice in self.param.choices:
            self.combo.addItem(str(choice))
        
        # 현재 값 설정
        index = self.param.choices.index(self.param.value) if self.param.value in self.param.choices else 0
        self.combo.setCurrentIndex(index)
        self.combo.currentIndexChanged.connect(lambda: self.value_changed.emit())
        
        layout.addWidget(self.combo)
    
    def get_value(self):
        """현재 값 반환"""
        if self.param.param_type == "int":
            return self.spinbox.value()
        elif self.param.param_type == "float":
            return self.spinbox.value()
        elif self.param.param_type == "choice":
            return self.param.choices[self.combo.currentIndex()]
    
    def set_value(self, value):
        """값 설정"""
        if self.param.param_type == "int":
            self.spinbox.setValue(int(value))
        elif self.param.param_type == "float":
            self.spinbox.setValue(float(value))
        elif self.param.param_type == "choice":
            if value in self.param.choices:
                idx = self.param.choices.index(value)
                self.combo.setCurrentIndex(idx)


class SingleFilterOptWorker(QThread):
    """단일 필터 최적화 작업 스레드"""
    
    progress = Signal(int, int, float)  # current, total, score
    finished = Signal(object)  # OptimizationResult
    
    def __init__(
        self,
        optimizer,
        image: np.ndarray,
        filter_name: str,
        current_params: dict,
        parent=None
    ):
        super().__init__(parent)
        self.optimizer = optimizer
        self.image = image
        self.filter_name = filter_name
        self.current_params = current_params
    
    def run(self):
        """최적화 실행"""
        def apply_filter_func(img, filter_name, params):
            """필터 적용 함수"""
            filter_obj = FilterPipeline.create_filter(filter_name)
            if filter_obj:
                for name, value in params.items():
                    filter_obj.set_parameter(name, value)
                return filter_obj.apply(img)
            return img
        
        def analyze_func(img):
            """노이즈 분석 함수"""
            analyzer = NoiseAnalyzer()
            metrics = analyzer.analyze(img)
            return metrics.to_dict()
        
        self.optimizer.progress_callback = lambda c, t, s: self.progress.emit(c, t, s)
        
        result = self.optimizer.optimize(
            self.image,
            [self.filter_name],  # 단일 필터
            {self.filter_name: self.current_params},
            apply_filter_func,
            analyze_func
        )
        
        self.finished.emit(result)
    
    def stop(self):
        """최적화 중지"""
        if self.optimizer:
            self.optimizer.stop()


class SingleFilterTab(QWidget):
    """개별 필터 탭"""
    
    # 이미지 저장 요청 시그널
    save_requested = Signal(np.ndarray, str)
    # 파라미터 변경 시그널 (다른 탭에 알림)
    parameters_changed = Signal(str, dict)  # filter_name, params
    
    # 실시간 미리보기 딜레이 (ms)
    PREVIEW_DELAY = 300
    
    def __init__(self, filter_class: Type[FilterBase], parent=None):
        super().__init__(parent)
        self.filter = filter_class()
        self._original_image: Optional[np.ndarray] = None
        self._processed_image: Optional[np.ndarray] = None
        self._param_widgets: dict[str, ParameterWidget] = {}
        self._auto_apply = True
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._apply_filter_internal)
        self._optimization_worker: Optional[SingleFilterOptWorker] = None
        self._params_before_optimize: Optional[dict] = None  # 최적화 이전 파라미터 저장
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """UI 구성"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        
        # 왼쪽: 파라미터 패널
        param_panel = QWidget()
        param_panel.setFixedWidth(300)
        param_layout = QVBoxLayout(param_panel)
        param_layout.setContentsMargins(5, 5, 5, 5)
        
        # 필터 설명
        desc_label = QLabel(self.filter.description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #a0a0a0; font-style: italic;")
        param_layout.addWidget(desc_label)
        
        # 자동 적용 체크박스
        self.auto_apply_check = QCheckBox("Auto Apply (Real-time Preview)")
        self.auto_apply_check.setChecked(True)
        self.auto_apply_check.toggled.connect(self._on_auto_apply_changed)
        param_layout.addWidget(self.auto_apply_check)
        
        # 파라미터 그룹 - 세로 레이아웃으로 변경
        param_group = QGroupBox("Parameters")
        param_group_layout = QVBoxLayout(param_group)
        param_group_layout.setSpacing(5)
        param_group_layout.setContentsMargins(10, 15, 10, 10)
        
        for name, param in self.filter.get_parameters().items():
            widget = ParameterWidget(param)
            widget.value_changed.connect(self._on_param_changed)
            self._param_widgets[name] = widget
            param_group_layout.addWidget(widget)
        
        param_layout.addWidget(param_group)
        
        # 버튼들
        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        
        self.apply_btn = QPushButton("Apply Filter")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self._apply_filter)
        button_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save Result")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_image)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset Parameters")
        self.reset_btn.clicked.connect(self._reset_params)
        button_layout.addWidget(self.reset_btn)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3a3a3a;")
        button_layout.addWidget(separator)
        
        # Auto Optimize / Revert 버튼 레이아웃
        opt_btn_layout = QHBoxLayout()
        opt_btn_layout.setSpacing(5)
        
        # Auto Optimize 버튼
        self.optimize_btn = QPushButton("🔧 Optimize")
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: #1a1a2e;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #5a5a5a;
                color: #a0a0a0;
            }
        """)
        self.optimize_btn.clicked.connect(self._start_optimization)
        opt_btn_layout.addWidget(self.optimize_btn)
        
        # Revert 버튼 (이전 값으로 되돌리기)
        self.revert_btn = QPushButton("↩ Revert")
        self.revert_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #5a5a5a;
                color: #a0a0a0;
            }
        """)
        self.revert_btn.setEnabled(False)
        self.revert_btn.clicked.connect(self._revert_optimization)
        opt_btn_layout.addWidget(self.revert_btn)
        
        button_layout.addLayout(opt_btn_layout)
        
        # 최적화 중지 버튼
        self.stop_optimize_btn = QPushButton("⬛ Stop")
        self.stop_optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        self.stop_optimize_btn.setVisible(False)
        self.stop_optimize_btn.clicked.connect(self._stop_optimization)
        button_layout.addWidget(self.stop_optimize_btn)
        
        # 최적화 진행/결과 표시
        self.optimize_progress = QProgressBar()
        self.optimize_progress.setVisible(False)
        self.optimize_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                text-align: center;
                background-color: #2a2a2a;
                max-height: 15px;
            }
            QProgressBar::chunk {
                background-color: #f39c12;
            }
        """)
        button_layout.addWidget(self.optimize_progress)
        
        self.optimize_result_label = QLabel("")
        self.optimize_result_label.setWordWrap(True)
        self.optimize_result_label.setStyleSheet("color: #a0a0a0; font-size: 9px;")
        button_layout.addWidget(self.optimize_result_label)
        
        param_layout.addLayout(button_layout)
        param_layout.addStretch()
        
        # 오른쪽: 비교 뷰 (1280x960 최적화)
        self.compare_view = CompareView()
        self.compare_view.setMinimumSize(1280, 500)
        
        layout.addWidget(param_panel)
        layout.addWidget(self.compare_view, stretch=1)
    
    def _load_settings(self) -> None:
        """설정에서 파라미터 불러오기"""
        settings = get_settings()
        saved_params = settings.get_filter_params(self.filter.name)
        
        for name, value in saved_params.items():
            if name in self._param_widgets:
                self._param_widgets[name].set_value(value)
    
    def _save_settings(self) -> None:
        """현재 파라미터를 설정에 저장"""
        settings = get_settings()
        params = {}
        for name, widget in self._param_widgets.items():
            params[name] = widget.get_value()
        settings.set_filter_params(self.filter.name, params)
        settings.save()
    
    def _on_auto_apply_changed(self, checked: bool) -> None:
        """자동 적용 토글"""
        self._auto_apply = checked
        self.apply_btn.setVisible(not checked)
    
    def _on_param_changed(self) -> None:
        """파라미터 변경 시 처리"""
        # 파라미터 변경 알림
        params = {name: widget.get_value() for name, widget in self._param_widgets.items()}
        self.parameters_changed.emit(self.filter.name, params)
        
        # 자동 적용 (딜레이 적용)
        if self._auto_apply and self._original_image is not None:
            self._preview_timer.start(self.PREVIEW_DELAY)
    
    def set_image(self, image: Optional[np.ndarray]) -> None:
        """원본 이미지 설정"""
        self._original_image = image
        self._processed_image = None
        self.compare_view.set_original_image(image)
        self.compare_view.set_processed_image(None)
        self.save_btn.setEnabled(False)
        
        # 이미지가 설정되면 자동 적용
        if self._auto_apply and image is not None:
            self._preview_timer.start(self.PREVIEW_DELAY)
    
    def _apply_filter(self) -> None:
        """필터 적용 (버튼 클릭)"""
        self._apply_filter_internal()
    
    def _apply_filter_internal(self) -> None:
        """필터 적용 (내부)"""
        if self._original_image is None:
            return
        
        # 파라미터 업데이트
        for name, widget in self._param_widgets.items():
            self.filter.set_parameter(name, widget.get_value())
        
        try:
            self._processed_image = self.filter.apply(self._original_image)
            self.compare_view.set_processed_image(self._processed_image)
            self.save_btn.setEnabled(True)
            self._save_settings()
        except Exception as e:
            print(f"Filter error: {e}")
    
    def _save_image(self) -> None:
        """이미지 저장 요청"""
        if self._processed_image is not None:
            self.save_requested.emit(
                self._processed_image, 
                self.filter.get_filter_info()
            )
    
    def _reset_params(self) -> None:
        """파라미터 초기화"""
        filter_class = type(self.filter)
        self.filter = filter_class()
        
        for name, param in self.filter.get_parameters().items():
            if name in self._param_widgets:
                self._param_widgets[name].set_value(param.value)
    
    def get_current_params(self) -> dict:
        """현재 파라미터 반환"""
        return {name: widget.get_value() for name, widget in self._param_widgets.items()}
    
    def set_params(self, params: dict) -> None:
        """파라미터 설정"""
        for name, value in params.items():
            if name in self._param_widgets:
                self._param_widgets[name].set_value(value)
    
    def _revert_optimization(self) -> None:
        """최적화 이전 값으로 되돌리기"""
        if self._params_before_optimize is not None:
            for name, value in self._params_before_optimize.items():
                if name in self._param_widgets:
                    self._param_widgets[name].set_value(value)
            
            self.optimize_result_label.setText("↩ Reverted")
            self.optimize_result_label.setStyleSheet("color: #9b59b6; font-size: 9px;")
            self.revert_btn.setEnabled(False)
            
            # 필터 다시 적용
            self._apply_filter_internal()
    
    def _start_optimization(self) -> None:
        """최적화 시작"""
        if self._original_image is None:
            QMessageBox.warning(self, "Warning", "Please load an image first.")
            return
        
        # 현재 파라미터 저장 (Revert용)
        self._params_before_optimize = self.get_current_params()
        
        # 현재 파라미터 수집
        current_params = self.get_current_params()
        
        # Hill Climbing 사용 (단일 필터라 빠름)
        score_func = ScoreFunction()
        optimizer = HillClimbingOptimizer(
            score_func,
            max_iterations=50  # 단일 필터라 적은 반복
        )
        
        # UI 상태 업데이트
        self.optimize_btn.setEnabled(False)
        self.stop_optimize_btn.setVisible(True)
        self.optimize_progress.setVisible(True)
        self.optimize_progress.setValue(0)
        self.optimize_result_label.setText("Optimizing...")
        self.optimize_result_label.setStyleSheet("color: #a0a0a0; font-size: 9px;")
        
        # 워커 스레드 시작
        self._optimization_worker = SingleFilterOptWorker(
            optimizer,
            self._original_image,
            self.filter.name,
            current_params
        )
        self._optimization_worker.progress.connect(self._on_optimization_progress)
        self._optimization_worker.finished.connect(self._on_optimization_finished)
        self._optimization_worker.start()
    
    def _stop_optimization(self) -> None:
        """최적화 중지"""
        if self._optimization_worker:
            self._optimization_worker.stop()
            self.optimize_result_label.setText("Stopping...")
    
    def _on_optimization_progress(self, current: int, total: int, score: float) -> None:
        """최적화 진행 상황 업데이트"""
        if total > 0:
            self.optimize_progress.setMaximum(total)
            self.optimize_progress.setValue(current)
        self.optimize_result_label.setText(f"Iter {current}/{total}")
    
    def _on_optimization_finished(self, result: OptimizationResult) -> None:
        """최적화 완료 처리"""
        # UI 상태 복원
        self.optimize_btn.setEnabled(True)
        self.stop_optimize_btn.setVisible(False)
        self.optimize_progress.setVisible(False)
        
        if result.improved:
            # 최적화된 파라미터 적용
            filter_name = self.filter.name
            if filter_name in result.best_params:
                for name, value in result.best_params[filter_name].items():
                    if name in self._param_widgets:
                        self._param_widgets[name].set_value(value)
            
            # 결과 표시
            improvement = ((result.best_score - result.initial_score) / abs(result.initial_score) * 100) if result.initial_score != 0 else 0
            self.optimize_result_label.setText(
                f"✅ Done! {result.elapsed_time:.1f}s"
            )
            self.optimize_result_label.setStyleSheet("color: #27ae60; font-size: 9px;")
            
            # Revert 버튼 활성화
            self.revert_btn.setEnabled(True)
            
            # 필터 적용
            self._apply_filter_internal()
        else:
            self.optimize_result_label.setText("No improvement")
            self.optimize_result_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
            # 개선이 없어도 Revert 가능하게
            self.revert_btn.setEnabled(True)
        
        self._optimization_worker = None


class OptimizationWorker(QThread):
    """최적화 작업 스레드"""
    
    progress = Signal(int, int, float)  # current, total, score
    finished = Signal(object)  # OptimizationResult
    
    def __init__(
        self,
        optimizer,
        image: np.ndarray,
        pipeline_filters: list,
        current_params: dict,
        parent=None
    ):
        super().__init__(parent)
        self.optimizer = optimizer
        self.image = image
        self.pipeline_filters = pipeline_filters
        self.current_params = current_params
    
    def run(self):
        """최적화 실행"""
        def apply_filter_func(img, filter_name, params):
            """필터 적용 함수"""
            filter_obj = FilterPipeline.create_filter(filter_name)
            if filter_obj:
                for name, value in params.items():
                    filter_obj.set_parameter(name, value)
                return filter_obj.apply(img)
            return img
        
        def analyze_func(img):
            """노이즈 분석 함수"""
            analyzer = NoiseAnalyzer()
            metrics = analyzer.analyze(img)
            return metrics.to_dict()
        
        self.optimizer.progress_callback = lambda c, t, s: self.progress.emit(c, t, s)
        
        result = self.optimizer.optimize(
            self.image,
            self.pipeline_filters,
            self.current_params,
            apply_filter_func,
            analyze_func
        )
        
        self.finished.emit(result)
    
    def stop(self):
        """최적화 중지"""
        if self.optimizer:
            self.optimizer.stop()


class PipelineTab(QWidget):
    """다중 필터 파이프라인 탭"""
    
    save_requested = Signal(np.ndarray, str)
    image_processed = Signal(np.ndarray, np.ndarray)  # 최적화 완료 시 노이즈 분석 위해
    
    # 실시간 미리보기 딜레이 (ms)
    PREVIEW_DELAY = 500
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pipeline = FilterPipeline(max_filters=3)
        self._original_image: Optional[np.ndarray] = None
        self._processed_image: Optional[np.ndarray] = None
        self._filter_widgets: list[dict] = []
        self._auto_apply = True
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._apply_pipeline_internal)
        self._external_params: dict[str, dict] = {}  # 다른 탭에서 온 파라미터
        self._optimization_worker: Optional[OptimizationWorker] = None
        self._params_before_optimize: Optional[dict] = None  # 최적화 이전 파라미터 저장
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """UI 구성 - Collapsible 섹션과 스크롤 지원"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        
        # 왼쪽: 파이프라인 설정 패널 (스크롤 가능)
        config_container = QWidget()
        config_container.setFixedWidth(380)
        container_layout = QVBoxLayout(config_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
            }
        """)
        
        # 스크롤 내부 위젯
        scroll_content = QWidget()
        config_layout = QVBoxLayout(scroll_content)
        config_layout.setContentsMargins(5, 5, 5, 5)
        config_layout.setSpacing(10)
        
        # 설명
        desc_label = QLabel(
            "Select up to 3 filters to apply sequentially. "
            "Click headers to expand/collapse sections."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #a0a0a0; font-style: italic; font-size: 11px;")
        config_layout.addWidget(desc_label)
        
        # 자동 적용 체크박스
        self.auto_apply_check = QCheckBox("Auto Apply (Real-time Preview)")
        self.auto_apply_check.setChecked(True)
        self.auto_apply_check.toggled.connect(self._on_auto_apply_changed)
        config_layout.addWidget(self.auto_apply_check)
        
        # Expand All / Collapse All 버튼
        expand_collapse_layout = QHBoxLayout()
        expand_all_btn = QPushButton("Expand All")
        expand_all_btn.setFixedHeight(25)
        expand_all_btn.clicked.connect(self._expand_all_sections)
        collapse_all_btn = QPushButton("Collapse All")
        collapse_all_btn.setFixedHeight(25)
        collapse_all_btn.clicked.connect(self._collapse_all_sections)
        expand_collapse_layout.addWidget(expand_all_btn)
        expand_collapse_layout.addWidget(collapse_all_btn)
        config_layout.addLayout(expand_collapse_layout)
        
        # 필터 선택 그룹들 - Collapsible 섹션으로
        filter_names = ["(None)"] + FilterPipeline.get_available_filter_names()
        self._sections: list[CollapsibleSection] = []
        
        for i in range(3):
            section = CollapsibleSection(f"Step {i+1}: (None)", i)
            self._sections.append(section)
            
            content_layout = section.get_content_layout()
            
            # 필터 선택 콤보박스
            combo = QComboBox()
            combo.setMinimumHeight(35)
            combo.setStyleSheet("font-size: 12px;")
            for name in filter_names:
                combo.addItem(name)
            combo.currentIndexChanged.connect(lambda idx, num=i: self._on_filter_changed(num, idx))
            content_layout.addWidget(combo)
            
            # 파라미터 컨테이너
            param_container = QWidget()
            param_layout = QVBoxLayout(param_container)
            param_layout.setContentsMargins(0, 10, 0, 0)
            param_layout.setSpacing(5)
            content_layout.addWidget(param_container)
            
            config_layout.addWidget(section)
            
            self._filter_widgets.append({
                "combo": combo,
                "param_container": param_container,
                "param_layout": param_layout,
                "param_widgets": {},
                "filter": None,
                "section": section
            })
        
        # 스크롤 영역에 콘텐츠 설정
        scroll_area.setWidget(scroll_content)
        container_layout.addWidget(scroll_area, stretch=1)
        
        # 버튼들 (스크롤 영역 외부 - 항상 보임)
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(8)
        
        self.apply_btn = QPushButton("Apply Pipeline")
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self._apply_pipeline)
        self.apply_btn.setVisible(False)
        button_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save Final Result")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save_image)
        button_layout.addWidget(self.save_btn)
        
        self.clear_btn = QPushButton("Clear Pipeline")
        self.clear_btn.clicked.connect(self._clear_pipeline)
        button_layout.addWidget(self.clear_btn)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3a3a3a;")
        button_layout.addWidget(separator)
        
        # 자동 최적화 섹션
        optimize_label = QLabel("Auto Optimization")
        optimize_label.setStyleSheet("font-weight: bold; color: #f39c12; font-size: 12px;")
        button_layout.addWidget(optimize_label)
        
        # 최적화 방법 선택
        method_layout = QHBoxLayout()
        method_label = QLabel("Method:")
        method_label.setStyleSheet("color: #a0a0a0;")
        self.optimize_method_combo = QComboBox()
        self.optimize_method_combo.addItem("Hill Climbing (Fast)")
        self.optimize_method_combo.addItem("Grid Search (Thorough)")
        self.optimize_method_combo.setMinimumHeight(28)
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.optimize_method_combo, stretch=1)
        button_layout.addLayout(method_layout)
        
        # Auto Optimize / Revert 버튼 레이아웃
        opt_btn_layout = QHBoxLayout()
        opt_btn_layout.setSpacing(5)
        
        # Auto Optimize 버튼
        self.optimize_btn = QPushButton("🔧 Optimize")
        self.optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: #1a1a2e;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:disabled {
                background-color: #5a5a5a;
                color: #a0a0a0;
            }
        """)
        self.optimize_btn.clicked.connect(self._start_optimization)
        opt_btn_layout.addWidget(self.optimize_btn)
        
        # Revert 버튼 (이전 값으로 되돌리기)
        self.revert_btn = QPushButton("↩ Revert")
        self.revert_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #5a5a5a;
                color: #a0a0a0;
            }
        """)
        self.revert_btn.setEnabled(False)
        self.revert_btn.clicked.connect(self._revert_optimization)
        opt_btn_layout.addWidget(self.revert_btn)
        
        button_layout.addLayout(opt_btn_layout)
        
        # 최적화 중지 버튼
        self.stop_optimize_btn = QPushButton("⬛ Stop")
        self.stop_optimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_optimize_btn.setVisible(False)
        self.stop_optimize_btn.clicked.connect(self._stop_optimization)
        button_layout.addWidget(self.stop_optimize_btn)
        
        # 진행 상태
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                text-align: center;
                background-color: #2a2a2a;
            }
            QProgressBar::chunk {
                background-color: #f39c12;
            }
        """)
        button_layout.addWidget(self.progress)
        
        # 최적화 결과 표시
        self.optimize_result_label = QLabel("")
        self.optimize_result_label.setWordWrap(True)
        self.optimize_result_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")
        button_layout.addWidget(self.optimize_result_label)
        
        container_layout.addWidget(button_widget)
        
        # 오른쪽: 비교 뷰 (1280x960 최적화)
        self.compare_view = CompareView()
        self.compare_view.setMinimumSize(1280, 500)
        
        layout.addWidget(config_container)
        layout.addWidget(self.compare_view, stretch=1)
        
        # 기본 파이프라인 설정
        self._set_default_pipeline()
    
    def _expand_all_sections(self) -> None:
        """모든 섹션 펼치기"""
        for section in self._sections:
            section.expand()
    
    def _collapse_all_sections(self) -> None:
        """모든 섹션 접기"""
        for section in self._sections:
            section.collapse()
    
    def _set_default_pipeline(self) -> None:
        """기본 파이프라인 설정: Linewise -> Notch -> NLM (약하게)"""
        settings = get_settings()
        pipeline_filters = settings.get_pipeline_filters()
        
        if not pipeline_filters:
            pipeline_filters = ["Linewise", "Notch", "NLM"]
        
        filter_names = FilterPipeline.get_available_filter_names()
        
        # 기본 파라미터 (약한 NLM)
        default_params = {
            "Linewise": {"method": "mean", "strength": 0.8},
            "Notch": {"center_freq": 0.25, "bandwidth": 0.05, "direction": "both"},
            "NLM": {"h": 5.0, "templateWindowSize": 7, "searchWindowSize": 21},
        }
        
        for i, filter_name in enumerate(pipeline_filters[:3]):
            if filter_name in filter_names:
                filter_idx = filter_names.index(filter_name) + 1
                self._filter_widgets[i]["combo"].setCurrentIndex(filter_idx)
                
                # 저장된 파라미터 또는 외부 파라미터 또는 기본값 사용
                fw = self._filter_widgets[i]
                if fw["filter"]:
                    saved = settings.get_filter_params(filter_name)
                    params = saved if saved else default_params.get(filter_name, {})
                    
                    for param_name, param_value in params.items():
                        if param_name in fw["param_widgets"]:
                            fw["param_widgets"][param_name].set_value(param_value)
    
    def _on_auto_apply_changed(self, checked: bool) -> None:
        """자동 적용 토글"""
        self._auto_apply = checked
        self.apply_btn.setVisible(not checked)
    
    def _on_filter_changed(self, step: int, index: int) -> None:
        """필터 선택 변경 처리"""
        fw = self._filter_widgets[step]
        section = fw.get("section")
        
        # 기존 파라미터 위젯 제거
        while fw["param_layout"].count():
            item = fw["param_layout"].takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        fw["param_widgets"].clear()
        
        if index == 0:
            fw["filter"] = None
            # 섹션 제목 업데이트
            if section:
                section.set_title(f"Step {step+1}: (None)")
            self._trigger_auto_apply()
            return
        
        # 새 필터 생성
        filter_name = FilterPipeline.get_available_filter_names()[index - 1]
        filter_obj = FilterPipeline.create_filter(filter_name)
        fw["filter"] = filter_obj
        
        # 섹션 제목 업데이트
        if section:
            section.set_title(f"Step {step+1}: {filter_name}")
        
        # 파라미터 위젯 생성
        if filter_obj:
            # 외부에서 전달받은 파라미터 또는 저장된 설정 사용
            settings = get_settings()
            saved_params = settings.get_filter_params(filter_name)
            external_params = self._external_params.get(filter_name, {})
            
            for name, param in filter_obj.get_parameters().items():
                widget = ParameterWidget(param)
                
                # 외부 파라미터 우선, 그 다음 저장된 설정
                if name in external_params:
                    widget.set_value(external_params[name])
                elif name in saved_params:
                    widget.set_value(saved_params[name])
                
                widget.value_changed.connect(self._trigger_auto_apply)
                fw["param_widgets"][name] = widget
                
                fw["param_layout"].addWidget(widget)
        
        self._trigger_auto_apply()
    
    def update_filter_params(self, filter_name: str, params: dict) -> None:
        """다른 탭에서 파라미터 변경 시 호출"""
        self._external_params[filter_name] = params
        
        # 현재 파이프라인에서 해당 필터가 있으면 파라미터 업데이트
        for fw in self._filter_widgets:
            if fw["filter"] and fw["filter"].name == filter_name:
                for name, value in params.items():
                    if name in fw["param_widgets"]:
                        fw["param_widgets"][name].set_value(value)
    
    def _trigger_auto_apply(self) -> None:
        """자동 적용 트리거"""
        if self._auto_apply and self._original_image is not None:
            self._preview_timer.start(self.PREVIEW_DELAY)
    
    def set_image(self, image: Optional[np.ndarray]) -> None:
        """원본 이미지 설정"""
        self._original_image = image
        self._processed_image = None
        self.compare_view.set_original_image(image)
        self.compare_view.set_processed_image(None)
        self.save_btn.setEnabled(False)
        
        if self._auto_apply and image is not None:
            self._preview_timer.start(self.PREVIEW_DELAY)
    
    def _apply_pipeline(self) -> None:
        """파이프라인 적용 (버튼 클릭)"""
        self._apply_pipeline_internal()
    
    def _apply_pipeline_internal(self) -> None:
        """파이프라인 적용 (내부)"""
        if self._original_image is None:
            return
        
        # 파이프라인 구성
        self.pipeline.clear()
        selected_filters = []
        
        for fw in self._filter_widgets:
            if fw["filter"] is not None:
                # 파라미터 업데이트
                for name, widget in fw["param_widgets"].items():
                    fw["filter"].set_parameter(name, widget.get_value())
                self.pipeline.add_filter(fw["filter"])
                selected_filters.append(fw["filter"].name)
        
        if self.pipeline.get_filter_count() == 0:
            return
        
        try:
            self._processed_image = self.pipeline.apply(self._original_image)
            self.compare_view.set_processed_image(self._processed_image)
            self.save_btn.setEnabled(True)
            
            # 파이프라인 설정 저장
            settings = get_settings()
            settings.set_pipeline_filters(selected_filters)
            settings.save()
        except Exception as e:
            print(f"Pipeline error: {e}")
    
    def _save_image(self) -> None:
        """이미지 저장 요청"""
        if self._processed_image is not None:
            self.save_requested.emit(
                self._processed_image,
                self.pipeline.get_pipeline_info()
            )
    
    def _clear_pipeline(self) -> None:
        """파이프라인 초기화"""
        for fw in self._filter_widgets:
            fw["combo"].setCurrentIndex(0)
        self.pipeline.clear()
    
    def _revert_optimization(self) -> None:
        """최적화 이전 값으로 되돌리기"""
        if self._params_before_optimize is not None:
            for fw in self._filter_widgets:
                if fw["filter"] is not None:
                    filter_name = fw["filter"].name
                    if filter_name in self._params_before_optimize:
                        for name, value in self._params_before_optimize[filter_name].items():
                            if name in fw["param_widgets"]:
                                fw["param_widgets"][name].set_value(value)
            
            self.optimize_result_label.setText("↩ Reverted to previous parameters")
            self.optimize_result_label.setStyleSheet("color: #9b59b6; font-size: 10px;")
            self.revert_btn.setEnabled(False)
            
            # 파이프라인 다시 적용
            self._apply_pipeline_internal()
    
    def _start_optimization(self) -> None:
        """최적화 시작"""
        if self._original_image is None:
            QMessageBox.warning(self, "Warning", "Please load an image first.")
            return
        
        # 현재 파이프라인에서 필터 가져오기
        pipeline_filters = []
        current_params = {}
        
        # 현재 파라미터 저장 (Revert용)
        self._params_before_optimize = {}
        
        for fw in self._filter_widgets:
            if fw["filter"] is not None:
                filter_name = fw["filter"].name
                pipeline_filters.append(filter_name)
                
                # 현재 파라미터 수집
                params = {}
                for name, widget in fw["param_widgets"].items():
                    params[name] = widget.get_value()
                current_params[filter_name] = params
                
                # Revert용 파라미터 저장
                self._params_before_optimize[filter_name] = params.copy()
        
        if not pipeline_filters:
            QMessageBox.warning(self, "Warning", "Please select at least one filter.")
            return
        
        # 최적화 방법 선택
        method_idx = self.optimize_method_combo.currentIndex()
        score_func = ScoreFunction()
        
        if method_idx == 0:
            # Hill Climbing
            optimizer = HillClimbingOptimizer(
                score_func,
                max_iterations=100
            )
        else:
            # Grid Search
            optimizer = GridSearchOptimizer(
                score_func,
                max_iterations=500,
                coarse_divisions=3,
                fine_divisions=5
            )
        
        # UI 상태 업데이트
        self.optimize_btn.setEnabled(False)
        self.stop_optimize_btn.setVisible(True)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.optimize_result_label.setText("Optimizing...")
        
        # 워커 스레드 시작
        self._optimization_worker = OptimizationWorker(
            optimizer,
            self._original_image,
            pipeline_filters,
            current_params
        )
        self._optimization_worker.progress.connect(self._on_optimization_progress)
        self._optimization_worker.finished.connect(self._on_optimization_finished)
        self._optimization_worker.start()
    
    def _stop_optimization(self) -> None:
        """최적화 중지"""
        if self._optimization_worker:
            self._optimization_worker.stop()
            self.optimize_result_label.setText("Stopping...")
    
    def _on_optimization_progress(self, current: int, total: int, score: float) -> None:
        """최적화 진행 상황 업데이트"""
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(current)
        self.optimize_result_label.setText(f"Iteration {current}/{total}, Score: {score:.2f}")
    
    def _on_optimization_finished(self, result: OptimizationResult) -> None:
        """최적화 완료 처리"""
        # UI 상태 복원
        self.optimize_btn.setEnabled(True)
        self.stop_optimize_btn.setVisible(False)
        self.progress.setVisible(False)
        
        # Revert 버튼 활성화 (최적화 시도 후에는 항상 되돌릴 수 있음)
        self.revert_btn.setEnabled(True)
        
        if result.improved:
            # 최적화된 파라미터 적용
            for fw in self._filter_widgets:
                if fw["filter"] is not None:
                    filter_name = fw["filter"].name
                    if filter_name in result.best_params:
                        for name, value in result.best_params[filter_name].items():
                            if name in fw["param_widgets"]:
                                fw["param_widgets"][name].set_value(value)
            
            # 결과 표시
            improvement = ((result.best_score - result.initial_score) / abs(result.initial_score) * 100) if result.initial_score != 0 else 0
            self.optimize_result_label.setText(
                f"✅ Optimized! Score: {result.initial_score:.1f} → {result.best_score:.1f} "
                f"(+{improvement:.1f}%)\n"
                f"Time: {result.elapsed_time:.1f}s, Iterations: {result.iterations}"
            )
            self.optimize_result_label.setStyleSheet("color: #27ae60; font-size: 10px;")
            
            # 필터 적용
            self._apply_pipeline_internal()
        else:
            self.optimize_result_label.setText(
                f"No improvement found.\n"
                f"Time: {result.elapsed_time:.1f}s, Iterations: {result.iterations}"
            )
            self.optimize_result_label.setStyleSheet("color: #e74c3c; font-size: 10px;")
        
        self._optimization_worker = None


class FilterTabWidget(QTabWidget):
    """모든 필터 탭을 포함하는 메인 탭 위젯"""
    
    save_requested = Signal(np.ndarray, str)
    
    # 필터 클래스 목록
    FILTER_CLASSES = [
        ("1. Bilateral", BilateralFilter),
        ("2. NLM", NLMFilter),
        ("3. Wavelet", WaveletFilter),
        ("4. Fourier", FourierFilter),
        ("5. Line-wise", LinewiseFilter),
        ("6. Notch", NotchFilter),
        ("7. Anisotropic", AnisotropicFilter),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs: list = []
        self._pipeline_tab: Optional[PipelineTab] = None
        self._setup_tabs()
    
    def _setup_tabs(self) -> None:
        """탭 구성"""
        # 개별 필터 탭
        for name, filter_class in self.FILTER_CLASSES:
            tab = SingleFilterTab(filter_class)
            tab.save_requested.connect(self._on_save_requested)
            tab.parameters_changed.connect(self._on_parameters_changed)
            self.addTab(tab, name)
            self._tabs.append(tab)
        
        # 파이프라인 탭
        self._pipeline_tab = PipelineTab()
        self._pipeline_tab.save_requested.connect(self._on_save_requested)
        self.addTab(self._pipeline_tab, "8. Pipeline")
        self._tabs.append(self._pipeline_tab)
    
    def set_image(self, image: Optional[np.ndarray]) -> None:
        """모든 탭에 이미지 설정"""
        for tab in self._tabs:
            tab.set_image(image)
    
    def _on_save_requested(self, image: np.ndarray, filter_info: str) -> None:
        """저장 요청 전달"""
        self.save_requested.emit(image, filter_info)
    
    def _on_parameters_changed(self, filter_name: str, params: dict) -> None:
        """개별 탭에서 파라미터 변경 시 파이프라인 탭에 전달"""
        if self._pipeline_tab:
            self._pipeline_tab.update_filter_params(filter_name, params)
