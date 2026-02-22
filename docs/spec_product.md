# Product Specification

## Product name
NutraKinetics Studio

## Product purpose
Provide a transparent, auditable mechanistic simulation environment for supplement PK/PBPK workflows with support for:

- Oral vitamin B3 forms (NA, NAM)
- Optional NAD booster extensions (NR, NMN)
- IV NAD+ infusion route
- Tissue-level intracellular NAD pool dynamics
- Multi-supplement stack modeling with interaction-aware validation
- Persistent scenario compare and calibration-ready interaction tuning

## Primary users

- Translational scientists and pharmacometricians
- Formulation scientists
- Clinically oriented R&D modeling teams

## Core user jobs

1. Configure route/formulation/dosing scenario.
2. Build supplement stacks with per-supplement doses.
3. Tune fit-enabled interaction coefficients for what-if analysis.
4. Run mechanistic simulation and inspect PK/NAD trajectories.
5. Save runs and compare overlays across scenarios.
6. Fit interaction coefficients to observed data using calibration hooks.

## In-scope outputs

- Plasma and tissue concentration-time trajectories
- Supplement-specific plasma proxy traces
- Dynamic effect and multiplier trajectories
- Intracellular `NAD_cyt` and `NAD_mito` trajectories
- Interaction warnings/errors and parameter tables
- Saved-run compare overlays

## Out of scope (current)

- Clinical efficacy claims or treatment recommendations
- Patient-specific medical advice
- Regulatory submission package generation

## Non-functional requirements

- Parameter-level provenance
- Parameter lookup includes definition, description, and reference for every model constant
- Reproducible scenario state and saved runs
- Clear distinction between calibrated vs prior-driven interaction parameters
- Baseline interactive response under typical laptop constraints

## Acceptance criteria (current)

1. Streamlit app runs with stack-aware dynamics and validation.
2. Runs can be saved, reloaded, and compared in overlays.
3. Interaction coefficient overrides are visible and applied.
4. Calibration hooks run from CLI with expected input contract.
5. Unit tests pass for simulation, compare store, and calibration hooks.
