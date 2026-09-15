from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.comparison import (
    ComparisonCostAssumptions,
    ScenarioDefinition,
    compare_scenarios,
    comparison_interpretation,
    comparison_table,
)
from src.cost_of_quality import CostConfig, estimate_cost_shift
from src.diagnostics import (
    metric_integrity_diagnostic,
    quality_mirage_interpretation,
    spc_diagnostic,
)
from src.exports import (
    build_scenario_summary,
    comparison_summary_csv,
    comparison_summary_json,
    comparison_summary_markdown,
    scenario_results_csv,
    scenario_summary_json,
    scenario_summary_markdown,
)
from src.gaming_models import MECHANISMS
from src.imported_data import (
    CSV_TEMPLATE,
    CSVValidationError,
    imported_chart_series,
    imported_data_interpretation,
    validate_quality_csv,
)
from src.metric_integrity import MetricVulnerability, integrity_score
from src.recommendations import AUDIT_QUESTIONS, audit_diagnostic, audit_result
from src.scenarios import (
    CUSTOM_SCENARIO,
    DEFAULT_WIDGET_STATE,
    SCENARIO_PRESETS,
    get_scenario_preset,
    scenario_names,
)
from src.simulation_engine import SimulationConfig, simulate_quality_path
from src.spc_engine import SPCConfig, simulate_p_chart


st.set_page_config(
    page_title="Quality Metrics Integrity Lab",
    page_icon=":material/analytics:",
    layout="wide",
)


def apply_selected_preset() -> None:
    """Load the selected preset into keyed controls before the app reruns."""
    selected = st.session_state["scenario_mode"]
    if selected != CUSTOM_SCENARIO:
        st.session_state.update(get_scenario_preset(selected).as_widget_state())


def mark_scenario_custom() -> None:
    """Reflect manual control edits in the scenario selector."""
    st.session_state["scenario_mode"] = CUSTOM_SCENARIO


st.session_state.setdefault("scenario_mode", CUSTOM_SCENARIO)
for state_key, default_value in DEFAULT_WIDGET_STATE.items():
    st.session_state.setdefault(state_key, default_value)


st.title("Quality Metrics Integrity Lab")
st.caption("Explore when quality metrics stop representing quality. · v0.3.0")
st.write(
    "Explore how a high-stakes quality target can separate an underlying process "
    "from the number reported about it. Select a scenario or adjust the assumptions, "
    "then compare the five measurement-integrity views."
)
st.info(
    "Educational simulation only. Outputs are hypothetical and should not be "
    "interpreted as empirical forecasts, compliance findings, or audit conclusions.",
    icon=":material/info:",
)

with st.sidebar:
    st.header("Scenario controls")
    selected_scenario = st.selectbox(
        "Scenario",
        scenario_names(),
        key="scenario_mode",
        on_change=apply_selected_preset,
        help="Presets load coherent hypothetical assumptions. Any manual edit returns the mode to Custom.",
    )
    if selected_scenario == CUSTOM_SCENARIO:
        st.caption("Custom — adjust any assumption to build your own educational scenario.")
    else:
        st.caption(get_scenario_preset(selected_scenario).description)

    with st.expander("Process and reporting", expanded=True):
        baseline = st.slider(
            "Baseline defect rate (%)",
            min_value=0.5,
            max_value=8.0,
            step=0.1,
            key="baseline_pct",
            on_change=mark_scenario_custom,
            help="Starting defect rate; stored internally as a decimal fraction.",
        ) / 100
        target = st.slider(
            "Target defect rate (%)",
            min_value=0.1,
            max_value=5.0,
            step=0.1,
            key="target_pct",
            on_change=mark_scenario_custom,
            help="Reference line on the chart. Target pressure is controlled separately.",
        ) / 100
        pressure = st.slider(
            "Target pressure",
            min_value=0,
            max_value=100,
            key="pressure_pct",
            on_change=mark_scenario_custom,
            help="Illustrative intensity of consequences attached to meeting the target.",
        ) / 100
        susceptibility = st.slider(
            "Gaming susceptibility",
            min_value=0,
            max_value=100,
            key="susceptibility_pct",
            on_change=mark_scenario_custom,
            help="Illustrative ease with which reporting can diverge from the process.",
        ) / 100
        genuine_improvement = st.slider(
            "Genuine monthly process improvement (percentage points)",
            min_value=0.0,
            max_value=0.20,
            step=0.005,
            key="improvement_pp",
            on_change=mark_scenario_custom,
        ) / 100
        drift = st.slider(
            "Monthly process deterioration (percentage points)",
            min_value=0.0,
            max_value=0.20,
            step=0.005,
            key="drift_pp",
            on_change=mark_scenario_custom,
        ) / 100

    with st.expander("Metric vulnerability", expanded=True):
        single = st.slider(
            "Single-metric dependence",
            min_value=0,
            max_value=100,
            key="single_pct",
            on_change=mark_scenario_custom,
        ) / 100
        stakes = st.slider(
            "High-stakes consequences",
            min_value=0,
            max_value=100,
            key="stakes_pct",
            on_change=mark_scenario_custom,
        ) / 100
        manipulability = st.slider(
            "Ease of manipulation",
            min_value=0,
            max_value=100,
            key="manipulability_pct",
            on_change=mark_scenario_custom,
        ) / 100
        weak_link = st.slider(
            "Weak link to customer outcome",
            min_value=0,
            max_value=100,
            key="weak_link_pct",
            on_change=mark_scenario_custom,
        ) / 100

    with st.expander("Display assumptions"):
        sanitisation = st.slider(
            "SPC sanitisation strength",
            min_value=0,
            max_value=100,
            key="spc_sanitisation_pct",
            on_change=mark_scenario_custom,
            help="How strongly displayed SPC observations are compressed toward the baseline.",
        ) / 100
        hidden_fraction = st.slider(
            "Share of detected defects shifted downstream",
            min_value=0,
            max_value=100,
            key="hidden_fraction_pct",
            on_change=mark_scenario_custom,
            help="Illustrative share of internally detected defects hidden or reclassified.",
        ) / 100


