# -*- coding: utf-8 -*-
"""
최적화 알고리즘 베이스 클래스
모든 최적화 알고리즘이 상속받는 추상 클래스
"""
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable, Any
import time

# 파라미터 범위 정의 (min, max, step)
PARAM_BOUNDS = {
    "Linewise": {
        "window_size": (3, 31, 2),       # 홀수만
        "strength": (0.0, 1.0, 0.05),
    },
    "Notch": {
        "center_freq": (0.1, 0.5, 0.05),
        "bandwidth": (0.01, 0.2, 0.02),
        "num_notches": (1, 5, 1),
    },
    "Anisotropic": {
        "iterations": (5, 30, 5),
        "kappa": (10, 100, 10),
        "gamma": (0.05, 0.25, 0.05),
    },
    "Bilateral": {
        "d": (3, 15, 2),
        "sigmaColor": (10, 100, 10),
        "sigmaSpace": (10, 100, 10),
    },
    "NLM": {
        "h": (0.5, 15.0, 0.5),
        "templateWindowSize": (3, 11, 2),
        "searchWindowSize": (7, 21, 2),
    },
    "Wavelet": {
        "sigma": (0.1, 2.0, 0.1),
    },
    "Fourier": {
        "cutoff": (0.1, 0.9, 0.1),
        "order": (1, 8, 1),
        "bandwidth": (0.05, 0.3, 0.05),
    },
}


@dataclass
class OptimizationResult:
    """최적화 결과"""
    best_params: Dict[str, Dict[str, Any]]  # 필터별 최적 파라미터
    best_score: float  # 최고 점수
    initial_score: float  # 초기 점수
    iterations: int  # 반복 횟수
    elapsed_time: float  # 소요 시간 (초)
    score_history: List[float] = field(default_factory=list)  # 점수 변화 기록
    improved: bool = False  # 개선 여부


class OptimizerBase(ABC):
    """최적화 알고리즘 베이스 클래스"""
    
    def __init__(
        self,
        score_function: Any,  # ScoreFunction 인스턴스
        param_bounds: Optional[Dict] = None,
        max_iterations: int = 100,
        progress_callback: Optional[Callable[[int, int, float], None]] = None
    ):
        """
        Args:
            score_function: 점수 계산 함수 객체
            param_bounds: 파라미터 범위. None이면 기본값 사용
            max_iterations: 최대 반복 횟수
            progress_callback: 진행 상황 콜백 (current, total, score)
        """
        self.score_function = score_function
        self.param_bounds = param_bounds if param_bounds else PARAM_BOUNDS
        self.max_iterations = max_iterations
        self.progress_callback = progress_callback
        
        self._stop_requested = False
    
    @abstractmethod
    def optimize(
        self,
        image: np.ndarray,
        pipeline_filters: List[str],
        current_params: Dict[str, Dict[str, Any]],
        apply_filter_func: Callable,
        analyze_func: Callable
    ) -> OptimizationResult:
        """
        최적화 실행
        
        Args:
            image: 원본 이미지
            pipeline_filters: 파이프라인 필터 이름 리스트 (예: ["Linewise", "Notch", "Anisotropic"])
            current_params: 현재 파라미터 딕셔너리
            apply_filter_func: 필터 적용 함수 (image, filter_name, params) -> processed_image
            analyze_func: 노이즈 분석 함수 (image) -> metrics_dict
        
        Returns:
            OptimizationResult: 최적화 결과
        """
        pass
    
    def stop(self) -> None:
        """최적화 중지 요청"""
        self._stop_requested = True
    
    def _report_progress(self, current: int, total: int, score: float) -> None:
        """진행 상황 보고"""
        if self.progress_callback:
            self.progress_callback(current, total, score)
    
    def _get_param_range(
        self,
        filter_name: str,
        param_name: str
    ) -> Tuple[float, float, float]:
        """파라미터 범위 가져오기 (min, max, step)"""
        if filter_name in self.param_bounds:
            if param_name in self.param_bounds[filter_name]:
                return self.param_bounds[filter_name][param_name]
        return (0.0, 1.0, 0.1)  # 기본값
    
    def _clip_param(
        self,
        filter_name: str,
        param_name: str,
        value: float
    ) -> float:
        """파라미터 값을 범위 내로 클리핑"""
        min_val, max_val, _ = self._get_param_range(filter_name, param_name)
        return max(min_val, min(max_val, value))
    
    def _evaluate(
        self,
        image: np.ndarray,
        pipeline_filters: List[str],
        params: Dict[str, Dict[str, Any]],
        original_metrics: Dict[str, float],
        apply_filter_func: Callable,
        analyze_func: Callable
    ) -> float:
        """
        파라미터 조합 평가
        
        Returns:
            점수 (높을수록 좋음)
        """
        # 순차적으로 필터 적용
        processed = image.copy()
        for filter_name in pipeline_filters:
            if filter_name in params:
                processed = apply_filter_func(processed, filter_name, params[filter_name])
        
        # 처리된 이미지 분석
        processed_metrics = analyze_func(processed)
        
        # 점수 계산
        return self.score_function.quick_score(original_metrics, processed_metrics)
    
    def _copy_params(
        self,
        params: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """파라미터 딕셔너리 깊은 복사"""
        return {
            filter_name: {k: v for k, v in filter_params.items()}
            for filter_name, filter_params in params.items()
        }


