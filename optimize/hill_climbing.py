# -*- coding: utf-8 -*-
"""
Hill Climbing 최적화 알고리즘
현재 파라미터에서 시작해 점진적으로 개선
"""
import numpy as np
import time
from typing import Dict, List, Callable, Any, Optional

from .optimizer_base import OptimizerBase, OptimizationResult


class HillClimbingOptimizer(OptimizerBase):
    """
    Hill Climbing 최적화
    
    특징:
    - 빠른 수렴
    - 로컬 최적점에 빠질 수 있음
    - 현재 파라미터 근처에서 최적화
    """
    
    def __init__(
        self,
        score_function: Any,
        param_bounds: Optional[Dict] = None,
        max_iterations: int = 100,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        step_decay: float = 0.95,
        min_step_factor: float = 0.1
    ):
        """
        Args:
            step_decay: 개선 없을 때 step 크기 감소 비율
            min_step_factor: 최소 step 크기 (기본 step의 배수)
        """
        super().__init__(score_function, param_bounds, max_iterations, progress_callback)
        self.step_decay = step_decay
        self.min_step_factor = min_step_factor
    
    def optimize(
        self,
        image: np.ndarray,
        pipeline_filters: List[str],
        current_params: Dict[str, Dict[str, Any]],
        apply_filter_func: Callable,
        analyze_func: Callable
    ) -> OptimizationResult:
        """Hill Climbing 최적화 실행"""
        
        start_time = time.time()
        self._stop_requested = False
        
        # 원본 이미지 분석
        original_metrics = analyze_func(image)
        
        # 현재 파라미터 복사
        best_params = self._copy_params(current_params)
        
        # 초기 점수 계산
        initial_score = self._evaluate(
            image, pipeline_filters, best_params,
            original_metrics, apply_filter_func, analyze_func
        )
        best_score = initial_score
        
        score_history = [best_score]
        iteration = 0
        
        # 각 파라미터에 대한 step 크기 초기화
        step_multipliers = {
            filter_name: {
                param_name: 1.0
                for param_name in self.param_bounds.get(filter_name, {}).keys()
            }
            for filter_name in pipeline_filters
        }
        
        # 최적화 루프
        no_improvement_count = 0
        max_no_improvement = 10  # 연속 개선 없으면 종료
        
        while iteration < self.max_iterations and not self._stop_requested:
            improved = False
            
            # 각 필터의 각 파라미터에 대해
            for filter_name in pipeline_filters:
                if filter_name not in self.param_bounds:
                    continue
                if filter_name not in best_params:
                    continue
                
                for param_name in self.param_bounds[filter_name].keys():
                    if param_name not in best_params[filter_name]:
                        continue
                    
                    if self._stop_requested:
                        break
                    
                    # 현재 값과 step 가져오기
                    min_val, max_val, base_step = self._get_param_range(filter_name, param_name)
                    current_val = best_params[filter_name][param_name]
                    step = base_step * step_multipliers[filter_name][param_name]
                    
                    # 양방향으로 시도
                    for direction in [1, -1]:
                        new_val = current_val + direction * step
                        new_val = self._clip_param(filter_name, param_name, new_val)
                        
                        # 정수 파라미터 처리
                        if param_name in ['window_size', 'iterations', 'num_notches', 'd', 
                                         'templateWindowSize', 'searchWindowSize', 'order']:
                            new_val = int(round(new_val))
                            # window_size는 홀수만
                            if param_name in ['window_size', 'templateWindowSize', 'searchWindowSize']:
                                if new_val % 2 == 0:
                                    new_val += 1
                        
                        if new_val == current_val:
                            continue
                        
                        # 새 파라미터로 평가
                        test_params = self._copy_params(best_params)
                        test_params[filter_name][param_name] = new_val
                        
                        test_score = self._evaluate(
                            image, pipeline_filters, test_params,
                            original_metrics, apply_filter_func, analyze_func
                        )
                        
                        # 개선되었으면 업데이트
                        if test_score > best_score:
                            best_score = test_score
                            best_params = test_params
                            improved = True
                            step_multipliers[filter_name][param_name] = min(
                                1.0, 
                                step_multipliers[filter_name][param_name] * 1.1
                            )
                            break  # 개선 방향으로 계속
            
            iteration += 1
            score_history.append(best_score)
            self._report_progress(iteration, self.max_iterations, best_score)
            
            if improved:
                no_improvement_count = 0
            else:
                no_improvement_count += 1
                # step 크기 감소
                for filter_name in step_multipliers:
                    for param_name in step_multipliers[filter_name]:
                        step_multipliers[filter_name][param_name] = max(
                            self.min_step_factor,
                            step_multipliers[filter_name][param_name] * self.step_decay
                        )
            
            # 연속으로 개선 없으면 종료
            if no_improvement_count >= max_no_improvement:
                break
        
        elapsed_time = time.time() - start_time
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            initial_score=initial_score,
            iterations=iteration,
            elapsed_time=elapsed_time,
            score_history=score_history,
            improved=best_score > initial_score
        )