simulation_config = SimulationConfig(
    baseline_defect_rate=baseline,
    target_defect_rate=target,
    target_pressure=pressure,
    gaming_susceptibility=susceptibility,
    genuine_improvement_per_month=genuine_improvement,
    process_drift_per_month=drift,
)
vulnerability = MetricVulnerability(
    single_metric_dependence=single,
    stakes=stakes,
    manipulability=manipulability,
    customer_link_weakness=weak_link,
)

try:
    sim = simulate_quality_path(simulation_config)
    integrity = integrity_score(vulnerability)
    integrity_details = metric_integrity_diagnostic(vulnerability, integrity)
    spc_config = SPCConfig(sanitisation_strength=sanitisation)
    spc_df, limits = simulate_p_chart(spc_config)
    spc_details = spc_diagnostic(spc_df, limits)
except ValueError as exc:
    st.error(f"The scenario inputs are invalid: {exc}", icon=":material/error:")
    st.stop()


summary_columns = st.columns(4, border=True)
summary_columns[0].metric(
    "Metric integrity score",
    f"{integrity['integrity_score']}/100",
    help="A transparent heuristic, not an academically validated index.",
)
summary_columns[1].metric(
    "Final actual defect rate", f"{sim.actual_rate.iloc[-1] * 100:.2f}%"
)
summary_columns[2].metric(
    "Final reported defect rate", f"{sim.reported_rate.iloc[-1] * 100:.2f}%"
)
summary_columns[3].metric(
    "Final reporting gap",
    f"{sim.reporting_gap.iloc[-1] * 100:.2f} pp",
    help="Actual defect rate minus reported defect rate, in percentage points.",
)

with st.container(border=True):
    st.subheader("Metric integrity diagnostic", icon=":material/diagnosis:")
    diagnostic_columns = st.columns([0.8, 1.1, 1.1])
    diagnostic_columns[0].metric(
        "Risk classification", integrity_details["classification"]
    )
    with diagnostic_columns[1]:
        st.caption("Strongest vulnerability")
        st.markdown(f"**{integrity_details['strongest_driver']}**")
        st.caption(f"Input level: {integrity_details['strongest_value']:.0%}")
    with diagnostic_columns[2]:
        st.caption("Weakest vulnerability")
        st.markdown(f"**{integrity_details['weakest_driver']}**")
        st.caption(f"Input level: {integrity_details['weakest_value']:.0%}")
    st.caption(integrity_details["explanation"])


tabs = st.tabs(
    [
        "Quality Mirage",
        "Gaming Mechanisms",
        "SPC Integrity",
        "Cost of Quality",
        "Metric Audit",
    ]
)

