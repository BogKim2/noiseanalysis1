# -*- coding: utf-8 -*-
"""
전문적인 다크 테마 스타일 정의
SEM 이미지 분석에 적합한 눈의 피로를 줄이는 UI
"""

# 색상 팔레트
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text_primary": "#eaeaea",
    "text_secondary": "#a0a0a0",
    "border": "#2d2d4a",
    "success": "#4ecca3",
    "warning": "#ffc107",
    "error": "#e94560",
    "input_bg": "#0d1b2a",
    "button_bg": "#1b4965",
    "button_hover": "#2d6a8f",
}

# 폰트 설정
FONTS = {
    "family": "Segoe UI, Noto Sans, Arial",
    "size_small": "11px",
    "size_normal": "12px",
    "size_large": "14px",
    "size_title": "16px",
}


def get_stylesheet() -> str:
    """메인 스타일시트 반환"""
    return f"""
    /* 전역 스타일 */
    QWidget {{
        background-color: {COLORS["bg_dark"]};
        color: {COLORS["text_primary"]};
        font-family: {FONTS["family"]};
        font-size: {FONTS["size_normal"]};
    }}
    
    /* 메인 윈도우 */
    QMainWindow {{
        background-color: {COLORS["bg_dark"]};
    }}
    
    /* 탭 위젯 */
    QTabWidget::pane {{
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        background-color: {COLORS["bg_medium"]};
        padding: 5px;
    }}
    
    QTabBar::tab {{
        background-color: {COLORS["bg_medium"]};
        color: {COLORS["text_secondary"]};
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-weight: bold;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS["bg_light"]};
        color: {COLORS["text_primary"]};
        border-bottom: 2px solid {COLORS["accent"]};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {COLORS["border"]};
    }}
    
    /* 버튼 */
    QPushButton {{
        background-color: {COLORS["button_bg"]};
        color: {COLORS["text_primary"]};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS["button_hover"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["accent"]};
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS["border"]};
        color: {COLORS["text_secondary"]};
    }}
    
    /* 주요 액션 버튼 */
    QPushButton#primaryButton {{
        background-color: {COLORS["accent"]};
    }}
    
    QPushButton#primaryButton:hover {{
        background-color: {COLORS["accent_hover"]};
    }}
    
    /* 입력 필드 */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {COLORS["input_bg"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {COLORS["accent"]};
    }}
    
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {COLORS["accent"]};
    }}
    
    /* 슬라이더 */
    QSlider::groove:horizontal {{
        border: 1px solid {COLORS["border"]};
        height: 6px;
        background: {COLORS["input_bg"]};
        border-radius: 3px;
    }}
    
    QSlider::handle:horizontal {{
        background: {COLORS["accent"]};
        border: none;
        width: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: {COLORS["accent_hover"]};
    }}
    
    QSlider::sub-page:horizontal {{
        background: {COLORS["bg_light"]};
        border-radius: 3px;
    }}
    
    /* 콤보박스 */
    QComboBox {{
        background-color: {COLORS["input_bg"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 6px;
        min-width: 120px;
    }}
    
    QComboBox:hover {{
        border: 1px solid {COLORS["accent"]};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS["text_primary"]};
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS["bg_medium"]};
        color: {COLORS["text_primary"]};
        selection-background-color: {COLORS["accent"]};
        border: 1px solid {COLORS["border"]};
    }}
    
    /* 레이블 */
    QLabel {{
        color: {COLORS["text_primary"]};
        background: transparent;
    }}
    
    QLabel#titleLabel {{
        font-size: {FONTS["size_title"]};
        font-weight: bold;
        color: {COLORS["text_primary"]};
    }}
    
    QLabel#subtitleLabel {{
        font-size: {FONTS["size_large"]};
        color: {COLORS["text_secondary"]};
    }}
    
    /* 그룹박스 */
    QGroupBox {{
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 10px;
        background-color: {COLORS["bg_medium"]};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: {COLORS["accent"]};
        font-weight: bold;
    }}
    
    /* 스크롤바 */
    QScrollBar:vertical {{
        border: none;
        background: {COLORS["bg_dark"]};
        width: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS["border"]};
        border-radius: 5px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["bg_light"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background: {COLORS["bg_dark"]};
        height: 10px;
        border-radius: 5px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {COLORS["border"]};
        border-radius: 5px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS["bg_light"]};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* 상태바 */
    QStatusBar {{
        background-color: {COLORS["bg_medium"]};
        color: {COLORS["text_secondary"]};
        border-top: 1px solid {COLORS["border"]};
    }}
    
    /* 메뉴바 */
    QMenuBar {{
        background-color: {COLORS["bg_medium"]};
        color: {COLORS["text_primary"]};
        padding: 2px;
    }}
    
    QMenuBar::item {{
        padding: 5px 10px;
        background: transparent;
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS["bg_light"]};
    }}
    
    QMenu {{
        background-color: {COLORS["bg_medium"]};
        border: 1px solid {COLORS["border"]};
    }}
    
    QMenu::item {{
        padding: 8px 25px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS["accent"]};
    }}
    
    /* 프로그레스바 */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {COLORS["input_bg"]};
        text-align: center;
        color: {COLORS["text_primary"]};
    }}
    
    QProgressBar::chunk {{
        background-color: {COLORS["accent"]};
        border-radius: 4px;
    }}
    
    /* 스플리터 */
    QSplitter::handle {{
        background-color: {COLORS["border"]};
    }}
    
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    
    /* 프레임 */
    QFrame#imageFrame {{
        border: 2px solid {COLORS["border"]};
        border-radius: 4px;
        background-color: {COLORS["input_bg"]};
    }}
    """


def get_button_style(button_type: str = "normal") -> str:
    """버튼 타입별 스타일 반환"""
    styles = {
        "primary": f"""
            background-color: {COLORS["accent"]};
            color: white;
            font-weight: bold;
            padding: 10px 20px;
        """,
        "success": f"""
            background-color: {COLORS["success"]};
            color: white;
            font-weight: bold;
        """,
        "warning": f"""
            background-color: {COLORS["warning"]};
            color: black;
            font-weight: bold;
        """,
        "danger": f"""
            background-color: {COLORS["error"]};
            color: white;
            font-weight: bold;
        """,
    }
    return styles.get(button_type, "")

