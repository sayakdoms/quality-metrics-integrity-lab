"""Deterministic exports for the current educational scenario."""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Mapping

import pandas as pd

from src.cost_of_quality import CostConfig, CostShiftResult
from src.metric_integrity import MetricIntegrityResult, MetricVulnerability
from src.recommendations import AuditDiagnostic, AuditResult
from src.simulation_engine import SimulationConfig
from src.spc_engine import SPCConfig


DISCLAIMER = (
    "Educational simulation only; outputs are hypothetical and are not empirical "
    "forecasts, compliance findings, or audit conclusions."
)


def scenario_results_csv(simulation: pd.DataFrame) -> str:
    """Return the monthly model results as a stable, human-readable CSV string."""
    columns = {
        "month": "month",
        "actual_rate": "actual_defect_rate",
        "reported_rate": "reported_defect_rate",
        "target_rate": "target_defect_rate",
        "classification_gap": "classification_gap",
        "timing_gap": "timing_gap",
        "sampling_gap": "sampling_gap",
        "reporting_gap": "reporting_gap",
    }
    missing = set(columns) - set(simulation.columns)
    if simulation.empty or missing:
        raise ValueError("Simulation output is empty or missing required export fields.")
    export = simulation[list(columns)].rename(columns=columns)
    return export.to_csv(index=False, float_format="%.8f", lineterminator="\n")


def build_scenario_summary(
    *,
    scenario_name: str,
    simulation_config: SimulationConfig,
    vulnerability: MetricVulnerability,
    simulation: pd.DataFrame,
    integrity: MetricIntegrityResult,
    integrity_diagnostic: Mapping[str, Any],
    spc_config: SPCConfig,
    spc_limits: Mapping[str, float],
    spc_diagnostic: Mapping[str, Any],
    cost_config: CostConfig,
    cost_result: CostShiftResult,
    audit: AuditResult,
    audit_diagnostic: AuditDiagnostic,
) -> dict[str, Any]:
    """Build a JSON-serialisable snapshot without timestamps or random metadata."""
    if not scenario_name.strip():
        raise ValueError("scenario_name cannot be empty.")
    if simulation.empty:
        raise ValueError("Simulation output cannot be empty.")
    final = simulation.iloc[-1]
    return {
        "schema_version": 1,
        "product": "Quality Metrics Integrity Lab",
        "scenario": scenario_name,
        "disclaimer": DISCLAIMER,
        "inputs": {
            "simulation": asdict(simulation_config),
            "metric_vulnerability": asdict(vulnerability),
        },
        "metric_integrity": {
            **integrity,
            "strongest_driver": integrity_diagnostic["strongest_driver"],
            "weakest_driver": integrity_diagnostic["weakest_driver"],
        },
        "final_results": {
            "month": int(final["month"]),
            "actual_defect_rate": float(final["actual_rate"]),
            "reported_defect_rate": float(final["reported_rate"]),
            "target_defect_rate": float(final["target_rate"]),
            "reporting_gap": float(final["reporting_gap"]),
        },
        "gaming_mechanisms": {
            "classification_gap": float(final["classification_gap"]),
            "timing_gap": float(final["timing_gap"]),
            "sampling_gap": float(final["sampling_gap"]),
        },
        "spc_integrity": {
            "config": asdict(spc_config),
            "limits": dict(spc_limits),
            "diagnostic": dict(spc_diagnostic),
        },
        "cost_of_quality": {
            "config": asdict(cost_config),
            "result": dict(cost_result),
        },
        "metric_audit": {
            **audit,
            **audit_diagnostic,
        },
    }


