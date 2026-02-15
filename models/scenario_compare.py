from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from models.interfaces import SimulationResult, SimulationScenario


@dataclass(frozen=True)
class SavedScenarioRun:
    run_id: str
    label: str
    created_at_utc: str
    scenario: dict[str, object]
    warnings: tuple[str, ...]
    dataframe_payload: dict[str, object]


def _store_path() -> Path:
    override = os.getenv("NK_COMPARE_STORE")
    if override:
        return Path(override)

    path = Path(__file__).resolve().parents[1] / "data" / "processed" / "scenario_compare_runs.json"
    return path


def _serialize_dataframe(df: pd.DataFrame) -> dict[str, object]:
    return {
        "columns": list(df.columns),
        "data": {column: df[column].tolist() for column in df.columns},
    }


def _deserialize_dataframe(payload: dict[str, object]) -> pd.DataFrame:
    columns = payload.get("columns", [])
    data = payload.get("data", {})
    frame = pd.DataFrame(data)
    if columns:
        frame = frame[[column for column in columns if column in frame.columns]]
    return frame


def _scenario_to_dict(scenario: SimulationScenario) -> dict[str, object]:
    payload = asdict(scenario)
    payload["selected_supplements"] = list(scenario.selected_supplements)
    return payload


def load_saved_runs() -> list[SavedScenarioRun]:
    store = _store_path()
    if not store.exists():
        return []

    raw = json.loads(store.read_text())
    runs: list[SavedScenarioRun] = []
    for item in raw:
        runs.append(
            SavedScenarioRun(
                run_id=item["run_id"],
                label=item["label"],
                created_at_utc=item["created_at_utc"],
                scenario=item["scenario"],
                warnings=tuple(item.get("warnings", [])),
                dataframe_payload=item["dataframe_payload"],
            )
        )
    return runs


def _persist_runs(runs: list[SavedScenarioRun]) -> None:
    store = _store_path()
    store.parent.mkdir(parents=True, exist_ok=True)

    serialized = [
        {
            "run_id": run.run_id,
            "label": run.label,
            "created_at_utc": run.created_at_utc,
            "scenario": run.scenario,
            "warnings": list(run.warnings),
            "dataframe_payload": run.dataframe_payload,
        }
        for run in runs
    ]
    store.write_text(json.dumps(serialized, indent=2))


def save_run(
    scenario: SimulationScenario,
    result: SimulationResult,
    label: str,
    max_runs: int = 50,
) -> SavedScenarioRun:
    runs = load_saved_runs()

    run = SavedScenarioRun(
        run_id=str(uuid4()),
        label=label,
        created_at_utc=datetime.now(UTC).isoformat(),
        scenario=_scenario_to_dict(scenario),
        warnings=result.warnings,
        dataframe_payload=_serialize_dataframe(result.dataframe),
    )

    runs.append(run)
    if len(runs) > max_runs:
        runs = runs[-max_runs:]

    _persist_runs(runs)
    return run


def delete_runs(run_ids: list[str]) -> None:
    run_ids_set = set(run_ids)
    runs = [run for run in load_saved_runs() if run.run_id not in run_ids_set]
    _persist_runs(runs)


def clear_runs() -> None:
    _persist_runs([])


def run_dataframe(run: SavedScenarioRun) -> pd.DataFrame:
    frame = _deserialize_dataframe(run.dataframe_payload)
    frame["run_id"] = run.run_id
    frame["run_label"] = run.label
    return frame
