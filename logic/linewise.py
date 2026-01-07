# -*- coding: utf-8 -*-
"""
Line-wise Correction 구현
스캔라인 기반 노이즈 제거 (Y 방향 줄무늬 제거)
"""
import numpy as np
from scipy import ndimage
from .filter_base import FilterBase, FilterParameter


class LinewiseFilter(FilterBase):
    """Line-wise Correction - 스캔라인 노이즈 제거"""
    
    @property
    def name(self) -> str:
        return "Linewise"
    
    @property
    def description(self) -> str:
        return "Removes scan-line artifacts and stripe noise from SEM images."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="direction",
            display_name="Stripe Direction",
            value="horizontal",
            param_type="choice",
            choices=["horizontal", "vertical"],
            description="Direction of stripe noise to remove"
        ))
        self.add_parameter(FilterParameter(
            name="method",
            display_name="Correction Method",
            value="mean",
            param_type="choice",
            choices=["mean", "median", "polynomial"],
            description="Method for line-wise correction"
        ))
        self.add_parameter(FilterParameter(
            name="window_size",
            display_name="Window Size",
            value=5,
            min_value=3,
            max_value=51,
            step=2,
            param_type="int",
            description="Window size for local statistics"
        ))
        self.add_parameter(FilterParameter(
            name="strength",
            display_name="Correction Strength",
            value=1.0,
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            param_type="float",
            description="Strength of correction (0=none, 1=full)"
        ))
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Line-wise correction 적용"""
        image_float = self._ensure_float(image)
        
        direction = self.get_parameter("direction")
        method = self.get_parameter("method")
        window_size = self.get_parameter("window_size")
        strength = self.get_parameter("strength")
        
        # 홀수로 맞추기
        if window_size % 2 == 0:
            window_size += 1
        
        # grayscale 처리
        if len(image_float.shape) == 3:
            result = np.zeros_like(image_float)
            for i in range(image_float.shape[2]):
                result[:, :, i] = self._apply_correction(
                    image_float[:, :, i], direction, method, window_size, strength
                )
        else:
            result = self._apply_correction(
                image_float, direction, method, window_size, strength
            )
        
        return self._ensure_uint8(result)
    
    def _apply_correction(self, image: np.ndarray, direction: str, 
                          method: str, window_size: int, strength: float) -> np.ndarray:
        """2D 이미지에 보정 적용"""
        # 방향에 따라 처리
        if direction == "vertical":
            image = image.T
        
        rows, cols = image.shape
        corrected = image.copy()
        
        if method == "mean":
            # 각 행의 평균을 전체 평균으로 정규화
            global_mean = np.mean(image)
            line_means = np.mean(image, axis=1)
            
            for i in range(rows):
                if line_means[i] != 0:
                    correction = global_mean / line_means[i]
                    corrected[i, :] = image[i, :] * (1 - strength + strength * correction)
                    
        elif method == "median":
            # 각 행의 중앙값을 전체 중앙값으로 정규화
            global_median = np.median(image)
            line_medians = np.median(image, axis=1)
            
            for i in range(rows):
                if line_medians[i] != 0:
                    correction = global_median / line_medians[i]
                    corrected[i, :] = image[i, :] * (1 - strength + strength * correction)
                    
        elif method == "polynomial":
            # 다항식 피팅으로 트렌드 제거
            x = np.arange(cols)
            for i in range(rows):
                row = image[i, :]
                # 2차 다항식 피팅
                coeffs = np.polyfit(x, row, 2)
                trend = np.polyval(coeffs, x)
                row_mean = np.mean(row)
                
                # 트렌드 제거
                detrended = row - trend + row_mean
                corrected[i, :] = (1 - strength) * row + strength * detrended
        
        # 방향 복원
        if direction == "vertical":
            corrected = corrected.T
        
        # 값 범위 클리핑
        corrected = np.clip(corrected, 0, 1)
        
        return corrected

