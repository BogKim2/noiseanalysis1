# -*- coding: utf-8 -*-
"""
노이즈 분석기 - 모든 메트릭을 통합하여 분석
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from .snr import calculate_snr, estimate_noise_std, calculate_local_snr
from .noise_std import calculate_noise_std
from .psd import (
    calculate_1d_psd, analyze_psd_peaks, 
    calculate_total_spectral_energy, calculate_radial_psd
)
from .linewise import (
    calculate_linewise_noise, calculate_line_correlation,
    detect_scan_lines
)
from .edge_noise import (
    calculate_edge_noise, calculate_edge_preservation,
    calculate_gradient_variance, calculate_edge_sharpness,
    calculate_local_edge_coherence
)


@dataclass
class NoiseMetrics:
    """노이즈 메트릭 데이터 클래스 - 모든 메트릭 포함"""
    # SNR 관련
    snr: float = 0.0
    snr_rms: float = 0.0
    
    # 노이즈 표준편차 관련
    noise_std: float = 0.0
    noise_std_mad: float = 0.0
    noise_std_laplacian: float = 0.0
    
    # 라인별 노이즈
    linewise_h: float = 0.0
    linewise_v: float = 0.0
    line_correlation: float = 0.0
    abnormal_lines_count: int = 0
    
    # 에지 관련
    edge_noise: float = 0.0
    edge_sharpness: float = 0.0
    gradient_variance: float = 0.0
    edge_coherence: float = 0.0
    
    # PSD 관련
    total_spectral_energy: float = 0.0
    psd_peaks_count: int = 0
    psd_peaks: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, float]:
        """딕셔너리로 변환 (수치만)"""
        return {
            "snr": self.snr,
            "snr_rms": self.snr_rms,
            "noise_std": self.noise_std,
            "noise_std_mad": self.noise_std_mad,
            "noise_std_laplacian": self.noise_std_laplacian,
            "linewise_h": self.linewise_h,
            "linewise_v": self.linewise_v,
            "line_correlation": self.line_correlation,
            "abnormal_lines_count": self.abnormal_lines_count,
            "edge_noise": self.edge_noise,
            "edge_sharpness": self.edge_sharpness,
            "gradient_variance": self.gradient_variance,
            "edge_coherence": self.edge_coherence,
            "total_spectral_energy": self.total_spectral_energy,
            "psd_peaks_count": self.psd_peaks_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NoiseMetrics":
        """딕셔너리에서 생성"""
        return cls(
            snr=data.get("snr", 0.0),
            snr_rms=data.get("snr_rms", 0.0),
            noise_std=data.get("noise_std", 0.0),
            noise_std_mad=data.get("noise_std_mad", 0.0),
            noise_std_laplacian=data.get("noise_std_laplacian", 0.0),
            linewise_h=data.get("linewise_h", 0.0),
            linewise_v=data.get("linewise_v", 0.0),
            line_correlation=data.get("line_correlation", 0.0),
            abnormal_lines_count=int(data.get("abnormal_lines_count", 0)),
            edge_noise=data.get("edge_noise", 0.0),
            edge_sharpness=data.get("edge_sharpness", 0.0),
            gradient_variance=data.get("gradient_variance", 0.0),
            edge_coherence=data.get("edge_coherence", 0.0),
            total_spectral_energy=data.get("total_spectral_energy", 0.0),
            psd_peaks_count=int(data.get("psd_peaks_count", 0)),
            psd_peaks=data.get("psd_peaks", []),
        )


class NoiseAnalyzer:
    """노이즈 분석기 클래스"""
    
    def __init__(self):
        self._original_metrics: Optional[NoiseMetrics] = None
        self._processed_metrics: Optional[NoiseMetrics] = None
        self._original_image: Optional[np.ndarray] = None
        self._processed_image: Optional[np.ndarray] = None
    
    def analyze(self, image: np.ndarray) -> NoiseMetrics:
        """
        이미지의 모든 노이즈 메트릭을 계산합니다.
        """
        metrics = NoiseMetrics()
        
        # === SNR 관련 ===
        metrics.snr = calculate_snr(image, method="mean_std")
        metrics.snr_rms = calculate_snr(image, method="rms")
        
        # === 노이즈 표준편차 ===
        metrics.noise_std = calculate_noise_std(image, method="std")
        metrics.noise_std_mad = calculate_noise_std(image, method="mad")
        metrics.noise_std_laplacian = calculate_noise_std(image, method="laplacian")
        
        # === 라인별 노이즈 ===
        metrics.linewise_h = calculate_linewise_noise(image, "horizontal")
        metrics.linewise_v = calculate_linewise_noise(image, "vertical")
        metrics.line_correlation = calculate_line_correlation(image)
        abnormal_lines = detect_scan_lines(image)
        metrics.abnormal_lines_count = len(abnormal_lines)
        
        # === 에지 관련 ===
        metrics.edge_noise = calculate_edge_noise(image)
        metrics.edge_sharpness = calculate_edge_sharpness(image)
        metrics.gradient_variance = calculate_gradient_variance(image)
        metrics.edge_coherence = calculate_local_edge_coherence(image)
        
        # === PSD 관련 ===
        metrics.total_spectral_energy = calculate_total_spectral_energy(image)
        psd_h, freq_h = calculate_1d_psd(image, "horizontal")
        metrics.psd_peaks = analyze_psd_peaks(psd_h, freq_h)
        metrics.psd_peaks_count = len(metrics.psd_peaks)
        
        return metrics
    
    def analyze_original(self, image: np.ndarray) -> NoiseMetrics:
        """원본 이미지 분석"""
        self._original_image = image
        self._original_metrics = self.analyze(image)
        return self._original_metrics
    
    def analyze_processed(self, image: np.ndarray) -> NoiseMetrics:
        """처리된 이미지 분석"""
        self._processed_image = image
        self._processed_metrics = self.analyze(image)
        return self._processed_metrics
    
    def get_improvement(self) -> Optional[Dict[str, float]]:
        """
        원본 대비 개선율을 계산합니다.
        """
        if self._original_metrics is None or self._processed_metrics is None:
            return None
        
        orig = self._original_metrics
        proc = self._processed_metrics
        
        def calc_improvement(orig_val: float, proc_val: float, higher_is_better: bool) -> float:
            """개선율 계산"""
            if orig_val == 0:
                return 0.0
            if higher_is_better:
                return ((proc_val - orig_val) / abs(orig_val)) * 100
            else:
                return ((orig_val - proc_val) / abs(orig_val)) * 100
        
        return {
            # SNR: 높을수록 좋음
            "snr": calc_improvement(orig.snr, proc.snr, higher_is_better=True),
            "snr_rms": calc_improvement(orig.snr_rms, proc.snr_rms, higher_is_better=True),
            
            # 노이즈 표준편차: 낮을수록 좋음
            "noise_std": calc_improvement(orig.noise_std, proc.noise_std, higher_is_better=False),
            "noise_std_mad": calc_improvement(orig.noise_std_mad, proc.noise_std_mad, higher_is_better=False),
            "noise_std_laplacian": calc_improvement(orig.noise_std_laplacian, proc.noise_std_laplacian, higher_is_better=False),
            
            # 라인별 노이즈: 낮을수록 좋음
            "linewise_h": calc_improvement(orig.linewise_h, proc.linewise_h, higher_is_better=False),
            "linewise_v": calc_improvement(orig.linewise_v, proc.linewise_v, higher_is_better=False),
            
            # 라인 상관관계: 높을수록 좋음
            "line_correlation": calc_improvement(orig.line_correlation, proc.line_correlation, higher_is_better=True),
            
            # 비정상 라인 수: 낮을수록 좋음
            "abnormal_lines_count": calc_improvement(orig.abnormal_lines_count, proc.abnormal_lines_count, higher_is_better=False),
            
            # 에지 노이즈: 낮을수록 좋음
            "edge_noise": calc_improvement(orig.edge_noise, proc.edge_noise, higher_is_better=False),
            
            # 에지 선명도: 높을수록 좋음 (디노이징 후 보존되어야 함)
            "edge_sharpness": calc_improvement(orig.edge_sharpness, proc.edge_sharpness, higher_is_better=True),
            
            # 그래디언트 분산: 낮을수록 좋음
            "gradient_variance": calc_improvement(orig.gradient_variance, proc.gradient_variance, higher_is_better=False),
            
            # 에지 일관성: 높을수록 좋음
            "edge_coherence": calc_improvement(orig.edge_coherence, proc.edge_coherence, higher_is_better=True),
            
            # 총 스펙트럴 에너지: 낮을수록 좋음 (노이즈 에너지 감소)
            "total_spectral_energy": calc_improvement(orig.total_spectral_energy, proc.total_spectral_energy, higher_is_better=False),
            
            # PSD 피크 수: 낮을수록 좋음 (진동 노이즈 감소)
            "psd_peaks_count": calc_improvement(orig.psd_peaks_count, proc.psd_peaks_count, higher_is_better=False),
        }
    
    def get_edge_preservation(self) -> float:
        """에지 보존율 계산"""
        if self._original_image is None or self._processed_image is None:
            return 0.0
        return calculate_edge_preservation(self._original_image, self._processed_image)
    
    @property
    def original_metrics(self) -> Optional[NoiseMetrics]:
        return self._original_metrics
    
    @property
    def processed_metrics(self) -> Optional[NoiseMetrics]:
        return self._processed_metrics
    
    def get_summary(self) -> str:
        """분석 결과 요약 문자열 반환"""
        if self._original_metrics is None:
            return "No analysis performed"
        
        lines = ["=== Noise Analysis Summary ===", ""]
        
        orig = self._original_metrics
        lines.append("Original Image:")
        lines.append(f"  SNR (mean/std): {orig.snr:.2f}")
        lines.append(f"  SNR (RMS): {orig.snr_rms:.2f}")
        lines.append(f"  Noise σ (std): {orig.noise_std:.2f}")
        lines.append(f"  Noise σ (MAD): {orig.noise_std_mad:.2f}")
        lines.append(f"  Noise σ (Laplacian): {orig.noise_std_laplacian:.2f}")
        lines.append(f"  Line σ (H/V): {orig.linewise_h:.2f} / {orig.linewise_v:.2f}")
        lines.append(f"  Line Correlation: {orig.line_correlation:.4f}")
        lines.append(f"  Abnormal Lines: {orig.abnormal_lines_count}")
        lines.append(f"  Edge σ: {orig.edge_noise:.2f}")
        lines.append(f"  Edge Sharpness: {orig.edge_sharpness:.2f}")
        lines.append(f"  Gradient Var: {orig.gradient_variance:.2f}")
        lines.append(f"  Edge Coherence: {orig.edge_coherence:.4f}")
        lines.append(f"  Spectral Energy: {orig.total_spectral_energy:.2e}")
        lines.append(f"  PSD Peaks: {orig.psd_peaks_count}")
        
        if self._processed_metrics is not None:
            proc = self._processed_metrics
            improvement = self.get_improvement()
            
            lines.append("")
            lines.append("Processed Image:")
            lines.append(f"  SNR (mean/std): {proc.snr:.2f} ({improvement['snr']:+.1f}%)")
            lines.append(f"  SNR (RMS): {proc.snr_rms:.2f} ({improvement['snr_rms']:+.1f}%)")
            lines.append(f"  Noise σ (std): {proc.noise_std:.2f} ({improvement['noise_std']:+.1f}%)")
            lines.append(f"  Edge Preservation: {self.get_edge_preservation():.1%}")
        
        return "\n".join(lines)
