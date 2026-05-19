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

"""Tests for FinancialCalculator domain service."""

import numpy as np
import numpy_financial as npf
import pytest

from src.fhs.core.services.financial import FinancialCalculator
from src.fhs.core.services.financial.calculator import discount_cashflows


class TestDiscountCashflows:
    """Tests for the pure discount_cashflows function."""

    def test_empty_input_returns_empty(self):
        result = discount_cashflows([], 0.08)
        assert len(result) == 0

    def test_single_year(self):
        scenarios = [np.array([1080.0, 2160.0])]
        result = discount_cashflows(scenarios, 0.08)
        np.testing.assert_allclose(result, [1000.0, 2000.0])

    def test_two_years(self):
        yr1 = np.array([108.0])
        yr2 = np.array([116.64])  # 100 * 1.08^2
        result = discount_cashflows([yr1, yr2], 0.08)
        expected = 108.0 / 1.08 + 116.64 / 1.08**2
        np.testing.assert_allclose(result, [expected])

    def test_zero_discount_rate_equals_sum(self):
        yr1 = np.array([100.0, 200.0])
        yr2 = np.array([300.0, 400.0])
        result = discount_cashflows([yr1, yr2], 0.0)
        np.testing.assert_allclose(result, [400.0, 600.0])

    def test_higher_rate_lowers_npv(self):
        years = [np.array([1000.0])] * 3
        low = discount_cashflows(years, 0.05)
        high = discount_cashflows(years, 0.20)
        assert low[0] > high[0]

    def test_matches_numpy_financial_npv(self):
        """Verify equivalence with numpy_financial.npv (the standard lib)."""
        rng = np.random.default_rng(42)
        yr1 = rng.normal(1000, 100, 1_000)
        yr2 = rng.normal(1100, 110, 1_000)
        yr3 = rng.normal(1200, 120, 1_000)
        rate = 0.08

        ours = discount_cashflows([yr1, yr2, yr3], rate)
        reference = np.array(
            [
                npf.npv(rate, [0, cf1, cf2, cf3])
                for cf1, cf2, cf3 in zip(yr1, yr2, yr3, strict=False)
            ]
        )
        np.testing.assert_allclose(ours, reference)


class TestFinancialCalculator:
    """Tests for FinancialCalculator service methods."""

    def test_npv_delegates_to_discount_cashflows(self):
        scenarios = [np.array([1080.0])]
        result = FinancialCalculator.npv(scenarios, 0.08)
        np.testing.assert_allclose(result, [1000.0])

    def test_npv_metrics_keys(self):
        years = [np.random.default_rng(42).normal(1000, 100, 5000) for _ in range(3)]
        metrics = FinancialCalculator.npv_metrics(years, 0.08)
        # Now returns NpvSummary VO instead of dict
        assert hasattr(metrics, "expected")
        assert hasattr(metrics, "var_95")
        assert hasattr(metrics, "p95")
        assert hasattr(metrics, "std")

    def test_npv_metrics_ordering(self):
        years = [np.random.default_rng(42).normal(1000, 100, 5000) for _ in range(3)]
        m = FinancialCalculator.npv_metrics(years, 0.08)
        assert m.var_95 <= m.expected <= m.p95

    def test_npv_metrics_empty(self):
        m = FinancialCalculator.npv_metrics([], 0.08)
        assert m.expected == 0.0
        assert m.var_95 == 0.0
        assert m.p95 == 0.0
        assert m.std == 0.0

    def test_assess_npv_positive_with_downside_warning(self):
        from src.fhs.core.model.value_objects import NpvSummary

        assessment = FinancialCalculator.assess_npv(
            NpvSummary(expected=15_000.0, var_95=-5_000.0, p95=45_000.0, std=9_000.0)
        )

        assert assessment.verdict == "GO"
        assert assessment.positive_expected is True
        assert assessment.downside_risk is True
        assert assessment.downside_message is not None

    def test_assess_npv_negative_result(self):
        from src.fhs.core.model.value_objects import NpvSummary

        assessment = FinancialCalculator.assess_npv(
            NpvSummary(expected=-10_000.0, var_95=-25_000.0, p95=4_000.0, std=8_000.0)
        )

        assert assessment.verdict == "REVIEW"
        assert assessment.positive_expected is False

    def test_result_financial_view_combines_npv_irr_and_totals(self):
        from src.fhs.core.model.value_objects import MultiYearResult, YearResult

        scenarios = np.array([100.0, 100.0, 100.0], dtype=float)
        result = MultiYearResult(
            feature_name="Portfolio",
            years=[
                YearResult.from_scenarios(year=1, scenarios=scenarios),
                YearResult.from_scenarios(year=2, scenarios=scenarios),
                YearResult.from_scenarios(year=3, scenarios=scenarios),
            ],
            discount_rate=0.0,
        )

        view = FinancialCalculator.result_financial_view(
            result,
            investment=200.0,
            discount_rate=0.0,
        )

        assert view.npv_expected == 100.0
        assert view.npv_floor == 100.0
        assert view.npv_ceiling == 100.0
        assert view.total_3y_expected == 300.0
        assert view.total_3y_floor == 300.0
        assert view.irr_expected == npf.irr([-200.0, 100.0, 100.0, 100.0])


