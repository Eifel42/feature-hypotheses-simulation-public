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

"""Tests for _CapitalBudgetingMixin display methods."""

from __future__ import annotations

import math
from types import SimpleNamespace
from unittest.mock import patch

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

from fhs.presentation.notebook.widgets.facade import FHSDisplay


class _RecorderDisplay(FHSDisplay):
    def __init__(self) -> None:
        self.rendered: list[str] = []

    def __call__(self, html: str) -> None:
        self.rendered.append(html)


def _make_sched(option: str) -> dict:
    return {
        "years": [0, 1, 2, 3],
        "discount_factors": [1.0, 0.926, 0.857, 0.794],
        "rows": [
            {
                "name": "Feature A",
                "cashflows": [-100_000.0, 50_000.0, 60_000.0, 70_000.0],
                "npv": 45_000.0,
            }
        ],
        "portfolio": {
            "name": "Portfolio Total",
            "cashflows": [-100_000.0, 50_000.0, 60_000.0, 70_000.0],
            "npv": 45_000.0 if option == "a" else 55_000.0,
        },
        "inv_label": "Upfront investment: Year 0",
        "label": f"Option {option.upper()}",
    }


# ── operating_costs ───────────────────────────────────────────────────


class TestOperatingCosts:
    @staticmethod
    def _make_result() -> object:
        stats = SimpleNamespace(
            base_annual_cost=50_000.0,
            expected_cost=55_000.0,
            worst_case_cost=65_000.0,
            cost_uplift_eur=15_000.0,
        )
        return SimpleNamespace(
            per_feature={"H1: Feature A": stats},
            portfolio_base_cost=50_000.0,
            portfolio_expected_cost=55_000.0,
            portfolio_worst_case_cost=65_000.0,
            inflation_max=0.20,
            expected_inflation_pct=8.5,
        )

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.operating_costs(self._make_result())
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]

    def test_custom_title(self):
        display = _RecorderDisplay()
        display.operating_costs(self._make_result(), title="Custom OpEx")
        assert "Custom OpEx" in display.rendered[0]

    def test_feature_name_stripped(self):
        display = _RecorderDisplay()
        display.operating_costs(self._make_result())
        html = display.rendered[0]
        assert "Feature A" in html


# ── cost_variants ─────────────────────────────────────────────────────


class TestCostVariants:
    @staticmethod
    def _make_rows() -> list:
        return [
            (
                "H1: Feature A",
                "€500,000",
                "€100,000",
                "€10,000",
                "+€390,000",
                "€20,000",
                "+€470,000",
            ),
        ]

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.cost_variants(self._make_rows())
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]

    def test_custom_title(self):
        display = _RecorderDisplay()
        display.cost_variants(self._make_rows(), title="Cost Impact")
        html = display.rendered[0]
        assert "Cost Impact" in html

    def test_positive_net_cell_color(self):
        display = _RecorderDisplay()
        rows = [("F1", "€200K", "€50K", "€5K", "+€145K", "€10K", "+€185K")]
        display.cost_variants(rows)
        html = display.rendered[0]
        assert "+" in html


# ── year1_overview ────────────────────────────────────────────────────


class TestYear1Overview:
    @staticmethod
    def _make_rows(is_total: bool = False) -> tuple:
        return (
            "Portfolio Total" if is_total else "Feature A",
            500_000.0,
            350_000.0,
            300_000.0,
            100_000.0,
            10_000.0,
            390_000.0,
            20_000.0,
            470_000.0,
            is_total,
        )

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.year1_overview([self._make_rows(False)])
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]

    def test_total_row_rendering(self):
        display = _RecorderDisplay()
        display.year1_overview(
            [
                self._make_rows(False),
                self._make_rows(True),
            ]
        )
        html = display.rendered[0]
        assert "Portfolio Total" in html

    def test_negative_net_rendered(self):
        display = _RecorderDisplay()
        row = (
            "F1",
            50_000.0,
            30_000.0,
            25_000.0,
            100_000.0,
            10_000.0,
            -60_000.0,
            20_000.0,
            -70_000.0,
            False,
        )
        display.year1_overview([row])
        html = display.rendered[0]
        assert "−" in html


# ── portfolio_pl_variants ─────────────────────────────────────────────


