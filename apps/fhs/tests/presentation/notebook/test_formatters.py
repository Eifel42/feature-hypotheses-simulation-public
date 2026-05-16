#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Test suite for delivery risk analysis formatters."""

import numpy as np

from fhs.core.model import Feature
from fhs.core.model.value_objects.multi_year_result import MultiYearResult, YearResult
from fhs.presentation.notebook.formatters import (
    format_budget_risk_drop_rows,
    format_budget_status,
    format_feature_rows,
    format_multi_budget_rows,
    format_multi_year_result,
    format_summary_row,
)


class TestFormatFeatureRows:
    """Test suite for format_feature_rows()."""

    def test_empty_features(self):
        """Empty features list returns empty rows."""
        result = format_feature_rows({"features": []})
        assert result == []

    def test_no_features_key(self):
        """Missing 'features' key returns empty rows."""
        result = format_feature_rows({})
        assert result == []

    def test_single_feature(self):
        """Single feature with default values."""
        delivery_risk = {
            "features": [
                {
                    "name": "API Redesign",
                    "non_delivery_risk": 0.2,
                    "delivered_pct": 0.8,
                }
            ]
        }
        rows = format_feature_rows(delivery_risk)

        assert len(rows) == 1
        name, risk, delivered = rows[0]
        assert name == "API Redesign"
        assert risk == "20%"
        assert delivered == "80.0%"

    def test_strip_section_prefix(self):
        """Section prefix 'Section: Name' is stripped."""
        delivery_risk = {
            "features": [
                {
                    "name": "Core: API Redesign",
                    "non_delivery_risk": 0.15,
                    "delivered_pct": 0.85,
                }
            ]
        }
        rows = format_feature_rows(delivery_risk)
        name, _, _ = rows[0]
        assert name == "API Redesign"

    def test_high_risk_feature(self):
        """Feature with 40% non-delivery risk."""
        delivery_risk = {
            "features": [
                {
                    "name": "Risky Feature",
                    "non_delivery_risk": 0.40,
                    "delivered_pct": 0.60,
                }
            ]
        }
        rows = format_feature_rows(delivery_risk)
        _name, risk, delivered = rows[0]
        assert risk == "40%"
        assert delivered == "60.0%"

    def test_multiple_features(self):
        """Multiple features are formatted correctly."""
        delivery_risk = {
            "features": [
                {
                    "name": "Feature 1",
                    "non_delivery_risk": 0.1,
                    "delivered_pct": 0.9,
                },
                {
                    "name": "Feature 2",
                    "non_delivery_risk": 0.3,
                    "delivered_pct": 0.7,
                },
            ]
        }
        rows = format_feature_rows(delivery_risk)

        assert len(rows) == 2
        assert rows[0] == ("Feature 1", "10%", "90.0%")
        assert rows[1] == ("Feature 2", "30%", "70.0%")

    def test_percentage_formatting(self):
        """Risk percentages are formatted with 0 decimals, delivery with 1."""
        delivery_risk = {
            "features": [
                {
                    "name": "Test",
                    "non_delivery_risk": 0.123,
                    "delivered_pct": 0.765,
                }
            ]
        }
        rows = format_feature_rows(delivery_risk)
        _, risk, delivered = rows[0]
        assert risk == "12%"  # Rounded to 0 decimals
        assert delivered == "76.5%"  # 1 decimal


