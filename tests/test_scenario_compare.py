from models.interfaces import SimulationScenario
from models.scenario_compare import clear_runs, delete_runs, load_saved_runs, run_dataframe, save_run
from models.simulation import run_simulation


def test_save_load_delete_compare_runs(monkeypatch, tmp_path) -> None:
    store_path = tmp_path / "scenario_compare.json"
    monkeypatch.setenv("NK_COMPARE_STORE", str(store_path))

    clear_runs()
    assert load_saved_runs() == []

    scenario = SimulationScenario(
        route="oral",
        compound="NA",
        dose_mg=300.0,
        duration_h=12.0,
        formulation="IR",
        cd38_scale=1.0,
    )
    result = run_simulation(scenario)

    saved = save_run(scenario=scenario, result=result, label="baseline")
    loaded = load_saved_runs()

    assert len(loaded) == 1
    assert loaded[0].label == "baseline"

    frame = run_dataframe(loaded[0])
    assert "run_label" in frame.columns
    assert frame["run_label"].iloc[0] == "baseline"

    delete_runs([saved.run_id])
    assert load_saved_runs() == []
