# -*- coding: utf-8 -*-
"""
필터 기본 클래스 정의
모든 denoising 필터가 상속받는 추상 클래스
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class FilterParameter:
    """필터 파라미터 정의"""
    name: str
    display_name: str
    value: Any
    min_value: Any = None
    max_value: Any = None
    step: Any = None
    param_type: str = "int"  # "int", "float", "choice"
    choices: list = field(default_factory=list)
    description: str = ""


class FilterBase(ABC):
    """모든 denoising 필터의 기본 클래스"""
    
    def __init__(self):
        self._parameters: dict[str, FilterParameter] = {}
        self._setup_parameters()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """필터 이름 반환"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """필터 설명 반환"""
        pass
    
    @abstractmethod
    def _setup_parameters(self) -> None:
        """필터 파라미터 초기화"""
        pass
    
    @abstractmethod
    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        이미지에 필터 적용
        
        Args:
            image: 입력 이미지 (grayscale 또는 color)
        
        Returns:
            처리된 이미지
        """
        pass
    
    def add_parameter(self, param: FilterParameter) -> None:
        """파라미터 추가"""
        self._parameters[param.name] = param
    
    def get_parameter(self, name: str) -> Any:
        """파라미터 값 가져오기"""
        if name in self._parameters:
            return self._parameters[name].value
        raise KeyError(f"Parameter '{name}' not found")
    
    def set_parameter(self, name: str, value: Any) -> None:
        """파라미터 값 설정"""
        if name in self._parameters:
            param = self._parameters[name]
            # 값 범위 검증
            if param.min_value is not None and value < param.min_value:
                value = param.min_value
            if param.max_value is not None and value > param.max_value:
                value = param.max_value
            param.value = value
        else:
            raise KeyError(f"Parameter '{name}' not found")
    
    def get_parameters(self) -> dict[str, FilterParameter]:
        """모든 파라미터 반환"""
        return self._parameters.copy()
    
    def get_filter_info(self) -> str:
        """필터 정보 문자열 생성 (파일명용)"""
        params = []
        for name, param in self._parameters.items():
            if param.param_type == "float":
                params.append(f"{name}{param.value:.2f}")
            else:
                params.append(f"{name}{param.value}")
        return f"{self.name}_{'_'.join(params)}" if params else self.name
    
    def _ensure_uint8(self, image: np.ndarray) -> np.ndarray:
        """이미지를 uint8로 변환"""
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = np.clip(image, 0, 255).astype(np.uint8)
        return image
    
    def _ensure_float(self, image: np.ndarray) -> np.ndarray:
        """이미지를 float으로 변환 (0-1 범위)"""
        if image.dtype == np.uint8:
            return image.astype(np.float64) / 255.0
        return image.astype(np.float64)