class TestFormatBudgetStatus:
    def test_budget_below_cheapest_feature_is_danger(self):
        features = [
            Feature(
                name="H1: UI",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=30_000,
            ),
            Feature(
                name="H2: Traceability",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=20_000,
            ),
        ]

        result = format_budget_status(
            features, 10_000, source="cfg.yml", scenarios=100_000
        )

        assert result["level"] == "danger"
        assert "cheapest feature" in result["message"]
        assert result["affordable_count"] == 0
        assert "Source: cfg.yml" in result["note"]

    def test_budget_below_full_portfolio_is_warning(self):
        features = [
            Feature(
                name="H1: UI",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=75_000,
            ),
            Feature(
                name="H2: Traceability",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=50_000,
            ),
            Feature(
                name="H3: Alerts",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=20_000,
            ),
        ]

        result = format_budget_status(features, 20_000)

        assert result["level"] == "warning"
        assert "need to choose the first step" in result["message"]
        assert result["affordable_count"] == 1

    def test_budget_covering_all_features_is_success(self):
        features = [
            Feature(
                name="H1: UI",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=10_000,
            ),
            Feature(
                name="H2: Traceability",
                expected_users=1,
                conversion_rate=0.1,
                uncertainty=0.1,
                development_cost=15_000,
            ),
        ]

        result = format_budget_status(features, 30_000)

        assert result["level"] == "success"
        assert result["total_cost"] == 25_000
        assert result["affordable_count"] == 2


class TestFormatMultiYearResult:
    def test_renders_year_rows_and_aggregates(self):
        result = MultiYearResult(
            feature_name="H1: UI",
            years=[
                YearResult(
                    1, np.array([1.0, 2.0]), 100_000, 70_000, 65_000, 130_000, 10_000
                ),
                YearResult(
                    2, np.array([1.0, 2.0]), 120_000, 84_000, 78_000, 156_000, 12_000
                ),
                YearResult(
                    3, np.array([1.0, 2.0]), 144_000, 101_000, 94_000, 187_000, 14_000
                ),
            ],
            discount_rate=0.08,
        )

        html = format_multi_year_result(result)

        assert "Multi-Year Simulation" in html
        assert "Year 1" in html
        assert "3Y Total" in html
        assert "NPV 8%" in html
        assert "€100,000" in html

    def test_empty_result_still_renders(self):
        result = MultiYearResult(feature_name="Empty", years=[], discount_rate=0.08)
        html = format_multi_year_result(result)
        assert "Empty" in html

    @staticmethod
    def _make_result() -> MultiYearResult:
        return MultiYearResult(
            feature_name="H1: UI",
            years=[
                YearResult(
                    1, np.array([1.0, 2.0]), 100_000, 70_000, 65_000, 130_000, 10_000
                ),
                YearResult(
                    2, np.array([1.0, 2.0]), 120_000, 84_000, 78_000, 156_000, 12_000
                ),
                YearResult(
                    3, np.array([1.0, 2.0]), 144_000, 101_000, 94_000, 187_000, 14_000
                ),
            ],
            discount_rate=0.08,
        )

    def test_installment_years_gt1_shows_period_label(self):
        html = format_multi_year_result(
            self._make_result(),
            annual_installment=25_000,
            installment_years=3,
        )
        assert "Installment (3 yrs)" in html
        assert "straight-line over 3 years" in html

    def test_installment_years_default_keeps_original_label(self):
        html = format_multi_year_result(
            self._make_result(),
            annual_installment=25_000,
        )
        assert "Annual Installment" in html
        assert "Straight-line cost charge per year" in html

    def test_development_cost_shows_investment_row(self):
        html = format_multi_year_result(
            self._make_result(),
            annual_installment=25_000,
            installment_years=3,
            development_cost=75_000,
        )
        assert "Total Investment" in html
        assert "€75,000" in html
        assert "Year-1 charge" in html
        assert "33%" in html

    def test_development_cost_zero_hides_investment_row(self):
        html = format_multi_year_result(
            self._make_result(),
            annual_installment=25_000,
            installment_years=3,
            development_cost=0.0,
        )
        assert "Total Investment" not in html

    def test_no_installment_hides_both_rows(self):
        html = format_multi_year_result(self._make_result())
        assert "Total Investment" not in html
        assert "Annual Installment" not in html


