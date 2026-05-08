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

"""Tests for FeatureCalculationService."""

import pytest

from fhs.application.calculation_service import FeatureCalculationService
from fhs.core.model import BudgetCheckResult, Feature


def _feature(name: str, cost: float) -> Feature:
    return Feature(
        name=name,
        expected_users=10_000,
        conversion_rate=0.20,
        uncertainty=0.15,
        business_value_per_conversion=10.0,
        development_cost=cost,
        annual_growth_rate=0.05,
        likelihood_of_non_delivery=0.10,
    )


def test_budget_check_returns_typed_result() -> None:
    features = [
        _feature("H1: Feature One", 50_000.0),
        _feature("H2: Feature Two", 30_000.0),
    ]

    result = FeatureCalculationService.budget_check(features, budget=100_000.0)

    assert isinstance(result, BudgetCheckResult)
    assert len(result.rows) == 2
    assert result.total_cost == 80_000.0
    assert result.budget_left == 20_000.0
    assert result.fits_budget is True
    assert result.small_buffer is False


def test_budget_check_marks_small_buffer_and_over_budget() -> None:
    features = [
        _feature("H1: Feature One", 70_000.0),
        _feature("H2: Feature Two", 35_000.0),
    ]

    result = FeatureCalculationService.budget_check(features, budget=100_000.0)

    assert result.fits_budget is False
    assert result.budget_left == -5_000.0

    near_limit = FeatureCalculationService.budget_check(
        [_feature("H3: Feature Three", 94_000.0)],
        budget=100_000.0,
    )
    assert near_limit.fits_budget is True
    assert near_limit.small_buffer is True


class TestNetValueMethods:
    @staticmethod
    def _feature(dev_cost=60_000.0, installment_years=3, opex=12_000.0):
        from fhs.core.model import Feature

        return Feature(
            name="F",
            expected_users=1_000,
            conversion_rate=0.2,
            uncertainty=0.1,
            development_cost=dev_cost,
            installment_years=installment_years,
            annual_operating_cost=opex,
        )

    def test_net_value_full_cost_positive(self):
        f = self._feature(dev_cost=10_000.0, opex=5_000.0)
        result = FeatureCalculationService.net_value_full_cost_year1(f, 20_000.0)
        assert result == pytest.approx(5_000.0)

    def test_net_value_full_cost_negative(self):
        f = self._feature(dev_cost=80_000.0, opex=10_000.0)
        result = FeatureCalculationService.net_value_full_cost_year1(f, 50_000.0)
        assert result == pytest.approx(-40_000.0)

    def test_net_value_pl_uses_annual_installment(self):
        # dev_cost=60_000, installment_years=3 → annual_installment=20_000
        f = self._feature(dev_cost=60_000.0, installment_years=3, opex=5_000.0)
        result = FeatureCalculationService.net_value_pl_year1(f, 30_000.0)
        # 30_000 - 20_000 - 5_000 = 5_000
        assert result == pytest.approx(5_000.0)

    def test_net_value_pl_positive_when_full_cost_negative(self):
        # Feature that does not pay back full cost in year 1 but covers P&L charge
        f = self._feature(dev_cost=60_000.0, installment_years=3, opex=5_000.0)
        # v1: 25_000 - 60_000 - 5_000 = -40_000 (negative)
        # v2: 25_000 - 20_000 - 5_000 =   0 (breakeven)
        assert FeatureCalculationService.net_value_full_cost_year1(
            f, 25_000.0
        ) == pytest.approx(-40_000.0)
        assert FeatureCalculationService.net_value_pl_year1(
            f, 25_000.0
        ) == pytest.approx(0.0)

    def test_net_value_zero_opex(self):
        f = self._feature(dev_cost=10_000.0, installment_years=1, opex=0.0)
        assert FeatureCalculationService.net_value_full_cost_year1(
            f, 15_000.0
        ) == pytest.approx(5_000.0)
        assert FeatureCalculationService.net_value_pl_year1(
            f, 15_000.0
        ) == pytest.approx(5_000.0)
