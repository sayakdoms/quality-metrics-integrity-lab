from __future__ import annotations

from collections.abc import Sequence
from typing import Final, TypedDict


class AuditResult(TypedDict):
    risk_count: int
    risk_level: str
    recommendation: str


class AuditDiagnostic(TypedDict):
    flagged_questions: list[str]
    recommendations: list[str]


AUDIT_QUESTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("Who controls the number?", "Can the person being evaluated influence how it is recorded?"),
    ("Can definitions move?", 'Has "defect", "complaint" or "on-time" quietly been redefined?'),
    ("Can timing move?", "Can failures be shifted into another reporting period?"),
    ("What external signal should agree with it?", "Returns, warranty claims, customer complaints."),
    ("What behaviour changed?", "What happened after the target became important?"),
)

_TAILORED_RECOMMENDATIONS: Final[tuple[str, ...]] = (
    "Separate metric ownership from independent verification or add a documented review step.",
    "Freeze operational definitions for the reporting period and log every approved definition change.",
    "Reconcile reporting-period adjustments and monitor unusual activity near cut-off dates.",
    "Triangulate the KPI with returns, warranty claims, complaints, or another customer-facing signal.",
    "Review the behaviours rewarded by the target and add a balancing quality measure where needed.",
)


def audit_result(risk_answers: Sequence[bool]) -> AuditResult:
    """Classify the five measurement-system risk signals."""
    if len(risk_answers) != len(AUDIT_QUESTIONS):
        raise ValueError(f"Exactly {len(AUDIT_QUESTIONS)} audit answers are required.")
    if any(type(answer) is not bool for answer in risk_answers):
        raise ValueError("Audit answers must be boolean values.")

    score = sum(risk_answers)
    if score <= 1:
        level = "Low"
        recommendation = "Keep triangulating the KPI with external quality signals."
    elif score <= 3:
        level = "Moderate"
        recommendation = "Review definitions, incentives and sampling before relying on the KPI alone."
    else:
        level = "High"
        recommendation = "Audit the measurement system and redesign the target before using it for high-stakes decisions."
    return {"risk_count": score, "risk_level": level, "recommendation": recommendation}


def audit_diagnostic(risk_answers: Sequence[bool]) -> AuditDiagnostic:
    """Return flagged questions and restrained recommendations for those signals."""
    audit_result(risk_answers)
    flagged = [
        AUDIT_QUESTIONS[index][0]
        for index, answer in enumerate(risk_answers)
        if answer
    ]
    recommendations = [
        _TAILORED_RECOMMENDATIONS[index]
        for index, answer in enumerate(risk_answers)
        if answer
    ][:4]
    if len(recommendations) < 2:
        general_recommendations = [
            "Retain periodic definition and sampling reviews as the KPI evolves.",
            "Continue triangulating the KPI with at least one independent customer or process signal.",
        ]
        recommendations.extend(
            recommendation
            for recommendation in general_recommendations
            if recommendation not in recommendations
        )
        recommendations = recommendations[:2]
    return {
        "flagged_questions": flagged,
        "recommendations": recommendations,
    }
