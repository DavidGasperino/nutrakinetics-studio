from __future__ import annotations

import numpy as np

from nutrakinetics_studio.parameters import CoreModelParameters


def _route_inputs(route: str, absorption_multiplier: float, params: CoreModelParameters) -> tuple[float, float]:
    oral = (params.route_inputs.oral_input_base_uM_per_h if route == "oral" else 0.0) * absorption_multiplier
    iv = params.route_inputs.iv_input_base_uM_per_h if route == "iv" else 0.0
    return oral, iv


def compute_human_derivatives(
    y: np.ndarray,
    route: str,
    cd38_scale: float,
    synthesis_multiplier: float,
    cd38_multiplier: float,
    absorption_multiplier: float,
    params: CoreModelParameters,
) -> np.ndarray:
    plasma_precursor, nad_cyt, nad_mito = y

    oral_input, iv_input = _route_inputs(route, absorption_multiplier=absorption_multiplier, params=params)

    uptake = params.precursor_kinetics.uptake_rate_per_h * plasma_precursor
    clearance = params.precursor_kinetics.clearance_rate_per_h * plasma_precursor

    synth = (
        params.nad_flux.precursor_to_nad_gain_per_h * plasma_precursor
        + params.nad_flux.oral_input_to_nad_gain_per_h * oral_input
        + params.nad_flux.iv_input_to_nad_gain_per_h * iv_input
    ) * synthesis_multiplier

    to_mito = params.nad_flux.cyt_to_mito_rate_per_h * nad_cyt
    to_cyt = params.nad_flux.mito_to_cyt_rate_per_h * nad_mito

    cd38_sink = params.nad_flux.cd38_base_rate_per_h * cd38_scale * cd38_multiplier * nad_cyt
    parp_sink = params.nad_flux.parp_base_rate_per_h * nad_cyt
    sirt_sink = params.nad_flux.sirt_base_rate_per_h * nad_cyt

    d_plasma = -uptake - clearance + oral_input + iv_input
    d_nad_cyt = synth - to_mito + to_cyt - cd38_sink - parp_sink - sirt_sink
    d_nad_mito = to_mito - to_cyt - params.nad_flux.mito_loss_rate_per_h * nad_mito

    return np.array([d_plasma, d_nad_cyt, d_nad_mito], dtype=float)