class TestIRR:
    """Tests for IRR calculations using numpy_financial.irr."""

    def test_irr_simple_case(self):
        """Invest 100k, get 50k/year for 3 years → positive IRR."""
        irr = FinancialCalculator.irr(100_000, [50_000, 50_000, 50_000])
        # npf.irr([-100000, 50000, 50000, 50000]) ≈ 0.2339
        assert 0.20 < irr < 0.30

    def test_irr_matches_numpy_financial(self):
        """Verify exact match with npf.irr."""
        cashflows = [40_000, 60_000, 80_000]
        ours = FinancialCalculator.irr(100_000, cashflows)
        reference = float(npf.irr([-100000, *cashflows]))
        np.testing.assert_allclose(ours, reference)

    def test_irr_breakeven_is_zero(self):
        """Invest 100, get 100 back in year 1 → IRR = 0."""
        irr = FinancialCalculator.irr(100, [100])
        np.testing.assert_allclose(irr, 0.0, atol=1e-6)

    def test_irr_no_solution_returns_nan(self):
        """All negative cashflows → no IRR solution."""
        irr = FinancialCalculator.irr(100_000, [-10_000, -10_000])
        assert np.isnan(irr)

    def test_irr_higher_than_discount_means_value_creation(self):
        """If IRR > discount rate, NPV must be positive."""
        investment = 100_000
        cashflows = [50_000, 50_000, 50_000]
        irr = FinancialCalculator.irr(investment, cashflows)
        discount_rate = 0.10
        assert irr > discount_rate
        # Confirm: NPV at discount_rate is positive
        npv = float(npf.npv(discount_rate, [-investment, *cashflows]))
        assert npv > 0

    def test_irr_from_scenarios_keys(self):
        """irr_from_scenarios returns IrrSummary with expected, floor, ceiling."""
        rng = np.random.default_rng(42)
        years = [rng.normal(50_000, 5_000, 1_000) for _ in range(3)]
        result = FinancialCalculator.irr_from_scenarios(100_000, years)
        assert hasattr(result, "expected")
        assert hasattr(result, "floor")
        assert hasattr(result, "ceiling")

    def test_irr_from_scenarios_ordering(self):
        """Floor IRR < expected IRR < ceiling IRR."""
        rng = np.random.default_rng(42)
        years = [rng.normal(50_000, 5_000, 10_000) for _ in range(3)]
        r = FinancialCalculator.irr_from_scenarios(100_000, years)
        assert r.floor < r.expected < r.ceiling

    def test_irr_from_scenarios_empty(self):
        r = FinancialCalculator.irr_from_scenarios(100_000, [])
        assert np.isnan(r.expected)

    def test_assess_irr_go_with_downside_warning(self):
        from src.fhs.core.model.value_objects import IrrSummary

        assessment = FinancialCalculator.assess_irr(
            IrrSummary(expected=0.24, floor=0.07, ceiling=0.36),
            discount_rate=0.10,
        )

        assert assessment.verdict == "GO"
        assert assessment.expected_above_hurdle is True
        assert assessment.downside_below_hurdle is True
        assert assessment.downside_message is not None

    def test_assess_irr_conditional_and_review(self):
        from src.fhs.core.model.value_objects import IrrSummary

        near = FinancialCalculator.assess_irr(
            IrrSummary(expected=0.09, floor=0.08, ceiling=0.12),
            discount_rate=0.10,
        )
        weak = FinancialCalculator.assess_irr(
            IrrSummary(expected=0.06, floor=0.03, ceiling=0.09),
            discount_rate=0.10,
        )

        assert near.verdict == "CONDITIONAL_GO"
        assert weak.verdict == "REVIEW"

    def test_cumulative_metrics_returns_npv_summary(self):
        from src.fhs.core.model.value_objects import NpvSummary

        yearly = [
            np.array([100.0, 200.0, 150.0]),
            np.array([110.0, 210.0, 160.0]),
        ]
        result = FinancialCalculator.cumulative_metrics(yearly)
        assert isinstance(result, NpvSummary)
        assert result.expected == pytest.approx(310.0)
