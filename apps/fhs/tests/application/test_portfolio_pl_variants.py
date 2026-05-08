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

"""Tests for BlockchainCaseStudyService.portfolio_pl_variants()."""

import pytest

from fhs.application import BlockchainCaseStudyService
from fhs.core.model import Feature
from fhs.core.model.value_objects import PortfolioPLVariants


@pytest.fixture
def features() -> list[Feature]:
    return [
        Feature(
            name="H1: Simplified UI",
            expected_users=100_000,
            conversion_rate=0.26,
            uncertainty=0.20,
            business_value_per_conversion=4.7,
            development_cost=75_000.0,
            installment_years=3,
            annual_operating_cost=25_000.0,
        ),
        Feature(
            name="H2: Traceability",
            expected_users=69_700,
            conversion_rate=0.55,
            uncertainty=0.20,
            business_value_per_conversion=1.77,
            development_cost=50_000.0,
            installment_years=2,
            annual_operating_cost=40_000.0,
        ),
        Feature(
            name="H3: Expiration Alerts",
            expected_users=60_000,
            conversion_rate=0.45,
            uncertainty=0.25,
            business_value_per_conversion=1.52,
            development_cost=20_000.0,
            installment_years=2,
            annual_operating_cost=3_000.0,
        ),
    ]


@pytest.fixture
def case() -> BlockchainCaseStudyService:
    return BlockchainCaseStudyService(seed=42, scenarios=5_000)


@pytest.fixture
def year1(case, features):
    by_key = {f.name.split(":")[0].strip(): f for f in features}
    return case.simulate_year1(by_key)


@pytest.fixture
def portfolio(case, year1):
    return case.portfolio_year1(year1)


class TestPortfolioPLVariants:
    def test_returns_correct_type(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        assert isinstance(result, PortfolioPLVariants)

    def test_four_rows(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        assert len(result.rows) == 4

    def test_row_labels(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        labels = [r.label for r in result.rows]
        assert "Best (P95)" in labels
        assert "Mean (Expected)" in labels
        assert "Floor (BVF 95%)" in labels
        assert "Tail (CVaR 95%)" in labels

    def test_totals_correct(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        # H1 75k + H2 50k + H3 20k = 145k
        assert result.total_investment == pytest.approx(145_000, abs=1)
        # H1 25k + H2 25k + H3 10k = 60k (straight-line)
        assert result.total_annual_installment == pytest.approx(60_000, abs=1)
        # H1 25k + H2 40k + H3 3k = 68k
        assert result.total_annual_opex == pytest.approx(68_000, abs=1)

    def test_v2_net_better_than_v1_net(self, case, year1, portfolio):
        """V2 always better: installment (€60k) < full investment (€145k)."""
        result = case.portfolio_pl_variants(year1, portfolio)
        for row in result.rows:
            assert row.v2_net > row.v1_net

    def test_net_formula_v1(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        mean_row = next(r for r in result.rows if r.label == "Mean (Expected)")
        expected_v1 = portfolio.expected - 145_000 - 68_000
        assert mean_row.v1_net == pytest.approx(expected_v1, abs=1)

    def test_net_formula_v2(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        mean_row = next(r for r in result.rows if r.label == "Mean (Expected)")
        expected_v2 = portfolio.expected - 60_000 - 68_000
        assert mean_row.v2_net == pytest.approx(expected_v2, abs=1)

    def test_bv_ordering(self, case, year1, portfolio):
        """P95 >= Expected >= VaR95 >= CVaR95 in terms of BV."""
        result = case.portfolio_pl_variants(year1, portfolio)
        rows_by_label = {r.label: r for r in result.rows}
        assert rows_by_label["Best (P95)"].bv >= rows_by_label["Mean (Expected)"].bv
        assert (
            rows_by_label["Mean (Expected)"].bv >= rows_by_label["Floor (BVF 95%)"].bv
        )
        assert (
            rows_by_label["Floor (BVF 95%)"].bv >= rows_by_label["Tail (CVaR 95%)"].bv
        )

    def test_result_has_cost_totals_and_rows(self, case, year1, portfolio):
        result = case.portfolio_pl_variants(year1, portfolio)
        assert result.total_annual_installment == pytest.approx(60_000, abs=1)
        assert result.total_annual_opex == pytest.approx(68_000, abs=1)
        assert len(result.rows) == 4

    def test_empty_year1_returns_zero_rows(self, case, portfolio):
        from fhs.core.model.value_objects import PortfolioSnapshot

        empty_portfolio = PortfolioSnapshot(
            expected=0.0, var_95=0.0, cvar_95=0.0, std_dev=0.0, investment=0.0
        )
        result = case.portfolio_pl_variants({}, empty_portfolio)
        assert len(result.rows) == 4
        for row in result.rows:
            assert row.bv == 0.0
