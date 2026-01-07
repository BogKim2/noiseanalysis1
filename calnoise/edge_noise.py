# -*- coding: utf-8 -*-
"""
Edge-based Noise (경계 노이즈)
해상도 보존 평가용 - 경계 법선 방향 intensity std, Gradient magnitude variance
denoise가 구조를 망쳤는지 판단 가능
"""
import numpy as np
from typing import Tuple, Optional


def calculate_edge_noise(
    image: np.ndarray,
    edge_threshold: Optional[float] = None
) -> float:
    """
    에지 기반 노이즈를 계산합니다.
    에지 영역에서의 그래디언트 크기 분산
    
    Args:
        image: 입력 이미지 (grayscale)
        edge_threshold: 에지 탐지 임계값. None이면 자동
    
    Returns:
        에지 노이즈 (낮을수록 깨끗한 에지)
    """
    from scipy.ndimage import sobel
    
    # grayscale 변환
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    # Sobel 그래디언트
    gx = sobel(img, axis=1)
    gy = sobel(img, axis=0)
    
    # 그래디언트 크기
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    # 에지 마스크
    if edge_threshold is None:
        edge_threshold = np.mean(grad_mag) + np.std(grad_mag)
    
    edge_mask = grad_mag > edge_threshold
    
    if not np.any(edge_mask):
        return 0.0
    
    # 에지 영역에서의 그래디언트 변화 (노이즈)
    edge_gradients = grad_mag[edge_mask]
    
    # 에지 노이즈 = 에지 영역의 그래디언트 표준편차
    return float(np.std(edge_gradients))


def calculate_gradient_variance(
    image: np.ndarray
) -> float:
    """
    전체 그래디언트 크기의 분산을 계산합니다.
    
    Returns:
        그래디언트 분산
    """
    from scipy.ndimage import sobel
    
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    gx = sobel(img, axis=1)
    gy = sobel(img, axis=0)
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    return float(np.var(grad_mag))


def calculate_edge_sharpness(
    image: np.ndarray
) -> float:
    """
    에지 선명도를 계산합니다.
    높은 값은 선명한 에지, 낮은 값은 흐릿한 에지
    
    Returns:
        에지 선명도 점수
    """
    from scipy.ndimage import sobel
    
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    gx = sobel(img, axis=1)
    gy = sobel(img, axis=0)
    grad_mag = np.sqrt(gx**2 + gy**2)
    
    # 평균 그래디언트 크기
    return float(np.mean(grad_mag))


def calculate_edge_preservation(
    original: np.ndarray,
    processed: np.ndarray
) -> float:
    """
    디노이징 후 에지 보존율을 계산합니다.
    
    Args:
        original: 원본 이미지
        processed: 처리된 이미지
    
    Returns:
        에지 보존율 (0~1, 높을수록 좋음)
    """
    from scipy.ndimage import sobel
    
    # grayscale 변환
    if len(original.shape) == 3:
        orig = np.mean(original, axis=2)
    else:
        orig = original.astype(np.float64)
    
    if len(processed.shape) == 3:
        proc = np.mean(processed, axis=2)
    else:
        proc = processed.astype(np.float64)
    
    # 원본 그래디언트
    gx_orig = sobel(orig, axis=1)
    gy_orig = sobel(orig, axis=0)
    grad_orig = np.sqrt(gx_orig**2 + gy_orig**2)
    
    # 처리된 이미지 그래디언트
    gx_proc = sobel(proc, axis=1)
    gy_proc = sobel(proc, axis=0)
    grad_proc = np.sqrt(gx_proc**2 + gy_proc**2)
    
    # 에지 영역 마스크 (원본 기준)
    threshold = np.mean(grad_orig) + np.std(grad_orig)
    edge_mask = grad_orig > threshold
    
    if not np.any(edge_mask):
        return 1.0
    
    # 에지 영역에서의 그래디언트 비율
    orig_edge_mag = np.mean(grad_orig[edge_mask])
    proc_edge_mag = np.mean(grad_proc[edge_mask])
    
    if orig_edge_mag == 0:
        return 1.0
    
    preservation = proc_edge_mag / orig_edge_mag
    return float(min(preservation, 1.0))


def calculate_local_edge_coherence(
    image: np.ndarray,
    block_size: int = 16
) -> float:
    """
    로컬 에지 일관성을 계산합니다.
    에지 방향의 일관성 - 노이즈가 있으면 에지 방향이 불규칙
    
    Returns:
        에지 일관성 (0~1, 높을수록 좋음)
    """
    from scipy.ndimage import sobel
    
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    gx = sobel(img, axis=1)
    gy = sobel(img, axis=0)
    
    h, w = img.shape
    coherence_values = []
    
    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block_gx = gx[y:y+block_size, x:x+block_size]
            block_gy = gy[y:y+block_size, x:x+block_size]
            
            # 그래디언트 방향
            angles = np.arctan2(block_gy, block_gx)
            
            # 방향의 일관성 (원형 분산)
            cos_mean = np.mean(np.cos(angles))
            sin_mean = np.mean(np.sin(angles))
            coherence = np.sqrt(cos_mean**2 + sin_mean**2)
            coherence_values.append(coherence)
    
    if not coherence_values:
        return 0.0
    
    return float(np.mean(coherence_values))


