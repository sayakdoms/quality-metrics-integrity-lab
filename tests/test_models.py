import numpy as np
import pandas as pd
import pytest

from src.cost_of_quality import CostConfig, estimate_cost_shift
from src.gaming_models import MECHANISMS
from src.metric_integrity import MetricVulnerability, integrity_score
from src.recommendations import AUDIT_QUESTIONS, audit_result
from src.simulation_engine import SimulationConfig, simulate_quality_path
from src.spc_engine import SPCConfig, simulate_p_chart


@pytest.mark.parametrize(
    "overrides",
    [{"target_pressure": 0.0}, {"gaming_susceptibility": 0.0}],
)
def test_zero_gaming_driver_produces_no_reporting_gap(overrides):
    result = simulate_quality_path(SimulationConfig(**overrides))
    pd.testing.assert_series_equal(
        result["reported_rate"], result["actual_rate"], check_names=False
    )
    assert np.allclose(result["reporting_gap"], 0.0)


def test_reported_rate_and_gap_invariants():
    result = simulate_quality_path(
        SimulationConfig(target_pressure=0.8, gaming_susceptibility=0.8)
    )
    component_sum = result[
        ["classification_gap", "timing_gap", "sampling_gap"]
    ].sum(axis=1)
    assert (result["reported_rate"] <= result["actual_rate"]).all()
    assert np.allclose(result["reporting_gap"], component_sum)
    assert np.allclose(
        result["actual_rate"] - result["reported_rate"], result["reporting_gap"]
    )
    assert result.filter(like="rate").to_numpy().min() >= 0.0
    assert result.filter(like="rate").to_numpy().max() <= 1.0


def test_simulation_is_reproducible_for_same_seed():
    config = SimulationConfig(seed=123)
    pd.testing.assert_frame_equal(
        simulate_quality_path(config), simulate_quality_path(config)
    )


def test_simulation_uses_normalised_mechanism_weights():
    result = simulate_quality_path(
        SimulationConfig(
            months=1,
            noise_sd=0.0,
            classification_weight=2.0,
            timing_weight=3.0,
            sampling_weight=5.0,
        )
    ).iloc[0]
    assert result["classification_gap"] == pytest.approx(result["reporting_gap"] * 0.2)
    assert result["timing_gap"] == pytest.approx(result["reporting_gap"] * 0.3)
    assert result["sampling_gap"] == pytest.approx(result["reporting_gap"] * 0.5)


def test_zero_mechanism_weights_fall_back_to_equal_shares():
    result = simulate_quality_path(
        SimulationConfig(
            months=1,
            noise_sd=0.0,
            classification_weight=0.0,
            timing_weight=0.0,
            sampling_weight=0.0,
        )
    ).iloc[0]
    assert result["classification_gap"] == pytest.approx(result["reporting_gap"] / 3)
    assert result["timing_gap"] == pytest.approx(result["reporting_gap"] / 3)
    assert result["sampling_gap"] == pytest.approx(result["reporting_gap"] / 3)


@pytest.mark.parametrize(
    "config",
    [
        SimulationConfig(months=0),
        SimulationConfig(baseline_defect_rate=-0.01),
        SimulationConfig(target_pressure=1.01),
        SimulationConfig(noise_sd=-0.01),
        SimulationConfig(classification_weight=-1.0),
    ],
)
def test_invalid_simulation_config_is_rejected(config):
    with pytest.raises(ValueError):
        simulate_quality_path(config)


def test_metric_integrity_extremes_and_weighting():
    strong = integrity_score(MetricVulnerability(0.0, 0.0, 0.0, 0.0))
    high_risk = integrity_score(MetricVulnerability(1.0, 1.0, 1.0, 1.0))
    single_only = integrity_score(MetricVulnerability(1.0, 0.0, 0.0, 0.0))
    assert strong == {"integrity_score": 100.0, "risk_score": 0.0, "label": "Strong"}
    assert high_risk == {
        "integrity_score": 0.0,
        "risk_score": 100.0,
        "label": "High risk",
    }
    assert single_only["risk_score"] == 20.0
    assert single_only["integrity_score"] == 80.0


@pytest.mark.parametrize("value", [-0.01, 1.01, float("nan"), float("inf")])
def test_metric_integrity_rejects_invalid_vulnerability(value):
    with pytest.raises(ValueError):
        integrity_score(MetricVulnerability(value, 0.0, 0.0, 0.0))


