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
    def _make_feature(self, name: str, cost: float) -> object:
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


# ── multi_year ────────────────────────────────────────────────────────


class TestMultiYear:
    def _make_result(self) -> object:
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
    def _metrics(self) -> dict:
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
