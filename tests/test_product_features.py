from io import StringIO
import json

import numpy as np
import pandas as pd
import pytest

from src.cost_of_quality import CostConfig, estimate_cost_shift
from src.diagnostics import (
    metric_integrity_diagnostic,
    quality_mirage_interpretation,
    spc_diagnostic,
)
from src.exports import (
    DISCLAIMER,
    build_scenario_summary,
    scenario_results_csv,
    scenario_summary_json,
    scenario_summary_markdown,
)
from src.metric_integrity import MetricVulnerability, integrity_score
from src.recommendations import audit_diagnostic, audit_result
from src.scenarios import (
    CUSTOM_SCENARIO,
    SCENARIO_PRESETS,
    get_scenario_preset,
    scenario_names,
)
from src.simulation_engine import SimulationConfig, simulate_quality_path
from src.spc_engine import SPCConfig, simulate_p_chart


def test_scenario_catalog_contains_custom_and_expected_presets():
    assert scenario_names() == (
        CUSTOM_SCENARIO,
        "Healthy Measurement System",
        "High-Pressure Defect Target",
        "Gaming-Prone KPI",
        "Customer-Disconnected KPI",
    )
    assert all(preset.description.endswith(".") for preset in SCENARIO_PRESETS.values())
    assert all(len(preset.audit_answers) == 5 for preset in SCENARIO_PRESETS.values())
    assert all(
        all(type(answer) is bool for answer in preset.audit_answers)
        for preset in SCENARIO_PRESETS.values()
    )


@pytest.mark.parametrize("preset", SCENARIO_PRESETS.values(), ids=lambda item: item.name)
def test_presets_produce_valid_deterministic_model_inputs(preset):
    config = SimulationConfig(
        baseline_defect_rate=preset.baseline_defect_rate,
        target_defect_rate=preset.target_defect_rate,
        target_pressure=preset.target_pressure,
        gaming_susceptibility=preset.gaming_susceptibility,
        genuine_improvement_per_month=preset.genuine_improvement_per_month,
        process_drift_per_month=preset.process_drift_per_month,
    )
    vulnerability = MetricVulnerability(
        preset.single_metric_dependence,
        preset.stakes,
        preset.manipulability,
        preset.customer_link_weakness,
    )

    pd.testing.assert_frame_equal(
        simulate_quality_path(config), simulate_quality_path(config)
    )
    assert 0.0 <= integrity_score(vulnerability)["integrity_score"] <= 100.0
    simulate_p_chart(
        SPCConfig(sanitisation_strength=preset.spc_sanitisation_strength)
    )
    widget_state = preset.as_widget_state()
    assert widget_state["baseline_pct"] == preset.baseline_defect_rate * 100
    assert widget_state["pressure_pct"] == round(preset.target_pressure * 100)
    assert widget_state["spc_sanitisation_pct"] == round(
        preset.spc_sanitisation_strength * 100
    )


def test_unknown_scenario_is_rejected():
    with pytest.raises(ValueError, match="Unknown scenario preset"):
        get_scenario_preset("Not a scenario")


def test_metric_integrity_diagnostic_identifies_driver_extremes():
    vulnerability = MetricVulnerability(0.4, 0.9, 0.7, 0.2)
    diagnostic = metric_integrity_diagnostic(vulnerability)

    assert diagnostic["strongest_driver"] == "High-stakes consequences"
    assert diagnostic["strongest_value"] == 0.9
    assert diagnostic["weakest_driver"] == "Weak customer linkage"
    assert diagnostic["weakest_value"] == 0.2
    assert diagnostic["classification"] in {"Strong", "Watch", "Fragile", "High risk"}
    assert diagnostic["explanation"]


def test_quality_mirage_interpretation_handles_alignment_and_divergence():
    aligned = simulate_quality_path(SimulationConfig(target_pressure=0.0))
    divergent = simulate_quality_path(
        SimulationConfig(
            target_pressure=1.0,
            gaming_susceptibility=1.0,
            genuine_improvement_per_month=0.0,
            process_drift_per_month=0.001,
            noise_sd=0.0,
        )
    )

    assert "remain aligned" in quality_mirage_interpretation(aligned)
    assert "underlying process does not" in quality_mirage_interpretation(divergent)


