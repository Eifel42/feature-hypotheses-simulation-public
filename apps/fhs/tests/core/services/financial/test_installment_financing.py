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

"""Tests for installment-financing NPV/IRR in FinancialCalculator.

Covers:
- result_npv_installment: first installment at Year 0, remaining in years 1..(n-1)
- irr_installment: Year-0 anchor, always has sign change when annual_installment > 0
- irr_installment_from_scenarios: summary statistics from scenario arrays
"""

import math

import numpy as np

from src.fhs.core.services.financial.calculator import FinancialCalculator

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_result(yearly_values: list[float], discount_rate: float = 0.08):
    """Build a minimal MultiYearResult-like object with constant scenario arrays."""
    from src.fhs.core.model.value_objects.multi_year_result import (
        MultiYearResult,
        YearResult,
    )

    years = [
        YearResult.from_scenarios(year=i + 1, scenarios=np.full(1_000, v))
        for i, v in enumerate(yearly_values)
    ]
    return MultiYearResult(
        feature_name="Test",
        years=years,
        discount_rate=discount_rate,
    )


# ── result_npv_installment ────────────────────────────────────────────────────


class TestNpvInstallment:
    def test_n1_year0_only_payment(self):
        """With installment_years=1, only Year 0 pays; Year 1 has no installment.

        Y0: -100, Y1: +200 (no installment since year_num=1 is NOT < 1).
        NPV_B (r=0) = -100 + 200 = 100.
        """
        result = _make_result([200.0], discount_rate=0.0)
        npv = FinancialCalculator.result_npv_installment(result, 100.0, 1, 0.0)
        assert abs(npv.expected - 100.0) < 0.01

    def test_installment_deducted_only_in_first_n_minus_1_years(self):
        """Installment applies to Y0 and years 1..(n-1), not year n onward.

        3 years, installment_years=2, Inst=50, r=0.
        Y0=-50, Y1=200-50=150, Y2=200 (no installment since 2 NOT < 2), Y3=200.
        NPV_B (r=0) = -50 + 150 + 200 + 200 = 500.
        """
        result = _make_result([200.0, 200.0, 200.0], discount_rate=0.0)
        npv = FinancialCalculator.result_npv_installment(result, 50.0, 2, 0.0)
        assert abs(npv.expected - 500.0) < 0.01

    def test_npv_b_higher_than_npv_a_with_positive_discount(self):
        """NPV_B > NPV_A when r > 0: spreading payments captures time value."""
        result = _make_result([100.0, 100.0, 100.0], discount_rate=0.08)
        investment = 200.0
        installment = investment / 3
        npv_a = FinancialCalculator.result_npv(result, investment, 0.08)
        npv_b = FinancialCalculator.result_npv_installment(result, installment, 3, 0.08)
        assert npv_b.expected > npv_a.expected

    def test_npv_b_equals_npv_a_when_rate_zero(self):
        """At r=0, timing makes no difference — NPV_B = NPV_A."""
        result = _make_result([100.0, 100.0, 100.0], discount_rate=0.0)
        investment = 90.0
        npv_a = FinancialCalculator.result_npv(result, investment, 0.0)
        npv_b = FinancialCalculator.result_npv_installment(
            result, investment / 3, 3, 0.0
        )
        assert abs(npv_b.expected - npv_a.expected) < 0.01

    def test_empty_result_returns_zero_summary(self):
        from src.fhs.core.model.value_objects.multi_year_result import MultiYearResult

        result = MultiYearResult(feature_name="Empty", years=[], discount_rate=0.08)
        npv = FinancialCalculator.result_npv_installment(result, 50.0, 2, 0.08)
        assert npv.expected == 0.0
        assert npv.var_95 == 0.0

    def test_var_95_and_p95_populated(self):
        """Percentile statistics should be present in the result."""
        result = _make_result([80.0, 80.0, 80.0], discount_rate=0.08)
        npv = FinancialCalculator.result_npv_installment(result, 30.0, 2, 0.08)
        # Constant scenarios → all percentiles equal (allow tiny float noise)
        assert npv.var_95 <= npv.expected + 1e-6
        assert npv.p95 >= npv.expected - 1e-6


# ── irr_installment ───────────────────────────────────────────────────────────


class TestIrrInstallment:
    def test_always_has_sign_change_with_positive_installment(self):
        """Year-0 installment is always negative → sign change always exists."""
        # Y0=-50, Y1=200 (no installment since 1 NOT < 1), Y2=200, Y3=200
        irr = FinancialCalculator.irr_installment(50.0, 1, [200.0, 200.0, 200.0])
        assert not math.isnan(irr)
        assert irr > 0.0

    def test_returns_valid_irr_with_n1(self):
        """n=1: only Y0 pays; all future cashflows are positive."""
        # cf = [-200, 10, 300, 300] → valid IRR
        irr = FinancialCalculator.irr_installment(200.0, 1, [10.0, 300.0, 300.0])
        assert not math.isnan(irr)
        assert irr > 0.0

    def test_installment_years_2_pays_y0_and_y1(self):
        """installment_years=2: pays at Y0 and Y1 only; Y2+ free.

        Y0=-1000, Y1=50-1000=-950, Y2=2000 (free). Sign change exists.
        """
        irr = FinancialCalculator.irr_installment(1000.0, 2, [50.0, 50.0, 2000.0])
        assert not math.isnan(irr)

    def test_returns_nan_when_truly_no_sign_change(self):
        """Returns NaN only when no cashflow is negative (e.g. zero installment)."""
        irr = FinancialCalculator.irr_installment(0.0, 1, [200.0, 200.0, 200.0])
        assert math.isnan(irr)

    def test_n3_pays_y0_y1_y2_free_y3(self):
        """installment_years=3: pays at Y0, Y1, Y2; Y3 is free."""
        # Y0=-30, Y1=100-30=70, Y2=100-30=70, Y3=100 (free since 3 NOT < 3)
        irr = FinancialCalculator.irr_installment(30.0, 3, [100.0, 100.0, 100.0])
        assert not math.isnan(irr)
        assert irr > 0.0


# ── irr_installment_from_scenarios ────────────────────────────────────────────


class TestIrrInstallmentFromScenarios:
    def test_returns_irr_summary(self):
        from src.fhs.core.model.value_objects import IrrSummary

        scenarios = [np.full(500, 10.0), np.full(500, 400.0), np.full(500, 400.0)]
        result = FinancialCalculator.irr_installment_from_scenarios(200.0, 1, scenarios)
        assert isinstance(result, IrrSummary)

    def test_valid_irr_when_year0_creates_sign_change(self):
        """Year-0 installment creates sign change → IRR is finite."""
        scenarios = [np.full(500, 300.0), np.full(500, 300.0), np.full(500, 300.0)]
        result = FinancialCalculator.irr_installment_from_scenarios(50.0, 1, scenarios)
        assert not math.isnan(result.expected)
        assert result.expected > 0.0

    def test_empty_scenarios_returns_nan_summary(self):
        result = FinancialCalculator.irr_installment_from_scenarios(100.0, 2, [])
        assert math.isnan(result.expected)
