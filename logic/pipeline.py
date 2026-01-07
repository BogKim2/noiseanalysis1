# -*- coding: utf-8 -*-
"""
Multi-Filter Pipeline 구현
여러 필터를 순차적으로 조합하여 적용
"""
import numpy as np
from typing import Optional
from .filter_base import FilterBase
from .bilateral import BilateralFilter
from .nlm import NLMFilter
from .wavelet import WaveletFilter
from .fourier import FourierFilter
from .linewise import LinewiseFilter
from .notch import NotchFilter
from .anisotropic import AnisotropicFilter


class FilterPipeline:
    """여러 필터를 순차적으로 적용하는 파이프라인"""
    
    # 사용 가능한 필터 목록
    AVAILABLE_FILTERS = {
        "Bilateral": BilateralFilter,
        "NLM": NLMFilter,
        "Wavelet": WaveletFilter,
        "Fourier": FourierFilter,
        "Linewise": LinewiseFilter,
        "Notch": NotchFilter,
        "Anisotropic": AnisotropicFilter,
    }
    
    def __init__(self, max_filters: int = 3):
        self.max_filters = max_filters
        self._filters: list[FilterBase] = []
        self._intermediate_results: list[np.ndarray] = []
    
    @classmethod
    def get_available_filter_names(cls) -> list[str]:
        """사용 가능한 필터 이름 목록 반환"""
        return list(cls.AVAILABLE_FILTERS.keys())
    
    @classmethod
    def create_filter(cls, name: str) -> Optional[FilterBase]:
        """필터 이름으로 필터 인스턴스 생성"""
        if name in cls.AVAILABLE_FILTERS:
            return cls.AVAILABLE_FILTERS[name]()
        return None
    
    def clear(self) -> None:
        """파이프라인 초기화"""
        self._filters.clear()
        self._intermediate_results.clear()
    
    def add_filter(self, filter_obj: FilterBase) -> bool:
        """파이프라인에 필터 추가"""
        if len(self._filters) >= self.max_filters:
            print(f"Pipeline is full (max {self.max_filters} filters)")
            return False
        self._filters.append(filter_obj)
        return True
    
    def add_filter_by_name(self, name: str) -> Optional[FilterBase]:
        """필터 이름으로 파이프라인에 필터 추가"""
        filter_obj = self.create_filter(name)
        if filter_obj and self.add_filter(filter_obj):
            return filter_obj
        return None
    
    def remove_filter(self, index: int) -> bool:
        """인덱스로 필터 제거"""
        if 0 <= index < len(self._filters):
            self._filters.pop(index)
            return True
        return False
    
    def get_filters(self) -> list[FilterBase]:
        """현재 파이프라인의 필터 목록 반환"""
        return self._filters.copy()
    
    def get_filter_count(self) -> int:
        """현재 필터 개수 반환"""
        return len(self._filters)
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """
        파이프라인의 모든 필터를 순차적으로 적용
        
        Args:
            image: 입력 이미지
            
        Returns:
            최종 처리된 이미지
        """
        self._intermediate_results.clear()
        
        if not self._filters:
            return image.copy()
        
        result = image.copy()
        
        for i, filter_obj in enumerate(self._filters):
            print(f"Applying filter {i+1}/{len(self._filters)}: {filter_obj.name}")
            result = filter_obj.apply(result)
            self._intermediate_results.append(result.copy())
        
        return result
    
    def get_intermediate_results(self) -> list[np.ndarray]:
        """중간 결과 이미지들 반환"""
        return self._intermediate_results.copy()
    
    def get_pipeline_info(self) -> str:
        """파이프라인 정보 문자열 생성 (파일명용)"""
        if not self._filters:
            return "NoFilter"
        
        filter_names = [f.name for f in self._filters]
        return "_".join(filter_names)
    
    def get_detailed_info(self) -> str:
        """상세 파이프라인 정보"""
        if not self._filters:
            return "Empty pipeline"
        
        info_parts = []
        for i, f in enumerate(self._filters):
            info_parts.append(f"Step {i+1}: {f.get_filter_info()}")
        
        return " -> ".join(info_parts)

