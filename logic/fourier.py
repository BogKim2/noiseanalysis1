# -*- coding: utf-8 -*-
"""
Fourier Domain Filtering 구현
주파수 영역에서의 노이즈 필터링
"""
import numpy as np
from scipy import fft
from .filter_base import FilterBase, FilterParameter


class FourierFilter(FilterBase):
    """Fourier Domain Filtering - 주파수 영역 필터링"""
    
    @property
    def name(self) -> str:
        return "Fourier"
    
    @property
    def description(self) -> str:
        return "Frequency domain filtering using FFT for noise reduction."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="cutoff",
            display_name="Cutoff Frequency",
            value=0.3,
            min_value=0.01,
            max_value=1.0,
            step=0.01,
            param_type="float",
            description="Cutoff frequency (0-1, relative to max frequency)"
        ))
        self.add_parameter(FilterParameter(
            name="filter_type",
            display_name="Filter Type",
            value="lowpass",
            param_type="choice",
            choices=["lowpass", "highpass", "bandpass", "gaussian"],
            description="Type of frequency filter"
        ))
        self.add_parameter(FilterParameter(
            name="order",
            display_name="Filter Order",
            value=2,
            min_value=1,
            max_value=10,
            step=1,
            param_type="int",
            description="Butterworth filter order (sharpness)"
        ))
        self.add_parameter(FilterParameter(
            name="bandwidth",
            display_name="Bandwidth (for bandpass)",
            value=0.1,
            min_value=0.01,
            max_value=0.5,
            step=0.01,
            param_type="float",
            description="Bandwidth for bandpass filter"
        ))
    
    def _create_butterworth_filter(self, shape: tuple, cutoff: float, 
                                    order: int, highpass: bool = False) -> np.ndarray:
        """Butterworth 필터 생성"""
        rows, cols = shape
        crow, ccol = rows // 2, cols // 2
        
        # 주파수 좌표 생성
        u = np.arange(rows) - crow
        v = np.arange(cols) - ccol
        U, V = np.meshgrid(v, u)
        
        # 정규화된 거리
        D = np.sqrt(U**2 + V**2)
        D_max = np.sqrt(crow**2 + ccol**2)
        D_norm = D / D_max
        
        # Butterworth 필터
        cutoff = max(cutoff, 0.001)  # 0 방지
        H = 1 / (1 + (D_norm / cutoff) ** (2 * order))
        
        if highpass:
            H = 1 - H
        
        return H
    
    def _create_gaussian_filter(self, shape: tuple, cutoff: float) -> np.ndarray:
        """Gaussian 저역 필터 생성"""
        rows, cols = shape
        crow, ccol = rows // 2, cols // 2
        
        u = np.arange(rows) - crow
        v = np.arange(cols) - ccol
        U, V = np.meshgrid(v, u)
        
        D = np.sqrt(U**2 + V**2)
        D_max = np.sqrt(crow**2 + ccol**2)
        D_norm = D / D_max
        
        sigma = cutoff * D_max
        H = np.exp(-(D**2) / (2 * sigma**2))
        
        return H
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Fourier 필터링 적용"""
        image_float = self._ensure_float(image)
        
        cutoff = self.get_parameter("cutoff")
        filter_type = self.get_parameter("filter_type")
        order = self.get_parameter("order")
        bandwidth = self.get_parameter("bandwidth")
        
        # grayscale 처리
        if len(image_float.shape) == 3:
            # 각 채널에 대해 처리
            result = np.zeros_like(image_float)
            for i in range(image_float.shape[2]):
                result[:, :, i] = self._apply_filter_2d(
                    image_float[:, :, i], cutoff, filter_type, order, bandwidth
                )
        else:
            result = self._apply_filter_2d(
                image_float, cutoff, filter_type, order, bandwidth
            )
        
        return self._ensure_uint8(result)
    
    def _apply_filter_2d(self, image: np.ndarray, cutoff: float, 
                         filter_type: str, order: int, bandwidth: float) -> np.ndarray:
        """2D 이미지에 필터 적용"""
        # FFT
        f_transform = fft.fft2(image)
        f_shift = fft.fftshift(f_transform)
        
        shape = image.shape
        
        # 필터 생성
        if filter_type == "lowpass":
            H = self._create_butterworth_filter(shape, cutoff, order, highpass=False)
        elif filter_type == "highpass":
            H = self._create_butterworth_filter(shape, cutoff, order, highpass=True)
        elif filter_type == "bandpass":
            H_low = self._create_butterworth_filter(shape, cutoff + bandwidth/2, order, False)
            H_high = self._create_butterworth_filter(shape, cutoff - bandwidth/2, order, True)
            H = H_low * H_high
        else:  # gaussian
            H = self._create_gaussian_filter(shape, cutoff)
        
        # 필터 적용
        filtered = f_shift * H
        
        # 역변환
        f_ishift = fft.ifftshift(filtered)
        result = fft.ifft2(f_ishift)
        result = np.abs(result)
        
        # 클리핑
        result = np.clip(result, 0, 1)
        
        return result