class TestFormatSummaryRow:
    """Test suite for format_summary_row()."""

    def test_basic_summary_row(self):
        """Basic summary row with market and shock data."""
        l1 = {
            "market_expected": 1_000_000,
            "market_var_95": 800_000,
            "simulated_expected": 950_000,
            "simulated_var_95": 750_000,
        }
        l3 = {
            "shocked_expected": 600_000,
            "shocked_var_95": 400_000,
        }

        row = format_summary_row("Exact", l1, l3)

        assert row == (
            "Exact",
            "EUR 1,000,000",
            "EUR 800,000",
            "EUR 950,000",
            "EUR 750,000",
            "EUR 600,000",
            "EUR 400,000",
        )

    def test_ilp_solver_label(self):
        """ILP solver label is preserved."""
        l1 = {
            "market_expected": 500_000,
            "market_var_95": 400_000,
            "simulated_expected": 480_000,
            "simulated_var_95": 380_000,
        }
        l3 = {
            "shocked_expected": 300_000,
            "shocked_var_95": 200_000,
        }

        row = format_summary_row("ILP", l1, l3)
        assert row[0] == "ILP"

    def test_euro_formatting(self):
        """Large numbers are formatted with thousands separators."""
        l1 = {
            "market_expected": 1_234_567,
            "market_var_95": 1_000_000,
            "simulated_expected": 1_234_567,
            "simulated_var_95": 1_000_000,
        }
        l3 = {
            "shocked_expected": 500_000,
            "shocked_var_95": 400_000,
        }

        row = format_summary_row("Exact", l1, l3)
        assert "1,234,567" in row[1]

    def test_zero_values(self):
        """Zero values are formatted correctly."""
        l1 = {
            "market_expected": 0,
            "market_var_95": 0,
            "simulated_expected": 0,
            "simulated_var_95": 0,
        }
        l3 = {
            "shocked_expected": 0,
            "shocked_var_95": 0,
        }

        row = format_summary_row("Exact", l1, l3)
        assert row[1] == "EUR 0"