with tabs[0]:
    st.subheader("Actual and reported defect-rate paths")
    st.caption(
        "The shaded band is the reporting gap: the difference between the underlying "
        "simulated process and the reported metric."
    )
    quality_chart = go.Figure()
    quality_chart.add_trace(
        go.Scatter(
            x=sim.month,
            y=sim.reported_rate * 100,
            mode="lines+markers",
            name="Reported defect rate",
            line={"color": "#60A5FA", "width": 3},
            marker={"size": 7},
            hovertemplate="Month %{x}<br>Reported: %{y:.2f}%<extra></extra>",
        )
    )
    quality_chart.add_trace(
        go.Scatter(
            x=sim.month,
            y=sim.actual_rate * 100,
            mode="lines+markers",
            name="Actual underlying defect rate",
            line={"color": "#F87171", "width": 3},
            marker={"size": 7},
            fill="tonexty",
            fillcolor="rgba(248, 113, 113, 0.16)",
            hovertemplate="Month %{x}<br>Actual: %{y:.2f}%<extra></extra>",
        )
    )
    quality_chart.add_trace(
        go.Scatter(
            x=sim.month,
            y=sim.target_rate * 100,
            mode="lines",
            name="Target reference",
            line={"color": "#CBD5E1", "width": 2, "dash": "dot"},
            hovertemplate="Month %{x}<br>Target: %{y:.2f}%<extra></extra>",
        )
    )
    quality_chart.update_layout(
        xaxis_title="Month",
        yaxis_title="Defect rate (%)",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.12, "x": 0},
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
    )
    quality_chart.update_xaxes(dtick=1)
    st.plotly_chart(quality_chart, width="stretch", key="quality_mirage_chart")
    st.info(
        quality_mirage_interpretation(sim),
        icon=":material/insights:",
    )
    st.caption(
        "The model illustrates a possible measurement divergence; it does not infer "
        "intent or describe a real organisation."
    )

