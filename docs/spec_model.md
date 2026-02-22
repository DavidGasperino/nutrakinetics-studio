# Technical Model Specification

## 1. Modeling objective

Given a dosing regimen and formulation, simulate oral supplement exposure and intracellular NAD pool dynamics, plus IV NAD+ as a parallel route.

The simulator also supports multi-supplement stacks with explicit interaction-rule logic and calibration-ready coefficient overrides.

## 2. Architecture

Core module graph:

`PILL -> GI -> ENT -> LIVER -> PBPK <-> NAD_QSP -> OUT`

Parallel route:

`IV -> ECTO -> PBPK <-> NAD_QSP`

Supplement extension path:

`SUPPLEMENT_REGISTRY -> INTERACTION_VALIDATOR -> DYNAMIC_EFFECT_ENGINE -> PBPK/NAD_QSP`

Scenario compare path:

`SIMULATION_RESULT -> SCENARIO_COMPARE_STORE -> OVERLAY_VISUALIZATION`

## 3. Core state groups

- Drug product states: intact form, PSD solids, dissolved pools
- GI segment states: dissolved and particulate amounts per segment
- PBPK states: tissue amounts for central/peripheral compartments
- QSP states per tissue: `NAM`, `NMN`, `NAD_cyt`, `NAD_mito`, optional `NAAD`
- ECTO states for IV: plasma `NAD`, `NAM`, optional `ADPR`
- Supplement stack states:
  - per-supplement plasma proxy concentration traces
  - per-supplement saturating mechanism signals
  - interaction-effect trajectories

## 4. Units and conventions

- Amount: `umol`
- Concentration: `uM`
- Flow: `L/h`
- Volume: `L`
- First-order rate constants: `1/h`
- Enzyme kinetics: `Vmax` in `umol/h`, `Km` in `uM`

## 5. Minimum viable equation set

### 5.1 PILL release

- IR: first-order disintegration
- ER/SR: Weibull release fraction mapped into rate form

### 5.2 Dissolution

P-PSD-style driving force:

- dissolution proportional to particle surface area and unbound gradient
- supports pH/solubilization context by segment

### 5.3 GI transport/absorption

- CAT/ACAT-style segment transit
- permeability baseline with optional transporter extensions

### 5.4 Liver first-pass and PBPK

- perfusion-limited baseline
- portal inflow and hepatic extraction hooks

### 5.5 IV + ECTO

- infusion source term into plasma NAD state
- ecto-hydrolysis path to NAM

### 5.6 Intracellular NAD-QSP

- synthesis: NAMPT, NMNAT, optional Preiss-Handler
- sinks: CD38/PARP/SIRT-like
- cytosol-mitochondria coupling (SLC25A51-capable)

### 5.7 Supplement dynamic effect engine (implemented)

For each selected supplement:

1. Generate concentration proxy trace from supplement-specific PK parameters.
2. Convert concentration to saturating mechanism signal using `ec50` + Hill coefficient.
3. Apply mechanism-class scalar and supplement gains to dynamic effect terms:
   - `synthesis_effect`
   - `cd38_effect`
   - `absorption_effect`
4. Apply pairwise interaction rules (calibratable coefficients) to target effect term.
5. Convert effect terms to bounded multipliers used directly by the ODE at each time point.

## 6. Parameter traceability contract

Every parameter record includes:

- `value`
- `units`
- `definition`
- `description`
- `reference`
- `source_type`
- `source_id`
- `notes`

Applies to base PBPK/QSP parameters, supplement definitions, class scalars, and interaction coefficients.

Lookup sources:

- Core simulation constants: `config/parameters.base.yaml`
- Supplement parameter definitions: `config/supplement_parameter_catalog.yaml`

## 7. Calibration hooks

Implemented hooks:

- Interaction parameter inspection table: `src/nutrakinetics_studio/calibration.py`
- Interaction coefficient fitting routine: `fit_interaction_coefficients`
- CLI entrypoint: `scripts/fit_interactions.py`

Fitting target currently defaults to observed `NAD_cyt` trajectory (`time_h`, `observed_nad_cyt_uM`).

## 8. Validation checks

- Mass conservation
- Non-negativity
- Parameter bounds and unit consistency
- Scenario sanity checks (IR peak timing, age/CD38 directionality)
- Supplement stack checks (route support, unknown ids, pairwise rule handling)
- Scenario compare persistence checks (save/load/delete)

## 9. Code interfaces

- Typed parameter catalog: `nutrakinetics_studio.parameters`
- Supplement-agnostic human equations: `nutrakinetics_studio.processes.human_common`
- Supplement module abstractions: `nutrakinetics_studio.supplement_modules.base`
- Supplement module implementations: `nutrakinetics_studio.supplement_modules.default`
- Supplement module effect engine: `nutrakinetics_studio.supplement_modules.engine`
- Scenario/result contracts: `nutrakinetics_studio.interfaces`
- Core simulation: `nutrakinetics_studio.simulation`
- Supplement registry + validation: `nutrakinetics_studio.supplements`
- Persistent compare storage: `nutrakinetics_studio.scenario_compare`
- Calibration utilities: `nutrakinetics_studio.calibration`

## 10. Namespace migration

- Canonical imports are `nutrakinetics_studio.*`.
- Legacy `models.*` imports are supported by compatibility shims for one release cycle only.
- Shim removal is planned in the next explicit breaking-change migration.
