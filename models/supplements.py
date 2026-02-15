from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


@dataclass(frozen=True)
class SupplementDefinition:
    supplement_id: str
    label: str
    category: str
    enabled: bool
    default_dose_mg: float
    route_support: tuple[str, ...]
    mechanism_class: str
    ka_per_h: float
    kel_per_h: float
    exposure_scale: float
    ec50_uM: float
    hill_n: float
    synthesis_gain_per_signal: float
    cd38_effect_per_signal: float
    absorption_gain_per_signal: float
    fit_enabled: bool
    prior_mean: float
    prior_sd: float
    interaction_model_ready: bool
    backend_notes: str


@dataclass(frozen=True)
class InteractionRule:
    rule_id: str
    supplements: tuple[str, ...]
    target: str
    effect_direction: str
    coefficient: float
    lower_bound: float
    upper_bound: float
    fit_enabled: bool
    prior_mean: float
    prior_sd: float
    source_type: str
    source_id: str
    severity: str
    message: str


@dataclass(frozen=True)
class SupplementValidation:
    blocking_errors: tuple[str, ...]
    warnings: tuple[str, ...]


@lru_cache(maxsize=1)
def _load_supplement_payload() -> dict[str, object]:
    config_path = Path(__file__).resolve().parents[1] / "config" / "supplements.yaml"
    return yaml.safe_load(config_path.read_text())


@lru_cache(maxsize=1)
def _load_parameter_payload() -> dict[str, object]:
    config_path = Path(__file__).resolve().parents[1] / "config" / "parameters.base.yaml"
    return yaml.safe_load(config_path.read_text())


@lru_cache(maxsize=1)
def load_registry() -> dict[str, SupplementDefinition]:
    payload = _load_supplement_payload()

    supplements: dict[str, SupplementDefinition] = {}
    for item in payload["supplements"]:
        supplements[item["id"]] = SupplementDefinition(
            supplement_id=item["id"],
            label=item["label"],
            category=item["category"],
            enabled=bool(item["enabled"]),
            default_dose_mg=float(item["default_dose_mg"]),
            route_support=tuple(item["route_support"]),
            mechanism_class=str(item["mechanism"]["class"]),
            ka_per_h=float(item["pk"]["ka_per_h"]),
            kel_per_h=float(item["pk"]["kel_per_h"]),
            exposure_scale=float(item["pk"]["exposure_scale"]),
            ec50_uM=float(item["dynamics"]["ec50_uM"]),
            hill_n=float(item["dynamics"]["hill_n"]),
            synthesis_gain_per_signal=float(item["dynamics"]["synthesis_gain_per_signal"]),
            cd38_effect_per_signal=float(item["dynamics"]["cd38_effect_per_signal"]),
            absorption_gain_per_signal=float(item["dynamics"]["absorption_gain_per_signal"]),
            fit_enabled=bool(item["calibration"]["fit_enabled"]),
            prior_mean=float(item["calibration"]["prior_mean"]),
            prior_sd=float(item["calibration"]["prior_sd"]),
            interaction_model_ready=bool(item["backend"]["interaction_model_ready"]),
            backend_notes=item["backend"]["notes"],
        )

    return supplements


@lru_cache(maxsize=1)
def load_interaction_rules() -> tuple[InteractionRule, ...]:
    payload = _load_supplement_payload()
    rules = payload.get("interaction_rules", [])

    parsed: list[InteractionRule] = []
    for rule in rules:
        bounds = rule.get("bounds", [0.0, 1.0])
        parsed.append(
            InteractionRule(
                rule_id=str(rule["id"]),
                supplements=tuple(rule["supplements"]),
                target=str(rule["target"]),
                effect_direction=str(rule.get("effect_direction", "increase")),
                coefficient=float(rule["coefficient"]),
                lower_bound=float(bounds[0]),
                upper_bound=float(bounds[1]),
                fit_enabled=bool(rule["fit"]["enabled"]),
                prior_mean=float(rule["fit"]["prior_mean"]),
                prior_sd=float(rule["fit"]["prior_sd"]),
                source_type=str(rule["source"]["source_type"]),
                source_id=str(rule["source"]["source_id"]),
                severity=str(rule.get("severity", "warning")),
                message=str(rule.get("message", "Interaction rule triggered.")),
            )
        )

    return tuple(parsed)


