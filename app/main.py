from __future__ import annotations

import plotly.express as px
import streamlit as st

from models.interfaces import SimulationScenario
from models.simulation import run_simulation


st.set_page_config(page_title="NutraKinetics Studio", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap');

    :root {
      --nk-primary: #0f5c74;
      --nk-secondary: #c98a2a;
      --nk-critical: #ad3f2f;
      --nk-bg-start: #f3f6fb;
      --nk-bg-end: #d9e3f2;
    }

    .stApp {
      background: linear-gradient(145deg, var(--nk-bg-start), var(--nk-bg-end));
      font-family: 'Source Sans 3', sans-serif;
    }

    h1, h2, h3 {
      font-family: 'Space Grotesk', sans-serif;
      letter-spacing: 0.02em;
    }

    .nk-card {
      background: #ffffff;
      border: 1px solid #d4deea;
      border-radius: 12px;
      box-shadow: 0 8px 18px rgba(0, 0, 0, 0.06);
      padding: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("NutraKinetics Studio")
st.caption("Mechanistic supplement PK/PBPK + NAD dynamics workbench")

with st.sidebar:
    st.header("Scenario Builder")

    route = st.selectbox("Route", ["oral", "iv"], index=0)
    compound = st.selectbox("Compound", ["NA", "NAM", "NA + NAM mix"], index=0)
    formulation = st.selectbox("Formulation", ["IR", "ER", "Enteric", "Custom Weibull"], index=0)
    dose_mg = st.slider("Dose (mg)", min_value=10, max_value=2000, value=300, step=10)
    duration_h = st.slider("Simulation horizon (hours)", min_value=2, max_value=48, value=24, step=1)
    cd38_scale = st.slider("CD38 scale", min_value=0.5, max_value=2.0, value=1.0, step=0.05)

    run_btn = st.button("Run Simulation", type="primary", use_container_width=True)

scenario = SimulationScenario(
    route=route,
    compound=compound,
    dose_mg=float(dose_mg),
    duration_h=float(duration_h),
    formulation=formulation,
    cd38_scale=float(cd38_scale),
)

if run_btn or "result_df" not in st.session_state:
    result = run_simulation(scenario)
    st.session_state["result_df"] = result.dataframe

df = st.session_state["result_df"]

overview_tab, pk_tab, nad_tab, params_tab, calibration_tab = st.tabs(
    ["Overview", "PK Curves", "NAD Pools", "Parameters", "Calibration"]
)

with overview_tab:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cmax precursor", f"{df['plasma_precursor_uM'].max():.2f} uM")
    c2.metric("Tmax precursor", f"{df.loc[df['plasma_precursor_uM'].idxmax(), 'time_h']:.2f} h")
    c3.metric("Peak NAD cyt", f"{df['nad_cyt_uM'].max():.2f} uM")
    c4.metric("Peak NAD mito", f"{df['nad_mito_uM'].max():.2f} uM")

    st.markdown("<div class='nk-card'>This is the v0 scaffold using a placeholder ODE system. Replace with full module graph implementation from docs/spec_model.md.</div>", unsafe_allow_html=True)

with pk_tab:
    fig_pk = px.line(
        df,
        x="time_h",
        y=["plasma_precursor_uM"],
        labels={"value": "Concentration (uM)", "time_h": "Time (h)", "variable": "State"},
        color_discrete_sequence=["#0f5c74"],
    )
    fig_pk.update_layout(height=420)
    st.plotly_chart(fig_pk, use_container_width=True)

with nad_tab:
    fig_nad = px.line(
        df,
        x="time_h",
        y=["nad_cyt_uM", "nad_mito_uM"],
        labels={"value": "Concentration (uM)", "time_h": "Time (h)", "variable": "Pool"},
        color_discrete_sequence=["#0f5c74", "#c98a2a"],
    )
    fig_nad.update_layout(height=420)
    st.plotly_chart(fig_nad, use_container_width=True)

with params_tab:
    st.markdown("Parameter provenance contract is defined in `config/parameters.base.yaml`.")
    st.code(
        """fields: value, units, source_type, source_id, notes""",
        language="yaml",
    )

with calibration_tab:
    st.markdown("Calibration workflow is specified in `docs/spec_roadmap.md` and `docs/spec_model.md`.")
    st.info("Planned: objective functions, dataset selectors, and fit diagnostics in Phase 3.")
