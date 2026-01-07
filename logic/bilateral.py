# -*- coding: utf-8 -*-
"""
Bilateral Filter 구현
에지를 보존하면서 노이즈를 제거하는 필터
"""
import cv2
import numpy as np
from .filter_base import FilterBase, FilterParameter


class BilateralFilter(FilterBase):
    """Bilateral Filter - 에지 보존 스무딩"""
    
    @property
    def name(self) -> str:
        return "Bilateral"
    
    @property
    def description(self) -> str:
        return "Edge-preserving smoothing filter that reduces noise while keeping edges sharp."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="d",
            display_name="Diameter",
            value=9,
            min_value=1,
            max_value=31,
            step=2,
            param_type="int",
            description="Diameter of each pixel neighborhood"
        ))
        self.add_parameter(FilterParameter(
            name="sigmaColor",
            display_name="Sigma Color",
            value=75.0,
            min_value=1.0,
            max_value=200.0,
            step=1.0,
            param_type="float",
            description="Filter sigma in the color space"
        ))
        self.add_parameter(FilterParameter(
            name="sigmaSpace",
            display_name="Sigma Space",
            value=75.0,
            min_value=1.0,
            max_value=200.0,
            step=1.0,
            param_type="float",
            description="Filter sigma in the coordinate space"
        ))
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Bilateral 필터 적용"""
        image = self._ensure_uint8(image)
        
        d = self.get_parameter("d")
        sigma_color = self.get_parameter("sigmaColor")
        sigma_space = self.get_parameter("sigmaSpace")
        
        # d는 홀수여야 함
        if d % 2 == 0:
            d += 1
        
        result = cv2.bilateralFilter(
            image, 
            d, 
            sigma_color, 
            sigma_space
        )
        
        return result

