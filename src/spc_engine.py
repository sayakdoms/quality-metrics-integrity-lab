from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

from src.validation import fraction, integer_at_least


@dataclass(frozen=True)
class SPCConfig:
    periods: int = 24
    sample_size: int = 250
    baseline_rate: float = 0.023
    special_cause_periods: tuple[int, ...] = (8, 15)
    special_cause_addition: float = 0.018
    sanitisation_strength: float = 0.55
    seed: int = 7


def _validate_config(config: SPCConfig) -> None:
    periods = integer_at_least("periods", config.periods, 1)
    integer_at_least("sample_size", config.sample_size, 1)
    baseline = fraction("baseline_rate", config.baseline_rate)
    addition = fraction("special_cause_addition", config.special_cause_addition)
    fraction("sanitisation_strength", config.sanitisation_strength)
    integer_at_least("seed", config.seed, 0)

    if baseline + addition > 1.0:
        raise ValueError("baseline_rate plus special_cause_addition cannot exceed 1.")
    validated_periods: list[int] = []
    for period in config.special_cause_periods:
        validated_period = integer_at_least("special cause period", period, 1)
        if validated_period > periods:
            raise ValueError("special cause periods must fall within the simulated periods.")
        validated_periods.append(validated_period)
    if len(set(validated_periods)) != len(validated_periods):
        raise ValueError("special_cause_periods must not contain duplicates.")


def simulate_p_chart(config: SPCConfig) -> tuple[pd.DataFrame, dict[str, float]]:
    """Generate deterministic synthetic p-chart data and real-data limits."""
    _validate_config(config)
    rng = np.random.default_rng(config.seed)
    p_true = np.full(config.periods, config.baseline_rate, dtype=float)
    for period in config.special_cause_periods:
        p_true[period - 1] += config.special_cause_addition

    defects = rng.binomial(config.sample_size, np.clip(p_true, 0, 1))
    observed = defects / config.sample_size

    # Sanitised series compresses unusual values toward the baseline.
    sanitised = config.baseline_rate + (observed - config.baseline_rate) * (
        1 - config.sanitisation_strength
    )
    sanitised = np.clip(sanitised, 0.0, 1.0)

    pbar = float(observed.mean())
    sigma = (pbar * (1 - pbar) / config.sample_size) ** 0.5
    ucl = min(1.0, pbar + 3 * sigma)
    lcl = max(0.0, pbar - 3 * sigma)

    df = pd.DataFrame(
        {
            "period": np.arange(1, config.periods + 1),
            "real_data": observed,
            "sanitised_data": sanitised,
            "ucl": ucl,
            "lcl": lcl,
            "center_line": pbar,
        }
    )
    return df, {"center_line": pbar, "ucl": ucl, "lcl": lcl}
