from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from models.calibration import interaction_parameter_rows
from models.interfaces import SimulationScenario
from models.scenario_compare import clear_runs, delete_runs, load_saved_runs, run_dataframe, save_run
from models.simulation import run_simulation
from models.supplements import fittable_interaction_rules, load_registry, validate_supplement_stack


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

if "saved_runs" not in st.session_state:
    st.session_state["saved_runs"] = load_saved_runs()

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
    interaction_overrides: dict[str, float] = {}

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

            fit_rules = fittable_interaction_rules(selected_supplements)
            if fit_rules:
                with st.expander("Interaction coefficient tuning", expanded=False):
                    st.caption("These coefficients are calibratable priors and can be overridden per scenario.")
                    for rule in fit_rules:
                        step = max((rule.upper_bound - rule.lower_bound) / 100.0, 0.001)
                        key = f"coef_{rule.rule_id}"
                        default_value = float(st.session_state.get(key, rule.coefficient))
                        override_value = st.slider(
                            f"{rule.rule_id} ({', '.join(rule.supplements)} -> {rule.target})",
                            min_value=float(rule.lower_bound),
                            max_value=float(rule.upper_bound),
                            value=float(default_value),
                            step=float(step),
                            key=key,
                        )
                        interaction_overrides[rule.rule_id] = float(override_value)

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

    st.divider()
    st.subheader("Scenario Compare")
    run_label_input = st.text_input("Run label (optional)", value="")
    save_btn = st.button("Save Current Run", use_container_width=True)
    reload_btn = st.button("Reload Saved Runs", use_container_width=True)

if reload_btn:
    st.session_state["saved_runs"] = load_saved_runs()

