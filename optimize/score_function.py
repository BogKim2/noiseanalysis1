# -*- coding: utf-8 -*-
"""
가중치 기반 점수 계산 함수
노이즈 메트릭의 개선율을 기반으로 종합 점수 계산
핵심: 음수(악화)가 나타나지 않도록 강력한 페널티 적용
"""
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from logic.settings import get_settings

# 기본 가중치 설정
# SNR, Correlation, Sharpness, Coherence: 높을수록 좋음
# σ 값들: 낮을수록 좋음
DEFAULT_WEIGHTS = {
    # SNR 관련 (높을수록 좋음)
    "snr": 2.0,
    "snr_rms": 1.0,
    
    # 노이즈 표준편차 (낮을수록 좋음)
    "noise_std": 0.5,
    "noise_std_mad": 1.0,  # MAD도 중요 (음수 방지)
    "noise_std_laplacian": 1.5,
    
    # 라인별 노이즈 (낮을수록 좋음)
    "linewise_h": 1.0,
    "linewise_v": 1.0,
    "line_correlation": 0.5,  # 높을수록 좋음
    "abnormal_lines_count": 1.0,  # 낮을수록 좋음 (음수 방지)
    
    # 에지 관련 - 에지 보존이 매우 중요!
    "edge_noise": 1.0,  # 낮을수록 좋음
    "edge_sharpness": 5.0,  # 높을수록 좋음 (에지 보존 매우 중요! 가중치 상향)
    "gradient_variance": 0.5,  # 낮을수록 좋음
    "edge_coherence": 1.0,  # 높을수록 좋음
    
    # PSD 관련 (낮을수록 좋음)
    "total_spectral_energy": 0.3,
    "psd_peaks_count": 0.3,
}

# 높을수록 좋은 메트릭 목록
HIGHER_IS_BETTER = {
    "snr", "snr_rms", "line_correlation", "edge_sharpness", "edge_coherence"
}

# 절대 악화되면 안 되는 핵심 메트릭 (강력 페널티)
CRITICAL_METRICS = {
    "edge_sharpness",  # 에지 선명도 악화 방지
    "noise_std_mad",   # MAD 기반 노이즈 악화 방지
    "abnormal_lines_count",  # 비정상 라인 증가 방지
}


@dataclass
class ScoreResult:
    """점수 계산 결과"""
    total_score: float  # 총 점수 (높을수록 좋음)
    metric_scores: Dict[str, float]  # 개별 메트릭 점수
    improvements: Dict[str, float]  # 개선율 (%)
    penalty: float  # 음수 페널티
    negative_count: int  # 음수(악화) 메트릭 개수
    

