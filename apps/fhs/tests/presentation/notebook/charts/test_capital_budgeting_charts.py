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

"""Tests for capital budgeting chart functions and widget helper functions."""

from __future__ import annotations

from unittest.mock import patch

import matplotlib
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")


# ── chart helpers (pure functions) ────────────────────────────────────


class TestContrastTextColor:
    def test_dark_fill_returns_light(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _contrast_text_color,
        )

        result = _contrast_text_color("#000000")
        assert isinstance(result, str)
        assert result.startswith("#")

    def test_light_fill_returns_dark(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _contrast_text_color,
        )

        result = _contrast_text_color("#ffffff")
        assert isinstance(result, str)

    def test_mid_gray(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _contrast_text_color,
        )

        result = _contrast_text_color("#808080")
        assert isinstance(result, str)

    def test_named_color(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _contrast_text_color,
        )

        result = _contrast_text_color("blue")
        assert isinstance(result, str)


class TestNpvValue:
    def test_zero_rate_sums_cashflows(self):
        from fhs.presentation.notebook.charts.capital_budgeting import _npv_value

        cashflows = [100.0, 200.0, 300.0]
        result = _npv_value(cashflows, 0.0)
        assert abs(result - 600.0) < 1e-6

    def test_positive_rate_discounts(self):
        from fhs.presentation.notebook.charts.capital_budgeting import _npv_value

        cashflows = [-100.0, 110.0]
        result = _npv_value(cashflows, 0.10)
        assert result > -100.0

    def test_single_cashflow(self):
        from fhs.presentation.notebook.charts.capital_budgeting import _npv_value

        assert abs(_npv_value([100.0], 0.05) - 100.0) < 1e-6

    def test_empty_cashflows(self):
        from fhs.presentation.notebook.charts.capital_budgeting import _npv_value

        assert _npv_value([], 0.10) == 0.0


class TestFindNonNegativeIrr:
    def test_typical_investment(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _find_non_negative_irr,
        )

        # [-100, 50, 60] has a positive IRR
        cashflows = [-100.0, 50.0, 60.0]
        result = _find_non_negative_irr(cashflows)
        assert result is not None
        assert result >= 0.0

    def test_no_irr_all_negative(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _find_non_negative_irr,
        )

        cashflows = [-100.0, -50.0, -60.0]
        result = _find_non_negative_irr(cashflows)
        # No positive IRR root exists
        assert result is None or result < 0

    def test_immediate_zero_npv(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _find_non_negative_irr,
        )

        # NPV is already 0 at rate=0
        cashflows = [0.0, 0.0]
        result = _find_non_negative_irr(cashflows)
        assert result == 0.0

    def test_high_irr(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            _find_non_negative_irr,
        )

        # Large positive cash immediately after investment
        cashflows = [-100.0, 300.0]
        result = _find_non_negative_irr(cashflows)
        assert result is not None
        assert result > 1.0  # >100%


class TestPctFormatter:
    def test_rounds_to_integer(self):
        from fhs.presentation.notebook.charts.capital_budgeting import _pct_formatter

        assert _pct_formatter(0.0, None) == "0%"
        assert _pct_formatter(15.7, None) == "16%"
        assert _pct_formatter(-5.3, None) == "-5%"


# ── chart functions (matplotlib) ──────────────────────────────────────


@pytest.fixture
def irr_rows():
    return [
        ("Feature A", 100_000, 25_000, 4, 0.15, 0.08, 0.25, 0.20, 0.12, 0.30),
        ("Feature B", 200_000, 50_000, 4, 0.12, 0.05, 0.20, 0.18, 0.10, 0.28),
    ]


@pytest.fixture
def cashflows_a():
    return [-500_000.0, 200_000.0, 200_000.0, 200_000.0]


@pytest.fixture
def cashflows_b():
    return [-150_000.0, 200_000.0, 150_000.0, 150_000.0]


@pytest.fixture
def schedule_a():
    return {
        "years": [0, 1, 2, 3],
        "portfolio": {
            "cashflows": [-500_000.0, 200_000.0, 200_000.0, 200_000.0],
            "npv": 50_000.0,
        },
    }


