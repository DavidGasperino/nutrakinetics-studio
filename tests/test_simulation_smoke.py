from dataclasses import replace

from nutrakinetics_studio.interfaces import SimulationScenario
from nutrakinetics_studio.simulation import run_simulation
from nutrakinetics_studio.supplements import validate_supplement_stack


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
    assert {
        "time_h",
        "plasma_precursor_uM",
        "nad_cyt_uM",
        "nad_mito_uM",
        "synthesis_multiplier",
        "cd38_multiplier",
        "absorption_multiplier",
    }.issubset(df.columns)
    assert (df[["plasma_precursor_uM", "nad_cyt_uM", "nad_mito_uM"]] >= 0).all().all()


def test_run_simulation_with_supplement_stack() -> None:
    scenario = SimulationScenario(
        route="oral",
        compound="NA + NAM mix",
        dose_mg=400.0,
        duration_h=18.0,
        formulation="ER",
        cd38_scale=1.1,
        selected_supplements=("quercetin", "tmg"),
        supplement_doses_mg={"quercetin": 500.0, "tmg": 1000.0},
    )

    result = run_simulation(scenario)
    df = result.dataframe

    assert "supp_quercetin_plasma_uM" in df.columns
    assert "supp_tmg_plasma_uM" in df.columns
    assert "supplement_stack_signal_uM" in df.columns
    assert "supp_quercetin_sat_signal" in df.columns
    assert len(result.warnings) >= 1


def test_interaction_override_changes_dynamic_output() -> None:
    base = SimulationScenario(
        route="oral",
        compound="NA",
        dose_mg=300.0,
        duration_h=16.0,
        formulation="IR",
        cd38_scale=1.0,
        selected_supplements=("nr", "nmn"),
        supplement_doses_mg={"nr": 300.0, "nmn": 250.0},
    )
    overridden = replace(base, interaction_coefficient_overrides={"nr_nmn_precursor_synergy": 0.25})

    base_result = run_simulation(base).dataframe
    override_result = run_simulation(overridden).dataframe

    assert override_result["synthesis_multiplier"].max() > base_result["synthesis_multiplier"].max()


def test_validation_blocks_route_mismatch() -> None:
    validation = validate_supplement_stack(
        selected_ids=("nr",),
        route="iv",
        primary_compound="NAM",
    )

    assert validation.blocking_errors