class ScoreFunction:
    """가중치 기반 점수 계산기 - 음수 최소화 중심"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None, use_saved_settings: bool = True):
        """
        Args:
            weights: 메트릭별 가중치. None이면 저장된 설정 또는 기본 가중치 사용
            use_saved_settings: True면 JSON에서 저장된 설정 로드
        """
        self.weights = weights if weights is not None else DEFAULT_WEIGHTS.copy()
        self.negative_penalty_factor = 5.0   # 일반 음수(악화) 페널티 배수
        self.critical_penalty_factor = 20.0  # 핵심 메트릭 악화 시 페널티
        self.negative_count_penalty = 50.0   # 음수 개수당 추가 페널티
        
        # 저장된 설정에서 값 로드
        if use_saved_settings:
            self._load_saved_settings()
    
    def calculate_score(
        self,
        original_metrics: Dict[str, float],
        processed_metrics: Dict[str, float]
    ) -> ScoreResult:
        """
        원본과 처리된 이미지의 메트릭을 비교하여 점수 계산
        핵심: 음수(악화)가 나타나면 강력한 페널티
        
        Args:
            original_metrics: 원본 이미지 메트릭 딕셔너리
            processed_metrics: 처리된 이미지 메트릭 딕셔너리
        
        Returns:
            ScoreResult: 점수 계산 결과
        """
        total_score = 0.0
        metric_scores = {}
        improvements = {}
        penalty = 0.0
        negative_count = 0
        
        for metric_name, weight in self.weights.items():
            if metric_name not in original_metrics or metric_name not in processed_metrics:
                continue
            
            orig_val = original_metrics[metric_name]
            proc_val = processed_metrics[metric_name]
            
            # 0으로 나누기 방지
            if abs(orig_val) < 1e-10:
                continue
            
            # 개선율 계산
            if metric_name in HIGHER_IS_BETTER:
                # 높을수록 좋음: (proc - orig) / orig * 100
                improvement = (proc_val - orig_val) / abs(orig_val) * 100
            else:
                # 낮을수록 좋음: (orig - proc) / orig * 100
                improvement = (orig_val - proc_val) / abs(orig_val) * 100
            
            improvements[metric_name] = improvement
            
            # 가중치 적용 점수
            score = weight * improvement
            
            # 음수 페널티 적용 (악화된 경우)
            if improvement < 0:
                negative_count += 1
                
                # 핵심 메트릭인 경우 더 강력한 페널티
                if metric_name in CRITICAL_METRICS:
                    penalty_factor = self.critical_penalty_factor
                else:
                    penalty_factor = self.negative_penalty_factor
                
                penalty_amount = abs(score) * penalty_factor
                penalty += penalty_amount
                score = -penalty_amount  # 음수로 만들어서 점수 감소
            
            metric_scores[metric_name] = score
            total_score += score
        
        # 음수 개수에 따른 추가 페널티 (음수가 많을수록 큰 페널티)
        if negative_count > 0:
            count_penalty = negative_count * self.negative_count_penalty
            penalty += count_penalty
            total_score -= count_penalty
        
        return ScoreResult(
            total_score=total_score,
            metric_scores=metric_scores,
            improvements=improvements,
            penalty=penalty,
            negative_count=negative_count
        )
    
    def quick_score(
        self,
        original_metrics: Dict[str, float],
        processed_metrics: Dict[str, float]
    ) -> float:
        """
        빠른 점수 계산 (총 점수만 반환)
        최적화 과정에서 반복 호출용
        핵심: 음수가 있으면 매우 낮은 점수
        """
        total_score = 0.0
        negative_count = 0
        
        for metric_name, weight in self.weights.items():
            if metric_name not in original_metrics or metric_name not in processed_metrics:
                continue
            
            orig_val = original_metrics[metric_name]
            proc_val = processed_metrics[metric_name]
            
            if abs(orig_val) < 1e-10:
                continue
            
            if metric_name in HIGHER_IS_BETTER:
                improvement = (proc_val - orig_val) / abs(orig_val) * 100
            else:
                improvement = (orig_val - proc_val) / abs(orig_val) * 100
            
            score = weight * improvement
            
            # 음수(악화)에 강력한 페널티
            if improvement < 0:
                negative_count += 1
                
                if metric_name in CRITICAL_METRICS:
                    score = -abs(score) * self.critical_penalty_factor
                else:
                    score = -abs(score) * self.negative_penalty_factor
            
            total_score += score
        
        # 음수 개수 페널티
        if negative_count > 0:
            total_score -= negative_count * self.negative_count_penalty
        
        return total_score
    
    def set_weight(self, metric_name: str, weight: float) -> None:
        """개별 가중치 설정"""
        self.weights[metric_name] = weight
    
    def set_penalty_factor(self, factor: float) -> None:
        """음수 페널티 배수 설정"""
        self.negative_penalty_factor = factor
    
    def set_critical_penalty_factor(self, factor: float) -> None:
        """핵심 메트릭 페널티 배수 설정"""
        self.critical_penalty_factor = factor
    
    def _load_saved_settings(self) -> None:
        """저장된 최적화 설정 로드"""
        try:
            settings = get_settings()
            opt_weights = settings.get("optimization_weights", {})
            
            if not opt_weights:
                return
            
            # 핵심 메트릭 가중치 업데이트
            if "snr" in opt_weights:
                self.weights["snr"] = opt_weights["snr"]
            if "noise_std_mad" in opt_weights:
                self.weights["noise_std_mad"] = opt_weights["noise_std_mad"]
            if "edge_sharpness" in opt_weights:
                self.weights["edge_sharpness"] = opt_weights["edge_sharpness"]
            if "linewise_h" in opt_weights:
                self.weights["linewise_h"] = opt_weights["linewise_h"]
            if "abnormal_lines_count" in opt_weights:
                self.weights["abnormal_lines_count"] = opt_weights["abnormal_lines_count"]
            
            # 페널티 설정 업데이트
            if "negative_penalty_factor" in opt_weights:
                self.negative_penalty_factor = opt_weights["negative_penalty_factor"]
            if "critical_penalty_factor" in opt_weights:
                self.critical_penalty_factor = opt_weights["critical_penalty_factor"]
            if "negative_count_penalty" in opt_weights:
                self.negative_count_penalty = opt_weights["negative_count_penalty"]
                
        except Exception as e:
            print(f"Failed to load optimization settings: {e}")
    
    def reload_settings(self) -> None:
        """설정 다시 로드 (설정 변경 후 호출)"""
        self._load_saved_settings()

