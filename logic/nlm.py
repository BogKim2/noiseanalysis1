# -*- coding: utf-8 -*-
"""
Non-Local Means (NLM) Filter 구현
패치 기반 denoising
"""
import cv2
import numpy as np
from .filter_base import FilterBase, FilterParameter


class NLMFilter(FilterBase):
    """Non-Local Means Filter - 패치 기반 denoising"""
    
    @property
    def name(self) -> str:
        return "NLM"
    
    @property
    def description(self) -> str:
        return "Patch-based denoising that preserves texture and fine details."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="h",
            display_name="Filter Strength (h)",
            value=10.0,
            min_value=1.0,
            max_value=50.0,
            step=1.0,
            param_type="float",
            description="Filter strength. Higher h removes more noise but removes detail too"
        ))
        self.add_parameter(FilterParameter(
            name="templateWindowSize",
            display_name="Template Window Size",
            value=7,
            min_value=3,
            max_value=21,
            step=2,
            param_type="int",
            description="Size of template patch (should be odd)"
        ))
        self.add_parameter(FilterParameter(
            name="searchWindowSize",
            display_name="Search Window Size",
            value=21,
            min_value=7,
            max_value=51,
            step=2,
            param_type="int",
            description="Size of search area (should be odd)"
        ))
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """NLM 필터 적용"""
        image = self._ensure_uint8(image)
        
        h = self.get_parameter("h")
        template_size = self.get_parameter("templateWindowSize")
        search_size = self.get_parameter("searchWindowSize")
        
        # 홀수로 맞추기
        if template_size % 2 == 0:
            template_size += 1
        if search_size % 2 == 0:
            search_size += 1
        
        # grayscale vs color
        if len(image.shape) == 2:
            result = cv2.fastNlMeansDenoising(
                image,
                None,
                h,
                template_size,
                search_size
            )
        else:
            result = cv2.fastNlMeansDenoisingColored(
                image,
                None,
                h,
                h,
                template_size,
                search_size
            )
        
        return result

