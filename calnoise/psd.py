# -*- coding: utf-8 -*-
"""
Power Spectral Density (PSD) 분석
진동 노이즈 정량화의 핵심 - FFT → |F(u,v)|² 주파수별 에너지 분포 분석
"""
import numpy as np
from typing import Tuple, List, Optional


def calculate_psd(
    image: np.ndarray,
    normalize: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    이미지의 2D Power Spectral Density를 계산합니다.
    
    Args:
        image: 입력 이미지 (grayscale)
        normalize: 정규화 여부
    
    Returns:
        (psd_2d, freq_x, freq_y): 2D PSD와 주파수 축
    """
    # grayscale 변환
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    h, w = img.shape
    
    # 2D FFT
    fft = np.fft.fft2(img)
    fft_shifted = np.fft.fftshift(fft)
    
    # Power Spectral Density
    psd_2d = np.abs(fft_shifted) ** 2
    
    if normalize:
        psd_2d = psd_2d / (h * w)
    
    # 주파수 축
    freq_x = np.fft.fftshift(np.fft.fftfreq(w))
    freq_y = np.fft.fftshift(np.fft.fftfreq(h))
    
    return psd_2d, freq_x, freq_y


def calculate_1d_psd(
    image: np.ndarray,
    direction: str = "horizontal"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    1D PSD를 계산합니다 (수평 또는 수직 방향).
    
    Args:
        image: 입력 이미지
        direction: "horizontal" 또는 "vertical"
    
    Returns:
        (psd_1d, frequencies): 1D PSD와 주파수
    """
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    if direction == "horizontal":
        # 행별로 FFT 후 평균
        fft_rows = np.fft.fft(img, axis=1)
        psd_rows = np.abs(fft_rows) ** 2
        psd_1d = np.mean(psd_rows, axis=0)
        n = img.shape[1]
    else:
        # 열별로 FFT 후 평균
        fft_cols = np.fft.fft(img, axis=0)
        psd_cols = np.abs(fft_cols) ** 2
        psd_1d = np.mean(psd_cols, axis=1)
        n = img.shape[0]
    
    # 양의 주파수만
    psd_1d = psd_1d[:n//2]
    frequencies = np.fft.fftfreq(n)[:n//2]
    
    return psd_1d, frequencies


def calculate_radial_psd(
    image: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    방사형(radial) PSD를 계산합니다.
    
    Returns:
        (radial_psd, radii): 방사형 PSD와 반경
    """
    psd_2d, freq_x, freq_y = calculate_psd(image)
    
    h, w = psd_2d.shape
    cy, cx = h // 2, w // 2
    
    # 거리 맵
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2).astype(int)
    
    # 방사형 평균
    max_r = min(cx, cy)
    radial_psd = np.zeros(max_r)
    for i in range(max_r):
        mask = (r == i)
        if np.any(mask):
            radial_psd[i] = np.mean(psd_2d[mask])
    
    radii = np.arange(max_r)
    
    return radial_psd, radii


def analyze_psd_peaks(
    psd_1d: np.ndarray,
    frequencies: np.ndarray,
    threshold_factor: float = 3.0
) -> List[dict]:
    """
    PSD에서 피크(진동 노이즈)를 분석합니다.
    
    Args:
        psd_1d: 1D PSD
        frequencies: 주파수 배열
        threshold_factor: 평균 대비 피크 탐지 임계값
    
    Returns:
        피크 정보 리스트 [{"frequency": f, "power": p, "relative_power": rp}, ...]
    """
    # DC 성분 제외
    psd_no_dc = psd_1d[1:]
    freq_no_dc = frequencies[1:]
    
    if len(psd_no_dc) == 0:
        return []
    
    # 기준선 (중앙값)
    baseline = np.median(psd_no_dc)
    threshold = baseline * threshold_factor
    
    # 피크 찾기
    peaks = []
    for i in range(1, len(psd_no_dc) - 1):
        if psd_no_dc[i] > threshold:
            # 지역 최대값 확인
            if psd_no_dc[i] > psd_no_dc[i-1] and psd_no_dc[i] > psd_no_dc[i+1]:
                peaks.append({
                    "frequency": float(freq_no_dc[i]),
                    "power": float(psd_no_dc[i]),
                    "relative_power": float(psd_no_dc[i] / baseline) if baseline > 0 else 0
                })
    
    # 파워 순으로 정렬
    peaks.sort(key=lambda x: x["power"], reverse=True)
    
    return peaks


def calculate_total_spectral_energy(
    image: np.ndarray,
    freq_range: Optional[Tuple[float, float]] = None
) -> float:
    """
    특정 주파수 범위의 총 스펙트럴 에너지를 계산합니다.
    
    Args:
        image: 입력 이미지
        freq_range: (min_freq, max_freq). None이면 전체 범위
    
    Returns:
        총 에너지
    """
    psd_1d, frequencies = calculate_1d_psd(image, "horizontal")
    
    if freq_range is not None:
        min_f, max_f = freq_range
        mask = (np.abs(frequencies) >= min_f) & (np.abs(frequencies) <= max_f)
        return float(np.sum(psd_1d[mask]))
    
    return float(np.sum(psd_1d))


