# -*- coding: utf-8 -*-
"""
Wavelet Denoising 구현
다중 스케일 노이즈 제거
"""
import numpy as np
from skimage.restoration import denoise_wavelet, estimate_sigma
from .filter_base import FilterBase, FilterParameter


class WaveletFilter(FilterBase):
    """Wavelet Denoising - 다중 스케일 노이즈 제거"""
    
    @property
    def name(self) -> str:
        return "Wavelet"
    
    @property
    def description(self) -> str:
        return "Multi-scale denoising using wavelet decomposition."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="sigma",
            display_name="Sigma (0=auto)",
            value=0.0,
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            param_type="float",
            description="Noise standard deviation (0 for automatic estimation)"
        ))
        self.add_parameter(FilterParameter(
            name="wavelet",
            display_name="Wavelet Type",
            value="db1",
            param_type="choice",
            choices=["db1", "db2", "db4", "sym4", "coif1", "bior1.5"],
            description="Wavelet basis function"
        ))
        self.add_parameter(FilterParameter(
            name="mode",
            display_name="Thresholding Mode",
            value="soft",
            param_type="choice",
            choices=["soft", "hard"],
            description="Thresholding mode"
        ))
        self.add_parameter(FilterParameter(
            name="rescale_sigma",
            display_name="Rescale Sigma",
            value=1,
            min_value=0,
            max_value=1,
            step=1,
            param_type="int",
            description="Rescale sigma for each level (1=yes, 0=no)"
        ))
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Wavelet denoising 적용"""
        image_float = self._ensure_float(image)
        
        sigma = self.get_parameter("sigma")
        wavelet = self.get_parameter("wavelet")
        mode = self.get_parameter("mode")
        rescale = bool(self.get_parameter("rescale_sigma"))
        
        # 자동 sigma 추정
        if sigma == 0.0:
            sigma = estimate_sigma(image_float, average_sigmas=True)
        
        # Wavelet denoising 적용
        is_color = len(image_float.shape) == 3
        
        result = denoise_wavelet(
            image_float,
            sigma=sigma,
            wavelet=wavelet,
            mode=mode,
            rescale_sigma=rescale,
            channel_axis=-1 if is_color else None
        )
        
        return self._ensure_uint8(result)

