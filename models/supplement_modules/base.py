from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from models.supplements import SupplementDefinition


@dataclass(frozen=True)
class SupplementEffectSeries:
    concentration_uM: np.ndarray
    sat_signal: np.ndarray
    synthesis_effect: np.ndarray
    cd38_effect: np.ndarray
    absorption_effect: np.ndarray


class SupplementModule(Protocol):
    definition: SupplementDefinition

    def effect_series(self, times_h: np.ndarray, dose_mg: float, class_scalar: float) -> SupplementEffectSeries:
        ...
