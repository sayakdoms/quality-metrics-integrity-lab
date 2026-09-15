from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from src.validation import fraction, integer_at_least, non_negative


@dataclass(frozen=True)
class SimulationConfig:
    months: int = 12
    baseline_defect_rate: float = 0.023
    target_defect_rate: float = 0.010
    genuine_improvement_per_month: float = 0.00015
    process_drift_per_month: float = 0.00020
    target_pressure: float = 0.70
    gaming_susceptibility: float = 0.65
    classification_weight: float = 0.40
    timing_weight: float = 0.30
    sampling_weight: float = 0.30
    noise_sd: float = 0.0009
    seed: int = 42


def _normalise_weights(config: SimulationConfig) -> tuple[float, float, float]:
    weights = np.array(
        [
            non_negative("classification_weight", config.classification_weight),
            non_negative("timing_weight", config.timing_weight),
            non_negative("sampling_weight", config.sampling_weight),
        ],
        dtype=float,
    )
    total = weights.sum()
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    weights = weights / total
    return tuple(float(x) for x in weights)


def _validate_config(config: SimulationConfig) -> None:
    integer_at_least("months", config.months, 1)
    fraction("baseline_defect_rate", config.baseline_defect_rate)
    fraction("target_defect_rate", config.target_defect_rate)
    non_negative("genuine_improvement_per_month", config.genuine_improvement_per_month)
    non_negative("process_drift_per_month", config.process_drift_per_month)
    fraction("target_pressure", config.target_pressure)
    fraction("gaming_susceptibility", config.gaming_susceptibility)
    non_negative("noise_sd", config.noise_sd)
    integer_at_least("seed", config.seed, 0)


def simulate_quality_path(config: SimulationConfig) -> pd.DataFrame:
    """Simulate actual vs reported defect rates.

    This is an illustrative educational model, not an empirical forecasting model.
    Rates are stored as decimals (e.g. 0.023 = 2.3%).
    """
    _validate_config(config)
    rng = np.random.default_rng(config.seed)
    months = np.arange(1, config.months + 1)

    structural_change = (
        config.process_drift_per_month - config.genuine_improvement_per_month
    ) * (months - 1)
    noise = rng.normal(0.0, config.noise_sd, size=config.months)
    actual = np.clip(config.baseline_defect_rate + structural_change + noise, 0.0, 1.0)

    c_w, t_w, s_w = _normalise_weights(config)

    # Gaming pressure gradually intensifies rather than appearing fully formed in month 1.
    maturity = np.linspace(0.15, 1.0, config.months)
    max_gap = actual * config.target_pressure * config.gaming_susceptibility * 0.85 * maturity

    classification_gap = max_gap * c_w
    timing_gap = max_gap * t_w
    sampling_gap = max_gap * s_w

    reporting_gap = classification_gap + timing_gap + sampling_gap
    reported = np.clip(actual - reporting_gap, 0.0, 1.0)

    return pd.DataFrame(
        {
            "month": months,
            "actual_rate": actual,
            "reported_rate": reported,
            "target_rate": config.target_defect_rate,
            "classification_gap": classification_gap,
            "timing_gap": timing_gap,
            "sampling_gap": sampling_gap,
            "reporting_gap": actual - reported,
        }
    )
