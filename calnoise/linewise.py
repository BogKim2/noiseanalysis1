# -*- coding: utf-8 -*-
"""
Line-wise Noise Metric (SEM 특화)
Scan / 진동 구분용 - 각 라인의 평균값 변화: σ_line = std(μ_row)
Y방향 σ ↑ → scan/진동 문제
"""
import numpy as np
from typing import Tuple


def calculate_linewise_noise(
    image: np.ndarray,
    direction: str = "horizontal"
) -> float:
    """
    라인별 노이즈 메트릭을 계산합니다.
    각 라인(행 또는 열)의 평균값 변화의 표준편차
    
    Args:
        image: 입력 이미지 (grayscale)
        direction: "horizontal" (행 기준) 또는 "vertical" (열 기준)
    
    Returns:
        라인별 노이즈 표준편차 (낮을수록 좋음)
    """
    # grayscale 변환
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    if direction == "horizontal":
        # 각 행의 평균
        line_means = np.mean(img, axis=1)
    else:
        # 각 열의 평균
        line_means = np.mean(img, axis=0)
    
    # 라인 평균들의 표준편차
    return float(np.std(line_means))


def calculate_linewise_profile(
    image: np.ndarray,
    direction: str = "horizontal"
) -> np.ndarray:
    """
    라인별 프로파일(평균값 배열)을 반환합니다.
    
    Args:
        image: 입력 이미지
        direction: "horizontal" 또는 "vertical"
    
    Returns:
        라인별 평균값 배열
    """
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    if direction == "horizontal":
        return np.mean(img, axis=1)
    else:
        return np.mean(img, axis=0)


def calculate_linewise_variation(
    image: np.ndarray
) -> Tuple[float, float]:
    """
    수평 및 수직 방향의 라인별 변화를 모두 계산합니다.
    
    Returns:
        (horizontal_sigma, vertical_sigma)
    """
    h_sigma = calculate_linewise_noise(image, "horizontal")
    v_sigma = calculate_linewise_noise(image, "vertical")
    return h_sigma, v_sigma


def detect_scan_lines(
    image: np.ndarray,
    threshold_factor: float = 2.0
) -> np.ndarray:
    """
    비정상적인 스캔 라인을 탐지합니다.
    
    Args:
        image: 입력 이미지
        threshold_factor: 탐지 임계값 (평균 대비 몇 배)
    
    Returns:
        비정상 라인의 인덱스 배열
    """
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    # 각 행의 평균
    line_means = np.mean(img, axis=1)
    
    # 전체 평균과 표준편차
    global_mean = np.mean(line_means)
    global_std = np.std(line_means)
    
    if global_std == 0:
        return np.array([], dtype=int)
    
    # 비정상 라인 탐지
    threshold = threshold_factor * global_std
    abnormal_mask = np.abs(line_means - global_mean) > threshold
    
    return np.where(abnormal_mask)[0]


def calculate_line_correlation(
    image: np.ndarray,
    lag: int = 1
) -> float:
    """
    인접 라인 간의 상관관계를 계산합니다.
    높은 상관관계는 정상, 낮은 상관관계는 노이즈 존재
    
    Args:
        image: 입력 이미지
        lag: 라인 간격
    
    Returns:
        상관계수 (높을수록 좋음)
    """
    if len(image.shape) == 3:
        img = np.mean(image, axis=2)
    else:
        img = image.astype(np.float64)
    
    if img.shape[0] <= lag:
        return 0.0
    
    # 인접 라인 간 상관관계
    lines_a = img[:-lag].flatten()
    lines_b = img[lag:].flatten()
    
    # Pearson 상관계수
    corr = np.corrcoef(lines_a, lines_b)[0, 1]
    
    return float(corr) if not np.isnan(corr) else 0.0


