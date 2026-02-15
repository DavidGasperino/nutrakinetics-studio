from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class SimulationScenario:
    route: str
    compound: str
    dose_mg: float
    duration_h: float
    formulation: str
    cd38_scale: float
    selected_supplements: tuple[str, ...] = ()
    supplement_doses_mg: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationResult:
    times_h: list[float]
    dataframe: pd.DataFrame
    warnings: tuple[str, ...] = ()


class Module(Protocol):
    def step(self, t_h: float, y: list[float]) -> list[float]:
        ...


class Simulator(Protocol):
    def run(self, scenario: SimulationScenario) -> SimulationResult:
        ...
