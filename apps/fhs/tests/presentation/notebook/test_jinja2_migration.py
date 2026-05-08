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

"""Regression and fitness tests for Task A4: Jinja2 Template-Migration.

Quality Gates:
- [x] Template-Output contains same key elements as f-string output
- [x] No widget-API-breaking-change (function signatures unchanged)
- [x] autoescape=True in Jinja2 Environment (XSS protection)
- [x] CSS-Helpers registered as Jinja2 Globals
- [x] Templates in templates/ directory, not inline in Python
- [x] jinja2 in pyproject.toml as runtime dependency
"""

from __future__ import annotations

import inspect

import pytest

from src.fhs.presentation.notebook.styling import COLORS
from src.fhs.presentation.notebook.template_engine import env

# ── Quality Gate: autoescape=True ─────────────────────────────────────


class TestTemplateEngineConfig:
    """Verify Jinja2 environment configuration."""

    def test_autoescape_enabled(self):
        assert env.autoescape is True

    def test_trim_blocks_enabled(self):
        assert env.trim_blocks is True

    def test_lstrip_blocks_enabled(self):
        assert env.lstrip_blocks is True


# ── Quality Gate: CSS-Helpers as Jinja2 Globals ──────────────────────


class TestGlobalsRegistered:
    """All CSS helpers and COLORS must be registered as globals."""

    @pytest.mark.parametrize(
        "name",
        [
            "COLORS",
            "card_wrapper",
            "table_base",
            "table_caption",
            "table_header_row",
            "section_title",
            "flex_row",
            "text_style",
            "label_style",
            "grid_layout",
            "alternating_bg",
            "risk_icon",
            "footer_block",
        ],
    )
    def test_global_registered(self, name):
        assert name in env.globals, f"Global '{name}' not registered"

    def test_colors_is_colors_instance(self):
        assert env.globals["COLORS"] is COLORS


# ── Quality Gate: Custom Filters ─────────────────────────────────────


class TestCustomFilters:
    """Custom number formatting filters registered."""

    @pytest.mark.parametrize("name", ["eur", "pct", "pct1", "signed_pct", "thousands"])
    def test_filter_registered(self, name):
        assert name in env.filters

    def test_eur_filter(self):
        assert env.filters["eur"](1234567) == "EUR 1,234,567"

    def test_pct_filter_ratio(self):
        assert env.filters["pct"](0.5) == "50%"

    def test_pct_filter_percentage(self):
        assert env.filters["pct"](50) == "50%"

    def test_pct1_filter(self):
        assert env.filters["pct1"](23.456) == "23.5%"

    def test_signed_pct_filter(self):
        assert env.filters["signed_pct"](-5.3) == "-5.3%"

    def test_thousands_filter(self):
        assert env.filters["thousands"](1234567) == "1,234,567"


# ── Quality Gate: No widget-API-breaking-change ──────────────────────


