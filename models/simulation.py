from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from models.interfaces import SimulationResult, SimulationScenario
from models.parameters import CoreModelParameters, load_core_model_parameters
from models.processes import compute_human_derivatives
from models.supplement_modules import build_supplement_modules, compute_dynamic_modifier_series
from models.supplements import (
    apply_interaction_overrides,
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
    core_params: CoreModelParameters,
) -> np.ndarray:
    synthesis_multiplier = float(np.interp(t_h, t_eval, synthesis_multiplier_series))
    cd38_multiplier = float(np.interp(t_h, t_eval, cd38_multiplier_series))
    absorption_multiplier = float(np.interp(t_h, t_eval, absorption_multiplier_series))

    return compute_human_derivatives(
        y=y,
        route=route,
        cd38_scale=cd38_scale,
        synthesis_multiplier=synthesis_multiplier,
        cd38_multiplier=cd38_multiplier,
        absorption_multiplier=absorption_multiplier,
        params=core_params,
    )


def run_simulation(
    scenario: SimulationScenario,
    core_params: CoreModelParameters | None = None,
) -> SimulationResult:
    params = core_params or load_core_model_parameters()

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

    t_eval = np.linspace(0.0, scenario.duration_h, params.solver.time_grid_points)

    class_scalars = load_class_scalars()
    modules_by_id = build_supplement_modules(definitions=definitions, safeguards=params.numerical_safeguards)

    dynamic = compute_dynamic_modifier_series(
        times_h=t_eval,
        modules_by_id=modules_by_id,
        dose_map_mg=scenario.supplement_doses_mg,
        class_scalars=class_scalars,
        interaction_rules=interaction_rules,
        bounds=params.modifier_bounds,
    )

    y0 = np.array(
        [
            max(scenario.dose_mg * params.initial_conditions.precursor_dose_to_state_scale, 0.0),
            params.initial_conditions.nad_cyt_baseline_uM,
            params.initial_conditions.nad_mito_baseline_uM,
        ]
    )

    solution = solve_ivp(
        fun=lambda t, y: _ode_system(
            t_h=t,
            y=y,
            route=scenario.route,
            cd38_scale=scenario.cd38_scale,
            t_eval=t_eval,
            synthesis_multiplier_series=dynamic.modifier_df["synthesis_multiplier"].to_numpy(),
            cd38_multiplier_series=dynamic.modifier_df["cd38_multiplier"].to_numpy(),
            absorption_multiplier_series=dynamic.modifier_df["absorption_multiplier"].to_numpy(),
            core_params=params,
        ),
        t_span=(0.0, scenario.duration_h),
        y0=y0,
        t_eval=t_eval,
        method=params.solver.ode_method,
    )

    df = pd.DataFrame(
        {
            "time_h": solution.t,
            "plasma_precursor_uM": solution.y[0],
            "nad_cyt_uM": solution.y[1],
            "nad_mito_uM": solution.y[2],
            "synthesis_multiplier": dynamic.modifier_df["synthesis_multiplier"].to_numpy(),
            "cd38_multiplier": dynamic.modifier_df["cd38_multiplier"].to_numpy(),
            "absorption_multiplier": dynamic.modifier_df["absorption_multiplier"].to_numpy(),
            "synthesis_effect": dynamic.modifier_df["synthesis_effect"].to_numpy(),
            "cd38_effect": dynamic.modifier_df["cd38_effect"].to_numpy(),
            "absorption_effect": dynamic.modifier_df["absorption_effect"].to_numpy(),
        }
    )

    supplement_signal_uM = np.zeros_like(solution.t, dtype=float)
    for definition in definitions:
        trace = dynamic.traces_by_id.get(definition.supplement_id)
        if trace is None:
            continue

        column_name = f"supp_{definition.supplement_id}_plasma_uM"
        df[column_name] = trace
        supplement_signal_uM += trace

        signal_col = f"supp_{definition.supplement_id}_sat_signal"
        if signal_col in dynamic.modifier_df.columns:
            df[signal_col] = dynamic.modifier_df[signal_col].to_numpy()

    if definitions:
        df["supplement_stack_signal_uM"] = supplement_signal_uM

    for column in dynamic.modifier_df.columns:
        if column.startswith("interaction_") and column.endswith("_effect"):
            df[column] = dynamic.modifier_df[column].to_numpy()

    warnings = list(validation.warnings)
    if scenario.interaction_coefficient_overrides:
        warnings.append("Interaction coefficients were overridden for this run.")

    return SimulationResult(
        times_h=df["time_h"].tolist(),
        dataframe=df,
        warnings=tuple(dict.fromkeys(warnings)),
    )
