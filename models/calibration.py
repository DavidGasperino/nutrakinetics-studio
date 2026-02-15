from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from models.interfaces import SimulationScenario
from models.simulation import run_simulation
from models.supplements import fittable_interaction_rules, selected_interaction_rules


def interaction_parameter_rows(
    selected_ids: tuple[str, ...],
    overrides: dict[str, float] | None = None,
) -> list[dict[str, object]]:
    overrides = overrides or {}
    rows: list[dict[str, object]] = []

    for rule in selected_interaction_rules(selected_ids):
        effective = overrides.get(rule.rule_id, rule.coefficient)
        rows.append(
            {
                "rule_id": rule.rule_id,
                "supplements": ", ".join(rule.supplements),
                "target": rule.target,
                "direction": rule.effect_direction,
                "coefficient": float(rule.coefficient),
                "effective_coefficient": float(effective),
                "fit_enabled": bool(rule.fit_enabled),
                "bounds": f"[{rule.lower_bound:.3f}, {rule.upper_bound:.3f}]",
                "prior": f"mean={rule.prior_mean:.3f}, sd={rule.prior_sd:.3f}",
                "source_id": rule.source_id,
            }
        )

    return rows


def fit_interaction_coefficients(
    scenario: SimulationScenario,
    observed_df: pd.DataFrame,
    target_col: str = "observed_nad_cyt_uM",
    maxiter: int = 200,
) -> dict[str, object]:
    if "time_h" not in observed_df.columns or target_col not in observed_df.columns:
        raise ValueError(f"Observed dataset must include columns 'time_h' and '{target_col}'.")

    rules = fittable_interaction_rules(scenario.selected_supplements)
    if not rules:
        return {
            "success": False,
            "message": "No fittable interaction rules for selected supplements.",
            "optimized_coefficients": {},
        }

    initial = np.array([rule.coefficient for rule in rules], dtype=float)
    bounds = [(rule.lower_bound, rule.upper_bound) for rule in rules]

    obs_time = observed_df["time_h"].to_numpy(dtype=float)
    obs_target = observed_df[target_col].to_numpy(dtype=float)

    def objective(x: np.ndarray) -> float:
        overrides = {rule.rule_id: float(x[i]) for i, rule in enumerate(rules)}
        candidate = replace(scenario, interaction_coefficient_overrides=overrides)
        simulation = run_simulation(candidate).dataframe

        pred = np.interp(obs_time, simulation["time_h"].to_numpy(), simulation["nad_cyt_uM"].to_numpy())
        mse = float(np.mean((pred - obs_target) ** 2))

        prior_penalty = 0.0
        for i, rule in enumerate(rules):
            sd = max(rule.prior_sd, 1e-6)
            prior_penalty += ((x[i] - rule.prior_mean) / sd) ** 2

        return mse + 0.01 * float(prior_penalty)

    result = minimize(
        objective,
        x0=initial,
        bounds=bounds,
        method="L-BFGS-B",
        options={"maxiter": int(maxiter)},
    )

    optimized = {rule.rule_id: float(result.x[i]) for i, rule in enumerate(rules)}

    return {
        "success": bool(result.success),
        "message": str(result.message),
        "objective": float(result.fun),
        "optimized_coefficients": optimized,
        "iterations": int(result.nit),
    }
