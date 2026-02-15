from models.interfaces import SimulationScenario
from models.simulation import run_simulation


def test_run_simulation_smoke() -> None:
    scenario = SimulationScenario(
        route="oral",
        compound="NA",
        dose_mg=300.0,
        duration_h=24.0,
        formulation="IR",
        cd38_scale=1.0,
    )

    result = run_simulation(scenario)
    df = result.dataframe

    assert not df.empty
    assert {"time_h", "plasma_precursor_uM", "nad_cyt_uM", "nad_mito_uM"}.issubset(df.columns)
    assert (df[["plasma_precursor_uM", "nad_cyt_uM", "nad_mito_uM"]] >= 0).all().all()
