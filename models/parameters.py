from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


@dataclass(frozen=True)
class ParameterRecord:
    key: str
    value: Any
    units: str
    definition: str
    description: str
    reference: str
    source_type: str
    source_id: str
    notes: str


@dataclass(frozen=True)
class SolverConfig:
    time_grid_points: int
    ode_method: str


@dataclass(frozen=True)
class InitialConditions:
    precursor_dose_to_state_scale: float
    nad_cyt_baseline_uM: float
    nad_mito_baseline_uM: float


@dataclass(frozen=True)
class RouteInputs:
    oral_input_base_uM_per_h: float
    iv_input_base_uM_per_h: float


@dataclass(frozen=True)
class PrecursorKinetics:
    uptake_rate_per_h: float
    clearance_rate_per_h: float


@dataclass(frozen=True)
class NadFluxRates:
    precursor_to_nad_gain_per_h: float
    oral_input_to_nad_gain_per_h: float
    iv_input_to_nad_gain_per_h: float
    cyt_to_mito_rate_per_h: float
    mito_to_cyt_rate_per_h: float
    cd38_base_rate_per_h: float
    parp_base_rate_per_h: float
    sirt_base_rate_per_h: float
    mito_loss_rate_per_h: float


@dataclass(frozen=True)
class ModifierBounds:
    synthesis_multiplier_min: float
    synthesis_multiplier_max: float
    cd38_multiplier_min: float
    cd38_multiplier_max: float
    absorption_multiplier_min: float
    absorption_multiplier_max: float


@dataclass(frozen=True)
class NumericalSafeguards:
    ec50_min_uM: float
    hill_min: float
    ka_min_per_h: float
    kel_min_per_h: float
    ka_kel_equal_tolerance: float
    ka_kel_adjustment_factor: float


@dataclass(frozen=True)
class CoreModelParameters:
    solver: SolverConfig
    initial_conditions: InitialConditions
    route_inputs: RouteInputs
    precursor_kinetics: PrecursorKinetics
    nad_flux: NadFluxRates
    modifier_bounds: ModifierBounds
    numerical_safeguards: NumericalSafeguards
    records: dict[str, ParameterRecord]


@lru_cache(maxsize=1)
def _payload() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "config" / "parameters.base.yaml"
    return yaml.safe_load(path.read_text())


@lru_cache(maxsize=1)
def _supplement_catalog_payload() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "config" / "supplement_parameter_catalog.yaml"
    return yaml.safe_load(path.read_text())


def _node_at_path(parameters: dict[str, Any], path: str) -> dict[str, Any]:
    cursor: Any = parameters
    for part in path.split("."):
        cursor = cursor[part]
    if not isinstance(cursor, dict):
        raise ValueError(f"Parameter path '{path}' did not resolve to a mapping node.")
    return cursor


def _record(parameters: dict[str, Any], path: str) -> ParameterRecord:
    node = _node_at_path(parameters, path)
    return ParameterRecord(
        key=path,
        value=node["value"],
        units=str(node.get("units", "")),
        definition=str(node.get("definition", "")),
        description=str(node.get("description", "")),
        reference=str(node.get("reference", "")),
        source_type=str(node.get("source_type", "")),
        source_id=str(node.get("source_id", "")),
        notes=str(node.get("notes", "")),
    )


def _record_float(parameters: dict[str, Any], path: str, records: dict[str, ParameterRecord]) -> float:
    rec = _record(parameters, path)
    records[path] = rec
    return float(rec.value)


def _record_int(parameters: dict[str, Any], path: str, records: dict[str, ParameterRecord]) -> int:
    rec = _record(parameters, path)
    records[path] = rec
    return int(rec.value)


def _record_str(parameters: dict[str, Any], path: str, records: dict[str, ParameterRecord]) -> str:
    rec = _record(parameters, path)
    records[path] = rec
    return str(rec.value)


