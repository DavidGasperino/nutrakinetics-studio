# Technical Model Specification

## 1. Modeling objective

Given a dosing regimen and formulation, simulate oral supplement to systemic exposure and intracellular NAD pool dynamics, plus IV NAD+ as a parallel route.

## 2. Architecture

Module graph:

`PILL -> GI -> ENT -> LIVER -> PBPK <-> NAD_QSP -> OUT`

Parallel route:

`IV -> ECTO -> PBPK <-> NAD_QSP`

Each module owns:

- State vector entries
- Parameter namespace and units
- Rate laws
- Input/output ports

## 3. Core state groups

- Drug product states: intact form, PSD solids, dissolved pools
- GI segment states: dissolved and particulate amounts per segment
- PBPK states: tissue amounts for central and peripheral compartments
- QSP states per tissue: `NAM`, `NMN`, `NAD_cyt`, `NAD_mito`, optional `NAAD`
- ECTO states for IV: plasma `NAD`, `NAM`, optional `ADPR`

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

- Dissolution depends on particle surface area
- Uses unbound concentration gradient `(C*unbound - C_unbound)`
- Supports segment pH and solubilization conditions

### 5.3 GI transport/absorption

- Segmental transit using CAT/ACAT-like first-order transfer
- Default absorption: permeability-limited flux
- Optional NA transporters: SMCT1/SMCT2 MM component
- Optional NMN dual-path uptake with mixture weight `alpha_nmn`

### 5.4 Liver first-pass and PBPK

- Perfusion-limited tissue distribution baseline
- Portal vein inflow to liver for oral route
- Tissue extraction and hepatic metabolism hooks

### 5.5 IV + ECTO

- Infusion rate `R_inf(t)` into plasma NAD state
- Ecto-hydrolysis to NAM via CD38-like MM term

### 5.6 Intracellular NAD-QSP

Per tissue:

- Synthesis: NAMPT, NMNAT, optional Preiss-Handler branch
- Consumption: CD38, PARP-like, SIRT-like terms with stress toggles
- Cytosol-mitochondria exchange via transport (SLC25A51-capable)

## 6. Parameter traceability contract

Every parameter record must include:

- `value`
- `units`
- `source_type` (`peer_reviewed`, `database`, `estimated_from_fit`)
- `source_id` (DOI/PMID/dataset)
- `notes`

## 7. Calibration strategy

1. Fit release/dissolution to in vitro profiles.
2. Fit plasma PK for NA/NAM to known oral behavior.
3. Fit NAD metabolome time courses for intracellular module constraints.
4. Fit IV ecto-clearance behavior using infusion studies.

## 8. Validation checks

- Mass conservation
- Non-negativity
- Parameter bounds and unit consistency
- Scenario sanity checks (IR peak timing, age/CD38 effect directionality)

## 9. Code interfaces

Defined in `models/interfaces.py` as module contracts and scenario/result types. Implementation classes can be swapped without changing app orchestration.
