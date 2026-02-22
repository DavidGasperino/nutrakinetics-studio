# UI Specification (Streamlit)

## 1. UI objective

Provide a high-trust simulation workbench that supports:

- mechanistic scenario setup
- multi-supplement stack tuning
- persistent scenario comparison
- calibration visibility for interaction coefficients

## 2. Visual direction

Design language: "clinical lab notebook + systems console".

- Typography: `Source Sans Pro` + `Space Grotesk`
- Background: slate-to-steel gradient
- Accent palette:
  - primary: `#0f5c74`
  - secondary: `#c98a2a`
  - warning/critical: `#ad3f2f`
- Card styling: white, bordered, soft shadow

## 3. Sidebar interaction model

Primary controls:

- route, compound, formulation
- dose and horizon
- CD38 scale

Supplement stack controls:

- enable stack toggle
- supplement multiselect
- per-supplement dose sliders
- interaction-coefficient sliders for fit-enabled rules
- inline warnings and blocking errors

Compare controls:

- optional run label
- save current run
- reload saved run inventory

## 4. Main tab structure

1. `Overview`
- KPI tiles (`Cmax`, `Tmax`, `NAD_cyt`, `NAD_mito`, saved run count)

2. `PK Curves`
- primary precursor trace toggle
- supplement plasma trace overlays

3. `NAD Pools`
- NAD pool trajectories
- optional dynamic multiplier overlays

4. `Supplement Effects`
- selected supplement metadata table
- interaction-effect trajectory plot when active

5. `Scenario Compare`
- persistent saved-run multiselect
- include-current toggle
- metric selector
- overlay chart across saved/current runs
- delete selected / clear all actions

6. `Parameters`
- provenance contract fields (`value`, `units`, `definition`, `description`, `reference`, `source_id`)
- core parameter catalog table + supplement parameter-definition catalog table
- pointers to config sources

7. `Calibration`
- active interaction parameter table
- effective vs default coefficient visibility
- CLI fitting hook usage snippet
- implementation source: `nutrakinetics_studio.calibration`

## 5. UX guardrails

- blocking validation prevents unsupported simulations
- warnings explicitly state model confidence limits
- interaction overrides are always visible in calibration table
- saved-run overlays are metric-selectable to avoid unreadable multi-axis plots

## 6. Responsive behavior

- desktop-first layout for scientific workflows
- stacked fallback for smaller screens
- controls remain accessible without hidden nested interactions

## 7. Accessibility

- color contrast >= WCAG AA for text and warnings
- keyboard-friendly controls
- non-color cues in labels and legends

## 8. Namespace migration note

- UI/runtime code imports should use `nutrakinetics_studio.*`.
- Legacy `models.*` imports are temporary shims and should not be used for new UI features.