with tabs[1]:
    st.subheader("How the reporting gap is allocated")
    final_gap = float(sim.reporting_gap.iloc[-1])
    if final_gap == 0.0:
        st.info(
            "This scenario has no reporting gap, so all mechanism contributions are zero.",
            icon=":material/info:",
        )
    contribution_rows = []
    for mechanism, column in (
        ("Classification", "classification_gap"),
        ("Timing", "timing_gap"),
        ("Sampling", "sampling_gap"),
    ):
        gap = float(sim[column].iloc[-1])
        contribution_rows.append(
            {
                "Mechanism": mechanism,
                "Gap contribution (pp)": gap * 100,
                "Relative contribution (%)": 0.0 if final_gap == 0 else gap / final_gap * 100,
            }
        )
    contributions = pd.DataFrame(contribution_rows)
    contribution_chart = go.Figure(
        go.Bar(
            x=contributions["Relative contribution (%)"],
            y=contributions["Mechanism"],
            orientation="h",
            marker_color=["#60A5FA", "#A78BFA", "#34D399"],
            customdata=contributions[["Gap contribution (pp)"]],
            hovertemplate=(
                "%{y}<br>Share: %{x:.1f}%<br>Gap contribution: "
                "%{customdata[0]:.3f} pp<extra></extra>"
            ),
        )
    )
    contribution_chart.update_layout(
        xaxis_title="Share of final reporting gap (%)",
        yaxis_title=None,
        margin={"l": 20, "r": 20, "t": 15, "b": 20},
        height=290,
    )
    contribution_chart.update_xaxes(range=[0, 100])
    st.plotly_chart(
        contribution_chart, width="stretch", key="gaming_contribution_chart"
    )
    st.dataframe(
        contributions,
        hide_index=True,
        width="stretch",
        column_config={
            "Gap contribution (pp)": st.column_config.NumberColumn(format="%.3f"),
            "Relative contribution (%)": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )

    mechanism_columns = st.columns(3, border=True)
    for column, (name, details) in zip(mechanism_columns, MECHANISMS.items()):
        with column:
            st.markdown(f"**{name}**")
            st.write(details["description"])
            st.caption(f"Example: {details['example']}")
            st.caption(f"Audit signal: {details['audit_signal']}")

with tabs[2]:
    st.subheader("Real versus sanitised p-chart observations")
    st.caption(
        "Both series use the same limits calculated from the unsanitised observations. "
        "Compression can make the displayed process look calmer without changing the process."
    )
    spc_chart = go.Figure()
    spc_chart.add_trace(
        go.Scatter(
            x=spc_df.period,
            y=spc_df.real_data * 100,
            mode="lines+markers",
            name="Real observations",
            line={"color": "#F87171", "width": 2.5},
            hovertemplate="Period %{x}<br>Real: %{y:.2f}%<extra></extra>",
        )
    )
    spc_chart.add_trace(
        go.Scatter(
            x=spc_df.period,
            y=spc_df.sanitised_data * 100,
            mode="lines+markers",
            name="Sanitised observations",
            line={"color": "#60A5FA", "width": 2.5},
            hovertemplate="Period %{x}<br>Sanitised: %{y:.2f}%<extra></extra>",
        )
    )
    real_signal_mask = (spc_df.real_data > limits["ucl"]) | (
        spc_df.real_data < limits["lcl"]
    )
    spc_chart.add_trace(
        go.Scatter(
            x=spc_df.loc[real_signal_mask, "period"],
            y=spc_df.loc[real_signal_mask, "real_data"] * 100,
            mode="markers",
            name="Real limit-crossing signal",
            marker={"color": "#FBBF24", "size": 12, "symbol": "diamond"},
            hovertemplate="Period %{x}<br>Signal: %{y:.2f}%<extra></extra>",
        )
    )
    for value, label, color in (
        (limits["ucl"], "UCL", "#FBBF24"),
        (limits["center_line"], "Center line", "#94A3B8"),
        (limits["lcl"], "LCL", "#FBBF24"),
    ):
        spc_chart.add_hline(
            y=value * 100,
            line_dash="dash" if label != "Center line" else "dot",
            line_color=color,
            annotation_text=label,
        )
    spc_chart.update_layout(
        xaxis_title="Period",
        yaxis_title="Defect fraction (%)",
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.14, "x": 0},
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
    )
    spc_chart.update_xaxes(dtick=1)
    st.plotly_chart(spc_chart, width="stretch", key="spc_integrity_chart")
    spc_columns = st.columns(3, border=True)
    spc_columns[0].metric("Signals in real series", spc_details["real_signal_count"])
    spc_columns[1].metric(
        "Signals after sanitisation", spc_details["sanitised_signal_count"]
    )
    spc_columns[2].metric(
        "Displayed variation reduction",
        f"{spc_details['variation_reduction_pct']:.1f}%",
    )
    if spc_details["hidden_signal_count"]:
        st.warning(spc_details["interpretation"], icon=":material/warning:")
    else:
        st.info(spc_details["interpretation"], icon=":material/info:")
    st.caption("Synthetic educational p-chart; no empirical process data is used.")

