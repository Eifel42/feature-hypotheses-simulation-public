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

"""Tests for dual-financing (Option A/B) service methods.

Covers:
- npv_dual_rows: returns Option A and Option B NPV per feature
- irr_dual_rows: returns Option A and Option B IRR per feature
- portfolio_npv_installment: portfolio-level NPV_B
- portfolio_irr_installment: portfolio-level IRR_B
- financing_recommendation: plain-English text generation
- portfolio_profitability_index: PI = NPV / PV(investment) for both options
"""

import math

import pytest

from src.fhs.application.blockchain_case_study_service import BlockchainCaseStudyService
from src.fhs.core.model.entities.feature import Feature

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_feature(
    name: str,
    expected_users: int = 10_000,
    conversion_rate: float = 0.3,
    bv_per_conversion: float = 5.0,
    development_cost: float = 30_000.0,
    installment_years: int = 3,
    annual_operating_cost: float = 5_000.0,
    annual_growth_rate: float = 0.05,
) -> Feature:
    return Feature(
        name=name,
        expected_users=expected_users,
        conversion_rate=conversion_rate,
        business_value_per_conversion=bv_per_conversion,
        development_cost=development_cost,
        installment_years=installment_years,
        annual_operating_cost=annual_operating_cost,
        annual_growth_rate=annual_growth_rate,
        uncertainty=0.2,
    )


@pytest.fixture(scope="module")
def service():
    return BlockchainCaseStudyService(seed=42, scenarios=5_000)


@pytest.fixture(scope="module")
def features_by_key():
    return {
        "F1": _make_feature("Feature 1", development_cost=60_000, installment_years=3),
        "F2": _make_feature(
            "Feature 2",
            development_cost=30_000,
            installment_years=2,
            annual_operating_cost=8_000,
        ),
    }


@pytest.fixture(scope="module")
def multi_year(service, features_by_key):
    return service.simulate_multi_year(features_by_key, discount_rate=0.08, years=3)


@pytest.fixture(scope="module")
def year1(service, features_by_key):
    return service.simulate_year1(features_by_key)


# ── npv_dual_rows ─────────────────────────────────────────────────────────────


class TestNpvDualRows:
    def test_returns_one_row_per_feature(self, service, multi_year, features_by_key):
        rows = service.npv_dual_rows(multi_year, features_by_key, discount_rate=0.08)
        assert len(rows) == 2

    def test_row_has_11_elements(self, service, multi_year, features_by_key):
        rows = service.npv_dual_rows(multi_year, features_by_key, discount_rate=0.08)
        assert all(len(r) == 11 for r in rows)

    def test_npv_b_higher_than_a_at_positive_rate(
        self, service, multi_year, features_by_key
    ):
        rows = service.npv_dual_rows(multi_year, features_by_key, discount_rate=0.08)
        for row in rows:
            npv_a_exp, npv_b_exp = row[4], row[7]
            assert npv_b_exp >= npv_a_exp, (
                f"NPV_B ({npv_b_exp:.0f}) should be >= NPV_A ({npv_a_exp:.0f})"
            )

    def test_diff_column_equals_b_minus_a(self, service, multi_year, features_by_key):
        rows = service.npv_dual_rows(multi_year, features_by_key, discount_rate=0.08)
        for row in rows:
            npv_a_exp, npv_b_exp, diff = row[4], row[7], row[10]
            assert abs(diff - (npv_b_exp - npv_a_exp)) < 0.01

    def test_installment_column_equals_dev_cost_over_years(
        self, service, multi_year, features_by_key
    ):
        rows = service.npv_dual_rows(multi_year, features_by_key, discount_rate=0.08)
        for row in rows:
            dev_cost, installment, inst_years = row[1], row[2], row[3]
            expected_inst = dev_cost / inst_years
            assert abs(installment - expected_inst) < 0.01


# ── irr_dual_rows ─────────────────────────────────────────────────────────────


class TestIrrDualRows:
    def test_returns_one_row_per_feature(self, service, multi_year, features_by_key):
        rows = service.irr_dual_rows(multi_year, features_by_key)
        assert len(rows) == 2

    def test_row_has_10_elements(self, service, multi_year, features_by_key):
        rows = service.irr_dual_rows(multi_year, features_by_key)
        assert all(len(r) == 10 for r in rows)

    def test_irr_a_is_finite(self, service, multi_year, features_by_key):
        rows = service.irr_dual_rows(multi_year, features_by_key)
        for row in rows:
            irr_a_exp = row[4]
            assert not math.isnan(irr_a_exp), "Option A IRR should always be finite"

    def test_irr_b_is_nan_or_finite(self, service, multi_year, features_by_key):
        rows = service.irr_dual_rows(multi_year, features_by_key)
        for row in rows:
            irr_b_exp = row[7]
            # NaN is acceptable (positive Y1) — but should not raise
            assert isinstance(irr_b_exp, float)


