# -*- coding: utf-8 -*-
"""
SEM Image Denoising Application
Main entry point
"""
import sys
import os

# 현재 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.main_window import MainWindow


def main():
    """애플리케이션 메인 함수"""
    # High DPI 지원
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # 기본 폰트 설정
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    print("SEM Image Denoising Application started")
    print(f"Output directory: {window.file_io.get_output_directory()}")
    
    # 이벤트 루프 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

