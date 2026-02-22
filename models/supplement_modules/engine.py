from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from models.parameters import ModifierBounds, NumericalSafeguards
from models.supplement_modules.base import SupplementModule
from models.supplement_modules.default import GenericSupplementModule
from models.supplements import InteractionRule, SupplementDefinition


@dataclass(frozen=True)
class DynamicModifierResult:
    modifier_df: pd.DataFrame
    traces_by_id: dict[str, np.ndarray]


def build_supplement_modules(
    definitions: list[SupplementDefinition],
    safeguards: NumericalSafeguards,
) -> dict[str, SupplementModule]:
    modules: dict[str, SupplementModule] = {}

    # Strategy: default generic module now; mechanism-class-specific modules can be
    # registered here without changing the simulation orchestrator.
    for definition in definitions:
        modules[definition.supplement_id] = GenericSupplementModule(definition=definition, safeguards=safeguards)

    return modules


def _apply_interactions(
    times_h: np.ndarray,
    sat_signals: dict[str, np.ndarray],
    interaction_rules: tuple[InteractionRule, ...],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    synthesis_interaction = np.zeros_like(times_h, dtype=float)
    cd38_interaction = np.zeros_like(times_h, dtype=float)
    absorption_interaction = np.zeros_like(times_h, dtype=float)
    columns: dict[str, np.ndarray] = {}

    for rule in interaction_rules:
        if not all(supp_id in sat_signals for supp_id in rule.supplements):
            continue

        interaction_signal = np.ones_like(times_h, dtype=float)
        for supp_id in rule.supplements:
            interaction_signal *= sat_signals[supp_id]

        interaction_signal = np.power(interaction_signal, 1.0 / max(len(rule.supplements), 1))
        signed_effect = rule.coefficient * interaction_signal
        if rule.effect_direction.lower() == "decrease":
            signed_effect *= -1.0

        if rule.target == "synthesis":
            synthesis_interaction += signed_effect
        elif rule.target == "cd38":
            cd38_interaction += signed_effect
        elif rule.target == "absorption":
            absorption_interaction += signed_effect

        columns[f"interaction_{rule.rule_id}_effect"] = signed_effect

    return synthesis_interaction, cd38_interaction, absorption_interaction, columns


def compute_dynamic_modifier_series(
    times_h: np.ndarray,
    modules_by_id: dict[str, SupplementModule],
    dose_map_mg: dict[str, float],
    class_scalars: dict[str, float],
    interaction_rules: tuple[InteractionRule, ...],
    bounds: ModifierBounds,
) -> DynamicModifierResult:
    synthesis_effect = np.zeros_like(times_h, dtype=float)
    cd38_effect = np.zeros_like(times_h, dtype=float)
    absorption_effect = np.zeros_like(times_h, dtype=float)

    traces: dict[str, np.ndarray] = {}
    sat_signals: dict[str, np.ndarray] = {}
    columns: dict[str, np.ndarray] = {}

    for supplement_id, module in modules_by_id.items():
        class_scalar = class_scalars.get(module.definition.mechanism_class, 1.0)
        dose = dose_map_mg.get(supplement_id, module.definition.default_dose_mg)
        series = module.effect_series(times_h=times_h, dose_mg=dose, class_scalar=class_scalar)

        traces[supplement_id] = series.concentration_uM
        sat_signals[supplement_id] = series.sat_signal

        synthesis_effect += series.synthesis_effect
        cd38_effect += series.cd38_effect
        absorption_effect += series.absorption_effect

        columns[f"supp_{supplement_id}_sat_signal"] = series.sat_signal

    synth_interaction, cd38_interaction, abs_interaction, interaction_cols = _apply_interactions(
        times_h=times_h,
        sat_signals=sat_signals,
        interaction_rules=interaction_rules,
    )

    synthesis_effect += synth_interaction
    cd38_effect += cd38_interaction
    absorption_effect += abs_interaction

    columns.update(interaction_cols)

    synthesis_multiplier = np.clip(1.0 + synthesis_effect, bounds.synthesis_multiplier_min, bounds.synthesis_multiplier_max)
    cd38_multiplier = np.clip(1.0 + cd38_effect, bounds.cd38_multiplier_min, bounds.cd38_multiplier_max)
    absorption_multiplier = np.clip(1.0 + absorption_effect, bounds.absorption_multiplier_min, bounds.absorption_multiplier_max)

    payload = {
        "time_h": times_h,
        "synthesis_effect": synthesis_effect,
        "cd38_effect": cd38_effect,
        "absorption_effect": absorption_effect,
        "synthesis_multiplier": synthesis_multiplier,
        "cd38_multiplier": cd38_multiplier,
        "absorption_multiplier": absorption_multiplier,
    }
    payload.update(columns)

    return DynamicModifierResult(modifier_df=pd.DataFrame(payload), traces_by_id=traces)
