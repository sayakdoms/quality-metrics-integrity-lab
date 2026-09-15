from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from src.validation import fraction, integer_at_least, non_negative


class CostShiftResult(TypedDict):
    total_defects: float
    detected_internal_defects: float
    shifted_defects: float
    visible_internal_defects: float
    external_defects: float
    baseline_internal_cost: float
    baseline_external_cost: float
    post_shift_internal_cost: float
    post_shift_external_cost: float
    baseline_cost: float
    gaming_cost: float
    incremental_cost: float


@dataclass(frozen=True)
class CostConfig:
    units: int = 10000
    actual_defect_rate: float = 0.023
    internal_detection_rate: float = 0.85
    hidden_fraction: float = 0.25
    internal_failure_cost: float = 450.0
    external_failure_cost: float = 3500.0


def estimate_cost_shift(config: CostConfig) -> CostShiftResult:
    """Estimate the cost effect of shifting detected failures downstream.

    The calculation is deterministic and uses user-supplied scenario
    assumptions; it is not an empirical cost forecast.
    """
    units = integer_at_least("units", config.units, 0)
    defect_rate = fraction("actual_defect_rate", config.actual_defect_rate)
    detection_rate = fraction("internal_detection_rate", config.internal_detection_rate)
    hidden_fraction = fraction("hidden_fraction", config.hidden_fraction)
    internal_cost = non_negative("internal_failure_cost", config.internal_failure_cost)
    external_cost = non_negative("external_failure_cost", config.external_failure_cost)

    total_defects = units * defect_rate
    detected_internal = total_defects * detection_rate
    naturally_external = total_defects - detected_internal

    hidden_internal = detected_internal * hidden_fraction
    visible_internal = detected_internal - hidden_internal
    external_after_gaming = naturally_external + hidden_internal

    baseline_internal_cost = detected_internal * internal_cost
    baseline_external_cost = naturally_external * external_cost
    post_shift_internal_cost = visible_internal * internal_cost
    post_shift_external_cost = external_after_gaming * external_cost
    baseline_cost = baseline_internal_cost + baseline_external_cost
    gaming_cost = post_shift_internal_cost + post_shift_external_cost

    return {
        "total_defects": total_defects,
        "detected_internal_defects": detected_internal,
        "shifted_defects": hidden_internal,
        "visible_internal_defects": visible_internal,
        "external_defects": external_after_gaming,
        "baseline_internal_cost": baseline_internal_cost,
        "baseline_external_cost": baseline_external_cost,
        "post_shift_internal_cost": post_shift_internal_cost,
        "post_shift_external_cost": post_shift_external_cost,
        "baseline_cost": baseline_cost,
        "gaming_cost": gaming_cost,
        "incremental_cost": gaming_cost - baseline_cost,
    }
