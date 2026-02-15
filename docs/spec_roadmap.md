# Build Roadmap

## Phase 0: Foundation (current)

- Repository scaffold
- Streamlit shell
- Model interface contracts
- Parameter schema template
- Documentation handoff

Exit criteria:

- App runs locally
- Specs reviewed and approved

## Phase 1: Mechanistic core

- Implement PILL + GI + PBPK baseline ODE system
- Add oral NA/NAM simulation path
- Add exposure metric extraction
- Add unit tests for conservation and sign constraints

Exit criteria:

- Reproduces qualitative niacin PK characteristics
- Stable runtime under default scenarios

## Phase 2: NAD-QSP integration

- Add tissue intracellular states and fluxes
- CD38/PARP/SIRT toggles
- Mito pool transport option via SLC25A51
- NAAD optional marker path

Exit criteria:

- Produces plausible NAD pool dynamics
- Passes sensitivity sanity tests

## Phase 3: IV + ECTO and calibration

- Add IV infusion route and ecto-hydrolysis
- Dataset loaders and calibration objective plumbing
- Parameter fitting workflow (SciPy optimize / Bayesian optional)

Exit criteria:

- Fit pipeline works on at least one published human dataset
- Result artifacts saved with provenance metadata

## Phase 4: Hardening and deployment

- Streamlit app UX polish
- Batch scenario runner
- CI checks and packaging
- Streamlit Cloud or container deployment

Exit criteria:

- Reproducible deploy and versioned release tags
