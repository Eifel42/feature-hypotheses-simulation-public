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

"""Tests for _PortfolioMixin display methods."""

from __future__ import annotations

from types import SimpleNamespace

from fhs.presentation.notebook.widgets.facade import FHSDisplay


class _RecorderDisplay(FHSDisplay):
    def __init__(self) -> None:
        self.rendered: list[str] = []

    def __call__(self, html: str) -> None:
        self.rendered.append(html)


# ── portfolio ─────────────────────────────────────────────────────────


class TestPortfolioSummary:
    def test_renders_html(self):
        display = _RecorderDisplay()
        display.portfolio(expected=1_000_000.0, var95=700_000.0, std=150_000.0)
        assert len(display.rendered) == 1

    def test_with_cvar(self):
        display = _RecorderDisplay()
        display.portfolio(
            1_000_000.0, 700_000.0, 150_000.0, cvar95=650_000.0, title="Summary"
        )
        assert len(display.rendered) == 1


# ── kpi ───────────────────────────────────────────────────────────────


class TestKpi:
    def test_renders_html(self):
        display = _RecorderDisplay()
        card1 = FHSDisplay.kpi_card("€500K", "Expected Value")
        card2 = FHSDisplay.kpi_card("€350K", "Floor", color="#c62828")
        display.kpi(card1, card2)
        assert len(display.rendered) == 1

    def test_kpi_card_returns_string(self):
        card = FHSDisplay.kpi_card("€1M", "Label")
        assert isinstance(card, str)
        assert "€1M" in card
        assert "Label" in card


# ── feature_risk_card ─────────────────────────────────────────────────


class TestFeatureRiskCard:
    def test_returns_html_string(self):
        card = FHSDisplay.feature_risk_card(
            name="Feature A",
            expected_eur=500_000.0,
            var95_eur=350_000.0,
            risk_ratio=0.3,
        )
        assert isinstance(card, str)
        assert "Feature A" in card

    def test_with_optional_params(self):
        card = FHSDisplay.feature_risk_card(
            "F1",
            300_000.0,
            200_000.0,
            0.2,
            cvar95_eur=180_000.0,
            icon="📊",
            color="#1565c0",
        )
        assert isinstance(card, str)


# ── comparison ────────────────────────────────────────────────────────


class TestComparison:
    def test_renders_html(self):
        display = _RecorderDisplay()
        rows = [("Feature A", 500_000.0, 350_000.0, 300_000.0)]
        display.comparison(rows)
        assert len(display.rendered) == 1

    def test_custom_headers_and_title(self):
        display = _RecorderDisplay()
        rows = [("F1", 100_000.0, 80_000.0, 70_000.0)]
        display.comparison(
            rows,
            headers=("Name", "EV", "VaR", "CVaR"),
            title="My Comparison",
        )
        assert len(display.rendered) == 1


# ── budget_status ─────────────────────────────────────────────────────


class TestBudgetStatus:
    @staticmethod
    def _make_feature(name: str, cost: float) -> object:
        return SimpleNamespace(name=name, development_cost=cost)

    def test_renders_success_when_under_budget(self):
        display = _RecorderDisplay()
        features = [self._make_feature("F1", 100_000.0)]
        display.budget_status(500_000.0, features)
        # should call metrics + success/warning/danger
        assert len(display.rendered) >= 1

    def test_renders_warning_when_over_budget(self):
        display = _RecorderDisplay()
        features = [
            self._make_feature("F1", 400_000.0),
            self._make_feature("F2", 200_000.0),
        ]
        display.budget_status(500_000.0, features)
        assert len(display.rendered) >= 1

    def test_with_source_and_scenarios(self):
        display = _RecorderDisplay()
        features = [self._make_feature("F1", 50_000.0)]
        display.budget_status(
            100_000.0, features, source="blockchain.yaml", scenarios=10_000
        )
        assert len(display.rendered) >= 1

    def test_renders_danger_when_over_budget(self):
        display = _RecorderDisplay()
        features = [self._make_feature("F1", 700_000.0)]
        display.budget_status(100_000.0, features)
        assert len(display.rendered) >= 1


