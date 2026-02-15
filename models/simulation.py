from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from models.interfaces import SimulationResult, SimulationScenario
from models.supplements import (
    apply_interaction_overrides,
    compute_dynamic_modifier_series,
    generate_supplement_traces,
    load_class_scalars,
    selected_definitions,
    selected_interaction_rules,
    validate_supplement_stack,
)


def _ode_system(
    t_h: float,
    y: np.ndarray,
    route: str,
    cd38_scale: float,
    t_eval: np.ndarray,
    synthesis_multiplier_series: np.ndarray,
    cd38_multiplier_series: np.ndarray,
    absorption_multiplier_series: np.ndarray,
) -> np.ndarray:
    plasma_precursor, nad_cyt, nad_mito = y

    synthesis_multiplier = float(np.interp(t_h, t_eval, synthesis_multiplier_series))
    cd38_multiplier = float(np.interp(t_h, t_eval, cd38_multiplier_series))
    absorption_multiplier = float(np.interp(t_h, t_eval, absorption_multiplier_series))

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

    interaction_rules = selected_interaction_rules(scenario.selected_supplements)
    interaction_rules = apply_interaction_overrides(interaction_rules, scenario.interaction_coefficient_overrides)

    t_eval = np.linspace(0.0, scenario.duration_h, 250)

    traces = generate_supplement_traces(t_eval, definitions, scenario.supplement_doses_mg)
    class_scalars = load_class_scalars()
    modifier_df = compute_dynamic_modifier_series(
        times_h=t_eval,
        traces=traces,
        definitions=definitions,
        interaction_rules=interaction_rules,
        class_scalars=class_scalars,
    )

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
            t_eval,
            modifier_df["synthesis_multiplier"].to_numpy(),
            modifier_df["cd38_multiplier"].to_numpy(),
            modifier_df["absorption_multiplier"].to_numpy(),
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
            "synthesis_multiplier": modifier_df["synthesis_multiplier"].to_numpy(),
            "cd38_multiplier": modifier_df["cd38_multiplier"].to_numpy(),
            "absorption_multiplier": modifier_df["absorption_multiplier"].to_numpy(),
            "synthesis_effect": modifier_df["synthesis_effect"].to_numpy(),
            "cd38_effect": modifier_df["cd38_effect"].to_numpy(),
            "absorption_effect": modifier_df["absorption_effect"].to_numpy(),
        }
    )

    supplement_signal_uM = np.zeros_like(solution.t, dtype=float)
    for definition in definitions:
        trace = traces.get(definition.supplement_id)
        if trace is None:
            continue

        column_name = f"supp_{definition.supplement_id}_plasma_uM"
        df[column_name] = trace
        supplement_signal_uM += trace

        signal_col = f"supp_{definition.supplement_id}_sat_signal"
        if signal_col in modifier_df.columns:
            df[signal_col] = modifier_df[signal_col].to_numpy()

    if definitions:
        df["supplement_stack_signal_uM"] = supplement_signal_uM

    for column in modifier_df.columns:
        if column.startswith("interaction_") and column.endswith("_effect"):
            df[column] = modifier_df[column].to_numpy()

    warnings = list(validation.warnings)
    if scenario.interaction_coefficient_overrides:
        warnings.append("Interaction coefficients were overridden for this run.")

    return SimulationResult(
        times_h=df["time_h"].tolist(),
        dataframe=df,
        warnings=tuple(dict.fromkeys(warnings)),
    )