@pytest.fixture
def schedule_b():
    return {
        "years": [0, 1, 2, 3],
        "portfolio": {
            "cashflows": [-150_000.0, 200_000.0, 150_000.0, 150_000.0],
            "npv": 80_000.0,
        },
    }


class TestPlotIrrFeatureChart:
    def test_runs_without_error(self, irr_rows):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_irr_feature_chart,
        )

        with patch.object(plt, "show"):
            plot_irr_feature_chart(irr_rows, 0.14, 0.19, 0.08)
        plt.close("all")

    def test_with_nan_irr(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_irr_feature_chart,
        )

        rows = [
            (
                "Feature A",
                100_000,
                25_000,
                4,
                float("nan"),
                0.05,
                0.15,
                0.12,
                0.08,
                0.20,
            ),
        ]
        with patch.object(plt, "show"):
            plot_irr_feature_chart(rows, 0.10, 0.12, 0.08)
        plt.close("all")

    def test_custom_title(self, irr_rows):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_irr_feature_chart,
        )

        with patch.object(plt, "show"):
            plot_irr_feature_chart(irr_rows, 0.14, 0.19, title="My IRR Chart")
        plt.close("all")

    def test_empty_rows(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_irr_feature_chart,
        )

        with patch.object(plt, "show"):
            plot_irr_feature_chart([], 0.10, 0.12)
        plt.close("all")


class TestPlotNpvRateCurve:
    def test_runs_without_error(self, cashflows_a, cashflows_b):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_rate_curve,
        )

        with patch.object(plt, "show"):
            plot_npv_rate_curve(cashflows_a, cashflows_b)
        plt.close("all")

    def test_with_precomputed_irr(self, cashflows_a, cashflows_b):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_rate_curve,
        )

        with patch.object(plt, "show"):
            plot_npv_rate_curve(cashflows_a, cashflows_b, irr_a=0.15, irr_b=0.20)
        plt.close("all")

    def test_with_none_irr(self, cashflows_a, cashflows_b):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_rate_curve,
        )

        with patch.object(plt, "show"):
            plot_npv_rate_curve(cashflows_a, cashflows_b, irr_a=None, irr_b=None)
        plt.close("all")

    def test_custom_hurdle_rate(self, cashflows_a, cashflows_b):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_rate_curve,
        )

        with patch.object(plt, "show"):
            plot_npv_rate_curve(cashflows_a, cashflows_b, hurdle_rate=0.12)
        plt.close("all")


class TestPlotCashflowBars:
    def test_runs_without_error(self, schedule_a, schedule_b):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_cashflow_bars,
        )

        with patch.object(plt, "show"):
            plot_cashflow_bars(schedule_a, schedule_b)
        plt.close("all")

    def test_custom_title(self, schedule_a, schedule_b):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_cashflow_bars,
        )

        with patch.object(plt, "show"):
            plot_cashflow_bars(schedule_a, schedule_b, title="Custom")
        plt.close("all")

    def test_negative_cashflows(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_cashflow_bars,
        )

        sched_a = {
            "years": [0, 1],
            "portfolio": {"cashflows": [-500_000.0, -100_000.0], "npv": -400_000.0},
        }
        sched_b = {
            "years": [0, 1],
            "portfolio": {"cashflows": [-200_000.0, 50_000.0], "npv": -100_000.0},
        }
        with patch.object(plt, "show"):
            plot_cashflow_bars(sched_a, sched_b)
        plt.close("all")


class TestPlotNpvComparison:
    def test_runs_without_error(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_comparison,
        )

        with patch.object(plt, "show"):
            plot_npv_comparison(
                npv_a_expected=500_000.0,
                npv_a_floor=300_000.0,
                npv_a_ceiling=700_000.0,
                npv_b_expected=600_000.0,
                npv_b_floor=400_000.0,
                npv_b_ceiling=800_000.0,
                pi_a=1.5,
                pi_b=1.8,
            )
        plt.close("all")

    def test_negative_npv(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_comparison,
        )

        with patch.object(plt, "show"):
            plot_npv_comparison(
                npv_a_expected=-100_000.0,
                npv_a_floor=-300_000.0,
                npv_a_ceiling=50_000.0,
                npv_b_expected=200_000.0,
                npv_b_floor=50_000.0,
                npv_b_ceiling=400_000.0,
                pi_a=0.8,
                pi_b=1.3,
                discount_rate=0.08,
            )
        plt.close("all")

    def test_custom_title(self):
        from fhs.presentation.notebook.charts.capital_budgeting import (
            plot_npv_comparison,
        )

        with patch.object(plt, "show"):
            plot_npv_comparison(
                500_000.0,
                300_000.0,
                700_000.0,
                600_000.0,
                400_000.0,
                800_000.0,
                1.5,
                1.8,
                title="My NPV Chart",
            )
        plt.close("all")


