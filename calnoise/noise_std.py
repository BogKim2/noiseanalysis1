# -*- coding: utf-8 -*-
"""
노이즈 표준편차 계산
배경 영역에서의 픽셀 표준편차 - 노이즈 "절대 크기"
"""
import numpy as np
from typing import Optional, Tuple


def calculate_noise_std(
    image: np.ndarray,
    roi: Optional[Tuple[int, int, int, int]] = None,
    method: str = "std"
) -> float:
    """
    이미지의 노이즈 표준편차를 계산합니다.
    
    Args:
        image: 입력 이미지 (grayscale)
        roi: ROI 영역 (x, y, width, height). None이면 전체 이미지 사용
        method: 계산 방법
            - "std": 단순 표준편차 (기본)
            - "mad": MAD 기반 (이상치에 강함)
            - "laplacian": 라플라시안 기반 노이즈 추정
    
    Returns:
        노이즈 표준편차 (낮을수록 좋음)
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
    
    if method == "std":
        # 단순 표준편차
        return float(np.std(img))
    
    elif method == "mad":
        # MAD 기반 노이즈 추정 (이상치에 강함)
        # σ ≈ 1.4826 * MAD
        median_val = np.median(img)
        mad = np.median(np.abs(img - median_val))
        return float(1.4826 * mad)
    
    elif method == "laplacian":
        # 라플라시안 기반 노이즈 추정
        from scipy.ndimage import laplace
        lap = laplace(img)
        # MAD 기반 추정
        mad = np.median(np.abs(lap - np.median(lap)))
        return float(mad / 0.6745)
    
    else:
        raise ValueError(f"Unknown method: {method}")


def calculate_noise_variance(
    image: np.ndarray,
    roi: Optional[Tuple[int, int, int, int]] = None
) -> float:
    """
    노이즈 분산 계산 (표준편차의 제곱)
    """
    std = calculate_noise_std(image, roi, method="std")
    return std ** 2


def estimate_background_roi(image: np.ndarray) -> Tuple[int, int, int, int]:
    """
    이미지에서 배경 영역을 자동으로 찾습니다.
    가장 균일한 영역을 배경으로 가정합니다.
    
    Returns:
        (x, y, width, height) 형태의 ROI
    """
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    h, w = img.shape
    block_size = min(32, h // 4, w // 4)
    
    if block_size < 8:
        # 이미지가 너무 작으면 전체 사용
        return (0, 0, w, h)
    
    min_std = float('inf')
    best_roi = (0, 0, block_size, block_size)
    
    # 슬라이딩 윈도우로 가장 균일한 영역 찾기
    step = block_size // 2
    for y in range(0, h - block_size, step):
        for x in range(0, w - block_size, step):
            block = img[y:y+block_size, x:x+block_size]
            std = np.std(block)
            if std < min_std:
                min_std = std
                best_roi = (x, y, block_size, block_size)
    
    return best_roi