class TestPortfolioPLVariants:
    @staticmethod
    def _make_result() -> object:
        rows = [
            SimpleNamespace(
                label="Best (P95)", bv=700_000.0, v1_net=590_000.0, v2_net=680_000.0
            ),
            SimpleNamespace(
                label="Mean (Expected)",
                bv=500_000.0,
                v1_net=390_000.0,
                v2_net=480_000.0,
            ),
            SimpleNamespace(
                label="Floor (BVF 95%)",
                bv=300_000.0,
                v1_net=190_000.0,
                v2_net=280_000.0,
            ),
            SimpleNamespace(
                label="Tail (CVaR 95%)",
                bv=250_000.0,
                v1_net=140_000.0,
                v2_net=230_000.0,
            ),
        ]
        return SimpleNamespace(
            rows=rows,
            total_investment=100_000.0,
            total_annual_opex=10_000.0,
            total_annual_installment=20_000.0,
        )

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.portfolio_pl_variants(self._make_result())
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]

    def test_custom_title(self):
        display = _RecorderDisplay()
        display.portfolio_pl_variants(self._make_result(), title="P&L View")
        assert "P&L View" in display.rendered[0]

    def test_negative_net_in_result(self):
        display = _RecorderDisplay()
        result = self._make_result()
        result.rows[1] = SimpleNamespace(
            label="Mean (Expected)", bv=50_000.0, v1_net=-50_000.0, v2_net=-30_000.0
        )
        display.portfolio_pl_variants(result)
        assert len(display.rendered) == 1


# ── npv_dual_table ────────────────────────────────────────────────────


class TestNpvDualTable:
    @staticmethod
    def _make_row() -> tuple:
        return (
            "Feature A",
            100_000.0,
            20_000.0,
            3,
            150_000.0,
            90_000.0,
            200_000.0,  # a: exp, floor, ceil
            180_000.0,
            110_000.0,
            220_000.0,  # b: exp, floor, ceil
            30_000.0,  # b - a diff
        )

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.npv_dual_table([self._make_row()])
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]

    def test_with_discount_rate(self):
        display = _RecorderDisplay()
        display.npv_dual_table([self._make_row()], discount_rate=0.08)
        html = display.rendered[0]
        assert "8%" in html

    def test_custom_title(self):
        display = _RecorderDisplay()
        display.npv_dual_table([self._make_row()], title="NPV Table")
        assert "NPV Table" in display.rendered[0]


# ── irr_dual_table ────────────────────────────────────────────────────


class TestIrrDualTable:
    @staticmethod
    def _make_row(irr_a: float = 0.15, irr_b: float = 0.22) -> tuple:
        return (
            "Feature A",
            100_000.0,
            20_000.0,
            3,
            irr_a,
            0.10,
            0.20,  # a: exp, floor, ceil
            irr_b,
            0.15,
            0.28,  # b: exp, floor, ceil
        )

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.irr_dual_table([self._make_row()])
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]

    def test_with_nan_irr(self):
        display = _RecorderDisplay()
        display.irr_dual_table([self._make_row(math.nan, math.nan)])
        assert len(display.rendered) == 1

    def test_irr_below_hurdle(self):
        display = _RecorderDisplay()
        display.irr_dual_table([self._make_row(0.05, 0.06)], discount_rate=0.08)
        assert len(display.rendered) == 1


# ── feature_cashflow_comparison ───────────────────────────────────────


class TestFeatureCashflowComparison:
    def test_renders_html(self):
        display = _RecorderDisplay()
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        display.feature_cashflow_comparison(sched_a, sched_b)
        assert len(display.rendered) == 1

    def test_with_irr_rows(self):
        display = _RecorderDisplay()
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        irr_rows = [
            ("Feature A", 100_000.0, 20_000.0, 3, 0.15, 0.10, 0.20, 0.22, 0.15, 0.28)
        ]
        display.feature_cashflow_comparison(
            sched_a,
            sched_b,
            irr_rows=irr_rows,
            portfolio_irr_a=0.13,
            portfolio_irr_b=0.18,
            discount_rate=0.08,
        )
        assert len(display.rendered) == 1

    def test_benefit_positive_when_b_higher(self):
        display = _RecorderDisplay()
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        display.feature_cashflow_comparison(sched_a, sched_b)
        html = display.rendered[0]
        assert "+" in html


# ── financing_recommendation ──────────────────────────────────────────


class TestFinancingRecommendation:
    def test_renders_html(self):
        display = _RecorderDisplay()
        display.financing_recommendation(
            "Option B is preferred due to lower initial investment."
        )
        assert len(display.rendered) == 1
        html = display.rendered[0]
        assert "Option B is preferred" in html

    def test_custom_title(self):
        display = _RecorderDisplay()
        display.financing_recommendation("Use Option A.", title="My Decision")
        assert "My Decision" in display.rendered[0]


# ── capital_budgeting_summary ─────────────────────────────────────────