# ── widget helper functions ───────────────────────────────────────────


class TestIrrComparisonPanel:
    def test_empty_irr_rows_returns_empty_string(self):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _irr_comparison_panel,
        )

        result = _irr_comparison_panel([], {}, {}, 0.08, None, None, [], "Portfolio")
        assert result == ""

    def test_none_irr_rows_returns_empty_string(self):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _irr_comparison_panel,
        )

        result = _irr_comparison_panel(None, {}, {}, 0.08, None, None, [], "Portfolio")
        assert result == ""

    def test_with_features_returns_html(self):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _irr_comparison_panel,
        )

        irr_rows = [("Feature A",)]
        irr_map_a = {"Feature A": 0.15}
        irr_map_b = {"Feature A": 0.20}
        result = _irr_comparison_panel(
            irr_rows, irr_map_a, irr_map_b, 0.08, 0.14, 0.19, ["Feature A"], "Portfolio"
        )
        assert "<table" in result
        assert "Feature A" in result

    def test_portfolio_irr_none(self):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _irr_comparison_panel,
        )

        irr_rows = [("Feature A",)]
        result = _irr_comparison_panel(
            irr_rows,
            {"Feature A": 0.10},
            {},
            0.08,
            None,
            None,
            ["Feature A"],
            "Portfolio",
        )
        assert "<table" in result

    def test_hurdle_note_in_result(self):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _irr_comparison_panel,
        )

        irr_rows = [("F",)]
        result = _irr_comparison_panel(irr_rows, {}, {}, 0.10, 0.12, 0.15, ["F"], "PF")
        assert "Hurdle rate" in result
        assert "10%" in result


class TestRenderCashflowTable:
    @pytest.fixture
    def schedule(self):
        return {
            "years": [0, 1, 2, 3],
            "discount_factors": [1.0, 0.926, 0.857, 0.794],
            "rows": [
                {
                    "name": "Feature A",
                    "cashflows": [-100_000.0, 50_000.0, 60_000.0, 70_000.0],
                    "npv": 45_000.0,
                },
                {
                    "name": "Feature B",
                    "cashflows": [-200_000.0, 80_000.0, 90_000.0, 100_000.0],
                    "npv": 20_000.0,
                },
            ],
            "portfolio": {
                "name": "Portfolio Total",
                "cashflows": [-300_000.0, 130_000.0, 150_000.0, 170_000.0],
                "npv": 65_000.0,
            },
            "inv_label": "Upfront investment: Year 0",
            "label": "Option A — Upfront",
        }

    def test_returns_html_string(self, schedule):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _render_cashflow_table,
        )

        result = _render_cashflow_table(schedule, "#1565c0", 0.08)
        assert isinstance(result, str)
        assert "<table" in result

    def test_contains_feature_names(self, schedule):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _render_cashflow_table,
        )

        result = _render_cashflow_table(schedule, "#1565c0", 0.08)
        assert "Feature A" in result
        assert "Feature B" in result

    def test_contains_portfolio_total(self, schedule):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _render_cashflow_table,
        )

        result = _render_cashflow_table(schedule, "#1565c0", 0.08)
        assert "Portfolio Total" in result

    def test_contains_label(self, schedule):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _render_cashflow_table,
        )

        result = _render_cashflow_table(schedule, "#1565c0", 0.08)
        assert "Option A" in result

    def test_negative_npv_portfolio(self, schedule):
        from fhs.presentation.notebook.widgets._capital_budgeting import (
            _render_cashflow_table,
        )

        schedule["portfolio"]["npv"] = -50_000.0
        result = _render_cashflow_table(schedule, "#c62828", 0.08)
        assert "<table" in result
