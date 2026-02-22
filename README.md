# NutraKinetics Studio

NutraKinetics Studio is a Streamlit-first workspace for mechanistic supplement PK/PBPK and NAD-related systems modeling.

## What this repo includes

- Build-ready specs for oral vitamin B3 -> NAD+ and IV NAD+ routes
- Modular PBPK + intracellular NAD-QSP architecture
- Multi-supplement stack registry with explicit interaction rules
- Dynamic supplement-class effect equations (not static stack multipliers)
- Typed core-parameter catalog with definition/description/reference metadata
- Supplement parameter-definition catalog for lookup of stack PK/dynamic terms
- Persistent scenario compare mode (save runs and overlay later)
- Calibration hooks for fitting interaction coefficients from observed data

## Quick start

```bash
cd /Users/davidgasperino/workspace/nutrakinetics-studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

## Fit interaction coefficients

```bash
python scripts/fit_interactions.py \
  --dataset data/processed/your_observed_dataset.csv \
  --supplements nr,nmn \
  --dose-mg 300 \
  --duration-h 24
```

Expected dataset columns:

- `time_h`
- `observed_nad_cyt_uM`

## Repository structure

```text
app/                     Streamlit app
config/                  Parameter + supplement registry templates
data/                    Raw and processed datasets
docs/                    Product, technical, UI, and roadmap specifications
models/                  Simulation engine, supplement dynamics, compare store, calibration hooks
scripts/                 CLI tools (including interaction fitting)
tests/                   Unit/smoke tests
```

## Primary docs

- `docs/spec_product.md`
- `docs/spec_model.md`
- `docs/spec_ui.md`
- `docs/spec_roadmap.md`

## Strategic code layout

- `models/processes/`: supplement-agnostic human process equations
- `models/supplement_modules/`: supplement-specific module implementations and effect engine
- `models/parameters.py`: typed access to auditable parameter records
