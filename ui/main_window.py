# -*- coding: utf-8 -*-
"""
메인 윈도우 구현
파일 열기, 탭 컨테이너, 상태바 포함
설정 저장/불러오기, 노이즈 분석 지원
"""
import os
import sys
from pathlib import Path
from typing import Optional
import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QPushButton, QLabel, QFrame, QToolBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QCloseEvent

from .filter_tabs import FilterTabWidget
from .styles import get_stylesheet, COLORS
from .noise_panel import NoiseAnalysisWindow
from .optimization_settings import OptimizationSettingsWindow

from logic import FileIO, get_settings


class MainWindow(QMainWindow):
    """SEM Denoising 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        
        # 설정 로드
        self.settings = get_settings()
        
        # 파일 I/O 핸들러
        self.file_io = FileIO()
        self._current_image: Optional[np.ndarray] = None
        
        # 노이즈 분석 윈도우
        self.noise_window = NoiseAnalysisWindow(self)
        
        # 최적화 설정 윈도우
        self.optimization_settings_window = OptimizationSettingsWindow(self)
        
        self._setup_window()
        self._setup_ui()
        self._setup_menubar()
        self._setup_statusbar()
        self._apply_styles()
        self._connect_noise_signals()
        self._load_last_file()
        
        # 노이즈 분석 윈도우 자동 표시
        self.noise_window.show()
        
        # 최적화 설정 윈도우 자동 표시
        self.optimization_settings_window.show()
    
    def _setup_window(self) -> None:
        """윈도우 기본 설정 - 1280x960 이미지에 최적화"""
        self.setWindowTitle("SEM Image Denoising")
        
        # 설정에서 윈도우 위치/크기 로드
        geom = self.settings.get("window_geometry", {})
        width = geom.get("width", 1700)  # 1280*2 + 패널(350) 정도
        height = geom.get("height", 1050)  # 960 + 여유
        x = geom.get("x", 50)
        y = geom.get("y", 50)
        
        self.setMinimumSize(1400, 900)
        self.setGeometry(x, y, width, height)
        
        # 드래그 앤 드롭 활성화
        self.setAcceptDrops(True)
    
    def _setup_ui(self) -> None:
        """UI 구성"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 상단: 파일 정보 및 컨트롤
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 5, 10, 5)
        
        # 파일 열기 버튼
        self.open_btn = QPushButton("Open Image")
        self.open_btn.setObjectName("primaryButton")
        self.open_btn.clicked.connect(self._open_file)
        top_layout.addWidget(self.open_btn)
        
        # 파일명 레이블
        self.file_label = QLabel("No file loaded")
        self.file_label.setObjectName("subtitleLabel")
        top_layout.addWidget(self.file_label)
        
        top_layout.addStretch()
        
        # 출력 폴더 열기
        self.output_btn = QPushButton("Open Output Folder")
        self.output_btn.clicked.connect(self._open_output_folder)
        top_layout.addWidget(self.output_btn)
        
        main_layout.addWidget(top_bar)
        
        # 필터 탭 위젯
        self.filter_tabs = FilterTabWidget()
        self.filter_tabs.save_requested.connect(self._save_image)
        main_layout.addWidget(self.filter_tabs)
    
    def _setup_menubar(self) -> None:
        """메뉴바 구성"""
        menubar = self.menuBar()
        
        # File 메뉴
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Image...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        # 최근 파일 열기
        reload_action = QAction("Reload Last File", self)
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self._load_last_file)
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        output_action = QAction("Open Output Folder", self)
        output_action.triggered.connect(self._open_output_folder)
        file_menu.addAction(output_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View 메뉴
        view_menu = menubar.addMenu("View")
        
        fit_action = QAction("Fit to Window", self)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self._fit_to_window)
        view_menu.addAction(fit_action)
        
        view_menu.addSeparator()
        
        # 노이즈 분석 윈도우
        noise_action = QAction("Noise Analysis...", self)
        noise_action.setShortcut("Ctrl+N")
        noise_action.triggered.connect(self._show_noise_window)
        view_menu.addAction(noise_action)
        
        # 최적화 설정 윈도우
        opt_settings_action = QAction("Optimization Settings...", self)
        opt_settings_action.triggered.connect(self._show_optimization_settings)
        view_menu.addAction(opt_settings_action)
        
        # Help 메뉴
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_statusbar(self) -> None:
        """상태바 구성"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 이미지 정보 레이블
        self.image_info_label = QLabel("")
        self.statusbar.addPermanentWidget(self.image_info_label)
        
        self.statusbar.showMessage("Ready - Real-time preview enabled")
    
    def _apply_styles(self) -> None:
        """스타일 적용"""
        self.setStyleSheet(get_stylesheet())
    
    def _load_last_file(self) -> None:
        """마지막으로 열었던 파일 로드"""
        last_file = self.settings.get("last_file_path", "")
        if last_file and Path(last_file).exists():
            self._load_image(last_file)
    
    def _open_file(self) -> None:
        """파일 열기 다이얼로그"""
        # 마지막 디렉토리에서 시작
        last_dir = self.settings.get("last_open_directory", "")
        
        file_filter = FileIO.get_supported_read_formats()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SEM Image",
            last_dir,
            file_filter
        )
        
        if file_path:
            # 디렉토리 저장
            self.settings.set("last_open_directory", str(Path(file_path).parent))
            self._load_image(file_path)
    
    def _load_image(self, file_path: str) -> None:
        """이미지 로드"""
        self.statusbar.showMessage(f"Loading {file_path}...")
        
        image = self.file_io.load_image(file_path)
        
        if image is not None:
            self._current_image = image
            self.filter_tabs.set_image(image)
            
            # UI 업데이트
            filename = self.file_io.get_current_filename()
            self.file_label.setText(f"File: {filename}")
            
            # 이미지 정보
            if len(image.shape) == 2:
                info = f"{image.shape[1]}x{image.shape[0]} (Grayscale)"
            else:
                info = f"{image.shape[1]}x{image.shape[0]} (RGB)"
            self.image_info_label.setText(info)
            
            # 설정 저장
            self.settings.set("last_file_path", file_path)
            self.settings.save()
            
            self.statusbar.showMessage(f"Loaded: {filename} - Adjust parameters for real-time preview")
        else:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to load image: {file_path}"
            )
            self.statusbar.showMessage("Load failed")
    
    def _save_image(self, image: np.ndarray, filter_info: str) -> None:
        """이미지 저장"""
        saved_path = self.file_io.save_image(image, filter_info)
        
        if saved_path:
            self.statusbar.showMessage(f"Saved: {saved_path}")
            QMessageBox.information(
                self,
                "Saved",
                f"Image saved to:\n{saved_path}"
            )
        else:
            QMessageBox.critical(self, "Error", "Failed to save image")
    
    def _open_output_folder(self) -> None:
        """출력 폴더 열기"""
        output_dir = self.file_io.get_output_directory()
        
        # 디렉토리가 없으면 생성
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 탐색기로 열기
        if os.name == 'nt':  # Windows
            os.startfile(output_dir)
        elif os.name == 'posix':  # macOS/Linux
            import subprocess
            subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', output_dir])
        
        self.statusbar.showMessage(f"Opened: {output_dir}")
    
    def _fit_to_window(self) -> None:
        """현재 탭의 이미지를 윈도우에 맞춤"""
        current_tab = self.filter_tabs.currentWidget()
        if hasattr(current_tab, 'compare_view'):
            current_tab.compare_view.fit_to_view()
    
    def _show_about(self) -> None:
        """About 다이얼로그"""
        QMessageBox.about(
            self,
            "About SEM Denoising",
            "<h2>SEM Image Denoising</h2>"
            "<p>Version 1.1.0</p>"
            "<p>A professional image denoising tool for<br>"
            "Scanning Electron Microscope (SEM) images.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>7 denoising filters</li>"
            "<li>Multi-filter pipeline</li>"
            "<li>Real-time preview</li>"
            "<li>Settings persistence</li>"
            "</ul>"
            "<p>Built with Python + PySide6</p>"
        )
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """윈도우 닫힐 때 설정 저장"""
        # 윈도우 위치/크기 저장
        geom = self.geometry()
        self.settings.set("window_geometry", {
            "width": geom.width(),
            "height": geom.height(),
            "x": geom.x(),
            "y": geom.y()
        })
        self.settings.save()
        
        event.accept()
    
    def dragEnterEvent(self, event):
        """드래그 앤 드롭 지원"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """파일 드롭 처리"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # 지원 형식 확인
            ext = Path(file_path).suffix.lower()
            if ext in FileIO.SUPPORTED_FORMATS["read"]:
                self._load_image(file_path)
    
    def _show_noise_window(self) -> None:
        """노이즈 분석 윈도우 표시"""
        self.noise_window.show()
        self.noise_window.raise_()
        self.noise_window.activateWindow()
    
    def _show_optimization_settings(self) -> None:
        """최적화 설정 윈도우 표시"""
        self.optimization_settings_window.exec()
    
    def _connect_noise_signals(self) -> None:
        """필터 탭의 이미지 변경 시그널을 노이즈 윈도우에 연결"""
        # 각 SingleFilterTab의 compare_view 시그널 연결
        for i in range(self.filter_tabs.count()):
            tab = self.filter_tabs.widget(i)
            if hasattr(tab, 'compare_view'):
                tab.compare_view.original_image_changed.connect(
                    self.noise_window.set_original_image
                )
                tab.compare_view.processed_image_changed.connect(
                    self.noise_window.set_processed_image
                )
