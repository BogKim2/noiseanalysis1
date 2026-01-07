# -*- coding: utf-8 -*-
"""
SNR (Signal-to-Noise Ratio) 계산
기본 정의: SNR = μ_signal / σ_noise
"""
import numpy as np
from typing import Optional, Tuple


def calculate_snr(
    image: np.ndarray,
    roi: Optional[Tuple[int, int, int, int]] = None,
    method: str = "mean_std"
) -> float:
    """
    이미지의 SNR을 계산합니다.
    
    Args:
        image: 입력 이미지 (grayscale)
        roi: ROI 영역 (x, y, width, height). None이면 전체 이미지 사용
        method: 계산 방법
            - "mean_std": μ / σ (기본)
            - "rms": RMS 기반 SNR
    
    Returns:
        SNR 값 (높을수록 좋음)
    """
    # grayscale 변환
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    # ROI 적용
    if roi is not None:
        x, y, w, h = roi
        img = img[y:y+h, x:x+w]
    
    # SNR 계산
    if method == "mean_std":
        mean_val = np.mean(img)
        std_val = np.std(img)
        if std_val == 0:
            return float('inf')
        return mean_val / std_val
    
    elif method == "rms":
        # RMS 기반 SNR
        rms = np.sqrt(np.mean(img ** 2))
        noise_std = estimate_noise_std(img)
        if noise_std == 0:
            return float('inf')
        return rms / noise_std
    
    else:
        raise ValueError(f"Unknown method: {method}")


def estimate_noise_std(image: np.ndarray) -> float:
    """
    이미지에서 노이즈 표준편차를 추정합니다.
    MAD (Median Absolute Deviation) 기반 추정
    """
    # Laplacian을 사용한 노이즈 추정
    from scipy.ndimage import laplace
    lap = laplace(image.astype(np.float64))
    
    # MAD 기반 노이즈 추정
    # σ ≈ MAD / 0.6745
    mad = np.median(np.abs(lap - np.median(lap)))
    return mad / 0.6745


def calculate_local_snr(
    image: np.ndarray,
    block_size: int = 32
) -> np.ndarray:
    """
    로컬 SNR 맵을 계산합니다.
    
    Args:
        image: 입력 이미지
        block_size: 블록 크기
    
    Returns:
        SNR 맵 (각 블록의 SNR)
    """
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    h, w = img.shape
    snr_map = np.zeros((h // block_size, w // block_size))
    
    for i in range(snr_map.shape[0]):
        for j in range(snr_map.shape[1]):
            y_start = i * block_size
            x_start = j * block_size
            block = img[y_start:y_start+block_size, x_start:x_start+block_size]
            
            mean_val = np.mean(block)
            std_val = np.std(block)
            if std_val > 0:
                snr_map[i, j] = mean_val / std_val
            else:
                snr_map[i, j] = float('inf')
    
    return snr_map


