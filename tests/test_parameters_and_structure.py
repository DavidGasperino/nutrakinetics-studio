from dataclasses import replace

from nutrakinetics_studio.interfaces import SimulationScenario
from nutrakinetics_studio.parameters import (
    SolverConfig,
    core_parameter_catalog_df,
    load_core_model_parameters,
    supplement_parameter_catalog_df,
)
from nutrakinetics_studio.simulation import run_simulation
from nutrakinetics_studio.supplement_modules import build_supplement_modules
from nutrakinetics_studio.supplements import selected_definitions


def test_parameter_catalog_has_metadata_fields() -> None:
    catalog = core_parameter_catalog_df()

    assert not catalog.empty
    required_columns = {"key", "value", "units", "definition", "description", "reference", "source_type", "source_id"}
    assert required_columns.issubset(catalog.columns)

    for column in ["definition", "description", "reference"]:
        assert (catalog[column].astype(str).str.len() > 0).all()


def test_supplement_parameter_catalog_has_metadata_fields() -> None:
    catalog = supplement_parameter_catalog_df()
    assert not catalog.empty
    for column in ["definition", "description", "reference"]:
        assert (catalog[column].astype(str).str.len() > 0).all()


def test_simulation_uses_configured_solver_grid_points() -> None:
    params = load_core_model_parameters()
    custom_params = replace(params, solver=SolverConfig(time_grid_points=61, ode_method=params.solver.ode_method))

    scenario = SimulationScenario(
        route="oral",
        compound="NA",
        dose_mg=300.0,
        duration_h=24.0,
        formulation="IR",
        cd38_scale=1.0,
    )

    result = run_simulation(scenario=scenario, core_params=custom_params)
    assert len(result.times_h) == 61


def test_simulation_uses_configured_initial_dose_scaling() -> None:
    params = load_core_model_parameters()
    custom_initial = replace(params.initial_conditions, precursor_dose_to_state_scale=0.02)
    custom_params = replace(params, initial_conditions=custom_initial)

    scenario = SimulationScenario(
        route="oral",
        compound="NA",
        dose_mg=250.0,
        duration_h=8.0,
        formulation="IR",
        cd38_scale=1.0,
    )

    result = run_simulation(scenario=scenario, core_params=custom_params)
    first_value = float(result.dataframe["plasma_precursor_uM"].iloc[0])

    assert abs(first_value - 5.0) < 1e-9


def test_supplement_module_factory_builds_modules() -> None:
    definitions = selected_definitions(("nr", "nmn"))
    params = load_core_model_parameters()

    modules = build_supplement_modules(definitions=definitions, safeguards=params.numerical_safeguards)

    assert set(modules.keys()) == {"nr", "nmn"}