scenario = SimulationScenario(
    route=route,
    compound=compound,
    dose_mg=float(dose_mg),
    duration_h=float(duration_h),
    formulation=formulation,
    cd38_scale=float(cd38_scale),
    selected_supplements=selected_supplements,
    supplement_doses_mg=supplement_doses_mg,
    interaction_coefficient_overrides=interaction_overrides,
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

if save_btn:
    auto_label = (
        f"{compound}-{route}-{int(dose_mg)}mg-"
        f"{len(selected_supplements)}supp-"
        f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    )
    final_label = run_label_input.strip() or auto_label
    save_run(scenario=scenario, result=result, label=final_label)
    st.session_state["saved_runs"] = load_saved_runs()
    st.success(f"Saved run: {final_label}")

if result.warnings:
    st.warning("Simulation notes: " + " | ".join(result.warnings))

overview_tab, pk_tab, nad_tab, supplement_tab, compare_tab, params_tab, calibration_tab = st.tabs(
    [
        "Overview",
        "PK Curves",
        "NAD Pools",
        "Supplement Effects",
        "Scenario Compare",
        "Parameters",
        "Calibration",
    ]
)

with overview_tab:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cmax precursor", f"{df['plasma_precursor_uM'].max():.2f} uM")
    c2.metric("Tmax precursor", f"{df.loc[df['plasma_precursor_uM'].idxmax(), 'time_h']:.2f} h")
    c3.metric("Peak NAD cyt", f"{df['nad_cyt_uM'].max():.2f} uM")
    c4.metric("Peak NAD mito", f"{df['nad_mito_uM'].max():.2f} uM")
    c5.metric("Saved runs", str(len(st.session_state["saved_runs"])))

    st.markdown(
        "<div class='nk-card'>Use supplement stack controls for scenario-specific dynamics and save runs for persistent"
        " cross-scenario overlays in Scenario Compare.</div>",
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
    base_columns = ["nad_cyt_uM", "nad_mito_uM"]
    dynamic_columns = ["synthesis_multiplier", "cd38_multiplier", "absorption_multiplier"]

    show_dynamic = st.checkbox("Overlay dynamic multipliers", value=False)

    nad_columns = list(base_columns)
    if "supplement_stack_signal_uM" in df.columns:
        show_stack_signal = st.checkbox("Overlay supplement stack signal", value=True)
        if show_stack_signal:
            nad_columns.append("supplement_stack_signal_uM")

    if show_dynamic:
        nad_columns.extend(dynamic_columns)

    fig_nad = px.line(
        df,
        x="time_h",
        y=nad_columns,
        labels={"value": "Value", "time_h": "Time (h)", "variable": "State"},
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
                    "mechanism_class": definition.mechanism_class,
                    "dose_mg": supplement_doses_mg.get(s_id, definition.default_dose_mg),
                    "interaction_backend_ready": definition.interaction_model_ready,
                    "backend_notes": definition.backend_notes,
                }
            )

        st.dataframe(summary_rows, use_container_width=True)

        interaction_cols = [c for c in df.columns if c.startswith("interaction_") and c.endswith("_effect")]
        if interaction_cols:
            st.markdown("### Interaction effect trajectories")
            fig_interactions = px.line(df, x="time_h", y=interaction_cols)
            fig_interactions.update_layout(height=360)
            st.plotly_chart(fig_interactions, use_container_width=True)

with compare_tab:
    saved_runs = st.session_state["saved_runs"]
    if not saved_runs:
        st.info("No saved runs yet. Use 'Save Current Run' in the sidebar.")
    else:
        run_index = {run.run_id: run for run in saved_runs}
        options = list(run_index.keys())

        selected_ids = st.multiselect(
            "Saved runs to overlay",
            options=options,
            default=options[-3:] if len(options) >= 3 else options,
            format_func=lambda rid: f"{run_index[rid].label} | {run_index[rid].created_at_utc[:19]}",
        )
        include_current = st.checkbox("Include current scenario", value=True)

        compare_frames: list[pd.DataFrame] = []
        for run_id in selected_ids:
            compare_frames.append(run_dataframe(run_index[run_id]))

        if include_current:
            current_df = df.copy()
            current_df["run_id"] = "current"
            current_df["run_label"] = "Current scenario"
            compare_frames.append(current_df)

        if compare_frames:
            combined = pd.concat(compare_frames, ignore_index=True)
            metric_candidates = [
                c
                for c in combined.columns
                if c
                not in {
                    "time_h",
                    "run_id",
                    "run_label",
                }
                and combined[c].dtype.kind in {"f", "i"}
            ]
            metric = st.selectbox(
                "Metric",
                options=sorted(metric_candidates),
                index=sorted(metric_candidates).index("nad_cyt_uM") if "nad_cyt_uM" in metric_candidates else 0,
            )

            fig_compare = px.line(
                combined,
                x="time_h",
                y=metric,
                color="run_label",
                labels={"time_h": "Time (h)", metric: metric},
            )
            fig_compare.update_layout(height=480)
            st.plotly_chart(fig_compare, use_container_width=True)

        st.markdown("### Manage saved runs")
        delete_ids = st.multiselect(
            "Select runs to delete",
            options=options,
            default=[],
            format_func=lambda rid: f"{run_index[rid].label} | {run_index[rid].created_at_utc[:19]}",
            key="delete_saved_runs",
        )
        delete_btn = st.button("Delete selected runs")
        clear_btn = st.button("Clear all saved runs")

        if delete_btn and delete_ids:
            delete_runs(delete_ids)
            st.session_state["saved_runs"] = load_saved_runs()
            st.success(f"Deleted {len(delete_ids)} run(s).")

        if clear_btn:
            clear_runs()
            st.session_state["saved_runs"] = load_saved_runs()
            st.success("Cleared all saved runs.")

with params_tab:
    st.markdown("Base parameter provenance lives in `config/parameters.base.yaml`.")
    st.code(
        """fields: value, units, source_type, source_id, notes""",
        language="yaml",
    )

    st.markdown("Supplement dynamics and interaction priors are in `config/supplements.yaml`.")

with calibration_tab:
    st.markdown("Calibration hooks are available in `models/calibration.py` and `scripts/fit_interactions.py`.")

    rows = interaction_parameter_rows(
        selected_ids=selected_supplements,
        overrides=interaction_overrides,
    )
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No interaction rules are active for current supplement selection.")

    st.code(
        """python scripts/fit_interactions.py \
  --dataset data/processed/your_observed_dataset.csv \
  --supplements nr,nmn \
  --dose-mg 300 \
  --duration-h 24""",
        language="bash",
    )
