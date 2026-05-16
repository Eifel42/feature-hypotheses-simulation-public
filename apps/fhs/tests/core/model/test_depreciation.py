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

"""Tests for installment_years field and annual_installment property."""

import pytest

from fhs.core.model import Feature, SimulationResult


class TestFeatureInstallment:
    """Tests for installment_years and annual_installment on Feature."""

    def test_default_installment_years_is_one(self):
        """Default: full cost in year 1."""
        f = Feature(
            name="H1", expected_users=1000, conversion_rate=0.1, uncertainty=0.2
        )
        assert f.installment_years == 1

    def test_annual_installment_equals_full_cost_when_default(self):
        """With default of 1 year, annual_installment == development_cost."""
        f = Feature(
            name="H1",
            expected_users=1000,
            conversion_rate=0.1,
            uncertainty=0.2,
            development_cost=90_000.0,
        )
        assert f.annual_installment == pytest.approx(90_000.0)

    def test_annual_installment_spread_over_three_years(self):
        """3-year installment: annual charge = development_cost / 3."""
        f = Feature(
            name="H1",
            expected_users=1000,
            conversion_rate=0.1,
            uncertainty=0.2,
            development_cost=90_000.0,
            installment_years=3,
        )
        assert f.annual_installment == pytest.approx(30_000.0)

    def test_annual_installment_zero_cost(self):
        """Zero development cost → zero annual installment."""
        f = Feature(
            name="H1",
            expected_users=1000,
            conversion_rate=0.1,
            uncertainty=0.2,
            development_cost=0.0,
            installment_years=5,
        )
        assert f.annual_installment == 0.0

    def test_installment_years_minimum_is_one(self):
        """installment_years must be at least 1."""
        with pytest.raises(Exception):
            Feature(
                name="H1",
                expected_users=1000,
                conversion_rate=0.1,
                uncertainty=0.2,
                installment_years=0,
            )

    def test_installment_years_maximum_is_thirty(self):
        """installment_years must be at most 30."""
        with pytest.raises(Exception):
            Feature(
                name="H1",
                expected_users=1000,
                conversion_rate=0.1,
                uncertainty=0.2,
                installment_years=31,
            )

    def test_installment_years_valid_boundary(self):
        """installment_years=30 is valid."""
        f = Feature(
            name="H1",
            expected_users=1000,
            conversion_rate=0.1,
            uncertainty=0.2,
            development_cost=300_000.0,
            installment_years=30,
        )
        assert f.annual_installment == pytest.approx(10_000.0)


class TestSimulationResultInstallment:
    """Tests for installment_years and annual_installment on SimulationResult."""

    @staticmethod
    def _result(dev_cost: float, dep_years: int = 1) -> SimulationResult:
        return SimulationResult(
            feature_name="H1",
            results=[100.0, 120.0, 80.0],
            expected_value=100.0,
            business_value_per_conversion=10.0,
            development_cost=dev_cost,
            installment_years=dep_years,
        )

    def test_default_installment_years_is_one(self):
        r = self._result(60_000.0)
        assert r.installment_years == 1

    def test_annual_installment_default(self):
        """Default: annual_installment == development_cost."""
        r = self._result(60_000.0)
        assert r.annual_installment == pytest.approx(60_000.0)

    def test_annual_installment_multi_year(self):
        """3-year spread: annual_installment = cost / 3."""
        r = self._result(90_000.0, dep_years=3)
        assert r.annual_installment == pytest.approx(30_000.0)

    def test_net_value_uses_annual_installment(self):
        """net_value = expected_business_value - annual_installment."""
        r = self._result(90_000.0, dep_years=3)
        # expected_business_value = 100 * 10 = 1000
        # annual_installment = 90000 / 3 = 30000
        assert r.net_value == pytest.approx(1_000.0 - 30_000.0)

    def test_roi_uses_annual_installment(self):
        """ROI = (expected_business_value - annual_installment) / annual_installment."""
        r = self._result(90_000.0, dep_years=3)
        expected_bv = 1_000.0
        ann_dep = 30_000.0
        assert r.roi == pytest.approx((expected_bv - ann_dep) / ann_dep)

    def test_net_value_at_risk_uses_annual_installment(self):
        """net_value_at_risk_95 = business_value_at_risk_95 - annual_installment."""
        r = self._result(90_000.0, dep_years=3)
        assert r.net_value_at_risk_95 == pytest.approx(
            r.business_value_at_risk_95 - r.annual_installment
        )

    def test_cvar_95_net_value_uses_annual_installment(self):
        """cvar_95_net_value uses annual_installment, not full development_cost."""
        r_1y = self._result(90_000.0, dep_years=1)
        r_3y = self._result(90_000.0, dep_years=3)
        # r_3y should have a better (less negative) cvar_95_net_value
        assert r_3y.cvar_95_net_value > r_1y.cvar_95_net_value


class TestInstallmentScheduleInMultiYearPnL:
    """Tests for installment_schedule in MultiYearPnLResult."""

    def test_installment_schedule_length_matches_years(self):
        """installment_schedule has one entry per simulated year."""
        from fhs.application import AdvancedPortfolioService

        f = Feature(
            name="H1",
            expected_users=5000,
            conversion_rate=0.1,
            uncertainty=0.3,
            business_value_per_conversion=10.0,
            development_cost=60_000.0,
            installment_years=2,
        )
        service = AdvancedPortfolioService(
            [f], budget=200_000, discount_rate=0.10, seed=42, scenarios=1_000
        )
        result = service.multi_year.simulate_pnl(["H1"], years=3)
        assert len(result.installment_schedule) == 3

    def test_installment_schedule_correct_values(self):
        """Year 1 and 2 charge annual_dep; year 3 is 0 (beyond 2-year period)."""
        from fhs.application import AdvancedPortfolioService

        f = Feature(
            name="H1",
            expected_users=5000,
            conversion_rate=0.1,
            uncertainty=0.3,
            business_value_per_conversion=10.0,
            development_cost=60_000.0,
            installment_years=2,
        )
        service = AdvancedPortfolioService(
            [f], budget=200_000, discount_rate=0.10, seed=42, scenarios=1_000
        )
        result = service.multi_year.simulate_pnl(["H1"], years=3)
        annual = f.annual_installment  # 30_000
        assert result.installment_schedule[0] == pytest.approx(annual)  # year 1
        assert result.installment_schedule[1] == pytest.approx(annual)  # year 2
        assert result.installment_schedule[2] == pytest.approx(0.0)  # year 3

    def test_installment_schedule_all_years_when_period_exceeds_simulation(self):
        """If installment_years > simulation years, all years carry a charge."""
        from fhs.application import AdvancedPortfolioService

        f = Feature(
            name="H1",
            expected_users=5000,
            conversion_rate=0.1,
            uncertainty=0.3,
            business_value_per_conversion=10.0,
            development_cost=90_000.0,
            installment_years=5,
        )
        service = AdvancedPortfolioService(
            [f], budget=200_000, discount_rate=0.10, seed=42, scenarios=1_000
        )
        result = service.multi_year.simulate_pnl(["H1"], years=3)
        annual = f.annual_installment  # 18_000
        for charge in result.installment_schedule:
            assert charge == pytest.approx(annual)
