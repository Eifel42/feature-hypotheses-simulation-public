# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# Disclaimer: This software is provided "as is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and noninfringement.
# In no event shall the authors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract, tort or
# otherwise, arising from, out of or in connection with the software or the
# use or other dealings in the software.

"""Tests for specialized table wrappers on the notebook display facade."""

from types import SimpleNamespace

from fhs.presentation.notebook.widgets import facade as facade_module
from fhs.presentation.notebook.widgets.facade import FHSDisplay


class _RecorderDisplay(FHSDisplay):
    def __init__(self) -> None:
        self.rendered: list[str] = []

    def __call__(self, html: str) -> None:
        self.rendered.append(html)


def test_sprint_plan_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)

    display = _RecorderDisplay()
    display.sprint_plan(
        [
            SimpleNamespace(
                name="H1: Simplified UI",
                development_weeks=4.8,
                development_cost=12_000.0,
            )
        ],
        SimpleNamespace(sprint_length_weeks=2),
    )

    assert captured["rows"] == [("Simplified UI", "4.8", "3", "EUR 12,000")]
    assert captured["headers"] == (
        "Feature",
        "Planned weeks",
        "Planned sprints",
        "Planned investment",
    )
    assert captured["kwargs"] == {"title": "Sprint Plan per Feature"}
    assert display.rendered == ["<table>"]


def test_sprint_plan_uses_delivery_config_sprint_length(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)

    display = _RecorderDisplay()
    display.sprint_plan(
        [
            SimpleNamespace(
                name="H9: Partial Sprint",
                development_weeks=4.8,
                development_cost=12_000.0,
            )
        ],
        SimpleNamespace(sprint_length_weeks=1),
    )

    assert captured["rows"] == [("Partial Sprint", "4.8", "5", "EUR 12,000")]
    assert captured["headers"] == (
        "Feature",
        "Planned weeks",
        "Planned sprints",
        "Planned investment",
    )
    assert captured["kwargs"] == {"title": "Sprint Plan per Feature"}
    assert display.rendered == ["<table>"]


def test_delay_summary_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)

    display = _RecorderDisplay()
    result = SimpleNamespace(
        planned_sprints=2,
        sprints_p50=3,
        sprints_p75=4,
        sprints_p95=5,
        cancelled_pct=0.12,
    )

    display.delay_summary(
        {"H1: Simplified UI": result},
        feature_names=["H1: Simplified UI"],
    )

    assert captured["rows"] == [
        ("Simplified UI", "2", "3", "4", "5", "+1", "+2", "+3", "12.0%")
    ]
    assert captured["headers"] == (
        "Feature",
        "Planned sprints",
        "P50 actual",
        "P75 actual",
        "P95 actual",
        "P50 overrun",
        "P75 overrun",
        "P95 overrun",
        "Cancelled %",
    )
    assert captured["kwargs"] == {"title": "Sprint Overrun Summary"}
    assert display.rendered == ["<table>"]


def test_cost_comparison_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)

    display = _RecorderDisplay()
    feature = SimpleNamespace(
        name="H1: Simplified UI",
        development_cost=10_000.0,
    )
    delivery_result = SimpleNamespace(
        expected_actual_cost=12_500.0,
        cost_p95=14_000.0,
        cost_uplift=0.25,
    )

    display.cost_comparison(
        [feature],
        {"H1: Simplified UI": delivery_result},
    )

    assert captured["rows"] == [
        (
            "Simplified UI",
            "EUR 10,000",
            "EUR 10,000",
            "EUR 12,500",
            "EUR 14,000",
            "+25.0%",
        )
    ]
    assert captured["headers"] == (
        "Feature",
        "Planned feature investment",
        "Planned development burn",
        "Expected development burn",
        "P95 development burn",
        "Burn uplift vs plan",
    )
    assert captured["kwargs"] == {
        "title": "Feature Investment vs Development Burn Cost"
    }
    assert display.rendered == ["<table>"]