# ── portfolio_npv_installment ─────────────────────────────────────────────────


class TestPortfolioNpvInstallment:
    def test_returns_npv_summary(self, service, multi_year, features_by_key):
        portfolio_myr = service.combine_multi_year_results(
            multi_year, discount_rate=0.08, name="Portfolio"
        )
        total_annual_opex = sum(
            f.annual_operating_cost for f in features_by_key.values()
        )
        result = service.portfolio_npv_installment(
            portfolio_myr,
            features_by_key,
            total_annual_opex,
            0.08,
        )
        assert hasattr(result, "expected")
        assert hasattr(result, "var_95")
        assert hasattr(result, "p95")
        assert hasattr(result, "std")

    def test_npv_b_higher_than_a(self, service):
        """NPV_B > NPV_A: deferring payments captures time value of money."""
        features = {
            "F1": _make_feature("F1", development_cost=60_000, installment_years=3),
            "F2": _make_feature(
                "F2",
                development_cost=30_000,
                installment_years=3,
                annual_operating_cost=8_000,
            ),
        }
        myr = service.simulate_multi_year(features, discount_rate=0.08, years=3)
        portfolio_myr = service.combine_multi_year_results(
            myr, discount_rate=0.08, name="Portfolio"
        )
        total_cost = sum(f.development_cost for f in features.values())
        total_annual_opex = sum(f.annual_operating_cost for f in features.values())
        portfolio_myr_net = service.net_multi_year_scenarios(
            portfolio_myr, total_annual_opex
        )

        npv_a = service.portfolio_npv(portfolio_myr_net, total_cost, 0.08)
        npv_b = service.portfolio_npv_installment(
            portfolio_myr, features, total_annual_opex, 0.08
        )
        assert npv_b.expected >= npv_a.expected

    def test_per_year_schedule_lower_than_flat_max(self, service):
        """Per-year schedule must give higher NPV_B than the flat max-years shortcut.

        The old flat computation deducted total_annual_installment for ALL years
        up to max(installment_years), over-charging years where some features
        have already completed their installment window.
        """
        features_mixed = {
            "F1": _make_feature("F1", development_cost=75_000, installment_years=3),
            "F2": _make_feature("F2", development_cost=50_000, installment_years=2),
        }
        myr = service.simulate_multi_year(features_mixed, discount_rate=0.08, years=3)
        portfolio_myr = service.combine_multi_year_results(
            myr, discount_rate=0.08, name="Portfolio"
        )
        total_annual_opex = sum(
            f.annual_operating_cost for f in features_mixed.values()
        )

        # Correct per-year schedule
        npv_schedule = service.portfolio_npv_installment(
            portfolio_myr, features_mixed, total_annual_opex, 0.08
        )
        # Flat overestimate: charges F2's installment in year 3 as well
        from src.fhs.core.services.financial.calculator import FinancialCalculator

        total_inst = sum(f.annual_installment for f in features_mixed.values())
        net_result = service.net_multi_year_scenarios(portfolio_myr, total_annual_opex)
        npv_flat = FinancialCalculator.result_npv_installment(
            net_result, total_inst, 3, 0.08
        )

        # Schedule deducts less in year 3 → higher NPV_B
        assert npv_schedule.expected > npv_flat.expected


# ── financing_recommendation ──────────────────────────────────────────────────