@lru_cache(maxsize=1)
def load_core_model_parameters() -> CoreModelParameters:
    payload = _payload()
    params = payload.get("parameters", {})

    records: dict[str, ParameterRecord] = {}

    solver = SolverConfig(
        time_grid_points=_record_int(params, "simulation_core.solver.time_grid_points", records),
        ode_method=_record_str(params, "simulation_core.solver.ode_method", records),
    )

    initial_conditions = InitialConditions(
        precursor_dose_to_state_scale=_record_float(
            params, "simulation_core.initial_conditions.precursor_dose_to_state_scale", records
        ),
        nad_cyt_baseline_uM=_record_float(params, "simulation_core.initial_conditions.nad_cyt_baseline_uM", records),
        nad_mito_baseline_uM=_record_float(params, "simulation_core.initial_conditions.nad_mito_baseline_uM", records),
    )

    route_inputs = RouteInputs(
        oral_input_base_uM_per_h=_record_float(params, "simulation_core.route_inputs.oral_input_base_uM_per_h", records),
        iv_input_base_uM_per_h=_record_float(params, "simulation_core.route_inputs.iv_input_base_uM_per_h", records),
    )

    precursor_kinetics = PrecursorKinetics(
        uptake_rate_per_h=_record_float(params, "simulation_core.precursor_kinetics.uptake_rate_per_h", records),
        clearance_rate_per_h=_record_float(params, "simulation_core.precursor_kinetics.clearance_rate_per_h", records),
    )

    nad_flux = NadFluxRates(
        precursor_to_nad_gain_per_h=_record_float(params, "simulation_core.nad_flux.precursor_to_nad_gain_per_h", records),
        oral_input_to_nad_gain_per_h=_record_float(params, "simulation_core.nad_flux.oral_input_to_nad_gain_per_h", records),
        iv_input_to_nad_gain_per_h=_record_float(params, "simulation_core.nad_flux.iv_input_to_nad_gain_per_h", records),
        cyt_to_mito_rate_per_h=_record_float(params, "simulation_core.nad_flux.cyt_to_mito_rate_per_h", records),
        mito_to_cyt_rate_per_h=_record_float(params, "simulation_core.nad_flux.mito_to_cyt_rate_per_h", records),
        cd38_base_rate_per_h=_record_float(params, "simulation_core.nad_flux.cd38_base_rate_per_h", records),
        parp_base_rate_per_h=_record_float(params, "simulation_core.nad_flux.parp_base_rate_per_h", records),
        sirt_base_rate_per_h=_record_float(params, "simulation_core.nad_flux.sirt_base_rate_per_h", records),
        mito_loss_rate_per_h=_record_float(params, "simulation_core.nad_flux.mito_loss_rate_per_h", records),
    )

    modifier_bounds = ModifierBounds(
        synthesis_multiplier_min=_record_float(params, "simulation_core.modifier_bounds.synthesis_multiplier_min", records),
        synthesis_multiplier_max=_record_float(params, "simulation_core.modifier_bounds.synthesis_multiplier_max", records),
        cd38_multiplier_min=_record_float(params, "simulation_core.modifier_bounds.cd38_multiplier_min", records),
        cd38_multiplier_max=_record_float(params, "simulation_core.modifier_bounds.cd38_multiplier_max", records),
        absorption_multiplier_min=_record_float(params, "simulation_core.modifier_bounds.absorption_multiplier_min", records),
        absorption_multiplier_max=_record_float(params, "simulation_core.modifier_bounds.absorption_multiplier_max", records),
    )

    numerical_safeguards = NumericalSafeguards(
        ec50_min_uM=_record_float(params, "simulation_core.numerical_safeguards.ec50_min_uM", records),
        hill_min=_record_float(params, "simulation_core.numerical_safeguards.hill_min", records),
        ka_min_per_h=_record_float(params, "simulation_core.numerical_safeguards.ka_min_per_h", records),
        kel_min_per_h=_record_float(params, "simulation_core.numerical_safeguards.kel_min_per_h", records),
        ka_kel_equal_tolerance=_record_float(
            params, "simulation_core.numerical_safeguards.ka_kel_equal_tolerance", records
        ),
        ka_kel_adjustment_factor=_record_float(
            params, "simulation_core.numerical_safeguards.ka_kel_adjustment_factor", records
        ),
    )

    return CoreModelParameters(
        solver=solver,
        initial_conditions=initial_conditions,
        route_inputs=route_inputs,
        precursor_kinetics=precursor_kinetics,
        nad_flux=nad_flux,
        modifier_bounds=modifier_bounds,
        numerical_safeguards=numerical_safeguards,
        records=records,
    )


def core_parameter_catalog_df() -> pd.DataFrame:
    params = load_core_model_parameters()
    rows = [
        {
            "key": record.key,
            "value": record.value,
            "units": record.units,
            "definition": record.definition,
            "description": record.description,
            "reference": record.reference,
            "source_type": record.source_type,
            "source_id": record.source_id,
        }
        for record in params.records.values()
    ]
    return pd.DataFrame(rows)


def supplement_parameter_catalog_df() -> pd.DataFrame:
    payload = _supplement_catalog_payload()
    entries = payload.get("parameters", {})

    rows = []
    for key, node in entries.items():
        rows.append(
            {
                "key": key,
                "units": str(node.get("units", "")),
                "definition": str(node.get("definition", "")),
                "description": str(node.get("description", "")),
                "reference": str(node.get("reference", "")),
            }
        )

    return pd.DataFrame(rows)
