# -*- coding: utf-8 -*-
"""
Grid Search 최적화 알고리즘
Coarse-to-Fine 전략으로 전역 탐색
"""
import numpy as np
import time
from itertools import product
from typing import Dict, List, Callable, Any, Optional, Tuple

from .optimizer_base import OptimizerBase, OptimizationResult


class GridSearchOptimizer(OptimizerBase):
    """
    Grid Search 최적화 (Coarse-to-Fine)
    
    특징:
    - 전역 최적점 찾기 가능
    - 계산량이 많음
    - 2단계: Coarse → Fine 전략으로 효율성 향상
    """
    
    def __init__(
        self,
        score_function: Any,
        param_bounds: Optional[Dict] = None,
        max_iterations: int = 500,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        coarse_divisions: int = 3,  # Coarse 단계 분할 수
        fine_divisions: int = 5,    # Fine 단계 분할 수
        fine_range_factor: float = 0.3  # Fine 탐색 범위 (Coarse의 몇 배)
    ):
        """
        Args:
            coarse_divisions: Coarse 단계에서 각 파라미터 분할 수
            fine_divisions: Fine 단계에서 각 파라미터 분할 수
            fine_range_factor: Fine 탐색 범위 배수
        """
        super().__init__(score_function, param_bounds, max_iterations, progress_callback)
        self.coarse_divisions = coarse_divisions
        self.fine_divisions = fine_divisions
        self.fine_range_factor = fine_range_factor
    
    def _generate_grid_values(
        self,
        filter_name: str,
        param_name: str,
        divisions: int,
        center: Optional[float] = None,
        range_factor: float = 1.0
    ) -> List[float]:
        """그리드 값 생성"""
        min_val, max_val, base_step = self._get_param_range(filter_name, param_name)
        
        if center is not None and range_factor < 1.0:
            # Fine 단계: 중심점 주변 탐색
            full_range = max_val - min_val
            search_range = full_range * range_factor
            search_min = max(min_val, center - search_range / 2)
            search_max = min(max_val, center + search_range / 2)
        else:
            # Coarse 단계: 전체 범위 탐색
            search_min = min_val
            search_max = max_val
        
        # 정수 파라미터 처리
        is_integer = param_name in ['window_size', 'iterations', 'num_notches', 'd',
                                     'templateWindowSize', 'searchWindowSize', 'order', 'psf_size']
        needs_odd = param_name in ['window_size', 'templateWindowSize', 'searchWindowSize', 'psf_size']
        
        if is_integer:
            values = list(range(int(search_min), int(search_max) + 1, max(1, int(base_step))))
            if needs_odd:
                values = [v for v in values if v % 2 == 1]
            # divisions에 맞게 샘플링
            if len(values) > divisions:
                indices = np.linspace(0, len(values) - 1, divisions, dtype=int)
                values = [values[i] for i in indices]
        else:
            values = np.linspace(search_min, search_max, divisions).tolist()
        
        return values
    
    def _count_combinations(
        self,
        pipeline_filters: List[str],
        divisions: int
    ) -> int:
        """조합 수 계산"""
        total = 1
        for filter_name in pipeline_filters:
            if filter_name not in self.param_bounds:
                continue
            for param_name in self.param_bounds[filter_name].keys():
                total *= divisions
        return total
    
    def optimize(
        self,
        image: np.ndarray,
        pipeline_filters: List[str],
        current_params: Dict[str, Dict[str, Any]],
        apply_filter_func: Callable,
        analyze_func: Callable
    ) -> OptimizationResult:
        """Grid Search 최적화 실행 (Coarse-to-Fine)"""
        
        start_time = time.time()
        self._stop_requested = False
        
        # 원본 이미지 분석
        original_metrics = analyze_func(image)
        
        # 초기 점수 계산
        initial_score = self._evaluate(
            image, pipeline_filters, current_params,
            original_metrics, apply_filter_func, analyze_func
        )
        
        score_history = [initial_score]
        total_iterations = 0
        
        # ===== Phase 1: Coarse Search =====
        coarse_best_params, coarse_best_score, coarse_iters = self._grid_search_phase(
            image=image,
            pipeline_filters=pipeline_filters,
            current_params=current_params,
            original_metrics=original_metrics,
            apply_filter_func=apply_filter_func,
            analyze_func=analyze_func,
            divisions=self.coarse_divisions,
            center_params=None,
            range_factor=1.0,
            phase_name="Coarse"
        )
        
        total_iterations += coarse_iters
        score_history.append(coarse_best_score)
        
        if self._stop_requested:
            return self._create_result(
                coarse_best_params, coarse_best_score, initial_score,
                total_iterations, start_time, score_history
            )
        
        # ===== Phase 2: Fine Search =====
        fine_best_params, fine_best_score, fine_iters = self._grid_search_phase(
            image=image,
            pipeline_filters=pipeline_filters,
            current_params=current_params,
            original_metrics=original_metrics,
            apply_filter_func=apply_filter_func,
            analyze_func=analyze_func,
            divisions=self.fine_divisions,
            center_params=coarse_best_params,
            range_factor=self.fine_range_factor,
            phase_name="Fine"
        )
        
        total_iterations += fine_iters
        score_history.append(fine_best_score)
        
        return self._create_result(
            fine_best_params, fine_best_score, initial_score,
            total_iterations, start_time, score_history
        )
    
    def _grid_search_phase(
        self,
        image: np.ndarray,
        pipeline_filters: List[str],
        current_params: Dict[str, Dict[str, Any]],
        original_metrics: Dict[str, float],
        apply_filter_func: Callable,
        analyze_func: Callable,
        divisions: int,
        center_params: Optional[Dict[str, Dict[str, Any]]],
        range_factor: float,
        phase_name: str
    ) -> Tuple[Dict[str, Dict[str, Any]], float, int]:
        """한 단계의 Grid Search 수행"""
        
        # 각 파라미터에 대한 그리드 값 생성
        param_grids = {}
        for filter_name in pipeline_filters:
            if filter_name not in self.param_bounds:
                continue
            param_grids[filter_name] = {}
            for param_name in self.param_bounds[filter_name].keys():
                if filter_name in current_params and param_name in current_params[filter_name]:
                    center = center_params[filter_name][param_name] if center_params else None
                    param_grids[filter_name][param_name] = self._generate_grid_values(
                        filter_name, param_name, divisions, center, range_factor
                    )
        
        # 조합 생성을 위한 준비
        param_names = []
        param_values = []
        for filter_name in pipeline_filters:
            if filter_name not in param_grids:
                continue
            for param_name, values in param_grids[filter_name].items():
                param_names.append((filter_name, param_name))
                param_values.append(values)
        
        if not param_values:
            return current_params, 0.0, 0
        
        # 모든 조합 평가
        best_params = self._copy_params(current_params)
        best_score = float('-inf')
        iteration = 0
        total_combinations = 1
        for vals in param_values:
            total_combinations *= len(vals)
        
        for combination in product(*param_values):
            if self._stop_requested:
                break
            
            # 파라미터 설정
            test_params = self._copy_params(current_params)
            for (filter_name, param_name), value in zip(param_names, combination):
                if filter_name not in test_params:
                    test_params[filter_name] = {}
                test_params[filter_name][param_name] = value
            
            # 평가
            score = self._evaluate(
                image, pipeline_filters, test_params,
                original_metrics, apply_filter_func, analyze_func
            )
            
            if score > best_score:
                best_score = score
                best_params = self._copy_params(test_params)
            
            iteration += 1
            self._report_progress(iteration, total_combinations, best_score)
            
            if iteration >= self.max_iterations:
                break
        
        return best_params, best_score, iteration
    
    def _create_result(
        self,
        best_params: Dict[str, Dict[str, Any]],
        best_score: float,
        initial_score: float,
        iterations: int,
        start_time: float,
        score_history: List[float]
    ) -> OptimizationResult:
        """결과 객체 생성"""
        elapsed_time = time.time() - start_time
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            initial_score=initial_score,
            iterations=iterations,
            elapsed_time=elapsed_time,
            score_history=score_history,
            improved=best_score > initial_score
        )


