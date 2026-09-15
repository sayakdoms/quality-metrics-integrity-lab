from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parents[1] / "app.py"


def test_app_smoke_and_identity():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    assert not app.exception
    assert app.title[0].value == "Quality Metrics Integrity Lab"
    assert any("Educational simulation only" in item.value for item in app.info)
    assert len(app.metric) >= 4
    assert "v0.3.0" in app.caption[0].value
    assert any(
        "High-stakes consequences" in item.value for item in app.markdown
    )
    assert any("No file selected" in item.value for item in app.caption)
    assert any(
        "Exploratory visualisation using user-provided data." in item.value
        for item in app.subheader
    )
    assert app.selectbox(key="comparison_scenario_a").value == "Healthy Measurement System"
    assert app.selectbox(key="comparison_scenario_b").value == "High-Pressure Defect Target"


def test_zero_target_pressure_updates_reporting_gap():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    pressure_slider = next(
        slider for slider in app.slider if slider.label == "Target pressure"
    )
    pressure_slider.set_value(0).run()
    assert not app.exception
    reporting_gap = next(
        metric for metric in app.metric if metric.label == "Final reporting gap"
    )
    assert reporting_gap.value == "0.00 pp"


def test_named_preset_updates_linked_controls():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.selectbox(key="scenario_mode").select("Healthy Measurement System").run()

    assert not app.exception
    assert app.session_state["pressure_pct"] == 25
    assert app.session_state["susceptibility_pct"] == 15
    assert app.session_state["weak_link_pct"] == 20
    assert app.session_state["spc_sanitisation_pct"] == 5
    assert app.session_state["hidden_fraction_pct"] == 5


def test_manual_control_edit_returns_scenario_to_custom():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.selectbox(key="scenario_mode").select("Gaming-Prone KPI").run()
    app.slider(key="pressure_pct").set_value(50).run()

    assert not app.exception
    assert app.selectbox(key="scenario_mode").value == "Custom"


def test_comparison_selector_recomputes_scenario_b():
    app = AppTest.from_file(APP_PATH, default_timeout=10).run()
    app.selectbox(key="comparison_scenario_b").select("Gaming-Prone KPI").run()

    assert not app.exception
    reporting_gap = next(
        metric for metric in app.metric if metric.label == "Scenario B reporting gap"
    )
    assert reporting_gap.value.endswith(" pp")
    assert float(reporting_gap.value.removesuffix(" pp")) > 0
