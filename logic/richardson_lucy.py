# -*- coding: utf-8 -*-
"""
Richardson-Lucy Deconvolution 필터
반복적 복원 알고리즘으로 블러와 노이즈 제거
"""
import numpy as np
from scipy.signal import convolve2d
from .filter_base import FilterBase, FilterParameter


class RichardsonLucyFilter(FilterBase):
    """Richardson-Lucy Deconvolution 필터"""
    
    @property
    def name(self) -> str:
        return "Richardson-Lucy"
    
    @property
    def description(self) -> str:
        return "Iterative Richardson-Lucy deconvolution with optional TV regularization."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="psf_size",
            display_name="PSF Size",
            value=5,
            min_value=3,
            max_value=31,
            step=2,
            param_type="int",
            description="Point Spread Function kernel size (odd number)"
        ))
        self.add_parameter(FilterParameter(
            name="psf_sigma",
            display_name="PSF Sigma",
            value=1.0,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            param_type="float",
            description="Gaussian PSF standard deviation"
        ))
        self.add_parameter(FilterParameter(
            name="iterations",
            display_name="Iterations",
            value=10,
            min_value=1,
            max_value=100,
            step=1,
            param_type="int",
            description="Number of deconvolution iterations"
        ))
        self.add_parameter(FilterParameter(
            name="regularization",
            display_name="Regularization",
            value=0.001,
            min_value=0.0,
            max_value=0.1,
            step=0.001,
            param_type="float",
            description="Total Variation regularization strength"
        ))
    
    def _create_gaussian_psf(self, size: int, sigma: float) -> np.ndarray:
        """가우시안 PSF 생성"""
        # size가 홀수가 되도록 보장
        size = size if size % 2 == 1 else size + 1
        
        # 2D 가우시안 커널 생성
        x = np.arange(size) - size // 2
        y = np.arange(size) - size // 2
        xx, yy = np.meshgrid(x, y)
        
        psf = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        psf /= psf.sum()  # 정규화
        
        return psf
    
    def _convolve(self, image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
        """컨볼루션 수행"""
        return convolve2d(image, kernel, mode='same', boundary='symm')
    
    def _tv_regularization(self, image: np.ndarray, weight: float) -> np.ndarray:
        """Total Variation 정규화"""
        if weight <= 0:
            return np.zeros_like(image)
        
        # 그래디언트 계산
        grad_x = np.diff(image, axis=1, append=image[:, -1:])
        grad_y = np.diff(image, axis=0, append=image[-1:, :])
        
        # TV 그래디언트
        eps = 1e-8
        grad_mag = np.sqrt(grad_x**2 + grad_y**2 + eps)
        
        # TV 정규화 항
        tv_x = grad_x / grad_mag
        tv_y = grad_y / grad_mag
        
        # Divergence
        div_x = np.diff(tv_x, axis=1, prepend=tv_x[:, :1])
        div_y = np.diff(tv_y, axis=0, prepend=tv_y[:1, :])
        
        return weight * (div_x + div_y)
    
    def _apply_single_channel(self, channel: np.ndarray, psf_size: int, psf_sigma: float, 
                               iterations: int, regularization: float) -> np.ndarray:
        """단일 채널에 Richardson-Lucy deconvolution 적용"""
        # 0값 방지
        img = np.clip(channel, 1e-10, None)
        
        # PSF 생성
        psf = self._create_gaussian_psf(psf_size, psf_sigma)
        psf_flip = np.flip(psf)
        
        # 초기 추정값
        estimate = img.copy()
        
        # 반복 복원
        for i in range(iterations):
            blurred = self._convolve(estimate, psf)
            blurred = np.clip(blurred, 1e-10, None)
            
            ratio = img / blurred
            correction = self._convolve(ratio, psf_flip)
            
            if regularization > 0:
                tv_term = self._tv_regularization(estimate, regularization)
                estimate = estimate * correction / (1 + np.abs(tv_term) + 1e-10)
            else:
                estimate = estimate * correction
            
            estimate = np.clip(estimate, 1e-10, None)
        
        return np.clip(estimate, 0, 1)
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Richardson-Lucy deconvolution 적용"""
        psf_size = int(self.get_parameter("psf_size"))
        psf_sigma = float(self.get_parameter("psf_sigma"))
        iterations = int(self.get_parameter("iterations"))
        regularization = float(self.get_parameter("regularization"))
        
        # 입력 이미지 정규화
        img_float = self._ensure_float(image)
        
        # 컬러 이미지 처리
        if len(img_float.shape) == 3:
            # 각 채널에 개별 적용
            result = np.zeros_like(img_float)
            for c in range(img_float.shape[2]):
                result[:, :, c] = self._apply_single_channel(
                    img_float[:, :, c], psf_size, psf_sigma, iterations, regularization
                )
        else:
            # Grayscale
            result = self._apply_single_channel(img_float, psf_size, psf_sigma, iterations, regularization)
        
        return self._ensure_uint8(result)
