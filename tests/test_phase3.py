from io import StringIO
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.comparison import (
    ComparisonCostAssumptions,
    ScenarioDefinition,
    compare_scenarios,
    comparison_interpretation,
    comparison_table,
)
from src.exports import (
    DISCLAIMER,
    comparison_summary_csv,
    comparison_summary_json,
    comparison_summary_markdown,
)
from src.imported_data import (
    CSV_TEMPLATE,
    CSVValidationError,
    imported_chart_series,
    imported_data_interpretation,
    validate_quality_csv,
)
from src.metric_integrity import MetricVulnerability
from src.scenarios import get_scenario_preset
from src.simulation_engine import SimulationConfig
from src.spc_engine import SPCConfig


ROOT = Path(__file__).parents[1]


def _definition(name: str) -> ScenarioDefinition:
    preset = get_scenario_preset(name)
    return ScenarioDefinition(
        name=name,
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


@pytest.fixture
def comparison():
    return compare_scenarios(
        _definition("Healthy Measurement System"),
        _definition("High-Pressure Defect Target"),
        ComparisonCostAssumptions(),
    )


def test_comparison_contains_required_results(comparison):
    required = {
        "metric_integrity_score",
        "risk_classification",
        "actual_defect_rate",
        "reported_defect_rate",
        "reporting_gap",
        "classification_contribution",
        "timing_contribution",
        "sampling_contribution",
        "spc_signal_count",
        "suppressed_spc_signals",
        "estimated_internal_failure_cost",
        "estimated_external_failure_cost",
        "metric_audit_classification",
        "metric_audit_risk_count",
    }
    assert set(comparison["scenario_a"]["results"]) == required
    assert set(comparison["scenario_b"]["results"]) == required


def test_comparison_deltas_are_b_minus_a(comparison):
    a = comparison["scenario_a"]["results"]
    b = comparison["scenario_b"]["results"]
    for key, value in comparison["deltas"].items():
        assert value == pytest.approx(b[key] - a[key])


def test_comparison_is_deterministic():
    a = _definition("Healthy Measurement System")
    b = _definition("Gaming-Prone KPI")
    assert compare_scenarios(a, b) == compare_scenarios(a, b)


def test_comparison_table_has_all_requested_rows(comparison):
    table = comparison_table(comparison)
    assert len(table) == 13
    assert list(table.columns) == [
        "Metric",
        "Unit",
        "Scenario A",
        "Scenario B",
        "Delta (B − A)",
    ]
    assert "Metric Audit classification" in set(table["Metric"])


def test_comparison_interpretation_is_restrained(comparison):
    interpretation = comparison_interpretation(comparison)
    assert "Scenario B reports stronger KPI performance" in interpretation
    assert "misconduct" not in interpretation.lower()


def test_comparison_rejects_invalid_shared_cost_assumptions():
    with pytest.raises(ValueError, match="non-negative"):
        compare_scenarios(
            _definition("Healthy Measurement System"),
            _definition("Gaming-Prone KPI"),
            ComparisonCostAssumptions(internal_failure_cost=-1.0),
        )


def test_comparison_exports_are_deterministic_and_disclaimed(comparison):
    csv_text = comparison_summary_csv(comparison)
    json_text = comparison_summary_json(comparison)
    markdown_text = comparison_summary_markdown(comparison)

    assert comparison_summary_csv(comparison) == csv_text
    assert comparison_summary_json(comparison) == json_text
    assert comparison_summary_markdown(comparison) == markdown_text
    assert DISCLAIMER in csv_text
    assert json.loads(json_text)["disclaimer"] == DISCLAIMER
    assert DISCLAIMER in markdown_text
    parsed_csv = pd.read_csv(StringIO(csv_text))
    assert {"input", "result"} == set(parsed_csv["section"])
    assert parsed_csv["scenario_a_name"].nunique() == 1
    assert parsed_csv["scenario_b_name"].nunique() == 1


def test_valid_template_import():
    imported = validate_quality_csv(CSV_TEMPLATE)
    assert len(imported.frame) == 3
    assert imported.has_actual_rate
    assert imported.has_target_rate
    assert imported.can_compute_reporting_gap


def test_csv_without_optional_columns_is_valid_and_does_not_fabricate_actual():
    imported = validate_quality_csv("period,reported_rate\nP1,0.02\nP2,0.01\n")
    assert not imported.has_actual_rate
    assert not imported.has_target_rate
    assert list(imported.frame.columns) == ["period", "reported_rate"]
    assert "cannot be computed" in imported_data_interpretation(imported)


def test_optional_target_rate_is_supported_without_actual_rate():
    imported = validate_quality_csv(
        "period,reported_rate,target_rate\nP1,0.02,0.01\nP2,0.015,0.01\n"
    )
    assert imported.has_target_rate
    assert not imported.has_actual_rate
    assert set(imported_chart_series(imported)["series"]) == {
        "Reported defect rate",
        "Target reference",
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("", "empty"),
        ("period,actual_rate\nP1,0.02\n", "reported_rate"),
        ("period,reported_rate,secret\nP1,0.02,x\n", "Unsupported"),
        ("period,reported_rate\nP1,not-a-number\n", "only numbers"),
        ("period,reported_rate\nP1,nan\n", "missing or infinite"),
        ("period,reported_rate\nP1,inf\n", "missing or infinite"),
        ("period,reported_rate\nP1,1.1\n", "0 to 1"),
        ("period,reported_rate\nP1,-0.1\n", "0 to 1"),
        ("period,reported_rate\n,0.1\n", "non-empty period"),
        ("period,reported_rate\nP1,0.1\nP1,0.2\n", "unique"),
        ("period,period,reported_rate\nP1,P1,0.1\n", "unique"),
    ],
)
def test_invalid_csv_is_rejected(payload, message):
    with pytest.raises(CSVValidationError, match=message):
        validate_quality_csv(payload)


def test_import_preserves_period_order_and_chart_series():
    imported = validate_quality_csv(
        "period,actual_rate,reported_rate\nQ3,0.03,0.02\nQ1,0.02,0.01\nQ2,0.025,0.015\n"
    )
    assert imported.frame["period"].tolist() == ["Q3", "Q1", "Q2"]
    chart = imported_chart_series(imported)
    assert chart.groupby("series", sort=False)["period"].apply(list).tolist() == [
        ["Q3", "Q1", "Q2"],
        ["Q3", "Q1", "Q2"],
    ]
    assert np.isfinite(chart["rate"]).all()


def test_imported_data_interpretation_uses_actual_minus_reported():
    imported = validate_quality_csv(
        "period,actual_rate,reported_rate\nP1,0.03,0.02\n"
    )
    assert "1.00 percentage points" in imported_data_interpretation(imported)
    assert "not evidence" in imported_data_interpretation(imported)


def test_synthetic_sample_dataset_is_valid_and_shows_quality_mirage():
    sample_path = ROOT / "data" / "sample_quality_mirage.csv"
    imported = validate_quality_csv(sample_path.read_bytes())
    data = imported.frame
    assert len(data) == 12
    assert data["actual_rate"].iloc[-1] > data["actual_rate"].iloc[0]
    assert data["reported_rate"].iloc[-1] < data["reported_rate"].iloc[0]
    assert (data["actual_rate"] >= data["reported_rate"]).all()


def test_template_file_matches_downloadable_template():
    assert (ROOT / "data" / "quality_data_template.csv").read_text(
        encoding="utf-8"
    ) == CSV_TEMPLATE