class TestFinancingRecommendation:
    def test_returns_non_empty_string(self, service, multi_year, features_by_key):
        from src.fhs.core.model.value_objects import IrrSummary, NpvSummary

        npv_a = NpvSummary(expected=50_000, var_95=-10_000, p95=100_000, std=20_000)
        npv_b = NpvSummary(expected=60_000, var_95=5_000, p95=110_000, std=18_000)
        irr_a = IrrSummary(expected=0.15, floor=0.05, ceiling=0.30)
        irr_b = IrrSummary(
            expected=float("nan"), floor=float("nan"), ceiling=float("nan")
        )

        rec = BlockchainCaseStudyService.financing_recommendation(
            npv_a=npv_a,
            npv_b=npv_b,
            irr_a=irr_a,
            irr_b=irr_b,
            total_investment=90_000,
            total_annual_installment=30_000,
            installment_years=3,
            discount_rate=0.08,
        )
        assert isinstance(rec, str)
        assert len(rec) > 50

    def test_mentions_option_b_benefit(self, service):
        from src.fhs.core.model.value_objects import IrrSummary, NpvSummary

        npv_a = NpvSummary(expected=40_000, var_95=-5_000, p95=80_000, std=15_000)
        npv_b = NpvSummary(expected=55_000, var_95=10_000, p95=90_000, std=13_000)
        irr_a = IrrSummary(expected=0.18, floor=0.06, ceiling=0.35)
        irr_b = IrrSummary(expected=0.25, floor=0.10, ceiling=0.40)

        rec = BlockchainCaseStudyService.financing_recommendation(
            npv_a=npv_a,
            npv_b=npv_b,
            irr_a=irr_a,
            irr_b=irr_b,
            total_investment=90_000,
            total_annual_installment=30_000,
            installment_years=3,
            discount_rate=0.08,
        )
        # Should mention the positive NPV difference
        assert "installment" in rec.lower() or "Option B" in rec


# ── portfolio_profitability_index ──────────────────────────────────────────────


class TestPortfolioProfitabilityIndex:
    """Profitability Index: PI = NPV / PV(investment).

    Option A: PV(investment) = total_cost (paid at t=0).
    Option B: PV(investment) = sum of discounted annual installments.
    At r > 0: PV(installments) < total_cost → PI_B > PI_A.
    At r = 0: PV(installments) = total_cost → PI_B ≈ PI_A.
    """

    @staticmethod
    def _npv(expected: float) -> object:
        from src.fhs.core.model.value_objects import NpvSummary

        return NpvSummary(expected=expected, var_95=0.0, p95=0.0, std=0.0)

    def test_pi_a_greater_than_one_when_npv_positive(self, service, features_by_key):
        total_cost = sum(f.development_cost for f in features_by_key.values())
        # Fake NPV_A > total_cost so PI > 1
        npv_a = self._npv(total_cost * 1.5)
        npv_b = self._npv(total_cost * 1.6)
        pi_a, _ = service.portfolio_profitability_index(
            npv_a, npv_b, features_by_key, total_cost, discount_rate=0.08, years=3
        )
        assert pi_a > 1.0

    def test_pi_b_greater_than_pi_a_at_positive_rate(self, service, features_by_key):
        """Deferred installments have lower PV → dividing the same (or higher) NPV
        by a smaller denominator gives PI_B > PI_A."""
        total_cost = sum(f.development_cost for f in features_by_key.values())
        npv_a = self._npv(50_000.0)
        npv_b = self._npv(55_000.0)
        pi_a, pi_b = service.portfolio_profitability_index(
            npv_a, npv_b, features_by_key, total_cost, discount_rate=0.08, years=3
        )
        assert pi_b > pi_a

    def test_pi_ratio_equals_npv_over_cost(self, service, features_by_key):
        """At r=0 PV(installments) == total_cost, so PI_A and PI_B differ only
        because NPV_A ≠ NPV_B."""
        total_cost = sum(f.development_cost for f in features_by_key.values())
        npv_a = self._npv(total_cost)  # exactly 1× investment
        npv_b = self._npv(total_cost)
        pi_a, pi_b = service.portfolio_profitability_index(
            npv_a, npv_b, features_by_key, total_cost, discount_rate=0.0, years=3
        )
        assert abs(pi_a - 1.0) < 1e-6
        assert abs(pi_b - 1.0) < 1e-6

    def test_returns_tuple_of_two_floats(self, service, features_by_key):
        total_cost = sum(f.development_cost for f in features_by_key.values())
        result = service.portfolio_profitability_index(
            self._npv(40_000), self._npv(50_000), features_by_key, total_cost, 0.08
        )
        assert len(result) == 2
        pi_a, pi_b = result
        assert isinstance(pi_a, float)
        assert isinstance(pi_b, float)

    def test_zero_investment_returns_nan(self, service):
        """Edge case: no investment means PI is undefined."""
        import math

        empty: dict = {}
        result = service.portfolio_profitability_index(
            self._npv(10_000),
            self._npv(12_000),
            empty,
            total_investment=0.0,
            discount_rate=0.08,
        )
        pi_a, _ = result
        assert math.isnan(pi_a)


