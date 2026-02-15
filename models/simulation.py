from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from models.interfaces import SimulationResult, SimulationScenario
from models.supplements import (
    aggregate_modifiers,
    selected_definitions,
    supplement_concentration_trace,
    validate_supplement_stack,
)


def _ode_system(
    _t: float,
    y: np.ndarray,
    route: str,
    cd38_scale: float,
    synthesis_multiplier: float,
    cd38_multiplier: float,
    absorption_multiplier: float,
) -> np.ndarray:
    plasma_precursor, nad_cyt, nad_mito = y

    oral_input = (0.8 if route == "oral" else 0.0) * absorption_multiplier
    iv_input = 1.0 if route == "iv" else 0.0

    uptake = 0.15 * plasma_precursor
    clearance = 0.20 * plasma_precursor

    synth = (0.12 * plasma_precursor + oral_input * 0.02 + iv_input * 0.01) * synthesis_multiplier
    to_mito = 0.10 * nad_cyt
    to_cyt = 0.07 * nad_mito

    cd38_sink = 0.05 * cd38_scale * cd38_multiplier * nad_cyt
    parp_sink = 0.02 * nad_cyt
    sirt_sink = 0.01 * nad_cyt

    d_plasma = -uptake - clearance + oral_input + iv_input
    d_nad_cyt = synth - to_mito + to_cyt - cd38_sink - parp_sink - sirt_sink
    d_nad_mito = to_mito - to_cyt - 0.01 * nad_mito

    return np.array([d_plasma, d_nad_cyt, d_nad_mito], dtype=float)


def run_simulation(scenario: SimulationScenario) -> SimulationResult:
    validation = validate_supplement_stack(
        selected_ids=scenario.selected_supplements,
        route=scenario.route,
        primary_compound=scenario.compound,
    )
    if validation.blocking_errors:
        raise ValueError("; ".join(validation.blocking_errors))

    definitions = selected_definitions(scenario.selected_supplements)
    synthesis_multiplier, cd38_multiplier, absorption_multiplier = aggregate_modifiers(definitions)

    t_eval = np.linspace(0.0, scenario.duration_h, 250)

    y0 = np.array(
        [
            max(scenario.dose_mg / 100.0, 0.0),
            40.0,
            30.0,
        ]
    )

    solution = solve_ivp(
        fun=lambda t, y: _ode_system(
            t,
            y,
            scenario.route,
            scenario.cd38_scale,
            synthesis_multiplier,
            cd38_multiplier,
            absorption_multiplier,
        ),
        t_span=(0.0, scenario.duration_h),
        y0=y0,
        t_eval=t_eval,
        method="LSODA",
    )

    df = pd.DataFrame(
        {
            "time_h": solution.t,
            "plasma_precursor_uM": solution.y[0],
            "nad_cyt_uM": solution.y[1],
            "nad_mito_uM": solution.y[2],
        }
    )

    supplement_signal_uM = np.zeros_like(solution.t, dtype=float)
    for definition in definitions:
        dose_mg = scenario.supplement_doses_mg.get(definition.supplement_id, definition.default_dose_mg)
        trace = supplement_concentration_trace(solution.t, dose_mg=dose_mg, definition=definition)
        column_name = f"supp_{definition.supplement_id}_plasma_uM"
        df[column_name] = trace
        supplement_signal_uM += trace

    if definitions:
        df["supplement_stack_signal_uM"] = supplement_signal_uM

    return SimulationResult(
        times_h=df["time_h"].tolist(),
        dataframe=df,
        warnings=validation.warnings,
    )
