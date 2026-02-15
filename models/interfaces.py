from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SimulationResult:
    times_h: list[float]
    dataframe: pd.DataFrame


class Module(Protocol):
    def step(self, t_h: float, y: list[float]) -> list[float]:
        ...


class Simulator(Protocol):
    def run(self, scenario: SimulationScenario) -> SimulationResult:
        ...
