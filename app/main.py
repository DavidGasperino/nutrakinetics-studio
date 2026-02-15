from __future__ import annotations

import plotly.express as px
import streamlit as st

from models.interfaces import SimulationScenario
from models.simulation import run_simulation
from models.supplements import load_registry, validate_supplement_stack


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

registry = load_registry()
supplement_labels = {
    s_id: f"{definition.label} ({definition.category})"
    for s_id, definition in registry.items()
    if definition.enabled
}

with st.sidebar:
    st.header("Scenario Builder")

    route = st.selectbox("Route", ["oral", "iv"], index=0)
    compound = st.selectbox("Compound", ["NA", "NAM", "NA + NAM mix"], index=0)
    formulation = st.selectbox("Formulation", ["IR", "ER", "Enteric", "Custom Weibull"], index=0)
    dose_mg = st.slider("Dose (mg)", min_value=10, max_value=2000, value=300, step=10)
    duration_h = st.slider("Simulation horizon (hours)", min_value=2, max_value=48, value=24, step=1)
    cd38_scale = st.slider("CD38 scale", min_value=0.5, max_value=2.0, value=1.0, step=0.05)

    st.divider()
    st.subheader("Supplement Stack")
    enable_stack = st.checkbox("Enable additional supplements", value=False)

    selected_supplements: tuple[str, ...] = ()
    supplement_doses_mg: dict[str, float] = {}

    if enable_stack:
        selected = st.multiselect(
            "Select supplements",
            options=list(supplement_labels.keys()),
            default=[],
            format_func=lambda s_id: supplement_labels[s_id],
            help="Select 0..N supplements to add alongside the primary B3 regimen.",
        )
        selected_supplements = tuple(selected)

        if selected_supplements:
            with st.expander("Per-supplement dose controls", expanded=True):
                for s_id in selected_supplements:
                    definition = registry[s_id]
                    dose_value = st.slider(
                        f"{definition.label} dose (mg)",
                        min_value=25,
                        max_value=3000,
                        value=int(definition.default_dose_mg),
                        step=25,
                        key=f"dose_{s_id}",
                    )
                    supplement_doses_mg[s_id] = float(dose_value)

    validation = validate_supplement_stack(
        selected_ids=selected_supplements,
        route=route,
        primary_compound=compound,
    )

    for warning in validation.warnings:
        st.warning(warning)

    for error in validation.blocking_errors:
        st.error(error)

    can_run = len(validation.blocking_errors) == 0
    run_btn = st.button("Run Simulation", type="primary", use_container_width=True, disabled=not can_run)

scenario = SimulationScenario(
    route=route,
    compound=compound,
    dose_mg=float(dose_mg),
    duration_h=float(duration_h),
    formulation=formulation,
    cd38_scale=float(cd38_scale),
    selected_supplements=selected_supplements,
    supplement_doses_mg=supplement_doses_mg,
)

if "result" not in st.session_state and can_run:
    st.session_state["result"] = run_simulation(scenario)

if run_btn and can_run:
    st.session_state["result"] = run_simulation(scenario)

if "result" not in st.session_state:
    st.info("Resolve blocking supplement validation issues to run the simulation.")
    st.stop()

result = st.session_state["result"]
df = result.dataframe

if result.warnings:
    st.warning("Simulation notes: " + " | ".join(result.warnings))

overview_tab, pk_tab, nad_tab, supplement_tab, params_tab, calibration_tab = st.tabs(
    ["Overview", "PK Curves", "NAD Pools", "Supplement Effects", "Parameters", "Calibration"]
)

with overview_tab:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cmax precursor", f"{df['plasma_precursor_uM'].max():.2f} uM")
    c2.metric("Tmax precursor", f"{df.loc[df['plasma_precursor_uM'].idxmax(), 'time_h']:.2f} h")
    c3.metric("Peak NAD cyt", f"{df['nad_cyt_uM'].max():.2f} uM")
    c4.metric("Peak NAD mito", f"{df['nad_mito_uM'].max():.2f} uM")
    c5.metric("Stack size", str(len(selected_supplements)))

    st.markdown(
        "<div class='nk-card'>Use the supplement stack selector to compare base-regimen and stack behavior."
        " Validation errors block execution; warnings indicate areas where backend interaction models remain simplified.</div>",
        unsafe_allow_html=True,
    )

with pk_tab:
    st.markdown("### Plasma trajectories")
    supplement_columns = [c for c in df.columns if c.startswith("supp_") and c.endswith("_plasma_uM")]

    show_primary = st.checkbox("Show primary precursor", value=True)
    selected_plot_supps = st.multiselect(
        "Supplement traces to show",
        options=supplement_columns,
        default=supplement_columns,
    )

    y_columns: list[str] = []
    if show_primary:
        y_columns.append("plasma_precursor_uM")
    y_columns.extend(selected_plot_supps)

    if y_columns:
        fig_pk = px.line(
            df,
            x="time_h",
            y=y_columns,
            labels={"value": "Concentration (uM)", "time_h": "Time (h)", "variable": "State"},
        )
        fig_pk.update_layout(height=460)
        st.plotly_chart(fig_pk, use_container_width=True)
    else:
        st.info("Select at least one trace to visualize.")

with nad_tab:
    nad_columns = ["nad_cyt_uM", "nad_mito_uM"]
    if "supplement_stack_signal_uM" in df.columns:
        show_stack_signal = st.checkbox("Overlay supplement stack signal", value=True)
        if show_stack_signal:
            nad_columns.append("supplement_stack_signal_uM")

    fig_nad = px.line(
        df,
        x="time_h",
        y=nad_columns,
        labels={"value": "Concentration (uM)", "time_h": "Time (h)", "variable": "Pool"},
        color_discrete_sequence=["#0f5c74", "#c98a2a", "#ad3f2f"],
    )
    fig_nad.update_layout(height=460)
    st.plotly_chart(fig_nad, use_container_width=True)

with supplement_tab:
    if not selected_supplements:
        st.info("No supplementary compounds selected for this scenario.")
    else:
        summary_rows = []
        for s_id in selected_supplements:
            definition = registry[s_id]
            summary_rows.append(
                {
                    "supplement_id": s_id,
                    "label": definition.label,
                    "category": definition.category,
                    "dose_mg": supplement_doses_mg.get(s_id, definition.default_dose_mg),
                    "interaction_backend_ready": definition.interaction_model_ready,
                    "backend_notes": definition.backend_notes,
                }
            )

        st.dataframe(summary_rows, use_container_width=True)

with params_tab:
    st.markdown("Parameter provenance contract is defined in `config/parameters.base.yaml`.")
    st.code(
        """fields: value, units, source_type, source_id, notes""",
        language="yaml",
    )

    st.markdown("Supplement registry and interaction rules live in `config/supplements.yaml`.")

with calibration_tab:
    st.markdown("Calibration workflow is specified in `docs/spec_roadmap.md` and `docs/spec_model.md`.")
    st.info("Planned: objective functions, dataset selectors, supplement interaction fitting diagnostics.")
