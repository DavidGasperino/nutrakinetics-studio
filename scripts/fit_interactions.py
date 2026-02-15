#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models.calibration import fit_interaction_coefficients  # noqa: E402
from models.interfaces import SimulationScenario  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fit supplement interaction coefficients from observed NAD data.")
    parser.add_argument("--dataset", required=True, help="CSV file with columns: time_h, observed_nad_cyt_uM")
    parser.add_argument("--supplements", required=True, help="Comma-separated supplement ids, e.g. nr,nmn")
    parser.add_argument("--dose-mg", type=float, default=300.0, help="Primary regimen dose in mg")
    parser.add_argument("--duration-h", type=float, default=24.0, help="Simulation duration in hours")
    parser.add_argument("--route", default="oral", choices=["oral", "iv"], help="Route")
    parser.add_argument("--compound", default="NA", help="Primary compound label")
    parser.add_argument("--formulation", default="IR", help="Formulation")
    parser.add_argument("--cd38-scale", type=float, default=1.0, help="CD38 scaling factor")
    parser.add_argument("--maxiter", type=int, default=200, help="Max optimizer iterations")
    parser.add_argument(
        "--output",
        default="data/processed/interaction_fit_result.yaml",
        help="Output YAML path for optimized coefficients",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dataset = pd.read_csv(args.dataset)
    selected_supplements = tuple([s.strip() for s in args.supplements.split(",") if s.strip()])

    scenario = SimulationScenario(
        route=args.route,
        compound=args.compound,
        dose_mg=float(args.dose_mg),
        duration_h=float(args.duration_h),
        formulation=args.formulation,
        cd38_scale=float(args.cd38_scale),
        selected_supplements=selected_supplements,
        supplement_doses_mg={},
    )

    result = fit_interaction_coefficients(
        scenario=scenario,
        observed_df=dataset,
        target_col="observed_nad_cyt_uM",
        maxiter=int(args.maxiter),
    )

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(result, sort_keys=False))

    print(f"Wrote fit result to {output_path}")
    print(yaml.safe_dump(result, sort_keys=False))


if __name__ == "__main__":
    main()
