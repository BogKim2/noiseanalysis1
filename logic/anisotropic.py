# -*- coding: utf-8 -*-
"""
Anisotropic Diffusion 구현
경계 방향을 따라 스무딩 (Perona-Malik diffusion)
"""
import numpy as np
from scipy import ndimage
from .filter_base import FilterBase, FilterParameter


class AnisotropicFilter(FilterBase):
    """Anisotropic Diffusion - 구조 보존 스무딩"""
    
    @property
    def name(self) -> str:
        return "Anisotropic"
    
    @property
    def description(self) -> str:
        return "Structure-preserving smoothing that diffuses along edges, not across them (Perona-Malik)."
    
    def _setup_parameters(self) -> None:
        """파라미터 설정"""
        self.add_parameter(FilterParameter(
            name="iterations",
            display_name="Iterations",
            value=10,
            min_value=1,
            max_value=100,
            step=1,
            param_type="int",
            description="Number of diffusion iterations"
        ))
        self.add_parameter(FilterParameter(
            name="kappa",
            display_name="Kappa (Edge Threshold)",
            value=30.0,
            min_value=1.0,
            max_value=200.0,
            step=1.0,
            param_type="float",
            description="Conduction coefficient (controls edge sensitivity)"
        ))
        self.add_parameter(FilterParameter(
            name="gamma",
            display_name="Gamma (Step Size)",
            value=0.1,
            min_value=0.01,
            max_value=0.25,
            step=0.01,
            param_type="float",
            description="Step size per iteration (max 0.25 for stability)"
        ))
        self.add_parameter(FilterParameter(
            name="option",
            display_name="Diffusion Function",
            value=1,
            min_value=1,
            max_value=2,
            step=1,
            param_type="int",
            description="1: exp(-||grad||^2/kappa^2), 2: 1/(1+(||grad||/kappa)^2)"
        ))
    
    def apply(self, image: np.ndarray) -> np.ndarray:
        """Anisotropic diffusion 적용"""
        image_float = self._ensure_float(image)
        
        iterations = self.get_parameter("iterations")
        kappa = self.get_parameter("kappa")
        gamma = self.get_parameter("gamma")
        option = self.get_parameter("option")
        
        # grayscale 처리
        if len(image_float.shape) == 3:
            result = np.zeros_like(image_float)
            for i in range(image_float.shape[2]):
                result[:, :, i] = self._anisotropic_diffusion(
                    image_float[:, :, i], iterations, kappa, gamma, option
                )
        else:
            result = self._anisotropic_diffusion(
                image_float, iterations, kappa, gamma, option
            )
        
        return self._ensure_uint8(result)
    
    def _anisotropic_diffusion(self, image: np.ndarray, iterations: int,
                                kappa: float, gamma: float, option: int) -> np.ndarray:
        """
        Perona-Malik anisotropic diffusion
        
        Reference: P. Perona and J. Malik, Scale-space and edge detection 
                   using anisotropic diffusion, IEEE TPAMI, 1990.
        """
        # 스케일 조정 (0-1 범위에서 0-255 범위로)
        img = image * 255.0
        
        # 복사본 생성
        diffused = img.copy()
        
        # 방향별 차분 커널
        deltaS = np.array([[0, 1, 0], [0, -1, 0], [0, 0, 0]])  # South
        deltaN = np.array([[0, 0, 0], [0, -1, 0], [0, 1, 0]])  # North
        deltaE = np.array([[0, 0, 0], [0, -1, 1], [0, 0, 0]])  # East
        deltaW = np.array([[0, 0, 0], [1, -1, 0], [0, 0, 0]])  # West
        
        for _ in range(iterations):
            # 방향별 gradient 계산
            nablaS = ndimage.convolve(diffused, deltaS)
            nablaN = ndimage.convolve(diffused, deltaN)
            nablaE = ndimage.convolve(diffused, deltaE)
            nablaW = ndimage.convolve(diffused, deltaW)
            
            # Conduction coefficient 계산
            if option == 1:
                # Perona-Malik function 1: c = exp(-(||∇I||/κ)²)
                cS = np.exp(-(nablaS / kappa) ** 2)
                cN = np.exp(-(nablaN / kappa) ** 2)
                cE = np.exp(-(nablaE / kappa) ** 2)
                cW = np.exp(-(nablaW / kappa) ** 2)
            else:
                # Perona-Malik function 2: c = 1 / (1 + (||∇I||/κ)²)
                cS = 1.0 / (1.0 + (nablaS / kappa) ** 2)
                cN = 1.0 / (1.0 + (nablaN / kappa) ** 2)
                cE = 1.0 / (1.0 + (nablaE / kappa) ** 2)
                cW = 1.0 / (1.0 + (nablaW / kappa) ** 2)
            
            # 확산 업데이트
            diffused = diffused + gamma * (
                cS * nablaS + cN * nablaN + cE * nablaE + cW * nablaW
            )
        
        # 스케일 복원
        result = diffused / 255.0
        result = np.clip(result, 0, 1)
        
        return result