@lru_cache(maxsize=1)
def load_class_scalars() -> dict[str, float]:
    payload = _load_parameter_payload()
    class_scalars = payload.get("parameters", {}).get("supplement_dynamics", {}).get("class_scalars", {})

    parsed: dict[str, float] = {}
    for class_name, node in class_scalars.items():
        try:
            parsed[class_name] = float(node["value"])
        except Exception:
            parsed[class_name] = 1.0

    return parsed


def selected_definitions(selected_ids: tuple[str, ...]) -> list[SupplementDefinition]:
    registry = load_registry()
    return [registry[s_id] for s_id in selected_ids if s_id in registry and registry[s_id].enabled]


def selected_interaction_rules(selected_ids: tuple[str, ...]) -> tuple[InteractionRule, ...]:
    selected = set(selected_ids)
    rules = load_interaction_rules()
    return tuple(rule for rule in rules if set(rule.supplements).issubset(selected))


def fittable_interaction_rules(selected_ids: tuple[str, ...]) -> tuple[InteractionRule, ...]:
    return tuple(rule for rule in selected_interaction_rules(selected_ids) if rule.fit_enabled)


def apply_interaction_overrides(
    rules: tuple[InteractionRule, ...],
    overrides: dict[str, float],
) -> tuple[InteractionRule, ...]:
    if not overrides:
        return rules

    updated: list[InteractionRule] = []
    for rule in rules:
        if rule.rule_id not in overrides:
            updated.append(rule)
            continue

        coefficient = float(overrides[rule.rule_id])
        clipped = float(np.clip(coefficient, rule.lower_bound, rule.upper_bound))
        updated.append(replace(rule, coefficient=clipped))

    return tuple(updated)


def validate_supplement_stack(
    selected_ids: tuple[str, ...],
    route: str,
    primary_compound: str,
) -> SupplementValidation:
    registry = load_registry()
    rules = selected_interaction_rules(selected_ids)

    blocking_errors: list[str] = []
    warnings: list[str] = []

    if len(selected_ids) > 5:
        warnings.append("More than 5 supplements selected; scenario complexity may exceed current calibration quality.")

    seen: set[str] = set()
    for s_id in selected_ids:
        if s_id in seen:
            warnings.append(f"Duplicate supplement '{s_id}' ignored.")
            continue
        seen.add(s_id)

        definition = registry.get(s_id)
        if definition is None:
            blocking_errors.append(f"Unknown supplement id '{s_id}'.")
            continue

        if not definition.enabled:
            blocking_errors.append(f"Supplement '{definition.label}' is disabled in the registry.")
            continue

        if route not in definition.route_support:
            blocking_errors.append(
                f"Supplement '{definition.label}' does not currently support the '{route}' route."
            )

        if not definition.interaction_model_ready:
            warnings.append(
                f"{definition.label}: backend interaction model is placeholder only ({definition.backend_notes})."
            )

    selected_classes: dict[str, int] = {}
    for definition in selected_definitions(tuple(seen)):
        selected_classes[definition.mechanism_class] = selected_classes.get(definition.mechanism_class, 0) + 1

    if selected_classes.get("nad_precursor", 0) > 1:
        warnings.append(
            "Multiple NAD precursor supplements selected; pairwise interaction calibration is not complete."
        )

    if primary_compound in {"NA", "NAM", "NA + NAM mix"} and any(s in seen for s in ("nr", "nmn")):
        warnings.append(
            "Primary vitamin B3 plus NR/NMN stacking is allowed but transporter and microbiome interaction terms are still simplified."
        )

    for rule in rules:
        if rule.fit_enabled:
            warnings.append(
                f"Interaction '{rule.rule_id}' is currently driven by prior coefficient {rule.coefficient:.3f}; calibration recommended."
            )

        if rule.severity.lower() == "block":
            blocking_errors.append(rule.message)
        else:
            warnings.append(rule.message)

    unique_blocking = tuple(dict.fromkeys(blocking_errors))
    unique_warnings = tuple(dict.fromkeys(warnings))

    return SupplementValidation(blocking_errors=unique_blocking, warnings=unique_warnings)


