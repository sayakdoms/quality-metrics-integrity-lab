"""Plain-English diagnostics derived from validated model outputs."""

from __future__ import annotations

from typing import Final, TypedDict

import pandas as pd

from src.metric_integrity import MetricIntegrityResult, MetricVulnerability, integrity_score


DRIVER_LABELS: Final[dict[str, str]] = {
    "single_metric_dependence": "Single-metric dependence",
    "stakes": "High-stakes consequences",
    "manipulability": "Ease of manipulation",
    "customer_link_weakness": "Weak customer linkage",
}


class IntegrityDiagnostic(TypedDict):
    score: float
    classification: str
    strongest_driver: str
    strongest_value: float
    weakest_driver: str
    weakest_value: float
    explanation: str


class SPCDiagnostic(TypedDict):
    real_signal_count: int
    sanitised_signal_count: int
    hidden_signal_count: int
    variation_reduction_pct: float
    interpretation: str


def metric_integrity_diagnostic(
    vulnerability: MetricVulnerability,
    result: MetricIntegrityResult | None = None,
) -> IntegrityDiagnostic:
    """Identify the strongest/weakest vulnerability inputs and explain the score."""
    score_result = result or integrity_score(vulnerability)
    values = {
        "single_metric_dependence": vulnerability.single_metric_dependence,
        "stakes": vulnerability.stakes,
        "manipulability": vulnerability.manipulability,
        "customer_link_weakness": vulnerability.customer_link_weakness,
    }
    strongest_key = max(values, key=values.get)
    weakest_key = min(values, key=values.get)
    explanations = {
        "Strong": "Low combined vulnerability suggests the metric is comparatively well supported, though it should still be triangulated.",
        "Watch": "Moderate vulnerability warrants regular checks of definitions, incentives, and external quality signals.",
        "Fragile": "Several vulnerability drivers are elevated, so the reported KPI should not be relied on without corroboration.",
        "High risk": "High combined vulnerability means the measurement system needs review before the KPI supports high-stakes decisions.",
    }
    return {
        "score": float(score_result["integrity_score"]),
        "classification": str(score_result["label"]),
        "strongest_driver": DRIVER_LABELS[strongest_key],
        "strongest_value": float(values[strongest_key]),
        "weakest_driver": DRIVER_LABELS[weakest_key],
        "weakest_value": float(values[weakest_key]),
        "explanation": explanations[str(score_result["label"])],
    }


def quality_mirage_interpretation(simulation: pd.DataFrame) -> str:
    """Summarise the relationship between actual and reported defect trajectories."""
    required = {"actual_rate", "reported_rate", "reporting_gap"}
    if simulation.empty or not required.issubset(simulation.columns):
        raise ValueError("Simulation output is missing required quality-rate data.")

    first = simulation.iloc[0]
    final = simulation.iloc[-1]
    actual_improvement = float(first["actual_rate"] - final["actual_rate"])
    reported_improvement = float(first["reported_rate"] - final["reported_rate"])
    final_gap = float(final["reporting_gap"])

    if abs(final_gap) < 1e-12:
        return "Reported and underlying defect rates remain aligned in this scenario."
    if reported_improvement > 0 and actual_improvement <= 0:
        return "The reported defect rate improves while the underlying process does not."
    if reported_improvement > actual_improvement + 1e-12:
        return "The reported defect rate improves faster than the underlying process."
    return "The reported defect rate understates the underlying process rate in this scenario."


def spc_diagnostic(
    data: pd.DataFrame, limits: dict[str, float]
) -> SPCDiagnostic:
    """Compare visible special-cause signals and variation before/after sanitisation."""
    required = {"real_data", "sanitised_data"}
    if data.empty or not required.issubset(data.columns):
        raise ValueError("SPC output is missing required series.")
    if not {"ucl", "lcl"}.issubset(limits):
        raise ValueError("SPC limits must include ucl and lcl.")

    real_signals = (data["real_data"] > limits["ucl"]) | (
        data["real_data"] < limits["lcl"]
    )
    sanitised_signals = (data["sanitised_data"] > limits["ucl"]) | (
        data["sanitised_data"] < limits["lcl"]
    )
    real_variation = float(data["real_data"].std(ddof=0))
    sanitised_variation = float(data["sanitised_data"].std(ddof=0))
    reduction = (
        0.0
        if real_variation == 0.0
        else max(0.0, 1.0 - sanitised_variation / real_variation) * 100
    )
    real_count = int(real_signals.sum())
    sanitised_count = int(sanitised_signals.sum())
    hidden_count = int((real_signals & ~sanitised_signals).sum())
    if hidden_count:
        interpretation = (
            f"{hidden_count} signal(s) visible in the real series no longer cross the "
            "same limits after sanitisation."
        )
    else:
        interpretation = (
            "No limit-crossing signal disappears in this draw, but sanitisation still "
            "compresses the displayed variation."
        )
    return {
        "real_signal_count": real_count,
        "sanitised_signal_count": sanitised_count,
        "hidden_signal_count": hidden_count,
        "variation_reduction_pct": round(reduction, 1),
        "interpretation": interpretation,
    }
