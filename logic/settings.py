# -*- coding: utf-8 -*-
"""
설정 저장/불러오기 관리
JSON 파일로 파라미터, 파일 경로 등 저장
"""
import json
import os
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class Settings:
    """애플리케이션 설정 관리"""
    
    DEFAULT_SETTINGS = {
        "last_open_directory": "",
        "last_file_path": "",
        "window_geometry": {
            "width": 1600,
            "height": 1000,
            "x": 100,
            "y": 100
        },
        "filter_parameters": {
            "Bilateral": {"d": 9, "sigmaColor": 75.0, "sigmaSpace": 75.0},
            "NLM": {"h": 10.0, "templateWindowSize": 7, "searchWindowSize": 21},
            "Wavelet": {"sigma": 0.0, "wavelet": "db1", "mode": "soft", "rescale_sigma": 1},
            "Fourier": {"cutoff": 0.3, "filter_type": "lowpass", "order": 2, "bandwidth": 0.1},
            "Linewise": {"direction": "horizontal", "method": "mean", "window_size": 5, "strength": 1.0},
            "Notch": {"center_freq": 0.25, "bandwidth": 0.05, "direction": "both", "auto_detect": 0, "num_notches": 1},
            "Anisotropic": {"iterations": 10, "kappa": 30.0, "gamma": 0.1, "option": 1},
        },
        "pipeline_filters": ["Linewise", "Notch", "NLM"],
        "auto_apply": True,
        "last_modified": "",
        "optimization_weights": {
            "snr": 2.0,
            "noise_std_mad": 1.0,
            "edge_sharpness": 5.0,
            "linewise_h": 1.0,
            "abnormal_lines_count": 1.0,
            "negative_penalty_factor": 5.0,
            "critical_penalty_factor": 20.0,
            "negative_count_penalty": 50.0
        }
    }
    
    def __init__(self, settings_file: Optional[str] = None):
        """
        Args:
            settings_file: 설정 파일 경로 (None이면 기본 위치)
        """
        if settings_file:
            self.settings_file = Path(settings_file)
        else:
            # 프로그램 디렉토리에 settings.json 저장
            self.settings_file = Path(__file__).parent.parent / "settings.json"
        
        self._settings: dict = {}
        self.load()
    
    def load(self) -> bool:
        """설정 파일 로드"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # 기본값과 병합 (새 키가 추가된 경우 대비)
                self._settings = self._merge_settings(self.DEFAULT_SETTINGS.copy(), loaded)
                print(f"Settings loaded from: {self.settings_file}")
                return True
            except Exception as e:
                print(f"Failed to load settings: {e}")
                self._settings = self.DEFAULT_SETTINGS.copy()
                return False
        else:
            self._settings = self.DEFAULT_SETTINGS.copy()
            print("Using default settings")
            return False
    
    def _merge_settings(self, default: dict, loaded: dict) -> dict:
        """기본값과 로드된 값 병합"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_settings(result[key], value)
                else:
                    result[key] = value
        return result
    
    def save(self) -> bool:
        """설정 파일 저장"""
        try:
            self._settings["last_modified"] = datetime.now().isoformat()
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            print(f"Settings saved to: {self.settings_file}")
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정값 가져오기 (점 표기법 지원: 'window_geometry.width')"""
        keys = key.split('.')
        value = self._settings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """설정값 저장 (점 표기법 지원)"""
        keys = key.split('.')
        target = self._settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
    
    def get_filter_params(self, filter_name: str) -> dict:
        """특정 필터의 파라미터 가져오기"""
        return self._settings.get("filter_parameters", {}).get(filter_name, {})
    
    def set_filter_params(self, filter_name: str, params: dict) -> None:
        """특정 필터의 파라미터 저장"""
        if "filter_parameters" not in self._settings:
            self._settings["filter_parameters"] = {}
        self._settings["filter_parameters"][filter_name] = params
    
    def get_pipeline_filters(self) -> list:
        """파이프라인 필터 목록 가져오기"""
        return self._settings.get("pipeline_filters", [])
    
    def set_pipeline_filters(self, filters: list) -> None:
        """파이프라인 필터 목록 저장"""
        self._settings["pipeline_filters"] = filters
    
    def get_all(self) -> dict:
        """모든 설정 반환"""
        return self._settings.copy()


# 전역 설정 인스턴스
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """전역 설정 인스턴스 가져오기"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


