# Build Roadmap

## Phase 0: Foundation (completed)

- Repository scaffold
- Streamlit shell
- Base model interface contracts
- Parameter schema template
- Initial documentation stack

## Phase 1: Stack-aware simulation shell (completed)

- Supplement registry and validation rules
- Multi-supplement selection UI
- Dynamic supplement traces in outputs
- Basic warning/blocking behavior

## Phase 2: Dynamic supplement effects (completed)

- Explicit class-based effect equations
- Interaction-rule effects wired into ODE multipliers
- Interaction coefficient override support
- Tests for override sensitivity

## Phase 3: Compare + calibration hooks (completed)

- Persistent scenario compare store (save/load/delete)
- Overlay visualization across saved and current scenarios
- Interaction parameter inspection table
- CLI fitting hook (`scripts/fit_interactions.py`)

## Phase 4: Scientific hardening (next)

- Replace proxy supplement PK with data-backed modules per compound
- Add observed dataset ingestion + preprocessing templates
- Add calibration report artifacts (fit quality, parameter uncertainty)
- Expand objective set beyond `NAD_cyt` MSE (multi-objective)

Exit criteria:

- At least one real observed dataset reproducibly fitted
- Fit artifacts stored with provenance and timestamp

## Phase 5: Deployment and scale (next)

- CI pipeline for tests + lint + docs checks
- Scenario batch runner and export packager
- Streamlit Cloud / containerized deployment profile
- Versioned release process with changelog

Exit criteria:

- Reproducible deploy and versioned release tags