class TestCapitalBudgetingSummary:
    @staticmethod
    def _make_npv(expected: float, var_95: float) -> object:
        return SimpleNamespace(expected=expected, var_95=var_95)

    @staticmethod
    def _make_irr(expected: float) -> object:
        return SimpleNamespace(expected=expected)

    def test_renders_html(self):
        display = _RecorderDisplay()
        display.capital_budgeting_summary(
            npv_a=self._make_npv(150_000.0, 90_000.0),
            npv_b=self._make_npv(180_000.0, 110_000.0),
            irr_a=self._make_irr(0.15),
            irr_b=self._make_irr(0.22),
            pi_a=1.5,
            pi_b=1.8,
            discount_rate=0.08,
        )
        assert len(display.rendered) == 1

    def test_with_verdict(self):
        display = _RecorderDisplay()
        display.capital_budgeting_summary(
            self._make_npv(150_000.0, 90_000.0),
            self._make_npv(180_000.0, 110_000.0),
            self._make_irr(0.15),
            self._make_irr(0.22),
            1.5,
            1.8,
            0.08,
            verdict_message="GO — NPV positive above hurdle rate",
            verdict_is_go=True,
        )
        assert len(display.rendered) == 1


# ── cashflow_chart (static) ───────────────────────────────────────────


class TestCashflowChart:
    def test_calls_chart_function(self):
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        with patch.object(plt, "show"):
            FHSDisplay.cashflow_chart(sched_a, sched_b)
        plt.close("all")

    def test_custom_title(self):
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        with patch.object(plt, "show"):
            FHSDisplay.cashflow_chart(sched_a, sched_b, title="Cash Flow Chart")
        plt.close("all")


# ── npv_comparison_chart ──────────────────────────────────────────────


class TestNpvComparisonChart:
    @staticmethod
    def _make_npv(expected: float, var_95: float, p95: float) -> object:
        return SimpleNamespace(expected=expected, var_95=var_95, p95=p95)

    def test_renders_html_and_chart(self):
        display = _RecorderDisplay()
        with patch.object(plt, "show"):
            display.npv_comparison_chart(
                npv_a=self._make_npv(150_000.0, 90_000.0, 200_000.0),
                npv_b=self._make_npv(180_000.0, 110_000.0, 240_000.0),
                pi_a=1.5,
                pi_b=1.8,
            )
        plt.close("all")
        assert len(display.rendered) == 1
        assert "<table" in display.rendered[0]
        assert "Option B creates more value" in display.rendered[0]
        assert "€180,000" in display.rendered[0]

    def test_with_discount_rate(self):
        display = _RecorderDisplay()
        with patch.object(plt, "show"):
            display.npv_comparison_chart(
                self._make_npv(150_000.0, 90_000.0, 200_000.0),
                self._make_npv(180_000.0, 110_000.0, 240_000.0),
                1.5,
                1.8,
                discount_rate=0.08,
            )
        plt.close("all")
        assert len(display.rendered) == 1

    def test_b_lower_npv_shows_negative_benefit(self):
        display = _RecorderDisplay()
        with patch.object(plt, "show"):
            display.npv_comparison_chart(
                self._make_npv(200_000.0, 120_000.0, 260_000.0),
                self._make_npv(150_000.0, 90_000.0, 190_000.0),
                2.0,
                1.5,
            )
        plt.close("all")
        assert len(display.rendered) == 1
        assert "Option A creates more value" in display.rendered[0]


# ── irr_chart (static) ────────────────────────────────────────────────


class TestIrrChart:
    def test_calls_chart_function(self):
        rows = [
            ("Feature A", 100_000.0, 20_000.0, 3, 0.15, 0.10, 0.20, 0.22, 0.15, 0.28)
        ]
        with patch.object(plt, "show"):
            FHSDisplay.irr_chart(rows, portfolio_irr_a=0.13, portfolio_irr_b=0.18)
        plt.close("all")

    def test_with_custom_params(self):
        with patch.object(plt, "show"):
            FHSDisplay.irr_chart([], 0.10, 0.15, hurdle_rate=0.08, title="IRR Chart")
        plt.close("all")


# ── npv_rate_curve (static) ───────────────────────────────────────────


class TestNpvRateCurve:
    def test_calls_chart_function(self):
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        with patch.object(plt, "show"):
            FHSDisplay.npv_rate_curve(sched_a, sched_b)
        plt.close("all")

    def test_with_irr_and_title(self):
        sched_a = _make_sched("a")
        sched_b = _make_sched("b")
        with patch.object(plt, "show"):
            FHSDisplay.npv_rate_curve(
                sched_a, sched_b, irr_a=0.15, irr_b=0.22, title="Rate Curve"
            )
        plt.close("all")


# ── simple sensitivity wrappers ───────────────────────────────────────


class TestSensitivityWrappers:
    def test_year1_business_value_snapshot(self):
        display = _RecorderDisplay()
        rows = [("Feature A", "€500,000", "€350,000")]
        display.year1_business_value_snapshot(rows)
        assert len(display.rendered) == 1

    def test_roi_analysis_table(self):
        display = _RecorderDisplay()
        rows = [("F1", "€100,000", "€5,000", "€500,000", "4.0×", "3.95×")]
        display.roi_analysis_table(rows)
        assert len(display.rendered) == 1

    def test_growth_inputs_table(self):
        display = _RecorderDisplay()
        display.growth_inputs_table([("Feature A", "5%/year")])
        assert len(display.rendered) == 1