class TestWidgetAPISignatures:
    """Function signatures must not change after migration."""

    def test_metric_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import metric_table

        sig = inspect.signature(metric_table)
        assert "rows" in sig.parameters
        assert "title" in sig.parameters
        assert "metric_header" in sig.parameters
        assert "value_header" in sig.parameters

    def test_risk_contribution_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import risk_contribution_table

        sig = inspect.signature(risk_contribution_table)
        assert "rows" in sig.parameters

    def test_comparison_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import comparison_table

        sig = inspect.signature(comparison_table)
        assert "rows" in sig.parameters
        assert "headers" in sig.parameters
        assert "title" in sig.parameters

    def test_backlog_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import backlog_table

        sig = inspect.signature(backlog_table)
        assert "features" in sig.parameters
        assert "strategy" in sig.parameters
        assert "title" in sig.parameters

    def test_stress_test_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import stress_test_table

        sig = inspect.signature(stress_test_table)
        assert "scenarios" in sig.parameters
        assert "baseline" in sig.parameters
        assert "title" in sig.parameters

    def test_ranking_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import ranking_table

        sig = inspect.signature(ranking_table)
        assert "rows" in sig.parameters
        assert "title" in sig.parameters

    def test_sensitivity_table_signature(self):
        from src.fhs.presentation.notebook.widgets.tables import sensitivity_table

        sig = inspect.signature(sensitivity_table)
        assert "rows" in sig.parameters
        assert "headers" in sig.parameters
        assert "title" in sig.parameters

    def test_feature_risk_card_signature(self):
        from src.fhs.presentation.notebook.widgets.cards import feature_risk_card

        sig = inspect.signature(feature_risk_card)
        params = set(sig.parameters)
        assert {
            "name",
            "expected_eur",
            "var95_eur",
            "risk_ratio",
            "icon",
            "color",
        } <= params

    def test_selection_card_signature(self):
        from src.fhs.presentation.notebook.widgets.portfolio import selection_card

        sig = inspect.signature(selection_card)
        assert "selected_features" in sig.parameters
        assert "metrics" in sig.parameters

    def test_optimizer_results_card_signature(self):
        from src.fhs.presentation.notebook.widgets.portfolio import (
            optimizer_results_card,
        )

        sig = inspect.signature(optimizer_results_card)
        params = set(sig.parameters)
        assert {
            "selected",
            "total_cost",
            "expected_business_value",
            "var95",
            "budget_remaining",
        } <= params

    def test_decision_grid_signature(self):
        from src.fhs.presentation.notebook.widgets.comparison import decision_grid

        sig = inspect.signature(decision_grid)
        assert "items" in sig.parameters
        assert "title" in sig.parameters
        assert "footer" in sig.parameters

    def test_solver_comparison_card_signature(self):
        from src.fhs.presentation.notebook.widgets.comparison import (
            solver_comparison_card,
        )

        sig = inspect.signature(solver_comparison_card)
        assert "title" in sig.parameters


# ── Quality Gate: Template-Output contains key elements ──────────────


class TestMetricTableOutput:
    """metric_table renders correct HTML structure."""

    def test_contains_table_element(self):
        from src.fhs.presentation.notebook.widgets.tables import metric_table

        r = metric_table([("Business Value", "EUR 100,000", COLORS.secondary)])
        assert "<table" in r
        assert "Business Value" in r
        assert "EUR 100,000" in r

    def test_caption_present(self):
        from src.fhs.presentation.notebook.widgets.tables import metric_table

        r = metric_table([("X", "Y", None)], title="My Title")
        assert "My Title" in r
        assert "<caption" in r

    def test_alternating_bg(self):
        from src.fhs.presentation.notebook.widgets.tables import metric_table

        r = metric_table([("A", "1", None), ("B", "2", None)])
        assert COLORS.background in r
        assert COLORS.surface in r


class TestRiskContributionTableOutput:
    def test_contains_feature_data(self):
        from src.fhs.presentation.notebook.widgets.tables import risk_contribution_table

        r = risk_contribution_table([("FeatA", 0.5, 100000, 20000, 25.0, 60.0)])
        assert "FeatA" in r
        assert "<table" in r


class TestComparisonTableOutput:
    def test_contains_comparison_data(self):
        from src.fhs.presentation.notebook.widgets.tables import comparison_table

        r = comparison_table([("Alpha", 100000, 80000, 70000)])
        assert "Alpha" in r
        assert "<table" in r


class TestBacklogTableOutput:
    @staticmethod
    def _make_feature(
        name="Test",
        users=10000,
        conv=0.05,
        uncertainty=0.2,
        cost=50000,
        bvpc=10.0,
    ):
        from unittest.mock import MagicMock

        f = MagicMock()
        f.name = name
        f.expected_users = users
        f.conversion_rate = conv
        f.uncertainty = uncertainty
        f.development_cost = cost
        f.business_value_per_conversion = bvpc
        return f

    def test_contains_feature_name(self):
        from src.fhs.presentation.notebook.widgets.tables import backlog_table

        feat = self._make_feature()
        r = backlog_table([feat], {"Test": {"category": "Core"}})
        assert "Test" in r
        assert "Core" in r
        assert "📋" in r

    def test_contains_portfolio_total(self):
        from src.fhs.presentation.notebook.widgets.tables import backlog_table

        feat = self._make_feature()
        r = backlog_table([feat], {"Test": {"category": "Core"}})
        assert "Portfolio total" in r


