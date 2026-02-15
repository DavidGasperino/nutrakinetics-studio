# NutraKinetics Studio

NutraKinetics Studio is a Streamlit-first modeling workspace for mechanistic supplement PK/PBPK and NAD-related systems models.

## What this repo includes

- A build-ready specification stack for oral vitamin B3 -> NAD+ and IV NAD+ modeling
- A modular architecture for PBPK + intracellular NAD-QSP development
- A supplement stack registry with interaction-validation hooks for future multi-supplement simulation
- A runnable Streamlit shell to inspect scenarios and plots while model modules are incrementally implemented
- Calibration and validation planning docs for human-data fit workflows

## Current status

This repository is scaffolded for implementation. The full mechanistic model is specified in `docs/` and represented by code interfaces and a minimal simulation stub.

## Quick start

```bash
cd /Users/davidgasperino/workspace/nutrakinetics-studio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

## Repository structure

```text
app/                     Streamlit app
config/                  Parameter and supplement registry templates
data/                    Raw and processed datasets
docs/                    Product, technical, UI, and roadmap specifications
models/                  Module interfaces, simulation stubs, supplement stack engine
scripts/                 Utility scripts (ingestion, calibration hooks)
tests/                   Smoke tests
```

## Primary docs

- `docs/spec_product.md`
- `docs/spec_model.md`
- `docs/spec_ui.md`
- `docs/spec_roadmap.md`

## GitHub setup notes

After repo creation, connect remote with:

```bash
git remote add origin git@github.com:<YOUR_GITHUB_USER>/nutrakinetics-studio.git
git branch -M main
git push -u origin main
```