def _saturating_signal(concentration_uM: np.ndarray, ec50_uM: float, hill_n: float) -> np.ndarray:
    ec50 = max(ec50_uM, 1e-6)
    hill = max(hill_n, 0.1)
    numerator = np.power(np.maximum(concentration_uM, 0.0), hill)
    denominator = np.power(ec50, hill) + numerator
    return np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)


def supplement_concentration_trace(
    times_h: np.ndarray,
    dose_mg: float,
    definition: SupplementDefinition,
) -> np.ndarray:
    ka = max(definition.ka_per_h, 1e-4)
    kel = max(definition.kel_per_h, 1e-4)
    if abs(ka - kel) < 1e-6:
        kel = ka * 0.9

    scale = definition.exposure_scale * max(dose_mg, 0.0)
    trace = scale * (np.exp(-kel * times_h) - np.exp(-ka * times_h))
    return np.maximum(trace, 0.0)


def generate_supplement_traces(
    times_h: np.ndarray,
    definitions: list[SupplementDefinition],
    dose_map_mg: dict[str, float],
) -> dict[str, np.ndarray]:
    traces: dict[str, np.ndarray] = {}
    for definition in definitions:
        dose = dose_map_mg.get(definition.supplement_id, definition.default_dose_mg)
        traces[definition.supplement_id] = supplement_concentration_trace(times_h, dose_mg=dose, definition=definition)
    return traces


def compute_dynamic_modifier_series(
    times_h: np.ndarray,
    traces: dict[str, np.ndarray],
    definitions: list[SupplementDefinition],
    interaction_rules: tuple[InteractionRule, ...],
    class_scalars: dict[str, float],
) -> pd.DataFrame:
    synthesis_effect = np.zeros_like(times_h, dtype=float)
    cd38_effect = np.zeros_like(times_h, dtype=float)
    absorption_effect = np.zeros_like(times_h, dtype=float)

    columns: dict[str, np.ndarray] = {}
    sat_signals: dict[str, np.ndarray] = {}

    for definition in definitions:
        concentration = traces.get(definition.supplement_id)
        if concentration is None:
            continue

        sat_signal = _saturating_signal(concentration, definition.ec50_uM, definition.hill_n)
        sat_signals[definition.supplement_id] = sat_signal

        class_scalar = class_scalars.get(definition.mechanism_class, 1.0)

        synthesis_effect += class_scalar * definition.synthesis_gain_per_signal * sat_signal
        cd38_effect += class_scalar * definition.cd38_effect_per_signal * sat_signal
        absorption_effect += class_scalar * definition.absorption_gain_per_signal * sat_signal

        columns[f"supp_{definition.supplement_id}_sat_signal"] = sat_signal

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
            synthesis_effect += signed_effect
        elif rule.target == "cd38":
            cd38_effect += signed_effect
        elif rule.target == "absorption":
            absorption_effect += signed_effect

        columns[f"interaction_{rule.rule_id}_effect"] = signed_effect

    synthesis_multiplier = np.clip(1.0 + synthesis_effect, 0.50, 2.20)
    cd38_multiplier = np.clip(1.0 + cd38_effect, 0.30, 1.80)
    absorption_multiplier = np.clip(1.0 + absorption_effect, 0.50, 1.80)

    data = {
        "time_h": times_h,
        "synthesis_effect": synthesis_effect,
        "cd38_effect": cd38_effect,
        "absorption_effect": absorption_effect,
        "synthesis_multiplier": synthesis_multiplier,
        "cd38_multiplier": cd38_multiplier,
        "absorption_multiplier": absorption_multiplier,
    }
    data.update(columns)

    return pd.DataFrame(data)