def test_spc_diagnostic_quantifies_compression_and_hidden_signals():
    data, limits = simulate_p_chart(SPCConfig(sanitisation_strength=1.0))
    diagnostic = spc_diagnostic(data, limits)

    assert diagnostic["variation_reduction_pct"] == 100.0
    assert diagnostic["sanitised_signal_count"] == 0
    assert diagnostic["hidden_signal_count"] == diagnostic["real_signal_count"]
    assert diagnostic["interpretation"]


@pytest.mark.parametrize("risk_count", range(6))
def test_audit_diagnostic_returns_two_to_four_recommendations(risk_count):
    answers = [True] * risk_count + [False] * (5 - risk_count)
    diagnostic = audit_diagnostic(answers)

    assert len(diagnostic["flagged_questions"]) == risk_count
    assert 2 <= len(diagnostic["recommendations"]) <= 4


def test_csv_export_has_expected_fields_and_is_deterministic():
    simulation = simulate_quality_path(SimulationConfig(seed=99))
    first = scenario_results_csv(simulation)
    second = scenario_results_csv(simulation)
    parsed = pd.read_csv(StringIO(first))

    assert first == second
    assert list(parsed.columns) == [
        "month",
        "actual_defect_rate",
        "reported_defect_rate",
        "target_defect_rate",
        "classification_gap",
        "timing_gap",
        "sampling_gap",
        "reporting_gap",
    ]
    assert len(parsed) == 12


def test_summary_exports_include_expected_fields_and_disclaimer():
    config = SimulationConfig(seed=11)
    vulnerability = MetricVulnerability(0.7, 0.8, 0.65, 0.55)
    simulation = simulate_quality_path(config)
    integrity = integrity_score(vulnerability)
    diagnostic = metric_integrity_diagnostic(vulnerability, integrity)
    audit = audit_result([True, False, True, False, False])
    audit_details = audit_diagnostic([True, False, True, False, False])
    spc_config = SPCConfig(sanitisation_strength=0.5)
    spc_data, spc_limits = simulate_p_chart(spc_config)
    spc_details = spc_diagnostic(spc_data, spc_limits)
    cost_config = CostConfig()
    cost_result = estimate_cost_shift(cost_config)
    summary = build_scenario_summary(
        scenario_name="Custom",
        simulation_config=config,
        vulnerability=vulnerability,
        simulation=simulation,
        integrity=integrity,
        integrity_diagnostic=diagnostic,
        spc_config=spc_config,
        spc_limits=spc_limits,
        spc_diagnostic=spc_details,
        cost_config=cost_config,
        cost_result=cost_result,
        audit=audit,
        audit_diagnostic=audit_details,
    )

    json_text = scenario_summary_json(summary)
    markdown_text = scenario_summary_markdown(summary)
    parsed = json.loads(json_text)

    assert parsed["product"] == "Quality Metrics Integrity Lab"
    assert parsed["schema_version"] == 1
    assert parsed["disclaimer"] == DISCLAIMER
    assert set(parsed) == {
        "schema_version",
        "product",
        "scenario",
        "disclaimer",
        "inputs",
        "metric_integrity",
        "final_results",
        "gaming_mechanisms",
        "spc_integrity",
        "cost_of_quality",
        "metric_audit",
    }
    assert set(parsed["gaming_mechanisms"]) == {
        "classification_gap",
        "timing_gap",
        "sampling_gap",
    }
    assert "diagnostic" in parsed["spc_integrity"]
    assert "incremental_cost" in parsed["cost_of_quality"]["result"]
    assert len(parsed["metric_audit"]["recommendations"]) >= 2
    assert "Educational simulation only" in markdown_text
    assert scenario_summary_json(summary) == json_text
