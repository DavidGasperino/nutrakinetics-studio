# UI Specification (Streamlit)

## 1. UI objective

Present a high-trust scientific simulator where users can configure mechanistic scenarios, run simulations quickly, and inspect uncertainty and calibration status.

## 2. Visual direction

Design language: "clinical lab notebook + systems console".

- Typography: `Source Sans Pro` for body, `Space Grotesk` for headings (via Streamlit CSS override)
- Color system:
  - Background gradient: slate -> steel blue (`#f3f6fb` to `#d9e3f2`)
  - Primary accent: deep teal (`#0f5c74`)
  - Secondary accent: amber (`#c98a2a`)
  - Critical/state warnings: rust (`#ad3f2f`)
- Card style: high contrast white cards, subtle border and shadow
- Charts: route-aware color mapping (oral vs IV) and tissue-specific line styles

## 3. App information architecture

### Sidebar: Scenario Builder

Controls:

- Route: oral / iv
- Compound profile: NA, NAM, mixed, custom
- Formulation: IR, ER, enteric, custom Weibull
- Dose and regimen timing
- Physiology profile: adult baseline, higher CD38 aging profile
- Simulation horizon and step density

### Main tabs

1. `Overview`
- Scenario summary cards
- Key KPI tiles (`AUC`, `Cmax`, `Tmax`, `NAD delta`)

2. `PK Curves`
- Plasma and portal curves
- Segmental GI transit plot
- Optional route comparison overlay

3. `NAD Pools`
- Tissue intracellular NAD trajectories (`cyt`, `mito`)
- Consumption flux decomposition (CD38/PARP/SIRT)

4. `Parameters`
- Table with source provenance fields
- Filter by module and source type

5. `Calibration`
- Dataset selector
- Objective metric visualization
- Parameter posterior/fit summary placeholder

## 4. Interaction requirements

- Every run tagged with scenario id and timestamp
- User can export current run (`csv` + `yaml` config)
- Inline warnings for unsupported mechanism combinations
- Tooltips for mechanistic terms and assumptions

## 5. Responsive behavior

- Desktop-first two-column grid for controls + charts
- Mobile fallback to stacked controls and single-chart viewport
- Preserve usability for 1280px width and above as primary target

## 6. Accessibility

- Color contrast >= WCAG AA for text and critical charts
- Keyboard-friendly tab navigation
- Avoid color-only encoding (line style/marker also used)