class TestStressTestTableOutput:
    def test_contains_scenario_data(self):
        from src.fhs.presentation.notebook.widgets.tables import stress_test_table

        r = stress_test_table(
            [
                {
                    "name": "Recession",
                    "stressed_value": 60000,
                    "change_pct": -20.0,
                    "color": COLORS.danger,
                }
            ],
            baseline=75000,
        )
        assert "Recession" in r
        assert "75,000" in r


class TestRankingTableOutput:
    def test_contains_ranked_features(self):
        from src.fhs.presentation.notebook.widgets.tables import ranking_table

        r = ranking_table(
            [
                {
                    "feature": "Alpha",
                    "expected_business_value": 100000,
                    "var_95_business_value": 80000,
                    "risk_ratio": 0.15,
                },
            ]
        )
        assert "Alpha" in r
        assert "🟢" in r  # low risk icon


class TestSensitivityTableOutput:
    def test_contains_data(self):
        from src.fhs.presentation.notebook.widgets.tables import sensitivity_table

        r = sensitivity_table(
            [("Low", "80,000", "70,000")],
            ("Scenario", "Business Value", "VaR95"),
        )
        assert "Low" in r
        assert "Sensitivity" in r


class TestFeatureRiskCardOutput:
    def test_contains_feature_data(self):
        from src.fhs.presentation.notebook.widgets.cards import feature_risk_card

        r = feature_risk_card("MyFeature", 100000, 80000, 0.15)
        assert "MyFeature" in r
        assert "EUR 100,000" in r
        assert "EUR 80,000" in r
        assert "🟢" in r  # low risk

    def test_contains_risk_ratio(self):
        from src.fhs.presentation.notebook.widgets.cards import feature_risk_card

        r = feature_risk_card("X", 100000, 80000, 0.45)
        assert "🔴" in r  # high risk
        assert "45%" in r


class TestSelectionCardOutput:
    def test_contains_selection_data(self):
        from src.fhs.presentation.notebook.widgets.portfolio import selection_card

        r = selection_card(
            ["FeatureA", "FeatureB"],
            {
                "total_expected_business_value": 200000,
                "portfolio_var_95": 150000,
                "portfolio_risk_ratio": 0.25,
            },
        )
        assert "FeatureA" in r
        assert "FeatureB" in r
        assert "200,000" in r
        assert "✅" in r

    def test_excluded_features(self):
        from src.fhs.presentation.notebook.widgets.portfolio import selection_card

        r = selection_card(
            ["A"],
            {
                "total_expected_business_value": 100000,
                "portfolio_var_95": 80000,
                "portfolio_risk_ratio": 0.2,
            },
            excluded_features=["B"],
        )
        assert "❌" in r
        assert "B" in r


class TestOptimizerResultsCardOutput:
    def test_contains_optimizer_data(self):
        from src.fhs.presentation.notebook.widgets.portfolio import (
            optimizer_results_card,
        )

        r = optimizer_results_card(["A", "B"], 100000, 200000, 80000, 50000)
        assert "Optimization Results" in r
        assert "TOTAL COST" in r
        assert "BUDGET REMAINING" in r
        assert "EXPECTED PROFIT" in r
        assert "VAR 95%" in r
        assert "✅" in r


class TestDecisionGridOutput:
    def test_contains_grid_items(self):
        from src.fhs.presentation.notebook.widgets.comparison import decision_grid

        r = decision_grid(
            [
                {
                    "title": "Option A",
                    "color": COLORS.primary,
                    "description": "First option",
                }
            ],
            title="Decision",
        )
        assert "Option A" in r
        assert "Decision" in r


class TestSolverComparisonOutput:
    def test_contains_solver_data(self):
        from src.fhs.presentation.notebook.widgets.comparison import (
            solver_comparison_card,
        )

        solver = {
            "recommended_features": ["A", "B"],
            "total_cost": 100000,
            "portfolio_expected": 200000,
            "portfolio_var_95": 150000,
            "roi": 0.5,
            "combinations_evaluated": 100,
            "computation_time_sec": 0.01,
        }
        r = solver_comparison_card(solver, solver)
        assert "A, B" in r
        assert "same portfolio" in r