def scenario_summary_json(summary: Mapping[str, Any]) -> str:
    """Serialise a scenario summary deterministically."""
    return json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def scenario_summary_markdown(summary: Mapping[str, Any]) -> str:
    """Render a concise portable Markdown summary."""
    integrity = summary["metric_integrity"]
    final = summary["final_results"]
    audit = summary["metric_audit"]
    return (
        "# Quality Metrics Integrity Lab — Scenario Summary\n\n"
        f"**Scenario:** {summary['scenario']}\n\n"
        f"- Metric integrity: {integrity['integrity_score']}/100 "
        f"({integrity['label']})\n"
        f"- Strongest vulnerability: {integrity['strongest_driver']}\n"
        f"- Final actual defect rate: {final['actual_defect_rate']:.2%}\n"
        f"- Final reported defect rate: {final['reported_defect_rate']:.2%}\n"
        f"- Final reporting gap: {final['reporting_gap'] * 100:.2f} pp\n"
        f"- Metric audit risk: {audit['risk_level']} "
        f"({audit['risk_count']} signals)\n\n"
        f"> {summary['disclaimer']}\n"
    )


def comparison_summary_json(comparison: Mapping[str, Any]) -> str:
    """Serialise comparison results with the educational disclaimer."""
    payload = dict(comparison)
    payload["product"] = "Quality Metrics Integrity Lab"
    payload["disclaimer"] = DISCLAIMER
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def comparison_summary_csv(comparison: Mapping[str, Any]) -> str:
    """Return a stable long-form comparison export with inputs, results and deltas."""
    a = comparison["scenario_a"]
    b = comparison["scenario_b"]
    rows: list[dict[str, Any]] = []

    def add_row(section: str, metric: str, value_a: Any, value_b: Any, delta: Any = "") -> None:
        rows.append(
            {
                "section": section,
                "metric": metric,
                "scenario_a_name": a["name"],
                "scenario_a_value": value_a,
                "scenario_b_name": b["name"],
                "scenario_b_value": value_b,
                "delta_b_minus_a": delta,
                "disclaimer": DISCLAIMER,
            }
        )

    for group in ("simulation", "metric_vulnerability", "spc", "cost"):
        keys = sorted(set(a["inputs"][group]) | set(b["inputs"][group]))
        for key in keys:
            add_row("input", f"{group}.{key}", a["inputs"][group].get(key), b["inputs"][group].get(key))
    for key in ("hidden_fraction", "audit_answers"):
        add_row("input", key, a["inputs"][key], b["inputs"][key])
    for key in sorted(set(a["results"]) | set(b["results"])):
        add_row(
            "result",
            key,
            a["results"].get(key),
            b["results"].get(key),
            comparison["deltas"].get(key, ""),
        )
    return pd.DataFrame(rows).to_csv(index=False, float_format="%.8f", lineterminator="\n")


def comparison_summary_markdown(comparison: Mapping[str, Any]) -> str:
    """Render a concise deterministic comparison summary."""
    a = comparison["scenario_a"]
    b = comparison["scenario_b"]
    delta = comparison["deltas"]
    return (
        "# Quality Metrics Integrity Lab — Scenario Comparison\n\n"
        f"**Scenario A:** {a['name']}  \n"
        f"**Scenario B:** {b['name']}  \n"
        "**Delta convention:** Scenario B minus Scenario A\n\n"
        "| Measure | Scenario A | Scenario B | Delta |\n"
        "|---|---:|---:|---:|\n"
        f"| Metric integrity score | {a['results']['metric_integrity_score']:.1f} | "
        f"{b['results']['metric_integrity_score']:.1f} | {delta['metric_integrity_score']:+.1f} |\n"
        f"| Actual defect rate | {a['results']['actual_defect_rate']:.2%} | "
        f"{b['results']['actual_defect_rate']:.2%} | {delta['actual_defect_rate'] * 100:+.2f} pp |\n"
        f"| Reported defect rate | {a['results']['reported_defect_rate']:.2%} | "
        f"{b['results']['reported_defect_rate']:.2%} | {delta['reported_defect_rate'] * 100:+.2f} pp |\n"
        f"| Reporting gap | {a['results']['reporting_gap'] * 100:.2f} pp | "
        f"{b['results']['reporting_gap'] * 100:.2f} pp | {delta['reporting_gap'] * 100:+.2f} pp |\n\n"
        f"> {DISCLAIMER}\n"
    )