# ── multi_year ────────────────────────────────────────────────────────


class TestMultiYear:
    @staticmethod
    def _make_result() -> object:
        import numpy as np

        scenarios = np.array([450_000.0, 500_000.0, 550_000.0])
        year_result = SimpleNamespace(
            year=1,
            expected=500_000.0,
            var_95=350_000.0,
            p95=700_000.0,
            spread_pct=20.0,
            scenarios=scenarios,
        )
        return SimpleNamespace(
            years=[year_result], discount_rate=0.08, feature_name="Feature A"
        )

    def test_renders_html(self):
        display = _RecorderDisplay()
        result = self._make_result()
        display.multi_year(result)
        assert len(display.rendered) == 1

    def test_with_installment_and_cost(self):
        display = _RecorderDisplay()
        result = self._make_result()
        display.multi_year(
            result,
            annual_installment=50_000.0,
            installment_years=3,
            development_cost=150_000.0,
        )
        assert len(display.rendered) == 1


# ── selection ─────────────────────────────────────────────────────────


class TestSelection:
    @staticmethod
    def _metrics() -> dict:
        return {
            "total_expected_business_value": 800_000.0,
            "portfolio_var_95": 550_000.0,
            "portfolio_risk_ratio": 0.31,
        }

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.selection(
            selected_features=["Feature A", "Feature B"],
            metrics=self._metrics(),
        )
        assert len(display.rendered) == 1

    def test_with_excluded_features(self):
        display = _RecorderDisplay()
        display.selection(
            ["F1"],
            self._metrics(),
            excluded_features=["F2", "F3"],
        )
        assert len(display.rendered) == 1


# ── optimizer ─────────────────────────────────────────────────────────


class TestOptimizer:
    def test_renders_html(self):
        display = _RecorderDisplay()
        display.optimizer(
            selected=["Feature A"],
            total_cost=100_000.0,
            expected_business_value=500_000.0,
            var95=350_000.0,
            budget_remaining=400_000.0,
        )
        assert len(display.rendered) == 1

    def test_with_optional_params(self):
        display = _RecorderDisplay()
        display.optimizer(
            selected=["F1", "F2"],
            total_cost=200_000.0,
            expected_business_value=800_000.0,
            var95=550_000.0,
            budget_remaining=300_000.0,
            roi=3.0,
            net_value=600_000.0,
            cvar95=500_000.0,
            budget_pressure=-0.05,
            objective="Maximise expected value",
            accent="#1565c0",
            title="My Optimizer",
        )
        assert len(display.rendered) == 1


# ── npv_comparison ────────────────────────────────────────────────────


class TestNpvComparison:
    def test_renders_html(self):
        display = _RecorderDisplay()
        rows = [("Feature A", "EUR 100,000", "EUR 50,000", "EUR 150,000", "1.5")]
        display.npv_comparison(rows)
        assert len(display.rendered) == 1


# ── npv_decision_table ────────────────────────────────────────────────


class TestNpvDecisionTable:
    def test_renders_html(self):
        display = _RecorderDisplay()
        rows = [("Low", "EUR 300K", "1Y", "F1, F2", "EUR 100K", "Proceed")]
        display.npv_decision_table(rows)
        assert len(display.rendered) == 1


