# -*- coding: utf-8 -*-
"""
이미지 비교 뷰 구현
원본과 처리된 이미지를 나란히 비교하는 Split View
확대/이동 컨트롤 포함
"""
from typing import Optional
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QSplitter, QSizePolicy,
    QPushButton, QSlider, QToolButton
)
from PySide6.QtCore import Qt, Signal, QPoint, QPointF, QRectF
from PySide6.QtGui import (
    QImage, QPixmap, QWheelEvent, QMouseEvent, 
    QPainter, QTransform, QPen, QColor
)


class ZoomableImageWidget(QWidget):
    """줌/팬 기능이 있는 이미지 위젯"""
    
    zoom_changed = Signal(float)
    pan_changed = Signal(float, float)  # x_ratio, y_ratio
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._image: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._dragging = False
        self._drag_start = QPointF()
        self._last_pan_offset = QPointF(0, 0)
        
        # 마우스 추적 활성화
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
    
    def set_image(self, image: Optional[np.ndarray]) -> None:
        """numpy 배열 이미지 설정"""
        self._image = image
        
        if image is None:
            self._pixmap = None
            self.update()
            return
        
        # numpy 배열을 QPixmap으로 변환
        if len(image.shape) == 2:
            height, width = image.shape
            qimage = QImage(
                image.data.tobytes(), width, height, width,
                QImage.Format_Grayscale8
            )
        else:
            height, width, channels = image.shape
            bytes_per_line = channels * width
            qimage = QImage(
                image.data.tobytes(), width, height, bytes_per_line,
                QImage.Format_RGB888
            )
        
        self._pixmap = QPixmap.fromImage(qimage)
        self.update()
    
    def paintEvent(self, event):
        """이미지 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 배경
        painter.fillRect(self.rect(), QColor("#0d1b2a"))
        
        if self._pixmap is None:
            painter.setPen(QColor("#a0a0a0"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Image")
            return
        
        # 변환 행렬 설정
        painter.translate(self.width() / 2, self.height() / 2)
        painter.translate(self._pan_offset)
        painter.scale(self._zoom_factor, self._zoom_factor)
        
        # 이미지 그리기 (중앙 기준)
        img_rect = QRectF(
            -self._pixmap.width() / 2,
            -self._pixmap.height() / 2,
            self._pixmap.width(),
            self._pixmap.height()
        )
        painter.drawPixmap(img_rect.toRect(), self._pixmap)
    
    def set_zoom(self, factor: float) -> None:
        """줌 팩터 설정"""
        self._zoom_factor = max(0.1, min(10.0, factor))
        self.update()
        self.zoom_changed.emit(self._zoom_factor)
    
    def get_zoom(self) -> float:
        """현재 줌 팩터 반환"""
        return self._zoom_factor
    
    def set_pan(self, x: float, y: float) -> None:
        """팬 위치 설정"""
        self._pan_offset = QPointF(x, y)
        self.update()
    
    def get_pan(self) -> tuple:
        """현재 팬 위치 반환"""
        return (self._pan_offset.x(), self._pan_offset.y())
    
    def fit_to_view(self) -> None:
        """뷰에 맞게 이미지 조정"""
        if self._pixmap is None:
            return
        
        # 위젯 크기와 이미지 크기 비율 계산
        width_ratio = (self.width() - 20) / self._pixmap.width()
        height_ratio = (self.height() - 20) / self._pixmap.height()
        
        self._zoom_factor = min(width_ratio, height_ratio)
        self._pan_offset = QPointF(0, 0)
        self.update()
        self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_in(self) -> None:
        """확대"""
        self.set_zoom(self._zoom_factor * 1.25)
    
    def zoom_out(self) -> None:
        """축소"""
        self.set_zoom(self._zoom_factor / 1.25)
    
    def reset_view(self) -> None:
        """100% 보기"""
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self.update()
        self.zoom_changed.emit(self._zoom_factor)
    
    def move_view(self, dx: float, dy: float) -> None:
        """뷰 이동"""
        self._pan_offset += QPointF(dx, dy)
        self.update()
        self._emit_pan_ratio()
    
    def _emit_pan_ratio(self) -> None:
        """팬 비율 시그널 발생"""
        if self._pixmap:
            x_ratio = self._pan_offset.x() / (self._pixmap.width() * self._zoom_factor) if self._pixmap.width() > 0 else 0
            y_ratio = self._pan_offset.y() / (self._pixmap.height() * self._zoom_factor) if self._pixmap.height() > 0 else 0
            self.pan_changed.emit(x_ratio, y_ratio)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """마우스 휠로 줌"""
        delta = event.angleDelta().y()
        
        # 마우스 위치 기준 줌
        mouse_pos = event.position()
        old_zoom = self._zoom_factor
        
        if delta > 0:
            new_zoom = self._zoom_factor * 1.15
        else:
            new_zoom = self._zoom_factor / 1.15
        
        self.set_zoom(new_zoom)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """마우스 드래그 시작"""
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start = event.position()
            self._last_pan_offset = QPointF(self._pan_offset)
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """마우스 드래그 종료"""
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.OpenHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """마우스 드래그로 팬"""
        if self._dragging:
            delta = event.position() - self._drag_start
            self._pan_offset = self._last_pan_offset + delta
            self.update()
            self._emit_pan_ratio()
    
    def enterEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
    
    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)


class ImagePanel(QWidget):
    """이미지 패널 - 제목 + 이미지 위젯 + 컨트롤"""
    
    zoom_changed = Signal(float)
    pan_changed = Signal(float, float)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._setup_ui(title)
    
    def _setup_ui(self, title: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 제목
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # 이미지 위젯
        self.image_widget = ZoomableImageWidget()
        self.image_widget.zoom_changed.connect(self.zoom_changed.emit)
        self.image_widget.pan_changed.connect(self.pan_changed.emit)
        layout.addWidget(self.image_widget, stretch=1)
        
        # 줌 레벨 표시
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        self.image_widget.zoom_changed.connect(
            lambda z: self.zoom_label.setText(f"{z*100:.0f}%")
        )
        layout.addWidget(self.zoom_label)
    
    def set_image(self, image: Optional[np.ndarray]) -> None:
        self.image_widget.set_image(image)
    
    def set_zoom(self, factor: float) -> None:
        self.image_widget.set_zoom(factor)
    
    def set_pan(self, x: float, y: float) -> None:
        self.image_widget.set_pan(x, y)
    
    def fit_to_view(self) -> None:
        self.image_widget.fit_to_view()


class CompareView(QWidget):
    """원본/처리 이미지 비교 뷰 - 컨트롤 버튼 포함"""
    
    # 이미지 변경 시그널 (노이즈 분석 윈도우에 전달용)
    original_image_changed = Signal(object)  # np.ndarray or None
    processed_image_changed = Signal(object)  # np.ndarray or None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._syncing = False  # 동기화 중 플래그 (무한 재귀 방지)
        self._original_image = None
        self._processed_image = None
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self) -> None:
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 상단: 컨트롤 버튼
        control_bar = QWidget()
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(10)
        
        # 줌 컨트롤
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(zoom_label)
        
        self.fit_btn = QPushButton("Fit")
        self.fit_btn.setFixedWidth(60)
        self.fit_btn.setToolTip("Fit image to view (F)")
        self.fit_btn.clicked.connect(self.fit_to_view)
        control_layout.addWidget(self.fit_btn)
        
        self.zoom_100_btn = QPushButton("100%")
        self.zoom_100_btn.setFixedWidth(60)
        self.zoom_100_btn.setToolTip("View at 100% (1)")
        self.zoom_100_btn.clicked.connect(self._reset_zoom)
        control_layout.addWidget(self.zoom_100_btn)
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedWidth(40)
        self.zoom_out_btn.setToolTip("Zoom out (-)")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        control_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedWidth(40)
        self.zoom_in_btn.setToolTip("Zoom in (+)")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        control_layout.addWidget(self.zoom_in_btn)
        
        control_layout.addSpacing(20)
        
        # 이동 컨트롤
        move_label = QLabel("Move:")
        move_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(move_label)
        
        self.left_btn = QPushButton("←")
        self.left_btn.setFixedWidth(40)
        self.left_btn.setToolTip("Move left (Left Arrow)")
        self.left_btn.clicked.connect(lambda: self._move(-100, 0))
        control_layout.addWidget(self.left_btn)
        
        self.right_btn = QPushButton("→")
        self.right_btn.setFixedWidth(40)
        self.right_btn.setToolTip("Move right (Right Arrow)")
        self.right_btn.clicked.connect(lambda: self._move(100, 0))
        control_layout.addWidget(self.right_btn)
        
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedWidth(40)
        self.up_btn.setToolTip("Move up (Up Arrow)")
        self.up_btn.clicked.connect(lambda: self._move(0, 100))
        control_layout.addWidget(self.up_btn)
        
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedWidth(40)
        self.down_btn.setToolTip("Move down (Down Arrow)")
        self.down_btn.clicked.connect(lambda: self._move(0, -100))
        control_layout.addWidget(self.down_btn)
        
        self.center_btn = QPushButton("Center")
        self.center_btn.setFixedWidth(70)
        self.center_btn.setToolTip("Center view (C)")
        self.center_btn.clicked.connect(self._center_view)
        control_layout.addWidget(self.center_btn)
        
        control_layout.addStretch()
        
        # 동기화 상태 표시
        self.sync_label = QLabel("🔗 Views Synced")
        self.sync_label.setStyleSheet("color: #4ecca3;")
        control_layout.addWidget(self.sync_label)
        
        layout.addWidget(control_bar)
        
        # 스플리터로 좌우 분할 (이미지들)
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 원본 이미지 패널
        self.original_panel = ImagePanel("Original")
        self.splitter.addWidget(self.original_panel)
        
        # 처리된 이미지 패널
        self.processed_panel = ImagePanel("Processed")
        self.splitter.addWidget(self.processed_panel)
        
        self.splitter.setSizes([500, 500])
        layout.addWidget(self.splitter, stretch=1)
    
    def _connect_signals(self) -> None:
        """시그널 연결 - 동기화된 줌/팬"""
        # 줌 동기화
        self.original_panel.zoom_changed.connect(self._sync_zoom_from_original)
        self.processed_panel.zoom_changed.connect(self._sync_zoom_from_processed)
        
        # 팬 동기화
        self.original_panel.pan_changed.connect(self._sync_pan_from_original)
        self.processed_panel.pan_changed.connect(self._sync_pan_from_processed)
    
    def _sync_zoom_from_original(self, zoom: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            self.processed_panel.set_zoom(zoom)
        finally:
            self._syncing = False
    
    def _sync_zoom_from_processed(self, zoom: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            self.original_panel.set_zoom(zoom)
        finally:
            self._syncing = False
    
    def _sync_pan_from_original(self, x_ratio: float, y_ratio: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            orig_pan = self.original_panel.image_widget.get_pan()
            self.processed_panel.set_pan(orig_pan[0], orig_pan[1])
        finally:
            self._syncing = False
    
    def _sync_pan_from_processed(self, x_ratio: float, y_ratio: float) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            proc_pan = self.processed_panel.image_widget.get_pan()
            self.original_panel.set_pan(proc_pan[0], proc_pan[1])
        finally:
            self._syncing = False
    
    def set_original_image(self, image: Optional[np.ndarray]) -> None:
        """원본 이미지 설정"""
        self._original_image = image
        self.original_panel.set_image(image)
        self.original_image_changed.emit(image)
        if image is not None:
            self.original_panel.fit_to_view()
    
    def set_processed_image(self, image: Optional[np.ndarray]) -> None:
        """처리된 이미지 설정"""
        self._processed_image = image
        self.processed_panel.set_image(image)
        self.processed_image_changed.emit(image)
        if image is not None:
            # 원본과 같은 줌/팬 유지
            zoom = self.original_panel.image_widget.get_zoom()
            pan = self.original_panel.image_widget.get_pan()
            self.processed_panel.set_zoom(zoom)
            self.processed_panel.set_pan(pan[0], pan[1])
    
    def get_original_image(self) -> Optional[np.ndarray]:
        """원본 이미지 반환"""
        return self._original_image
    
    def get_processed_image(self) -> Optional[np.ndarray]:
        """처리된 이미지 반환"""
        return self._processed_image
    
    def fit_to_view(self) -> None:
        """뷰에 맞게 이미지 조정"""
        self.original_panel.fit_to_view()
        # 동기화됨
    
    def _reset_zoom(self) -> None:
        """100% 줌"""
        self.original_panel.image_widget.reset_view()
    
    def _zoom_in(self) -> None:
        """확대"""
        self.original_panel.image_widget.zoom_in()
    
    def _zoom_out(self) -> None:
        """축소"""
        self.original_panel.image_widget.zoom_out()
    
    def _move(self, dx: float, dy: float) -> None:
        """이동"""
        self.original_panel.image_widget.move_view(dx, dy)
    
    def _center_view(self) -> None:
        """중앙으로 이동"""
        self.original_panel.set_pan(0, 0)
        self.processed_panel.set_pan(0, 0)
    
    def clear(self) -> None:
        """모든 이미지 초기화"""
        self.original_panel.set_image(None)
        self.processed_panel.set_image(None)
    
    def keyPressEvent(self, event):
        """키보드 단축키"""
        key = event.key()
        if key == Qt.Key_F:
            self.fit_to_view()
        elif key == Qt.Key_1:
            self._reset_zoom()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self._zoom_in()
        elif key == Qt.Key_Minus:
            self._zoom_out()
        elif key == Qt.Key_Left:
            self._move(-50, 0)
        elif key == Qt.Key_Right:
            self._move(50, 0)
        elif key == Qt.Key_Up:
            self._move(0, 50)
        elif key == Qt.Key_Down:
            self._move(0, -50)
        elif key == Qt.Key_C:
            self._center_view()
        else:
            super().keyPressEvent(event)