def test_delivery_cost_risk_renders_var_cvar_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)

    display = _RecorderDisplay()
    feature = SimpleNamespace(
        name="H1: Simplified UI",
        development_cost=10_000.0,
    )
    delivery_result = SimpleNamespace(
        expected_actual_cost=11_000.0,
        cost_p95=14_000.0,
        cost_cvar=15_500.0,
        cancelled_pct=0.08,
    )

    display.delivery_cost_risk(
        [feature],
        {"H1: Simplified UI": delivery_result},
    )

    assert captured["rows"] == [
        (
            "Simplified UI",
            "EUR 10,000",
            "EUR 11,000",
            "EUR 14,000",
            "EUR 15,500",
            "+10.0%",
            "8.0%",
        )
    ]
    assert captured["headers"] == (
        "Feature",
        "Planned investment",
        "Expected cost",
        "Cost at Risk 95% (CaR)",
        "CVaR (worst 5% avg)",
        "Uplift vs plan",
        "Cancelled %",
    )
    assert captured["kwargs"] == {
        "title": "Development Cost Risk — Cost at Risk (CaR) & CVaR"
    }
    assert display.rendered == ["<table>"]


def test_advanced_table_wrappers_use_standard_headers(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    sample_rows_8 = [
        (
            "Exact",
            "2",
            "EUR 10,000",
            "EUR 20,000",
            "EUR 8,000",
            "30%",
            "EUR -2,000",
            "0.0100s",
        )
    ]
    display.solver_results(sample_rows_8)
    assert captured["headers"][0] == "Method"
    assert captured["kwargs"] == {"title": "Optimization Result Table"}

    sample_rows_6 = [("All features", "EXACT", "A", "1", "EUR 8,000", "EUR 9,000")]
    display.negative_score_effect(sample_rows_6)
    assert captured["headers"][0] == "Candidate set"

    sample_rows_5 = [("2", "ILP", "EUR 10,000", "EUR 8,000", "0.0010s")]
    display.runtime_scaling(sample_rows_5)
    assert captured["headers"][0] == "Num Features"

    detail_rows = [("H1: UI", "Growth", "EUR 10,000", "EUR 20,000", "EUR 8,000")]
    display.selected_portfolio_details(detail_rows)
    assert captured["headers"][0] == "Selected Feature"


def test_feature_risk_layers_renders_three_standard_tables(monkeypatch):
    """All three tables are full-width for optimal readability."""
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def _fake_table(_table_rows, headers, **kwargs):
        calls.append((headers, kwargs))
        return "<table>"

    # All tables are called via facade_module.sensitivity_table (self.sensitivity).
    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    risk_tables = SimpleNamespace(
        expected_rows=[("H1", "EUR 10")],
        expected_headers=("Feature", "Base"),
        probability_rows=[("H1", "10%")],
        prob_headers=("Feature", "Delivery LLP"),
        retention_rows=[("H1", "90%")],
        retention_headers=("Feature", "Retention"),
    )

    display.feature_risk_layers(risk_tables)

    assert len(calls) == 3
    assert calls[0][0] == ("Feature", "Base")
    assert (
        calls[0][1]["title"]
        == "Expected Business Value at Each Risk Layer (per feature)"
    )
    assert calls[1][0] == ("Feature", "Delivery LLP")
    assert calls[1][1]["title"] == "Risk Configuration per Feature Cluster"
    assert calls[2][0] == ("Feature", "Retention")
    assert (
        calls[2][1]["title"]
        == "Feature Business Value Retention across All Risk Layers"
    )


def test_risk_factor_sensitivity_renders_three_standard_tables(monkeypatch):
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def _fake_table(_table_rows, headers, **kwargs):
        calls.append((headers, kwargs))
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    display.risk_factor_sensitivity(
        market_rows=[("10%", "EUR 100,000")],
        global_rows=[("2.5%", "EUR 99,000")],
        component_rows=[("platform", "5% (x1.0)", "EUR 98,000")],
    )

    assert len(calls) == 3
    assert calls[0][0] == ("Market Probability", "Expected Portfolio Business Value")
    assert calls[0][1]["title"] == "Market Risk Sensitivity"
    assert calls[1][0] == ("Global Probability", "Expected Portfolio Business Value")
    assert calls[1][1]["title"] == "Global Risk Sensitivity"
    assert calls[2][0] == (
        "Cluster",
        "Failure Probability",
        "Expected Portfolio Business Value",
    )
    assert calls[2][1]["title"] == "Component Risk Sensitivity by Platform Cluster"


def test_budget_risk_path_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    display.budget_risk_path(
        [
            SimpleNamespace(
                label="50% Budget",
                selected_count=2,
                investment=100_000.0,
                l1_floor=180_000.0,
                l2_floor=150_000.0,
                l3_floor=120_000.0,
                l3_safety_buffer=20_000.0,
                risk_class="Medium",
            )
        ]
    )

    assert captured["rows"] == [
        (
            "50% Budget",
            "2",
            "EUR 100,000",
            "EUR 180,000",
            "EUR 150,000",
            "EUR 120,000",
            "EUR 20,000",
            "Medium",
        )
    ]
    assert captured["headers"] == (
        "Budget Level",
        "Num Features",
        "Investment",
        "Base Case Floor",
        "Development Risk Floor",
        "Crisis Shock Floor",
        "Crisis Shock Safety Buffer",
        "Risk Class",
    )
    assert captured["kwargs"] == {
        "title": "Budget Path - Floor and Risk Class (ILP var_floor)"
    }
    assert display.rendered == ["<table>"]


def test_three_level_risk_summary_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    display.three_level_risk_summary(
        {
            "market_expected": 200_000.0,
            "market_var_95": 150_000.0,
            "simulated_expected": 180_000.0,
            "simulated_var_95": 130_000.0,
            "var_delta_pct": -13.3,
        },
        {
            "shocked_expected": 140_000.0,
            "shocked_var_95": 90_000.0,
            "shocked_var_delta_pct": -40.0,
        },
    )

    assert len(captured["rows"]) == 3
    assert captured["rows"][0][0] == "Base Case (market uncertainty)"
    assert captured["rows"][2][0] == "After Crisis Shock (global event)"
    assert captured["headers"] == (
        "Risk Layer",
        "Expected Business Value",
        "Business Value Floor (BVF 95%)",
        "Comment",
    )
    assert captured["kwargs"] == {"title": "Three-Level Risk Summary"}
    assert display.rendered == ["<table>"]


def test_stress_scenario_table_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    display.stress_scenario_table(
        baseline=SimpleNamespace(expected=220_000.0, var_95=160_000.0),
        scenarios=[
            {
                "name": "Market pullback",
                "expected": 200_000.0,
                "var_95": 145_000.0,
                "var_delta_pct": -9.4,
            }
        ],
    )

    assert captured["rows"] == [
        ("Baseline", "EUR 220,000", "EUR 160,000", "0.0%"),
        ("Market pullback", "EUR 200,000", "EUR 145,000", "-9.4%"),
    ]
    assert captured["headers"] == (
        "Scenario",
        "Expected Business Value",
        "Business Value Floor (BVF 95%)",
        "Floor Change vs Baseline",
    )
    assert captured["kwargs"] == {"title": "Stress Scenario Table"}
    assert display.rendered == ["<table>"]


def test_llp_delivery_table_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [("H1", "20%", "EUR 100,000", "EUR 20,000", "platform")]
    display.llp_delivery_table(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Feature",
        "LLP",
        "Expected Business Value",
        "At-Risk Business Value",
        "Dependency Cluster",
    )
    assert captured["kwargs"] == {
        "title": "Feature Development Risk Table (all features)"
    }
    assert display.rendered == ["<table>"]


def test_practical_decision_table_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [
        (
            "50% Budget",
            "EUR 50,000",
            "H1",
            "Selected 1",
            "Keep H2",
            "EUR 100,000",
            "EUR 70,000",
            "EUR 20,000",
            "EUR 0",
            "Build now",
        )
    ]
    display.practical_decision_table(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Budget Level",
        "Budget",
        "ILP Selection",
        "Selection Note",
        "Backlog Guidance",
        "Expected",
        "Floor (BVF 95%)",
        "Safety Buffer",
        "Remaining Budget",
        "Suggested Action",
    )
    assert captured["kwargs"] == {"title": "Practical Decision Table"}
    assert display.rendered == ["<table>"]


def test_feature_value_risk_baseline_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [
        (
            "H1",
            "Feature Name",
            "EUR 10,000",
            "EUR 40,000",
            "EUR 20,000",
            "20%",
            "Balanced",
        )
    ]
    display.feature_value_risk_baseline(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Key",
        "Feature",
        "Cost",
        "Expected Business Value",
        "Business Value Floor (BVF 95%)",
        "LLP",
        "Risk Zone",
    )
    assert captured["kwargs"] == {
        "title": "Blockchain Features - Value and Outage Risk Baseline"
    }
    assert display.rendered == ["<table>"]


def test_ilp_selection_explanation_uses_selection_rows_and_headers(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    selection = SimpleNamespace(
        rows=[("100% Budget", "H1,H2")],
        headers=("Budget", "Selection"),
    )

    display.ilp_selection_explanation(selection)

    assert captured["rows"] == [("100% Budget", "H1,H2")]
    assert captured["headers"] == ("Budget", "Selection")
    assert captured["kwargs"] == {"title": "Why ILP may skip affordable features"}
    assert display.rendered == ["<table>"]


def test_negative_roi_reference_comparison_uses_rows_and_headers(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    comparison = SimpleNamespace(
        rows=[("Selected", "EUR 100,000")],
        headers=("Portfolio", "Expected"),
    )

    display.negative_roi_reference_comparison(comparison)

    assert captured["rows"] == [("Selected", "EUR 100,000")]
    assert captured["headers"] == ("Portfolio", "Expected")
    assert captured["kwargs"] == {
        "title": "Reference comparison when a feature has negative ROI"
    }
    assert display.rendered == ["<table>"]


def test_business_value_loss_by_risk_dimension_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    display.business_value_loss_by_risk_dimension(
        delivery_loss=1000.0,
        market_loss=2000.0,
        component_loss=500.0,
        global_loss=1500.0,
        base_expected=20_000.0,
    )

    assert captured["rows"][0] == ("Development risk", "EUR 1,000", "5.0%")
    assert captured["rows"][1] == ("Market risk", "EUR 2,000", "10.0%")
    assert captured["rows"][-1] == ("Total risk loss", "EUR 5,000", "25.0%")
    assert captured["headers"] == (
        "Risk Dimension",
        "Business Value Loss (EUR)",
        "% of Base Business Value",
    )
    assert captured["kwargs"] == {"title": "Business Value Loss by Risk Dimension"}
    assert display.rendered == ["<table>"]


def test_portfolio_risk_waterfall_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [
        ("Base", "EUR 100,000", "-"),
        ("After Delivery", "EUR 90,000", "EUR 10,000"),
    ]
    display.portfolio_risk_waterfall(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Risk Layer",
        "Expected Business Value",
        "Business Value Lost at This Layer",
    )
    assert captured["kwargs"] == {
        "title": "Portfolio Risk Waterfall (ILP-selected features)"
    }
    assert display.rendered == ["<table>"]


def test_cross_factor_sensitivity_summary_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    display.cross_factor_sensitivity_summary(
        r2_low=100_000.0,
        r2_high=90_000.0,
        r3_low=98_000.0,
        r3_high=92_000.0,
    )

    assert captured["rows"][0] == (
        "Market shock (10% -> 30%)",
        "EUR 100,000",
        "EUR 90,000",
        "EUR -10,000",
    )
    assert captured["rows"][1] == (
        "Global crisis (2.5% -> 7.5%)",
        "EUR 98,000",
        "EUR 92,000",
        "EUR -6,000",
    )
    assert captured["headers"] == (
        "Risk Factor",
        "Expected Business Value (low risk)",
        "Expected Business Value (high risk)",
        "Business Value Impact (EUR)",
    )
    assert captured["kwargs"] == {
        "title": "Cross-Factor Sensitivity - Expected Business Value Impact"
    }
    assert display.rendered == ["<table>"]


def test_risk_model_configuration_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    risk_model = SimpleNamespace(
        risk_2_market_probability=0.20,
        risk_2_market_multiplier=0.85,
        risk_3_global_probability=0.05,
        risk_3_global_multiplier=0.60,
        default_component_probability=0.10,
        component_risk_multiplier=0.70,
    )

    display.risk_model_configuration(risk_model)

    assert captured["rows"][0] == (
        "Development risk",
        "Per feature",
        "Feature is not completed -> sunk cost",
    )
    assert captured["rows"][1] == (
        "Market risk",
        "20% probability",
        "Business value drops to 85% of expected",
    )
    assert captured["headers"] == (
        "Risk Dimension",
        "Probability / Scope",
        "Impact when triggered",
    )
    assert captured["kwargs"] == {
        "title": "Risk Model Configuration (from blockchain.yaml)"
    }
    assert display.rendered == ["<table>"]


def test_portfolio_risk_waterfall_detail_handles_empty_component_cluster_map(
    monkeypatch,
):
    from fhs.presentation.notebook.charts import risk as risk_charts

    display = _RecorderDisplay()

    monkeypatch.setattr(display, "columns", lambda *args, **kwargs: None)
    monkeypatch.setattr(display, "metrics", lambda *args, **kwargs: None)
    monkeypatch.setattr(display, "sensitivity_html", lambda *args, **kwargs: "<table>")
    monkeypatch.setattr(
        risk_charts, "plot_risk_layer_decay", lambda *args, **kwargs: None
    )

    waterfall = SimpleNamespace(
        rows=[
            SimpleNamespace(layer="Base", expected=100_000.0, layer_loss=0.0),
            SimpleNamespace(
                layer="After Delivery", expected=90_000.0, layer_loss=10_000.0
            ),
        ]
    )
    portfolio_layers = SimpleNamespace(
        base=SimpleNamespace(expected=100_000.0),
        after_risk_1=SimpleNamespace(expected=90_000.0),
        after_risk_2=SimpleNamespace(expected=85_000.0),
        after_component=SimpleNamespace(expected=82_000.0),
        after_risk_3=SimpleNamespace(expected=80_000.0, var_95=70_000.0),
        waterfall_summary=lambda: waterfall,
    )
    risk_model = SimpleNamespace(
        risk_2_market_probability=0.20,
        risk_2_market_multiplier=0.85,
        risk_3_global_probability=0.05,
        risk_3_global_multiplier=0.60,
        component_risk_multiplier=0.70,
        default_component_probability=0.10,
        component_risk_by_cluster={},
    )
    features = [SimpleNamespace(likelihood_of_non_delivery=0.2)]

    display.portfolio_risk_waterfall_detail(
        portfolio_layers,
        risk_model,
        features,
        investment=75_000.0,
    )


def test_feature_profitability_matrix_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [
        (
            "Feature A",
            "72.0%",
            "EUR 12,000",
            "EUR 2,500",
            "EUR 8,000",
            "24.0%",
        )
    ]
    display.feature_profitability_matrix(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Feature",
        "Break-even probability",
        "Expected profit",
        "Expected loss",
        "Loss at Risk 95%",
        "Profit margin",
    )
    assert captured["kwargs"] == {"title": "Feature Profitability Matrix"}
    assert display.rendered == ["<table>"]


def test_feature_ranking_table_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [
        (
            "1",
            "H1: Value Stream",
            "EUR 20,000",
            "EUR 95,000",
            "EUR 60,000",
            "20%",
        )
    ]
    display.feature_ranking_table(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Rank",
        "Feature",
        "Cost",
        "Expected Business Value",
        "Business Value Floor (BVF 95%)",
        "LLP",
    )
    assert captured["kwargs"] == {"title": "Feature Ranking Table"}
    assert display.rendered == ["<table>"]


def test_risk_summary_table_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    rows = [("H1", "EUR 80,000", "EUR 45,000")]
    display.risk_summary_table(rows)

    assert captured["rows"] == rows
    assert captured["headers"] == (
        "Feature",
        "Expected Business Value",
        "BVF 95% Floor",
    )
    assert captured["kwargs"] == {"title": "Risk Summary"}
    assert display.rendered == ["<table>"]


def test_capital_budgeting_financial_wrappers_render_standard_tables(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    year1_rows = [("H1", "EUR 100,000", "EUR 60,000")]
    display.year1_business_value_snapshot(year1_rows)
    assert captured["rows"] == year1_rows
    assert captured["headers"] == (
        "Feature",
        "Expected Business Value (Year 1)",
        "BVF 95% Floor",
    )
    assert captured["kwargs"] == {"title": "Year 1 Business Value Snapshot"}

    roi_rows = [("H1", "EUR 20,000", "EUR 5,000", "EUR 100,000", "400%", "375%")]
    display.roi_analysis_table(roi_rows)
    assert captured["rows"] == roi_rows
    assert captured["headers"] == (
        "Feature",
        "Investment",
        "Annual OpEx",
        "Expected Business Value (Year 1)",
        "ROI (Gross)",
        "Net ROI (−OpEx)",
    )

    growth_rows = [("H1", "15%")]
    display.growth_inputs_table(growth_rows)
    assert captured["rows"] == growth_rows
    assert captured["headers"] == (
        "Feature",
        "Annual Growth Assumption",
    )

    npv_rows = [("H1", "EUR 20,000", "EUR 80,000", "EUR 40,000", "EUR 110,000")]
    display.npv_analysis_table(npv_rows, title="NPV")
    assert captured["rows"] == npv_rows
    assert captured["headers"] == (
        "Feature",
        "Investment",
        "NPV (Expected)",
        "NPV (Floor)",
        "NPV (Ceiling)",
    )
    assert captured["kwargs"] == {"title": "NPV"}

    irr_rows = [("H1", "EUR 20,000", "22%", "11%", "28%")]
    display.irr_analysis_table(irr_rows, title="IRR")
    assert captured["rows"] == irr_rows
    assert captured["headers"] == (
        "Feature",
        "Investment",
        "IRR (Expected)",
        "IRR (Floor)",
        "IRR (Ceiling)",
    )
    assert captured["kwargs"] == {"title": "IRR"}
    assert display.rendered == ["<table>"] * 5


def test_delivery_risk_configuration_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    delivery_config = SimpleNamespace(
        sprint_length_weeks=2,
        delay_model=SimpleNamespace(
            sprint_uncertainty=20,
            sprint_ceiling=2.5,
        ),
        cancellation=SimpleNamespace(
            max_sprints_over_plan=2,
            cancellation_probability=0.40,
        ),
    )

    display.delivery_risk_configuration(delivery_config)

    assert captured["rows"][0] == (
        "Sprint uncertainty",
        "20%",
        "Sprint duration volatility",
    )
    assert captured["rows"][2] == (
        "Sprint length",
        "2 weeks",
        "Fixed cadence for all development plans",
    )
    assert captured["rows"][-1] == (
        "Cancellation probability",
        "40%",
        "Chance after trigger",
    )
    assert captured["headers"] == ("Parameter", "Value", "Business meaning")
    assert captured["kwargs"] == {"title": "Deployment-Risk Configuration Overview"}
    assert display.rendered == ["<table>"]


def test_delivery_risk_configuration_renders_decimal_uncertainty_as_percent(
    monkeypatch,
):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    delivery_config = SimpleNamespace(
        sprint_length_weeks=2,
        delay_model=SimpleNamespace(
            sprint_uncertainty=0.2,
            sprint_ceiling=2.5,
        ),
        cancellation=SimpleNamespace(
            max_sprints_over_plan=2,
            cancellation_probability=0.40,
        ),
    )

    display.delivery_risk_configuration(delivery_config)

    assert captured["rows"][0] == (
        "Sprint uncertainty",
        "20%",
        "Sprint duration volatility",
    )


def test_profit_tail_optimization_comparison_renders_standard_table(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_table(table_rows, headers, **kwargs):
        captured["rows"] = table_rows
        captured["headers"] = headers
        captured["kwargs"] = kwargs
        return "<table>"

    monkeypatch.setattr(facade_module, "sensitivity_table", _fake_table)
    display = _RecorderDisplay()

    comparison = SimpleNamespace(
        rows=[("ILP", "EUR 10,000")],
        headers=("Method", "Profit-tail objective"),
    )

    display.profit_tail_optimization_comparison(comparison)

    assert captured["rows"] == [("ILP", "EUR 10,000")]
    assert captured["headers"] == ("Method", "Profit-tail objective")
    assert captured["kwargs"] == {"title": "Profit-Tail Optimization Comparison"}
    assert display.rendered == ["<table>"]
