from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from models.parameters import NumericalSafeguards
from models.supplement_modules.base import SupplementEffectSeries
from models.supplements import SupplementDefinition


@dataclass(frozen=True)
class GenericSupplementModule:
    definition: SupplementDefinition
    safeguards: NumericalSafeguards

    def _concentration_trace(self, times_h: np.ndarray, dose_mg: float) -> np.ndarray:
        ka = max(self.definition.ka_per_h, self.safeguards.ka_min_per_h)
        kel = max(self.definition.kel_per_h, self.safeguards.kel_min_per_h)

        if abs(ka - kel) < self.safeguards.ka_kel_equal_tolerance:
            kel = ka * self.safeguards.ka_kel_adjustment_factor

        scale = self.definition.exposure_scale * max(dose_mg, 0.0)
        trace = scale * (np.exp(-kel * times_h) - np.exp(-ka * times_h))
        return np.maximum(trace, 0.0)

    def _saturating_signal(self, concentration_uM: np.ndarray) -> np.ndarray:
        ec50 = max(self.definition.ec50_uM, self.safeguards.ec50_min_uM)
        hill = max(self.definition.hill_n, self.safeguards.hill_min)

        numerator = np.power(np.maximum(concentration_uM, 0.0), hill)
        denominator = np.power(ec50, hill) + numerator
        return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)

    def effect_series(self, times_h: np.ndarray, dose_mg: float, class_scalar: float) -> SupplementEffectSeries:
        concentration = self._concentration_trace(times_h, dose_mg=dose_mg)
        sat_signal = self._saturating_signal(concentration)

        return SupplementEffectSeries(
            concentration_uM=concentration,
            sat_signal=sat_signal,
            synthesis_effect=class_scalar * self.definition.synthesis_gain_per_signal * sat_signal,
            cd38_effect=class_scalar * self.definition.cd38_effect_per_signal * sat_signal,
            absorption_effect=class_scalar * self.definition.absorption_gain_per_signal * sat_signal,
        )
