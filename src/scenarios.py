"""Named educational scenarios for the Streamlit control panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


CUSTOM_SCENARIO: Final = "Custom"


@dataclass(frozen=True)
class ScenarioPreset:
    """A coherent set of hypothetical model and display inputs.

    Rates and vulnerability values use the same decimal-fraction convention as
    the validated model layer. ``as_widget_state`` performs the presentation
    conversion required by the percentage-based Streamlit controls.
    """

    name: str
    description: str
    baseline_defect_rate: float
    target_defect_rate: float
    target_pressure: float
    gaming_susceptibility: float
    genuine_improvement_per_month: float
    process_drift_per_month: float
    single_metric_dependence: float
    stakes: float
    manipulability: float
    customer_link_weakness: float
    spc_sanitisation_strength: float
    hidden_fraction: float
    audit_answers: tuple[bool, bool, bool, bool, bool]

    def as_widget_state(self) -> dict[str, int | float]:
        """Return values in the units used by the app's keyed widgets."""
        return {
            "baseline_pct": self.baseline_defect_rate * 100,
            "target_pct": self.target_defect_rate * 100,
            "pressure_pct": round(self.target_pressure * 100),
            "susceptibility_pct": round(self.gaming_susceptibility * 100),
            "improvement_pp": self.genuine_improvement_per_month * 100,
            "drift_pp": self.process_drift_per_month * 100,
            "single_pct": round(self.single_metric_dependence * 100),
            "stakes_pct": round(self.stakes * 100),
            "manipulability_pct": round(self.manipulability * 100),
            "weak_link_pct": round(self.customer_link_weakness * 100),
            "spc_sanitisation_pct": round(self.spc_sanitisation_strength * 100),
            "hidden_fraction_pct": round(self.hidden_fraction * 100),
        }


SCENARIO_PRESETS: Final[dict[str, ScenarioPreset]] = {
    "Healthy Measurement System": ScenarioPreset(
        name="Healthy Measurement System",
        description="Balanced incentives and strong customer linkage keep reported and underlying quality closely aligned.",
        baseline_defect_rate=0.023,
        target_defect_rate=0.018,
        target_pressure=0.25,
        gaming_susceptibility=0.15,
        genuine_improvement_per_month=0.00025,
        process_drift_per_month=0.00005,
        single_metric_dependence=0.25,
        stakes=0.30,
        manipulability=0.20,
        customer_link_weakness=0.20,
        spc_sanitisation_strength=0.05,
        hidden_fraction=0.05,
        audit_answers=(False, False, False, False, False),
    ),
    "High-Pressure Defect Target": ScenarioPreset(
        name="High-Pressure Defect Target",
        description="A demanding defect target creates strong reporting pressure even when manipulation is only moderately easy.",
        baseline_defect_rate=0.023,
        target_defect_rate=0.010,
        target_pressure=0.90,
        gaming_susceptibility=0.45,
        genuine_improvement_per_month=0.00015,
        process_drift_per_month=0.00020,
        single_metric_dependence=0.70,
        stakes=0.95,
        manipulability=0.55,
        customer_link_weakness=0.50,
        spc_sanitisation_strength=0.40,
        hidden_fraction=0.20,
        audit_answers=(True, False, True, False, True),
    ),
    "Gaming-Prone KPI": ScenarioPreset(
        name="Gaming-Prone KPI",
        description="High pressure combines with easy classification, timing, and sampling adjustments to widen the reporting gap.",
        baseline_defect_rate=0.023,
        target_defect_rate=0.010,
        target_pressure=0.80,
        gaming_susceptibility=0.90,
        genuine_improvement_per_month=0.00010,
        process_drift_per_month=0.00025,
        single_metric_dependence=0.85,
        stakes=0.85,
        manipulability=0.95,
        customer_link_weakness=0.65,
        spc_sanitisation_strength=0.80,
        hidden_fraction=0.30,
        audit_answers=(True, True, True, True, True),
    ),
    "Customer-Disconnected KPI": ScenarioPreset(
        name="Customer-Disconnected KPI",
        description="The internal KPI appears actionable but has a weak connection to returns, complaints, and other customer outcomes.",
        baseline_defect_rate=0.023,
        target_defect_rate=0.012,
        target_pressure=0.70,
        gaming_susceptibility=0.60,
        genuine_improvement_per_month=0.00015,
        process_drift_per_month=0.00020,
        single_metric_dependence=0.65,
        stakes=0.70,
        manipulability=0.60,
        customer_link_weakness=0.95,
        spc_sanitisation_strength=0.45,
        hidden_fraction=0.22,
        audit_answers=(True, False, False, True, True),
    ),
}


DEFAULT_WIDGET_STATE: Final[dict[str, int | float]] = {
    "baseline_pct": 2.3,
    "target_pct": 1.0,
    "pressure_pct": 70,
    "susceptibility_pct": 65,
    "improvement_pp": 0.015,
    "drift_pp": 0.020,
    "single_pct": 70,
    "stakes_pct": 80,
    "manipulability_pct": 65,
    "weak_link_pct": 55,
    "spc_sanitisation_pct": 45,
    "hidden_fraction_pct": 15,
}


def scenario_names() -> tuple[str, ...]:
    """Return Custom followed by the available named presets."""
    return (CUSTOM_SCENARIO, *SCENARIO_PRESETS)


def get_scenario_preset(name: str) -> ScenarioPreset:
    """Return a named preset or raise a clear error for an unknown name."""
    try:
        return SCENARIO_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown scenario preset: {name}") from exc
