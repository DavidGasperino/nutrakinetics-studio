# Product Specification

## Product name
NutraKinetics Studio

## Product purpose
Provide a transparent, auditable, mechanistic simulation environment for supplement PK/PBPK modeling with explicit support for:

- Oral vitamin B3 forms (NA, NAM)
- Optional NAD booster extensions (NR, NMN)
- IV NAD+ infusion route
- Tissue-level intracellular NAD pool dynamics

## Primary users

- Translational scientists and pharmacometricians
- Formulation scientists
- Clinically oriented R&D teams modeling protocol alternatives

## Core user jobs

1. Define a regimen (route, dose, schedule, formulation profile).
2. Run mechanistic simulation and inspect plasma/tissue trajectories.
3. Compare scenarios side-by-side.
4. Calibrate uncertain parameters to observed human datasets.
5. Export result bundles with assumptions and source traceability.

## In-scope outputs

- Plasma and tissue concentration-time outputs for NA/NAM and NAD metabolome states
- Intracellular `NAD_cyt` and `NAD_mito` trajectories by tissue
- Derived exposure metrics (`AUC`, `Cmax`, `Tmax`, delta-from-baseline)
- Regime indicators for PARP/SIRT/CD38 consumption dynamics

## Out of scope (initial release)

- Clinical efficacy or treatment recommendations
- Patient-specific diagnosis or dosing advice
- Full regulatory reporting automation

## Non-functional requirements

- Deterministic run mode with seedable stochastic options
- Parameter-level provenance for every constant and fitted value
- Model configuration versioning and reproducibility
- Interactive run target: <3 seconds for baseline scenario on laptop hardware

## Acceptance criteria (v0)

1. Streamlit app launches and runs baseline simulation.
2. Module boundaries are codified and independently testable.
3. Parameter template includes traceable metadata fields.
4. Documentation is sufficient for a separate implementation team to continue.