with tabs[3]:
    st.subheader("How internal failure can shift downstream")
    st.caption(
        "Choose hypothetical unit costs to see how reclassifying an internally detected "
        "defect changes where cost appears. Values are not calibrated to real operations."
    )
    input_columns = st.columns(3)
    units = input_columns[0].number_input(
        "Units produced",
        min_value=1000,
        max_value=1_000_000,
        value=10000,
        step=1000,
        key="units_produced",
    )
    internal_cost = input_columns[1].number_input(
        "Internal failure cost per defect (₹)",
        min_value=0.0,
        value=450.0,
        step=50.0,
        key="internal_cost",
    )
    external_cost = input_columns[2].number_input(
        "External failure cost per defect (₹)",
        min_value=0.0,
        value=3500.0,
        step=100.0,
        key="external_cost",
    )
    cost_config = CostConfig(
        units=int(units),
        actual_defect_rate=float(sim.actual_rate.iloc[-1]),
        hidden_fraction=hidden_fraction,
        internal_failure_cost=internal_cost,
        external_failure_cost=external_cost,
    )
    try:
        costs = estimate_cost_shift(cost_config)
    except ValueError as exc:
        st.error(f"The cost assumptions are invalid: {exc}", icon=":material/error:")
        st.stop()

    flow_columns = st.columns(3, border=True)
    flow_columns[0].markdown("**1. Internally detected**")
    flow_columns[0].metric("Defects", f"{costs['detected_internal_defects']:,.1f}")
    flow_columns[0].caption(
        f"Post-shift internal cost: ₹{costs['post_shift_internal_cost']:,.0f}"
    )
    flow_columns[1].markdown("**2. Hidden or reclassified**")
    flow_columns[1].metric("Defects shifted", f"{costs['shifted_defects']:,.1f}")
    flow_columns[1].caption(f"Selected share: {hidden_fraction:.0%}")
    flow_columns[2].markdown("**3. External exposure**")
    flow_columns[2].metric("Defects", f"{costs['external_defects']:,.1f}")
    flow_columns[2].caption(
        f"Post-shift external cost: ₹{costs['post_shift_external_cost']:,.0f}"
    )

    cost_summary_columns = st.columns(3)
    cost_summary_columns[0].metric(
        "Baseline quality cost", f"₹{costs['baseline_cost']:,.0f}"
    )
    cost_summary_columns[1].metric(
        "Quality cost after shifting", f"₹{costs['gaming_cost']:,.0f}"
    )
    cost_summary_columns[2].metric(
        "Incremental cost impact", f"₹{costs['incremental_cost']:,.0f}"
    )

    cost_chart = go.Figure()
    cost_chart.add_trace(
        go.Bar(
            name="Internal failure cost",
            x=["Before shifting", "After shifting"],
            y=[costs["baseline_internal_cost"], costs["post_shift_internal_cost"]],
            marker_color="#60A5FA",
            hovertemplate="%{x}<br>Internal: ₹%{y:,.0f}<extra></extra>",
        )
    )
    cost_chart.add_trace(
        go.Bar(
            name="External failure cost",
            x=["Before shifting", "After shifting"],
            y=[costs["baseline_external_cost"], costs["post_shift_external_cost"]],
            marker_color="#F87171",
            hovertemplate="%{x}<br>External: ₹%{y:,.0f}<extra></extra>",
        )
    )
    cost_chart.update_layout(
        barmode="stack",
        yaxis_title="Illustrative cost (₹)",
        legend={"orientation": "h", "y": 1.12, "x": 0},
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    st.plotly_chart(cost_chart, width="stretch", key="cost_of_quality_chart")
    if external_cost <= internal_cost:
        st.warning(
            "External failure cost is not higher than internal failure cost, so shifting "
            "failures downstream may not increase this simplified estimate."
        )

with tabs[4]:
    st.subheader("Audit the metric — not only the process")
    st.write(
        "Check each statement when it signals a risk in the metric's measurement system. "
        "Each checked question contributes one equally weighted risk signal."
    )
    answers: list[bool] = []
    for index, (title, detail) in enumerate(AUDIT_QUESTIONS):
        answers.append(
            st.checkbox(
                f"{index + 1}. {title} — {detail}",
                key=f"audit_question_{index}",
            )
        )

    audit = audit_result(answers)
    audit_details = audit_diagnostic(answers)
    audit_columns = st.columns([1, 2])
    with audit_columns[0].container(border=True, height="stretch"):
        st.metric(
            "Audit risk level",
            audit["risk_level"],
            f"{audit['risk_count']} of {len(AUDIT_QUESTIONS)} risk signals",
        )
        st.caption(audit["recommendation"])
    with audit_columns[1].container(border=True, height="stretch"):
        st.markdown("**Flagged risk signals**")
        if audit_details["flagged_questions"]:
            for flagged_question in audit_details["flagged_questions"]:
                st.markdown(f"- {flagged_question}")
        else:
            st.caption("No risk questions are currently selected.")

    st.markdown("**Recommended controls**")
    for recommendation in audit_details["recommendations"]:
        st.markdown(f"- {recommendation}")

    st.markdown("### Measure + Context + Behaviour")
    st.write(
        "**Measure:** define the number precisely and triangulate it.  \n"
        "**Context:** ask what changed in the process or reporting rule.  \n"
        "**Behaviour:** ask what the target rewards, discourages or makes easy to hide."
    )


def preset_definition(name: str) -> ScenarioDefinition:
    """Convert a named preset into a complete comparison definition."""
    preset = get_scenario_preset(name)
    return ScenarioDefinition(
        name=preset.name,
        simulation=SimulationConfig(
            baseline_defect_rate=preset.baseline_defect_rate,
            target_defect_rate=preset.target_defect_rate,
            target_pressure=preset.target_pressure,
            gaming_susceptibility=preset.gaming_susceptibility,
            genuine_improvement_per_month=preset.genuine_improvement_per_month,
            process_drift_per_month=preset.process_drift_per_month,
        ),
        vulnerability=MetricVulnerability(
            preset.single_metric_dependence,
            preset.stakes,
            preset.manipulability,
            preset.customer_link_weakness,
        ),
        spc=SPCConfig(sanitisation_strength=preset.spc_sanitisation_strength),
        hidden_fraction=preset.hidden_fraction,
        audit_answers=preset.audit_answers,
    )


current_definition = ScenarioDefinition(
    name=f"Current configuration ({selected_scenario})",
    simulation=simulation_config,
    vulnerability=vulnerability,
    spc=spc_config,
    hidden_fraction=hidden_fraction,
    audit_answers=tuple(answers),
)
comparison_options = ("Current configuration", *SCENARIO_PRESETS)

with st.expander(
    "Compare two scenarios",
    icon=":material/compare_arrows:",
    expanded=False,
):
    st.caption(
        "Compare two independently evaluated hypothetical configurations. Preset audit "
        "classifications use the documented risk answers embedded in each preset."
    )
    comparison_selectors = st.columns(2)
    scenario_a_choice = comparison_selectors[0].selectbox(
        "Scenario A",
        comparison_options,
        index=1,
        key="comparison_scenario_a",
    )
    scenario_b_choice = comparison_selectors[1].selectbox(
        "Scenario B",
        comparison_options,
        index=2,
        key="comparison_scenario_b",
    )
    scenario_a = (
        current_definition
        if scenario_a_choice == "Current configuration"
        else preset_definition(scenario_a_choice)
    )
    scenario_b = (
        current_definition
        if scenario_b_choice == "Current configuration"
        else preset_definition(scenario_b_choice)
    )
    try:
        comparison = compare_scenarios(
            scenario_a,
            scenario_b,
            ComparisonCostAssumptions(
                units=int(units),
                internal_failure_cost=float(internal_cost),
                external_failure_cost=float(external_cost),
            ),
        )
    except ValueError as exc:
        st.error(f"The scenarios could not be compared: {exc}", icon=":material/error:")
    else:
        result_a = comparison["scenario_a"]["results"]
        result_b = comparison["scenario_b"]["results"]
        delta = comparison["deltas"]
        comparison_metrics = st.columns(4, border=True)
        comparison_metrics[0].metric(
            "Scenario B integrity",
            f"{result_b['metric_integrity_score']:.1f}/100",
            f"{delta['metric_integrity_score']:+.1f} vs A",
        )
        comparison_metrics[1].metric(
            "Scenario B reported rate",
            f"{result_b['reported_defect_rate']:.2%}",
            f"{delta['reported_defect_rate'] * 100:+.2f} pp vs A",
            delta_color="inverse",
        )
        comparison_metrics[2].metric(
            "Scenario B reporting gap",
            f"{result_b['reporting_gap'] * 100:.2f} pp",
            f"{delta['reporting_gap'] * 100:+.2f} pp vs A",
            delta_color="inverse",
        )
        comparison_metrics[3].metric(
            "Scenario B suppressed signals",
            result_b["suppressed_spc_signals"],
            f"{delta['suppressed_spc_signals']:+d} vs A",
            delta_color="inverse",
        )

        rate_comparison = go.Figure()
        for label, results, color in (
            ("Scenario A", result_a, "#60A5FA"),
            ("Scenario B", result_b, "#A78BFA"),
        ):
            rate_comparison.add_trace(
                go.Bar(
                    name=label,
                    y=["Actual defect rate", "Reported defect rate", "Reporting gap"],
                    x=[
                        results["actual_defect_rate"] * 100,
                        results["reported_defect_rate"] * 100,
                        results["reporting_gap"] * 100,
                    ],
                    orientation="h",
                    marker_color=color,
                    hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
                )
            )
        rate_comparison.update_layout(
            barmode="group",
            xaxis_title="Rate or gap (percentage points)",
            yaxis_title=None,
            legend={"orientation": "h", "y": 1.15, "x": 0},
            height=300,
            margin={"l": 20, "r": 20, "t": 55, "b": 20},
        )
        st.plotly_chart(rate_comparison, width="stretch", key="scenario_comparison_chart")

        display_table = comparison_table(comparison).copy()
        for row_index, row in display_table.iterrows():
            unit = row["Unit"]
            for column in ("Scenario A", "Scenario B", "Delta (B − A)"):
                value = row[column]
                if isinstance(value, str):
                    formatted = value
                elif unit == "currency":
                    formatted = f"₹{float(value):,.0f}"
                elif unit in {"%", "pp"}:
                    formatted = f"{float(value):.2f}"
                elif unit == "points":
                    formatted = f"{float(value):.1f}"
                else:
                    formatted = str(int(value))
                display_table.at[row_index, column] = formatted
        st.dataframe(display_table, hide_index=True, width="stretch")
        st.info(comparison_interpretation(comparison), icon=":material/insights:")
        st.caption(
            "These contrasts arise from the selected hypothetical assumptions and do "
            "not establish intent, gaming, or misconduct."
        )

        comparison_slug = (
            f"{scenario_a_choice}-vs-{scenario_b_choice}".lower()
            .replace(" ", "-")
            .replace("/", "-")
        )
        with st.container(horizontal=True):
            st.download_button(
                "Download comparison (CSV)",
                comparison_summary_csv(comparison),
                file_name=f"quality-metrics-{comparison_slug}.csv",
                mime="text/csv",
                icon=":material/table_view:",
                on_click="ignore",
            )
            st.download_button(
                "Download comparison (JSON)",
                comparison_summary_json(comparison),
                file_name=f"quality-metrics-{comparison_slug}.json",
                mime="application/json",
                icon=":material/data_object:",
                on_click="ignore",
            )
            st.download_button(
                "Download comparison (Markdown)",
                comparison_summary_markdown(comparison),
                file_name=f"quality-metrics-{comparison_slug}.md",
                mime="text/markdown",
                icon=":material/description:",
                on_click="ignore",
            )


with st.expander(
    "Explore user-provided CSV data",
    icon=":material/upload_file:",
    expanded=False,
):
    st.subheader("Exploratory visualisation using user-provided data.")
    st.write(
        "Required columns are `period` and `reported_rate`. `actual_rate` and "
        "`target_rate` are optional. Rates must be decimal fractions from 0 to 1."
    )
    st.info(
        "Uploaded CSVs are processed within the active Streamlit session. Avoid "
        "uploading confidential or personally identifiable information. This tool is "
        "not a compliance, fraud-detection, or misconduct-detection system.",
        icon=":material/privacy_tip:",
    )
    with st.container(horizontal=True):
        st.download_button(
            "Download CSV template",
            CSV_TEMPLATE,
            file_name="quality_data_template.csv",
            mime="text/csv",
            icon=":material/download:",
            on_click="ignore",
        )
        st.download_button(
            "Download synthetic demo data",
            (Path(__file__).parent / "data" / "sample_quality_mirage.csv").read_text(
                encoding="utf-8"
            ),
            file_name="sample_quality_mirage.csv",
            mime="text/csv",
            icon=":material/download:",
            on_click="ignore",
        )
    st.caption(
        "The demo dataset is synthetic, exists only for demonstration, and does not "
        "represent any real company."
    )
    uploaded_csv = st.file_uploader(
        "Upload quality time series",
        type=["csv"],
        key="quality_csv_upload",
        help="The file is validated exactly as supplied; malformed values are not repaired.",
    )
    if uploaded_csv is None:
        st.caption(
            "No file selected. Upload a CSV to validate and chart it, or use one "
            "of the download buttons above to inspect the expected format."
        )
    else:
        try:
            imported = validate_quality_csv(uploaded_csv.getvalue())
            chart_series = imported_chart_series(imported)
        except CSVValidationError as exc:
            st.error(f"CSV validation failed: {exc}", icon=":material/error:")
        else:
            imported_chart = go.Figure()
            colors = {
                "Actual defect rate": "#F87171",
                "Reported defect rate": "#60A5FA",
                "Target reference": "#CBD5E1",
            }
            for series_name in chart_series["series"].drop_duplicates():
                series = chart_series[chart_series["series"] == series_name]
                imported_chart.add_trace(
                    go.Scatter(
                        x=series["period"],
                        y=series["rate"] * 100,
                        mode="lines+markers" if series_name != "Target reference" else "lines",
                        name=series_name,
                        line={
                            "color": colors[series_name],
                            "width": 3 if series_name != "Target reference" else 2,
                            "dash": "dot" if series_name == "Target reference" else "solid",
                        },
                        hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
                    )
                )
            imported_chart.update_layout(
                xaxis_title="Period (uploaded order)",
                yaxis_title="Rate (%)",
                hovermode="x unified",
                legend={"orientation": "h", "y": 1.12, "x": 0},
                margin={"l": 20, "r": 20, "t": 55, "b": 20},
            )
            st.plotly_chart(imported_chart, width="stretch", key="imported_quality_chart")
            st.info(imported_data_interpretation(imported), icon=":material/insights:")
            st.caption(
                "The chart describes user-supplied values. It does not validate the "
                "data or infer manipulation, intent, or misconduct."
            )


with st.expander("About and methodology", icon=":material/menu_book:"):
    st.markdown(
        """
**Goodhart's Law in this project:** when a quality measure becomes a high-stakes
target, behaviour around measurement can make the reported number less representative
of the underlying process.

**Quality Mirage:** the simulated reporting gap between actual underlying defects and
reported defects. Classification, timing, and sampling divide that illustrative gap.

**Metric Integrity Score:** a transparent 0–100 heuristic based on single-metric
dependence, stakes, manipulability, and weak customer linkage. It is not a validated
index.

**Major assumptions:** monthly process change is linear apart from seeded random noise;
gaming pressure matures gradually; p-chart observations are synthetic binomial draws;
and shifted internal failures are treated as external exposure in the cost illustration.

**Limitations:** the app cannot establish intent, forecast operational performance,
validate a KPI, or replace an independent quality or compliance audit. All scenarios and
outputs are hypothetical. Imported datasets remain the user's responsibility and are
used only for exploratory visualisation.

**Academic foundations:** the framing is informed by Goodhart and subsequent
performance-measurement literature, including Mattson, Bushardt & Artino (2021),
Elton (2004), Fisher (2021), Fisher & Kordupleski (2019), and the Deming Institute's
System of Profound Knowledge. These sources motivate questions about measurement;
they do not validate this app's coefficients or outputs.

- Goodhart, C. A. E. (1975). *Problems of Monetary Management: The U.K. Experience.*
- Mattson, B. W., Bushardt, R. L., & Artino, A. R. Jr. (2021). [When a Measure
  Becomes a Target, It Ceases to Be a Good Measure](https://doi.org/10.4300/JGME-D-20-01492.1).
- Elton, L. (2004). [Goodhart's Law and Performance Indicators in Higher
  Education](https://doi.org/10.1080/09500790408668312).
- Fisher, N. I. (2021). [Performance Measurement: Issues, Approaches, and
  Opportunities](https://doi.org/10.1162/99608f92.c28d2a68).
- Fisher, N. I., & Kordupleski, R. E. (2019). [Good and Bad Market Research: A
  Critical Review of Net Promoter Score](https://doi.org/10.1002/asmb.2417).
- The W. Edwards Deming Institute. [The Deming System of Profound
  Knowledge](https://deming.org/explore/sopk/).
"""
    )


try:
    export_summary = build_scenario_summary(
        scenario_name=selected_scenario,
        simulation_config=simulation_config,
        vulnerability=vulnerability,
        simulation=sim,
        integrity=integrity,
        integrity_diagnostic=integrity_details,
        spc_config=spc_config,
        spc_limits=limits,
        spc_diagnostic=spc_details,
        cost_config=cost_config,
        cost_result=costs,
        audit=audit,
        audit_diagnostic=audit_details,
    )
    csv_export = scenario_results_csv(sim)
    json_export = scenario_summary_json(export_summary)
    markdown_export = scenario_summary_markdown(export_summary)
except ValueError as exc:
    st.error(f"The current scenario could not be exported: {exc}")
else:
    scenario_slug = selected_scenario.lower().replace(" ", "-")
    with st.expander("Export current scenario", icon=":material/download:"):
        st.caption(
            "Exports contain the current hypothetical inputs and results. They retain "
            "the educational-use disclaimer."
        )
        with st.container(horizontal=True):
            st.download_button(
                "Download monthly results (CSV)",
                csv_export,
                file_name=f"quality-metrics-{scenario_slug}.csv",
                mime="text/csv",
                icon=":material/table_view:",
                on_click="ignore",
            )
            st.download_button(
                "Download scenario summary (JSON)",
                json_export,
                file_name=f"quality-metrics-{scenario_slug}.json",
                mime="application/json",
                icon=":material/data_object:",
                on_click="ignore",
            )
            st.download_button(
                "Download concise summary (Markdown)",
                markdown_export,
                file_name=f"quality-metrics-{scenario_slug}.md",
                mime="text/markdown",
                icon=":material/description:",
                on_click="ignore",
            )