class TestFormatMultiBudgetRows:
    """Test suite for format_multi_budget_rows()."""

    def test_empty_budgets(self):
        """Empty budget list returns empty rows."""
        rows = format_multi_budget_rows([], {})
        assert rows == []

    def test_single_budget_exact_solver(self):
        """Single budget with exact solver result."""
        budgets = [400_000]
        budget_results = {
            400_000: {
                "exact": {
                    "feature_count": 5,
                    "l1": {
                        "market_expected": 1_000_000,
                        "market_var_95": 800_000,
                        "simulated_var_95": 750_000,
                        "var_delta_pct": -6.25,
                    },
                    "l3": {
                        "shocked_var_95": 500_000,
                        "shocked_var_delta_pct": -37.5,
                    },
                }
            }
        }

        rows = format_multi_budget_rows(budgets, budget_results)

        assert len(rows) == 1
        budget, solver, count, l1_exp, _l1_var, _l2_var, _l3_var = rows[0]
        assert budget == "EUR 400k"
        assert solver == "Exact"
        assert count == "5"
        assert "EUR 1,000,000" in l1_exp

    def test_multi_budget_both_solvers(self):
        """Two budgets with both exact and ILP solvers."""
        budgets = [135_000, 400_000]
        budget_results = {
            135_000: {
                "exact": {
                    "feature_count": 2,
                    "l1": {
                        "market_expected": 500_000,
                        "market_var_95": 400_000,
                        "simulated_var_95": 380_000,
                        "var_delta_pct": -5.0,
                    },
                    "l3": {
                        "shocked_var_95": 250_000,
                        "shocked_var_delta_pct": -37.5,
                    },
                },
                "ilp": {
                    "feature_count": 3,
                    "l1": {
                        "market_expected": 550_000,
                        "market_var_95": 420_000,
                        "simulated_var_95": 400_000,
                        "var_delta_pct": -4.8,
                    },
                    "l3": {
                        "shocked_var_95": 260_000,
                        "shocked_var_delta_pct": -38.1,
                    },
                },
            },
            400_000: {
                "exact": {
                    "feature_count": 5,
                    "l1": {
                        "market_expected": 1_000_000,
                        "market_var_95": 800_000,
                        "simulated_var_95": 750_000,
                        "var_delta_pct": -6.25,
                    },
                    "l3": {
                        "shocked_var_95": 500_000,
                        "shocked_var_delta_pct": -37.5,
                    },
                },
            },
        }

        rows = format_multi_budget_rows(budgets, budget_results)

        assert len(rows) == 3  # 2 from 135k (exact+ilp) + 1 from 400k (exact)
        assert rows[0][0] == "EUR 135k"
        assert rows[1][0] == "EUR 135k"
        assert rows[2][0] == "EUR 400k"

    def test_missing_budget_skipped(self):
        """Budgets not in results are skipped."""
        budgets = [100_000, 200_000]
        budget_results = {
            200_000: {
                "exact": {
                    "feature_count": 3,
                    "l1": {
                        "market_expected": 600_000,
                        "market_var_95": 500_000,
                        "simulated_var_95": 480_000,
                        "var_delta_pct": -4.0,
                    },
                    "l3": {
                        "shocked_var_95": 350_000,
                        "shocked_var_delta_pct": -30.0,
                    },
                }
            }
        }

        rows = format_multi_budget_rows(budgets, budget_results)

        assert len(rows) == 1
        assert rows[0][0] == "EUR 200k"

    def test_missing_solver_skipped(self):
        """Budget entries without target solver are skipped."""
        budgets = [400_000]
        budget_results = {
            400_000: {
                "exact": {
                    "feature_count": 5,
                    "l1": {
                        "market_expected": 1_000_000,
                        "market_var_95": 800_000,
                        "simulated_var_95": 750_000,
                        "var_delta_pct": -6.25,
                    },
                    "l3": {
                        "shocked_var_95": 500_000,
                        "shocked_var_delta_pct": -37.5,
                    },
                }
                # ILP missing
            }
        }

        rows = format_multi_budget_rows(budgets, budget_results)

        assert len(rows) == 1
        assert rows[0][1] == "Exact"

    def test_zero_features_skipped(self):
        """Solver results with zero features are skipped."""
        budgets = [400_000]
        budget_results = {
            400_000: {
                "exact": {
                    "feature_count": 0,  # Empty portfolio
                    "l1": {},
                    "l3": {},
                }
            }
        }

        rows = format_multi_budget_rows(budgets, budget_results)
        assert rows == []

    def test_delta_percentage_formatting(self):
        """Delta percentages include +/- sign."""
        budgets = [400_000]
        budget_results = {
            400_000: {
                "exact": {
                    "feature_count": 5,
                    "l1": {
                        "market_expected": 1_000_000,
                        "market_var_95": 800_000,
                        "simulated_var_95": 750_000,
                        "var_delta_pct": -6.25,
                    },
                    "l3": {
                        "shocked_var_95": 500_000,
                        "shocked_var_delta_pct": -37.5,
                    },
                }
            }
        }

        rows = format_multi_budget_rows(budgets, budget_results)
        _, _, _, _, _, l2_var, _ = rows[0]
        assert "-6.2%" in l2_var  # L2 formatting should include sign


class TestFormatBudgetRiskDropRows:
    """Test suite for format_budget_risk_drop_rows()."""

    def test_formats_budget_risk_drop_rows(self):
        budgets = [135_000]
        budget_results = {
            135_000: {
                "exact": {
                    "feature_count": 2,
                    "l1": {
                        "var_delta_pct": -12.5,
                    },
                    "l3": {
                        "shocked_var_delta_pct": -44.0,
                    },
                }
            }
        }

        rows = format_budget_risk_drop_rows(budgets, budget_results)

        assert rows == [("EUR 135k", "Exact", "2", "-12.5%", "-44.0%")]

    def test_skips_missing_solver_data(self):
        rows = format_budget_risk_drop_rows([135_000], {135_000: {}})
        assert rows == []
