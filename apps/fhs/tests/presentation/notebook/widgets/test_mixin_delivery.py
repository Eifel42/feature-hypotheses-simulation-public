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

"""Tests for _DeliveryMixin display methods."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from fhs.presentation.notebook.widgets.facade import FHSDisplay


class _RecorderDisplay(FHSDisplay):
    def __init__(self) -> None:
        self.rendered: list[str] = []

    def __call__(self, html: str) -> None:
        self.rendered.append(html)


def _make_feature(name: str, cost: float) -> object:
    return SimpleNamespace(name=name, development_cost=cost)


def _make_delivery_result(cost_cvar: float = 120_000.0) -> object:
    return SimpleNamespace(
        cost_cvar=cost_cvar,
        expected_actual_cost=115_000.0,
        cost_p95=130_000.0,
        cancelled_pct=0.05,
        cost_uplift=0.15,
    )


# ── budget_fit_ranking ────────────────────────────────────────────────


class TestBudgetFitRanking:
    def test_renders_samples_table(self):
        display = _RecorderDisplay()
        features = [_make_feature("F1", 100_000.0), _make_feature("F2", 150_000.0)]
        delivery_results = {
            "F1": _make_delivery_result(110_000.0),
            "F2": _make_delivery_result(160_000.0),
        }
        display.budget_fit_ranking(features, delivery_results)
        assert len(display.rendered) == 1

    def test_custom_title(self):
        display = _RecorderDisplay()
        features = [_make_feature("F1", 100_000.0)]
        delivery_results = {"F1": _make_delivery_result()}
        display.budget_fit_ranking(features, delivery_results, title="Custom Ranking")
        assert len(display.rendered) == 1


# ── budget_fit_summary_cvar ───────────────────────────────────────────


class TestBudgetFitSummaryCvar:
    def test_renders_metrics(self):
        display = _RecorderDisplay()
        features = [_make_feature("F1", 100_000.0)]
        delivery_results = {"F1": _make_delivery_result()}
        display.budget_fit_summary_cvar(features, delivery_results, budget=500_000.0)
        assert len(display.rendered) == 1

    def test_custom_title(self):
        display = _RecorderDisplay()
        features = [_make_feature("F1", 100_000.0)]
        delivery_results = {"F1": _make_delivery_result()}
        display.budget_fit_summary_cvar(
            features, delivery_results, 500_000.0, title="Budget Overview"
        )
        assert len(display.rendered) == 1


# ── cost_risk_selection ───────────────────────────────────────────────


class TestCostRiskSelection:
    def _make_result(self, budget_pressure: float = 0.10) -> dict:
        return {
            "selected": ["Feature A", "Feature B"],
            "budget_pressure": budget_pressure,
            "total_planned_cost": 200_000.0,
            "budget_remaining": 300_000.0,
            "expected_cost": 215_000.0,
            "portfolio_car": 240_000.0,
            "portfolio_cvar": 250_000.0,
        }

    def test_renders_columns(self):
        display = _RecorderDisplay()
        display.cost_risk_selection(self._make_result(0.10))
        assert len(display.rendered) == 1

    def test_positive_budget_pressure(self):
        display = _RecorderDisplay()
        display.cost_risk_selection(self._make_result(0.25))
        assert len(display.rendered) == 1

    def test_negative_budget_pressure(self):
        display = _RecorderDisplay()
        display.cost_risk_selection(self._make_result(-0.05))
        assert len(display.rendered) == 1

    def test_empty_selected(self):
        display = _RecorderDisplay()
        result = self._make_result()
        result["selected"] = []
        display.cost_risk_selection(result)
        assert len(display.rendered) == 1

    def test_custom_title_and_objective(self):
        display = _RecorderDisplay()
        display.cost_risk_selection(
            self._make_result(),
            title="My Selection",
            objective="Minimise CVaR",
        )
        assert len(display.rendered) == 1


# ── budget_fit_and_select ─────────────────────────────────────────────


class TestBudgetFitAndSelect:
    def test_renders_all_sections(self):
        display = _RecorderDisplay()
        features = [_make_feature("F1", 100_000.0)]
        delivery_results = {"F1": _make_delivery_result()}
        mock_selection = {
            "selected": ["F1"],
            "budget_pressure": 0.05,
            "total_planned_cost": 100_000.0,
            "budget_remaining": 400_000.0,
            "expected_cost": 115_000.0,
            "portfolio_car": 130_000.0,
            "portfolio_cvar": 120_000.0,
        }
        mock_combination_rows = [
            (
                "1",
                "Yes",
                "1",
                "F1",
                "EUR 100,000",
                "EUR 400,000",
                "EUR 120,000",
                "+5.0%",
            )
        ]
        with (
            patch(
                "fhs.application.delivery_analysis_operations.DeliveryAnalysisOperations.min_cost_cvar_selection",
                return_value=mock_selection,
            ),
            patch(
                "fhs.application.delivery_analysis_operations.DeliveryAnalysisOperations.cost_risk_combination_rows",
                return_value=mock_combination_rows,
            ),
        ):
            display.budget_fit_and_select(features, delivery_results, budget=500_000.0)
        assert len(display.rendered) >= 1
