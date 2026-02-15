import pandas as pd

from models.calibration import fit_interaction_coefficients, interaction_parameter_rows
from models.interfaces import SimulationScenario
from models.simulation import run_simulation


def test_interaction_parameter_rows_exposes_rules() -> None:
    rows = interaction_parameter_rows(selected_ids=("nr", "nmn"))
    assert rows
    assert any(row["rule_id"] == "nr_nmn_precursor_synergy" for row in rows)


def test_fit_interaction_coefficients_returns_coefficients() -> None:
    scenario = SimulationScenario(
        route="oral",
        compound="NA",
        dose_mg=300.0,
        duration_h=12.0,
        formulation="IR",
        cd38_scale=1.0,
        selected_supplements=("nr", "nmn"),
        supplement_doses_mg={"nr": 300.0, "nmn": 250.0},
    )

    baseline = run_simulation(scenario).dataframe
    observed = pd.DataFrame(
        {
            "time_h": baseline["time_h"],
            "observed_nad_cyt_uM": baseline["nad_cyt_uM"],
        }
    )

    fit = fit_interaction_coefficients(scenario=scenario, observed_df=observed, maxiter=25)

    assert "optimized_coefficients" in fit
    assert "nr_nmn_precursor_synergy" in fit["optimized_coefficients"]
