# -*- coding: utf-8 -*-
"""
파일 입출력 처리
이미지 로딩, 저장 및 파일명 관리
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image


class FileIO:
    """파일 입출력 관리 클래스"""
    
    SUPPORTED_FORMATS = {
        "read": [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"],
        "write": [".png", ".jpg", ".tiff", ".bmp"]
    }
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Args:
            output_dir: 출력 디렉토리 경로 (None이면 현재 디렉토리/output)
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.cwd() / "output"
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_file: Optional[Path] = None
        self._original_image: Optional[np.ndarray] = None
    
    @classmethod
    def get_supported_read_formats(cls) -> str:
        """읽기 지원 형식 필터 문자열 반환 (파일 다이얼로그용)"""
        extensions = " ".join(f"*{ext}" for ext in cls.SUPPORTED_FORMATS["read"])
        return f"Images ({extensions})"
    
    @classmethod
    def get_supported_write_formats(cls) -> list[str]:
        """쓰기 지원 형식 목록 반환"""
        return cls.SUPPORTED_FORMATS["write"].copy()
    
    def load_image(self, file_path: str) -> Optional[np.ndarray]:
        """
        이미지 파일 로드
        
        Args:
            file_path: 이미지 파일 경로
            
        Returns:
            numpy 배열 (grayscale 또는 RGB)
        """
        path = Path(file_path)
        
        if not path.exists():
            print(f"Error: File not found - {file_path}")
            return None
        
        if path.suffix.lower() not in self.SUPPORTED_FORMATS["read"]:
            print(f"Error: Unsupported format - {path.suffix}")
            return None
        
        try:
            # PIL로 이미지 로드
            img = Image.open(path)
            
            # 모드에 따른 처리
            if img.mode == "L":
                # Grayscale
                image = np.array(img)
            elif img.mode == "RGB":
                image = np.array(img)
            elif img.mode == "RGBA":
                # RGBA -> RGB
                image = np.array(img.convert("RGB"))
            elif img.mode == "I;16":
                # 16-bit grayscale
                image = np.array(img)
                # 8-bit로 변환 (스케일링)
                image = (image / 256).astype(np.uint8)
            else:
                # 기타 모드는 RGB로 변환
                image = np.array(img.convert("RGB"))
            
            self._current_file = path
            self._original_image = image.copy()
            
            print(f"Loaded: {path.name} ({image.shape})")
            return image
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def save_image(self, image: np.ndarray, filter_name: str, 
                   format: str = ".png", custom_name: Optional[str] = None) -> Optional[str]:
        """
        처리된 이미지 저장
        
        파일명 형식: {원본이름}_{필터명}_{날짜시간}.{확장자}
        예: image_NLM_Bilateral_20251227_143052.png
        
        Args:
            image: 저장할 이미지
            filter_name: 적용된 필터 이름 (파이프라인인 경우 조합)
            format: 저장 형식 (.png, .jpg 등)
            custom_name: 사용자 지정 파일명 (None이면 자동 생성)
            
        Returns:
            저장된 파일 경로 (실패 시 None)
        """
        # 형식 검증
        if format not in self.SUPPORTED_FORMATS["write"]:
            format = ".png"
        
        # 파일명 생성
        if custom_name:
            filename = custom_name
        else:
            # 원본 파일명 (확장자 제외)
            if self._current_file:
                base_name = self._current_file.stem
            else:
                base_name = "image"
            
            # 타임스탬프
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 필터명 정리 (공백, 특수문자 제거)
            safe_filter_name = filter_name.replace(" ", "_").replace("/", "-")
            
            filename = f"{base_name}_{safe_filter_name}_{timestamp}"
        
        # 전체 경로
        output_path = self.output_dir / f"{filename}{format}"
        
        try:
            # numpy 배열을 PIL Image로 변환
            if image.dtype != np.uint8:
                if image.max() <= 1.0:
                    image = (image * 255).astype(np.uint8)
                else:
                    image = np.clip(image, 0, 255).astype(np.uint8)
            
            img = Image.fromarray(image)
            
            # JPEG 품질 설정
            if format.lower() in [".jpg", ".jpeg"]:
                img.save(output_path, quality=95)
            else:
                img.save(output_path)
            
            print(f"Saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
    
    def get_current_filename(self) -> Optional[str]:
        """현재 로드된 파일명 반환"""
        if self._current_file:
            return self._current_file.name
        return None
    
    def get_original_image(self) -> Optional[np.ndarray]:
        """원본 이미지 반환"""
        if self._original_image is not None:
            return self._original_image.copy()
        return None
    
    def get_output_directory(self) -> str:
        """출력 디렉토리 경로 반환"""
        return str(self.output_dir)

