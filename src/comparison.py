"""Deterministic side-by-side evaluation of educational scenarios."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import pandas as pd

from src.cost_of_quality import CostConfig, estimate_cost_shift
from src.diagnostics import metric_integrity_diagnostic, spc_diagnostic
from src.metric_integrity import MetricVulnerability, integrity_score
from src.recommendations import audit_diagnostic, audit_result
from src.simulation_engine import SimulationConfig, simulate_quality_path
from src.spc_engine import SPCConfig, simulate_p_chart
from src.validation import integer_at_least, non_negative


@dataclass(frozen=True)
class ComparisonCostAssumptions:
    """Shared hypothetical cost assumptions used for both scenarios."""

    units: int = 10_000
    internal_detection_rate: float = 0.85
    internal_failure_cost: float = 450.0
    external_failure_cost: float = 3_500.0


@dataclass(frozen=True)
class ScenarioDefinition:
    """All inputs needed to evaluate one scenario without Streamlit state."""

    name: str
    simulation: SimulationConfig
    vulnerability: MetricVulnerability
    spc: SPCConfig
    hidden_fraction: float
    audit_answers: tuple[bool, ...]


def evaluate_scenario(
    scenario: ScenarioDefinition,
    cost_assumptions: ComparisonCostAssumptions,
) -> dict[str, Any]:
    """Evaluate one complete scenario using the existing model modules."""
    if not scenario.name.strip():
        raise ValueError("Scenario name cannot be empty.")
    units = integer_at_least("units", cost_assumptions.units, 0)
    internal_cost = non_negative(
        "internal_failure_cost", cost_assumptions.internal_failure_cost
    )
    external_cost = non_negative(
        "external_failure_cost", cost_assumptions.external_failure_cost
    )

    simulation = simulate_quality_path(scenario.simulation)
    integrity = integrity_score(scenario.vulnerability)
    integrity_details = metric_integrity_diagnostic(scenario.vulnerability, integrity)
    spc_data, spc_limits = simulate_p_chart(scenario.spc)
    spc_details = spc_diagnostic(spc_data, spc_limits)
    audit = audit_result(scenario.audit_answers)
    audit_details = audit_diagnostic(scenario.audit_answers)
    final = simulation.iloc[-1]
    cost_config = CostConfig(
        units=units,
        actual_defect_rate=float(final["actual_rate"]),
        internal_detection_rate=cost_assumptions.internal_detection_rate,
        hidden_fraction=scenario.hidden_fraction,
        internal_failure_cost=internal_cost,
        external_failure_cost=external_cost,
    )
    costs = estimate_cost_shift(cost_config)

    return {
        "name": scenario.name,
        "inputs": {
            "simulation": asdict(scenario.simulation),
            "metric_vulnerability": asdict(scenario.vulnerability),
            "spc": asdict(scenario.spc),
            "hidden_fraction": scenario.hidden_fraction,
            "audit_answers": list(scenario.audit_answers),
            "cost": asdict(cost_config),
        },
        "results": {
            "metric_integrity_score": integrity["integrity_score"],
            "risk_classification": integrity_details["classification"],
            "actual_defect_rate": float(final["actual_rate"]),
            "reported_defect_rate": float(final["reported_rate"]),
            "reporting_gap": float(final["reporting_gap"]),
            "classification_contribution": float(final["classification_gap"]),
            "timing_contribution": float(final["timing_gap"]),
            "sampling_contribution": float(final["sampling_gap"]),
            "spc_signal_count": spc_details["real_signal_count"],
            "suppressed_spc_signals": spc_details["hidden_signal_count"],
            "estimated_internal_failure_cost": costs["post_shift_internal_cost"],
            "estimated_external_failure_cost": costs["post_shift_external_cost"],
            "metric_audit_classification": audit["risk_level"],
            "metric_audit_risk_count": audit["risk_count"],
        },
        "audit": {**audit, **audit_details},
    }


_DELTA_FIELDS = (
    "metric_integrity_score",
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
    "metric_audit_risk_count",
)


def compare_scenarios(
    scenario_a: ScenarioDefinition,
    scenario_b: ScenarioDefinition,
    cost_assumptions: ComparisonCostAssumptions | None = None,
) -> dict[str, Any]:
    """Return complete results and numeric deltas, defined as scenario B minus A."""
    assumptions = cost_assumptions or ComparisonCostAssumptions()
    result_a = evaluate_scenario(scenario_a, assumptions)
    result_b = evaluate_scenario(scenario_b, assumptions)
    deltas = {
        field: result_b["results"][field] - result_a["results"][field]
        for field in _DELTA_FIELDS
    }
    return {
        "schema_version": 1,
        "delta_definition": "Scenario B minus Scenario A",
        "shared_cost_assumptions": asdict(assumptions),
        "scenario_a": result_a,
        "scenario_b": result_b,
        "deltas": deltas,
    }


def comparison_interpretation(comparison: Mapping[str, Any]) -> str:
    """Describe the most visible contrast without inferring intent or misconduct."""
    a = comparison["scenario_a"]["results"]
    b = comparison["scenario_b"]["results"]
    if (
        b["reported_defect_rate"] < a["reported_defect_rate"]
        and b["reporting_gap"] > a["reporting_gap"]
    ):
        return (
            "Scenario B reports stronger KPI performance but exhibits a larger "
            "measurement-integrity gap."
        )
    if b["reporting_gap"] > a["reporting_gap"]:
        return "Scenario B has a larger simulated reporting gap than Scenario A."
    if b["reporting_gap"] < a["reporting_gap"]:
        return "Scenario B has a smaller simulated reporting gap than Scenario A."
    return "The two scenarios have the same final simulated reporting gap."


def comparison_table(comparison: Mapping[str, Any]) -> pd.DataFrame:
    """Build a compact presentation table with explicit units and B-minus-A deltas."""
    a = comparison["scenario_a"]["results"]
    b = comparison["scenario_b"]["results"]
    deltas = comparison["deltas"]
    rows: Sequence[tuple[str, str, float | int | str, float | int | str, Any]] = (
        ("Metric integrity score", "points", a["metric_integrity_score"], b["metric_integrity_score"], deltas["metric_integrity_score"]),
        ("Risk classification", "class", a["risk_classification"], b["risk_classification"], "n.a."),
        ("Actual defect rate", "%", a["actual_defect_rate"] * 100, b["actual_defect_rate"] * 100, deltas["actual_defect_rate"] * 100),
        ("Reported defect rate", "%", a["reported_defect_rate"] * 100, b["reported_defect_rate"] * 100, deltas["reported_defect_rate"] * 100),
        ("Reporting gap", "pp", a["reporting_gap"] * 100, b["reporting_gap"] * 100, deltas["reporting_gap"] * 100),
        ("Classification contribution", "pp", a["classification_contribution"] * 100, b["classification_contribution"] * 100, deltas["classification_contribution"] * 100),
        ("Timing contribution", "pp", a["timing_contribution"] * 100, b["timing_contribution"] * 100, deltas["timing_contribution"] * 100),
        ("Sampling contribution", "pp", a["sampling_contribution"] * 100, b["sampling_contribution"] * 100, deltas["sampling_contribution"] * 100),
        ("SPC signal count", "count", a["spc_signal_count"], b["spc_signal_count"], deltas["spc_signal_count"]),
        ("Suppressed SPC signals", "count", a["suppressed_spc_signals"], b["suppressed_spc_signals"], deltas["suppressed_spc_signals"]),
        ("Estimated internal failure cost", "currency", a["estimated_internal_failure_cost"], b["estimated_internal_failure_cost"], deltas["estimated_internal_failure_cost"]),
        ("Estimated external/downstream cost", "currency", a["estimated_external_failure_cost"], b["estimated_external_failure_cost"], deltas["estimated_external_failure_cost"]),
        ("Metric Audit classification", "class", a["metric_audit_classification"], b["metric_audit_classification"], "n.a."),
    )
    return pd.DataFrame(rows, columns=["Metric", "Unit", "Scenario A", "Scenario B", "Delta (B − A)"])