# ── capital_budgeting_context ──────────────────────────────────────────────────


class TestCapitalBudgetingContext:
    """CapitalBudgetingContext bundles all NB 03 KPIs in a single call.

    The context is built manually from the module-level fixtures that are
    already computed, so we avoid re-running expensive simulations and the
    isinstance issue that occurs with the test Feature stubs.
    """

    @pytest.fixture(scope="class")
    def ctx(self, service, features_by_key, multi_year):
        """Build CapitalBudgetingContext directly from pre-computed fixtures.

        Avoids calling simulate_year1() here — that method is exercised by
        the integration notebook-check pipeline. The unit tests focus on the
        KPI computations and dataclass structure.
        """
        from src.fhs.application import CapitalBudgetingContext

        dr = 0.08
        portfolio_myr = service.combine_multi_year_results(
            multi_year, discount_rate=dr, name="Portfolio"
        )
        total_cost = service.total_investment(features_by_key)
        total_annual_opex = service.total_annual_opex(features_by_key)
        total_annual_installment = float(
            sum(f.annual_installment for f in features_by_key.values())
        )
        total_installment_years = int(
            max(f.installment_years for f in features_by_key.values())
        )
        portfolio_myr_net = service.net_multi_year_scenarios(
            portfolio_myr, total_annual_opex
        )
        npv_a = service.portfolio_npv(portfolio_myr_net, total_cost, dr)
        npv_b = service.portfolio_npv_installment(
            portfolio_myr, features_by_key, total_annual_opex, dr
        )
        irr_a = service.portfolio_irr(portfolio_myr_net, total_cost)
        irr_b = service.portfolio_irr_installment(
            portfolio_myr, features_by_key, total_annual_opex
        )
        pi_a, pi_b = service.portfolio_profitability_index(
            npv_a, npv_b, features_by_key, total_cost, dr
        )
        npv_a_assessment = service.assess_portfolio_npv(npv_a)
        feat_sched_a, feat_sched_b = service.feature_cashflow_schedules(
            multi_year, features_by_key, dr
        )

        return CapitalBudgetingContext(
            features_by_key=features_by_key,
            discount_rate=dr,
            scenarios=service.scenarios,
            year1=None,  # simulate_year1 tested by notebook integration pipeline
            portfolio_overview=None,
            multi_year=multi_year,
            portfolio_myr=portfolio_myr,
            total_cost=total_cost,
            total_annual_opex=total_annual_opex,
            total_annual_installment=total_annual_installment,
            total_installment_years=total_installment_years,
            portfolio_npv_a=npv_a,
            portfolio_npv_b=npv_b,
            portfolio_irr_a=irr_a,
            portfolio_irr_b=irr_b,
            pi_a=pi_a,
            pi_b=pi_b,
            npv_a_assessment=npv_a_assessment,
            feat_sched_a=feat_sched_a,
            feat_sched_b=feat_sched_b,
        )

    def test_is_correct_type(self, ctx):
        from src.fhs.application import CapitalBudgetingContext

        assert isinstance(ctx, CapitalBudgetingContext)

    def test_npv_b_greater_than_a(self, ctx):
        assert ctx.portfolio_npv_b.expected > ctx.portfolio_npv_a.expected

    def test_pi_b_greater_than_pi_a(self, ctx):
        assert ctx.pi_b > ctx.pi_a

    def test_total_cost_positive(self, ctx):
        assert ctx.total_cost > 0

    def test_feat_sched_keys(self, ctx):
        for key in ("label", "years", "discount_factors", "rows", "portfolio"):
            assert key in ctx.feat_sched_a
            assert key in ctx.feat_sched_b

    def test_portfolio_cashflows_length(self, ctx):
        assert len(ctx.feat_sched_a["portfolio"]["cashflows"]) == 4  # year 0..3
        assert len(ctx.feat_sched_b["portfolio"]["cashflows"]) == 4

    def test_irr_a_finite(self, ctx):
        assert math.isfinite(ctx.portfolio_irr_a.expected)

    def test_scenarios_matches_service(self, ctx, service):
        assert ctx.scenarios == service.scenarios

    def test_npv_b_matches_feat_sched(self, ctx):
        """Portfolio NPV from context equals NPV in cashflow schedule (±1 rounding)."""
        assert (
            abs(ctx.portfolio_npv_b.expected - ctx.feat_sched_b["portfolio"]["npv"])
            <= 1
        )