def test_cost_shift_matches_transparent_formula():
    config = CostConfig(
        units=1_000,
        actual_defect_rate=0.1,
        internal_detection_rate=0.8,
        hidden_fraction=0.25,
        internal_failure_cost=100.0,
        external_failure_cost=500.0,
    )
    result = estimate_cost_shift(config)
    assert result["total_defects"] == 100.0
    assert result["visible_internal_defects"] == 60.0
    assert result["external_defects"] == 40.0
    assert result["baseline_cost"] == 18_000.0
    assert result["gaming_cost"] == 26_000.0
    assert result["incremental_cost"] == 8_000.0


@pytest.mark.parametrize(
    "config",
    [
        CostConfig(units=0),
        CostConfig(actual_defect_rate=0.0),
        CostConfig(hidden_fraction=0.0),
    ],
)
def test_cost_shift_edge_cases_are_finite(config):
    result = estimate_cost_shift(config)
    assert all(np.isfinite(value) for value in result.values())
    assert result["incremental_cost"] == 0.0


def test_cost_shift_can_be_negative_when_external_failure_is_cheaper():
    result = estimate_cost_shift(
        CostConfig(
            internal_failure_cost=500.0,
            external_failure_cost=100.0,
            hidden_fraction=0.5,
        )
    )
    assert result["incremental_cost"] < 0.0


@pytest.mark.parametrize(
    "config",
    [
        CostConfig(units=-1),
        CostConfig(actual_defect_rate=1.1),
        CostConfig(internal_detection_rate=-0.1),
        CostConfig(hidden_fraction=1.1),
        CostConfig(internal_failure_cost=-1.0),
    ],
)
def test_invalid_cost_config_is_rejected(config):
    with pytest.raises(ValueError):
        estimate_cost_shift(config)


def test_spc_limits_and_series_are_bounded():
    data, limits = simulate_p_chart(SPCConfig())
    assert 0.0 <= limits["lcl"] <= limits["center_line"] <= limits["ucl"] <= 1.0
    assert data[["real_data", "sanitised_data"]].to_numpy().min() >= 0.0
    assert data[["real_data", "sanitised_data"]].to_numpy().max() <= 1.0


def test_spc_is_reproducible_for_same_seed():
    config = SPCConfig(seed=321)
    first_data, first_limits = simulate_p_chart(config)
    second_data, second_limits = simulate_p_chart(config)
    pd.testing.assert_frame_equal(first_data, second_data)
    assert first_limits == second_limits


def test_spc_sanitisation_endpoints():
    raw, _ = simulate_p_chart(SPCConfig(sanitisation_strength=0.0))
    fully_sanitised, _ = simulate_p_chart(SPCConfig(sanitisation_strength=1.0))
    assert np.allclose(raw["sanitised_data"], raw["real_data"])
    assert np.allclose(fully_sanitised["sanitised_data"], 0.023)


@pytest.mark.parametrize(
    "config",
    [
        SPCConfig(periods=0),
        SPCConfig(sample_size=0),
        SPCConfig(baseline_rate=-0.1),
        SPCConfig(sanitisation_strength=1.1),
        SPCConfig(periods=5, special_cause_periods=(6,)),
        SPCConfig(special_cause_periods=(8, 8)),
        SPCConfig(baseline_rate=0.9, special_cause_addition=0.2),
    ],
)
def test_invalid_spc_config_is_rejected(config):
    with pytest.raises(ValueError):
        simulate_p_chart(config)


@pytest.mark.parametrize(
    ("risk_count", "expected_level"),
    [
        (0, "Low"),
        (1, "Low"),
        (2, "Moderate"),
        (3, "Moderate"),
        (4, "High"),
        (5, "High"),
    ],
)
def test_audit_risk_classification_boundaries(risk_count, expected_level):
    answers = [True] * risk_count + [False] * (len(AUDIT_QUESTIONS) - risk_count)
    result = audit_result(answers)
    assert result["risk_count"] == risk_count
    assert result["risk_level"] == expected_level


@pytest.mark.parametrize(
    "answers",
    [[], [False] * 4, [False] * 6, [0, False, False, False, False]],
)
def test_audit_rejects_invalid_answers(answers):
    with pytest.raises(ValueError):
        audit_result(answers)


def test_gaming_mechanisms_have_complete_explanations():
    assert tuple(MECHANISMS) == ("Classification", "Timing", "Sampling")
    assert all(
        set(details) == {"description", "example", "audit_signal"}
        and all(details.values())
        for details in MECHANISMS.values()
    )
