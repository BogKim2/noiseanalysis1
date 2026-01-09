# -*- coding: utf-8 -*-
"""
Wiener Deconvolution 필터
주파수 도메인에서 노이즈와 블러를 동시에 처리
"""
import numpy as np
from scipy import fft
from typing import Tuple
from .filter_base import FilterBase, FilterParameter


class WienerFilter(FilterBase):
    """Wiener Deconvolution 필터"""
    
    @property
    def name(self) -> str:
        return "Wiener"
    
    @property
    def description(self) -> str:
        return "Wiener deconvolution for noise reduction and deblurring in frequency domain."
    
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
            name="nsr",
            display_name="NSR",
            value=0.01,
            min_value=0.001,
            max_value=1.0,
            step=0.001,
            param_type="float",
            description="Noise-to-Signal Ratio (regularization parameter)"
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
    
    def _pad_psf_to_image_size(self, psf: np.ndarray, image_shape: Tuple[int, int]) -> np.ndarray:
        """PSF를 이미지 크기로 패딩"""
        padded = np.zeros(image_shape)
        
        # PSF를 중앙에 배치
        ph, pw = psf.shape
        ih, iw = image_shape
        
        # 시작 위치 계산
        start_h = (ih - ph) // 2
        start_w = (iw - pw) // 2
        
        padded[start_h:start_h+ph, start_w:start_w+pw] = psf
        
        # 중심을 (0,0)으로 이동 (fftshift의 역)
        padded = np.roll(padded, -start_h - ph//2, axis=0)
        padded = np.roll(padded, -start_w - pw//2, axis=1)
        
        return padded
    
    def _apply_single_channel(self, channel: np.ndarray, psf_size: int, psf_sigma: float, nsr: float) -> np.ndarray:
        """단일 채널에 Wiener deconvolution 적용"""
        # PSF 생성
        psf = self._create_gaussian_psf(psf_size, psf_sigma)
        
        # PSF를 이미지 크기로 패딩
        psf_padded = self._pad_psf_to_image_size(psf, channel.shape)
        
        # FFT 수행
        img_fft = fft.fft2(channel)
        psf_fft = fft.fft2(psf_padded)
        
        # Wiener 필터 적용
        psf_conj = np.conj(psf_fft)
        psf_abs_sq = np.abs(psf_fft) ** 2
        wiener_filter = psf_conj / (psf_abs_sq + nsr)
        
        # 복원
        restored_fft = img_fft * wiener_filter
        restored = np.real(fft.ifft2(restored_fft))
        
        return np.clip(restored, 0, 1)
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Wiener deconvolution 적용"""
        psf_size = int(self.get_parameter("psf_size"))
        psf_sigma = float(self.get_parameter("psf_sigma"))
        nsr = float(self.get_parameter("nsr"))
        
        # 입력 이미지 정규화
        img_float = self._ensure_float(image)
        
        # 컬러 이미지 처리
        if len(img_float.shape) == 3:
            # 각 채널에 개별 적용
            result = np.zeros_like(img_float)
            for c in range(img_float.shape[2]):
                result[:, :, c] = self._apply_single_channel(
                    img_float[:, :, c], psf_size, psf_sigma, nsr
                )
        else:
            # Grayscale
            result = self._apply_single_channel(img_float, psf_size, psf_sigma, nsr)
        
        return self._ensure_uint8(result)