# ── Quality Gate: capital_budgeting_summary template ─────────────────


class TestCapitalBudgetingSummaryTemplate:
    """capital_budgeting_summary renders via Jinja2 template."""

    @staticmethod
    def _make_npv(expected, var_95):
        from types import SimpleNamespace

        return SimpleNamespace(expected=expected, var_95=var_95)

    @staticmethod
    def _make_irr(expected):
        from types import SimpleNamespace

        return SimpleNamespace(expected=expected)

    def test_contains_key_elements(self):
        from src.fhs.presentation.notebook.template_engine import render

        html = render(
            "capital_budgeting/summary.html.j2",
            title="My Summary",
            npv_a_expected=100_000,
            npv_a_var95=-10_000,
            npv_b_expected=150_000,
            npv_b_var95=20_000,
            irr_a_expected=0.12,
            irr_b_expected=0.18,
            pi_a=1.2,
            pi_b=1.6,
            discount_rate=0.08,
            benefit=50_000,
            benefit_floor=30_000,
            verdict_message="",
            verdict_is_go=True,
        )
        assert "My Summary" in html
        assert "Option A" in html
        assert "Option B" in html
        assert "12%" in html  # irr_a
        assert "1.60" in html  # pi_b

    def test_nan_irr_shows_positive_y1(self):
        from src.fhs.presentation.notebook.template_engine import render

        html = render(
            "capital_budgeting/summary.html.j2",
            title="T",
            npv_a_expected=0,
            npv_a_var95=0,
            npv_b_expected=0,
            npv_b_var95=0,
            irr_a_expected=float("nan"),
            irr_b_expected=float("nan"),
            pi_a=1.0,
            pi_b=1.0,
            discount_rate=0.08,
            benefit=0,
            benefit_floor=0,
            verdict_message="",
            verdict_is_go=True,
        )
        assert "Positive Y1" in html

    def test_verdict_shown_when_set(self):
        from src.fhs.presentation.notebook.template_engine import render

        html = render(
            "capital_budgeting/summary.html.j2",
            title="T",
            npv_a_expected=0,
            npv_a_var95=0,
            npv_b_expected=0,
            npv_b_var95=0,
            irr_a_expected=0.1,
            irr_b_expected=0.2,
            pi_a=1.0,
            pi_b=1.5,
            discount_rate=0.08,
            benefit=0,
            benefit_floor=0,
            verdict_message="GO — B is better",
            verdict_is_go=True,
        )
        assert "GO — B is better" in html

    def test_verdict_hidden_when_empty(self):
        from src.fhs.presentation.notebook.template_engine import render

        html = render(
            "capital_budgeting/summary.html.j2",
            title="T",
            npv_a_expected=0,
            npv_a_var95=0,
            npv_b_expected=0,
            npv_b_var95=0,
            irr_a_expected=0.1,
            irr_b_expected=0.2,
            pi_a=1.0,
            pi_b=1.5,
            discount_rate=0.08,
            benefit=0,
            benefit_floor=0,
            verdict_message="",
            verdict_is_go=True,
        )
        # Verdict block only rendered when message is non-empty
        assert "border-left:4px solid" not in html or "margin-top:10px" not in html


# ── Quality Gate: XSS Protection ─────────────────────────────────────


class TestXSSProtection:
    """autoescape=True must prevent XSS in user-controlled data."""

    def test_feature_name_escaped(self):
        from src.fhs.presentation.notebook.widgets.cards import feature_risk_card

        r = feature_risk_card('<script>alert("xss")</script>', 100000, 80000, 0.2)
        assert "<script>" not in r
        assert "&lt;script&gt;" in r

    def test_metric_table_escapes_values(self):
        from src.fhs.presentation.notebook.widgets.tables import metric_table

        r = metric_table([("<img src=x onerror=alert(1)>", "safe", None)])
        assert "<img src=x" not in r
        assert "&lt;img" in r