class TestAdditionalPortfolioTables:
    def test_backlog_scorecard_and_solver_compare_render(self):
        display = _RecorderDisplay()
        feature = SimpleNamespace(
            name="H1: Simplified UI",
            expected_users=1_000,
            conversion_rate=0.1,
            business_value_per_conversion=2.0,
            uncertainty=0.2,
            development_cost=10_000.0,
            likelihood_of_non_delivery=0.1,
            acceptance_model="binomial",
        )

        display.backlog(
            [feature], {feature.name: {"category": "Grow", "reason": "Test"}}
        )
        display.scorecard(["<div>card</div>"])
        display.solver_compare(
            {
                "recommended_features": ["H1"],
                "total_cost": 10_000.0,
                "portfolio_expected": 20_000.0,
                "portfolio_var_95": 12_000.0,
                "roi": 1.0,
                "computation_time_sec": 0.01,
            }
        )

        assert len(display.rendered) == 3

    def test_standard_table_wrappers_render(self):
        display = _RecorderDisplay()
        rows = [("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")]

        display.solver_results(rows)
        display.selected_portfolio_details([("H1", "Grow", "EUR 1", "EUR 2", "EUR 1")])
        display.practical_decision_table(rows)
        display.feature_value_risk_baseline(
            [("H1", "UI", "EUR 1", "EUR 2", "EUR 1", "10%", "Low")]
        )
        display.feature_profitability_matrix(
            [("H1", "90%", "EUR 1", "EUR 0", "EUR 0", "10%")]
        )
        display.feature_ranking_table([("1", "H1", "EUR 1", "EUR 2", "EUR 1", "10%")])

        assert len(display.rendered) == 6

    def test_ilp_selection_explanation_uses_selection_headers(self):
        display = _RecorderDisplay()
        selection = SimpleNamespace(
            headers=("Feature", "Reason"),
            rows=(("H1", "Budget"),),
        )

        display.ilp_selection_explanation(selection)

        assert len(display.rendered) == 1

    def test_sprint_plan_html_uses_configured_sprint_length(self):
        display = _RecorderDisplay()
        feature = SimpleNamespace(
            name="H9: Partial Sprint",
            development_weeks=4.8,
            development_cost=12_000.0,
        )
        config = SimpleNamespace(sprint_length_weeks=1)

        html, rows = display.sprint_plan_html([feature], config)

        assert "Partial Sprint" in html
        assert rows == [("Partial Sprint", "4.8", "5", "EUR 12,000")]

    def test_delivery_tables_skip_missing_and_handle_zero_planned(self):
        display = _RecorderDisplay()
        features = [
            SimpleNamespace(name="H1: Included", development_cost=0.0),
            SimpleNamespace(name="H2: Missing", development_cost=10_000.0),
        ]
        result = SimpleNamespace(
            expected_actual_cost=12_000.0,
            cost_p95=15_000.0,
            cost_cvar=16_000.0,
            cost_uplift=-1.0,
            cancelled_pct=0.25,
        )

        display.cost_comparison(features, {"H1: Included": result})
        display.delivery_cost_risk(features, {"H1: Included": result})

        assert len(display.rendered) == 2

    def test_delay_summary_sorts_when_feature_names_missing(self):
        display = _RecorderDisplay()
        result = SimpleNamespace(
            planned_sprints=2,
            sprints_p50=2,
            sprints_p75=3,
            sprints_p95=4,
            cancelled_pct=0.1,
        )

        display.delay_summary({"H2: Beta": result, "H1: Alpha": result})

        assert len(display.rendered) == 1

    def test_feature_overview_uses_grid_and_backlog(self, monkeypatch):
        display = _RecorderDisplay()
        calls: dict[str, object] = {}
        feature = SimpleNamespace(
            name="H1: Simplified UI",
            expected_users=1_000,
            conversion_rate=0.1,
            business_value_per_conversion=2.0,
            uncertainty=0.2,
            development_cost=10_000.0,
            likelihood_of_non_delivery=0.1,
            dependency_cluster="Customer Platform",
            planned_release="R1",
            installment_years=2,
            annual_installment=5_000.0,
            year1_business_value_at_risk=1_500.0,
            acceptance_model="binomial",
        )

        monkeypatch.setattr(
            display, "info", lambda message: calls.setdefault("info", message)
        )
        monkeypatch.setattr(
            display,
            "grid",
            lambda items, title="": calls.setdefault("grid", (items, title)),
        )
        monkeypatch.setattr(
            display,
            "backlog",
            lambda features, strategy, **kwargs: calls.setdefault(
                "backlog", (features, strategy, kwargs)
            ),
        )

        display.feature_overview(
            [feature],
            {feature.name: {"category": "Grow", "reason": "Improve flow"}},
            config_path="notebooks/config/blockchain.yaml",
            colors={"H1": "#123456"},
        )

        assert "blockchain.yaml" in calls["info"]
        assert calls["grid"][0][0]["title"] == "H1 — Simplified UI"
        assert calls["backlog"][0] == [feature]
