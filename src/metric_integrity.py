from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from src.validation import fraction


class MetricIntegrityResult(TypedDict):
    """Transparent score output used by the UI and tests."""

    integrity_score: float
    risk_score: float
    label: str


@dataclass(frozen=True)
class MetricVulnerability:
    single_metric_dependence: float
    stakes: float
    manipulability: float
    customer_link_weakness: float


def integrity_score(v: MetricVulnerability) -> MetricIntegrityResult:
    """Return a 0-100 integrity score and risk label.

    Inputs are expected on a 0-1 scale, where 1 indicates maximum vulnerability.
    """
    values = {
        "single": fraction("single_metric_dependence", v.single_metric_dependence),
        "stakes": fraction("stakes", v.stakes),
        "manipulability": fraction("manipulability", v.manipulability),
        "customer_link": fraction("customer_link_weakness", v.customer_link_weakness),
    }
    weights = {
        "single": 0.20,
        "stakes": 0.30,
        "manipulability": 0.30,
        "customer_link": 0.20,
    }
    risk = 100 * (
        weights["single"] * values["single"]
        + weights["stakes"] * values["stakes"]
        + weights["manipulability"] * values["manipulability"]
        + weights["customer_link"] * values["customer_link"]
    )
    score = 100.0 - risk

    if score >= 75:
        label = "Strong"
    elif score >= 55:
        label = "Watch"
    elif score >= 35:
        label = "Fragile"
    else:
        label = "High risk"

    return {"integrity_score": round(score, 1), "risk_score": round(risk, 1), "label": label}
