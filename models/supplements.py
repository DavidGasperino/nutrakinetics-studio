from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml


@dataclass(frozen=True)
class SupplementDefinition:
    supplement_id: str
    label: str
    category: str
    enabled: bool
    default_dose_mg: float
    route_support: tuple[str, ...]
    stack_group: str
    ka_per_h: float
    kel_per_h: float
    exposure_scale: float
    synthesis_multiplier: float
    cd38_multiplier: float
    absorption_multiplier: float
    interaction_model_ready: bool
    backend_notes: str


@dataclass(frozen=True)
class SupplementValidation:
    blocking_errors: tuple[str, ...]
    warnings: tuple[str, ...]


@lru_cache(maxsize=1)
def load_registry() -> dict[str, SupplementDefinition]:
    config_path = Path(__file__).resolve().parents[1] / "config" / "supplements.yaml"
    payload = yaml.safe_load(config_path.read_text())

    supplements: dict[str, SupplementDefinition] = {}
    for item in payload["supplements"]:
        supplements[item["id"]] = SupplementDefinition(
            supplement_id=item["id"],
            label=item["label"],
            category=item["category"],
            enabled=bool(item["enabled"]),
            default_dose_mg=float(item["default_dose_mg"]),
            route_support=tuple(item["route_support"]),
            stack_group=item.get("stack_group", "general"),
            ka_per_h=float(item["pk"]["ka_per_h"]),
            kel_per_h=float(item["pk"]["kel_per_h"]),
            exposure_scale=float(item["pk"]["exposure_scale"]),
            synthesis_multiplier=float(item["nad_effects"]["synthesis_multiplier"]),
            cd38_multiplier=float(item["nad_effects"]["cd38_multiplier"]),
            absorption_multiplier=float(item["nad_effects"]["absorption_multiplier"]),
            interaction_model_ready=bool(item["backend"]["interaction_model_ready"]),
            backend_notes=item["backend"]["notes"],
        )

    return supplements


@lru_cache(maxsize=1)
def load_interaction_rules() -> tuple[dict[str, object], ...]:
    config_path = Path(__file__).resolve().parents[1] / "config" / "supplements.yaml"
    payload = yaml.safe_load(config_path.read_text())
    rules = payload.get("interaction_rules", [])
    return tuple(rules)


def selected_definitions(selected_ids: tuple[str, ...]) -> list[SupplementDefinition]:
    registry = load_registry()
    return [registry[s_id] for s_id in selected_ids if s_id in registry and registry[s_id].enabled]


def validate_supplement_stack(
    selected_ids: tuple[str, ...],
    route: str,
    primary_compound: str,
) -> SupplementValidation:
    registry = load_registry()
    rules = load_interaction_rules()

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

    groups: dict[str, int] = {}
    for definition in selected_definitions(tuple(seen)):
        groups[definition.stack_group] = groups.get(definition.stack_group, 0) + 1

    for group, count in groups.items():
        if group == "nad_precursor" and count > 1:
            warnings.append(
                "Multiple NAD precursor supplements selected; pairwise stack interaction calibration is not complete."
            )

    if primary_compound in {"NA", "NAM", "NA + NAM mix"} and any(s in seen for s in ("nr", "nmn")):
        warnings.append(
            "Primary vitamin B3 plus NR/NMN stacking is allowed but transporter and microbiome interaction terms are still simplified."
        )

    selected_set = set(seen)
    for rule in rules:
        pair = set(rule["supplements"])
        if pair.issubset(selected_set):
            message = str(rule["message"])
            severity = str(rule.get("severity", "warning")).lower()
            if severity == "block":
                blocking_errors.append(message)
            else:
                warnings.append(message)

    # Deduplicate while preserving order.
    unique_blocking = tuple(dict.fromkeys(blocking_errors))
    unique_warnings = tuple(dict.fromkeys(warnings))

    return SupplementValidation(blocking_errors=unique_blocking, warnings=unique_warnings)


def aggregate_modifiers(definitions: list[SupplementDefinition]) -> tuple[float, float, float]:
    if not definitions:
        return (1.0, 1.0, 1.0)

    synthesis_multiplier = float(np.prod([d.synthesis_multiplier for d in definitions]))
    cd38_multiplier = float(np.prod([d.cd38_multiplier for d in definitions]))
    absorption_multiplier = float(np.prod([d.absorption_multiplier for d in definitions]))

    # Keep aggregate effects bounded for stable placeholder dynamics.
    synthesis_multiplier = float(np.clip(synthesis_multiplier, 0.75, 1.40))
    cd38_multiplier = float(np.clip(cd38_multiplier, 0.70, 1.35))
    absorption_multiplier = float(np.clip(absorption_multiplier, 0.70, 1.30))

    return synthesis_multiplier, cd38_multiplier, absorption_multiplier


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
