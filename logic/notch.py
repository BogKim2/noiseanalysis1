# -*- coding: utf-8 -*-
"""
Frequency Notch Filtering 구현
특정 주파수 제거 (주기적 노이즈 제거)
"""
import numpy as np
from scipy import fft
from .filter_base import FilterBase, FilterParameter


class NotchFilter(FilterBase):
    """Frequency Notch Filtering - 특정 주파수 제거"""
    
    @property
    def name(self) -> str:
        return "Notch"
    
    @property
    def description(self) -> str:
        return "Removes periodic noise by filtering specific frequencies (ideal for mechanical vibration artifacts)."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="center_freq",
            display_name="Center Frequency",
            value=0.25,
            min_value=0.01,
            max_value=0.5,
            step=0.01,
            param_type="float",
            description="Normalized center frequency to remove (0-0.5)"
        ))
        self.add_parameter(FilterParameter(
            name="bandwidth",
            display_name="Notch Bandwidth",
            value=0.05,
            min_value=0.01,
            max_value=0.2,
            step=0.01,
            param_type="float",
            description="Width of the notch filter"
        ))
        self.add_parameter(FilterParameter(
            name="direction",
            display_name="Notch Direction",
            value="both",
            param_type="choice",
            choices=["horizontal", "vertical", "both"],
            description="Direction of periodic noise"
        ))
        self.add_parameter(FilterParameter(
            name="auto_detect",
            display_name="Auto Detect Peaks",
            value=0,
            min_value=0,
            max_value=1,
            step=1,
            param_type="int",
            description="Automatically detect noise frequencies (1=yes, 0=no)"
        ))
        self.add_parameter(FilterParameter(
            name="num_notches",
            display_name="Number of Notches",
            value=1,
            min_value=1,
            max_value=5,
            step=1,
            param_type="int",
            description="Number of notch filters (harmonics)"
        ))
    
    def _create_notch_filter(self, shape: tuple, center_freq: float, 
                              bandwidth: float, direction: str) -> np.ndarray:
        """노치 필터 생성"""
        rows, cols = shape
        crow, ccol = rows // 2, cols // 2
        
        # 주파수 좌표
        u = np.arange(rows) - crow
        v = np.arange(cols) - ccol
        U, V = np.meshgrid(v, u)
        
        # 정규화된 주파수
        U_norm = U / cols
        V_norm = V / rows
        
        H = np.ones(shape)
        
        if direction in ["horizontal", "both"]:
            # 수평 방향 노치 (세로 줄무늬 제거)
            notch_u = np.abs(U_norm - center_freq) < bandwidth/2
            notch_u |= np.abs(U_norm + center_freq) < bandwidth/2
            # 중심 근처는 제외
            center_mask = np.abs(V_norm) < 0.05
            notch_u &= center_mask
            H[notch_u] = 0
            
        if direction in ["vertical", "both"]:
            # 수직 방향 노치 (가로 줄무늬 제거)
            notch_v = np.abs(V_norm - center_freq) < bandwidth/2
            notch_v |= np.abs(V_norm + center_freq) < bandwidth/2
            # 중심 근처는 제외
            center_mask = np.abs(U_norm) < 0.05
            notch_v &= center_mask
            H[notch_v] = 0
        
        # 부드러운 전환을 위해 가우시안 블러
        from scipy.ndimage import gaussian_filter
        H = gaussian_filter(H, sigma=1)
        
        return H
    
    def _detect_peaks(self, magnitude: np.ndarray, num_peaks: int = 3) -> list:
        """주파수 스펙트럼에서 피크 검출"""
        from scipy.ndimage import maximum_filter
        
        rows, cols = magnitude.shape
        crow, ccol = rows // 2, cols // 2
        
        # DC 성분 제거
        mag_copy = magnitude.copy()
        mag_copy[crow-5:crow+5, ccol-5:ccol+5] = 0
        
        # 로컬 최대값 찾기
        local_max = maximum_filter(mag_copy, size=10)
        peaks = (mag_copy == local_max) & (mag_copy > np.percentile(mag_copy, 99))
        
        # 피크 좌표
        peak_coords = np.argwhere(peaks)
        peak_values = mag_copy[peaks]
        
        # 상위 피크 선택
        if len(peak_values) > 0:
            sorted_idx = np.argsort(peak_values)[::-1]
            top_peaks = peak_coords[sorted_idx[:num_peaks]]
            
            # 정규화된 주파수로 변환
            freqs = []
            for p in top_peaks:
                fu = (p[1] - ccol) / cols
                fv = (p[0] - crow) / rows
                freqs.append((abs(fu), abs(fv)))
            return freqs
        
        return []
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Notch 필터링 적용"""
        image_float = self._ensure_float(image)
        
        center_freq = self.get_parameter("center_freq")
        bandwidth = self.get_parameter("bandwidth")
        direction = self.get_parameter("direction")
        auto_detect = bool(self.get_parameter("auto_detect"))
        num_notches = self.get_parameter("num_notches")
        
        # grayscale 처리
        if len(image_float.shape) == 3:
            result = np.zeros_like(image_float)
            for i in range(image_float.shape[2]):
                result[:, :, i] = self._apply_notch(
                    image_float[:, :, i], center_freq, bandwidth, 
                    direction, auto_detect, num_notches
                )
        else:
            result = self._apply_notch(
                image_float, center_freq, bandwidth, 
                direction, auto_detect, num_notches
            )
        
        return self._ensure_uint8(result)
    
    def _apply_notch(self, image: np.ndarray, center_freq: float, bandwidth: float,
                     direction: str, auto_detect: bool, num_notches: int) -> np.ndarray:
        """2D 이미지에 노치 필터 적용"""
        # FFT
        f_transform = fft.fft2(image)
        f_shift = fft.fftshift(f_transform)
        magnitude = np.log1p(np.abs(f_shift))
        
        shape = image.shape
        
        # 자동 피크 검출
        if auto_detect:
            peaks = self._detect_peaks(magnitude, num_notches)
            if peaks:
                center_freq = peaks[0][0] if peaks[0][0] > peaks[0][1] else peaks[0][1]
        
        # 노치 필터 생성 (하모닉 포함)
        H = np.ones(shape)
        for n in range(1, num_notches + 1):
            H_n = self._create_notch_filter(shape, center_freq * n, bandwidth, direction)
            H = H * H_n
        
        # 필터 적용
        filtered = f_shift * H
        
        # 역변환
        f_ishift = fft.ifftshift(filtered)
        result = fft.ifft2(f_ishift)
        result = np.abs(result)
        
        # 클리핑
        result = np.clip(result, 0, 1)
        
        return result

