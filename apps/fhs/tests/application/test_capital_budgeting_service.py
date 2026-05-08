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

"""Tests for capital-budgeting service methods with OpEx integration.

Covers:
- net_multi_year_scenarios() — T-10
- roi_rows(), npv_rows(), irr_rows() with OpEx — T-11
"""

from __future__ import annotations

import pytest

from fhs.application import BlockchainCaseStudyService
from fhs.core.model import Feature
from fhs.core.model.value_objects import MultiYearResult


@pytest.fixture
def features() -> dict[str, Feature]:
    return {
        "H1": Feature(
            name="H1: Simplified UI",
            expected_users=100_000,
            conversion_rate=0.26,
            uncertainty=0.20,
            business_value_per_conversion=4.7,
            development_cost=75_000.0,
            installment_years=3,
            annual_operating_cost=25_000.0,
        ),
        "H2": Feature(
            name="H2: Traceability",
            expected_users=69_700,
            conversion_rate=0.55,
            uncertainty=0.20,
            business_value_per_conversion=1.77,
            development_cost=50_000.0,
            installment_years=2,
            annual_operating_cost=40_000.0,
        ),
        "H3": Feature(
            name="H3: Expiration Alerts",
            expected_users=60_000,
            conversion_rate=0.45,
            uncertainty=0.25,
            business_value_per_conversion=1.52,
            development_cost=20_000.0,
            installment_years=2,
            annual_operating_cost=3_000.0,
        ),
    }


@pytest.fixture
def case() -> BlockchainCaseStudyService:
    return BlockchainCaseStudyService(seed=42, scenarios=5_000)


@pytest.fixture
def year1(case, features):
    return case.simulate_year1(features)


@pytest.fixture
def multi_year(case, features):
    return case.simulate_multi_year(features, discount_rate=0.10, years=3)


# ── T-10: net_multi_year_scenarios ───────────────────────────────────────────


class TestNetMultiYearScenarios:
    def test_returns_multi_year_result(self, case, multi_year):
        result = case.net_multi_year_scenarios(multi_year["H1"], annual_opex=25_000)
        assert isinstance(result, MultiYearResult)

    def test_feature_name_preserved(self, case, multi_year):
        result = case.net_multi_year_scenarios(multi_year["H1"], annual_opex=25_000)
        assert result.feature_name == multi_year["H1"].feature_name

    def test_discount_rate_preserved(self, case, multi_year):
        result = case.net_multi_year_scenarios(multi_year["H1"], annual_opex=25_000)
        assert result.discount_rate == multi_year["H1"].discount_rate

    def test_same_number_of_years(self, case, multi_year):
        result = case.net_multi_year_scenarios(multi_year["H1"], annual_opex=25_000)
        assert len(result.years) == len(multi_year["H1"].years)

    def test_expected_reduced_by_opex(self, case, multi_year):
        """Expected value per year must drop by exactly annual_opex."""
        opex = 25_000.0
        gross = multi_year["H1"]
        net = case.net_multi_year_scenarios(gross, annual_opex=opex)
        for yr_g, yr_n in zip(gross.years, net.years, strict=False):
            assert yr_n.expected == pytest.approx(yr_g.expected - opex, rel=1e-6)

    def test_year_index_preserved(self, case, multi_year):
        """Year numbers must remain unchanged."""
        result = case.net_multi_year_scenarios(multi_year["H1"], annual_opex=0)
        for yr_orig, yr_net in zip(multi_year["H1"].years, result.years, strict=False):
            assert yr_net.year == yr_orig.year

    def test_zero_opex_unchanged(self, case, multi_year):
        """Zero OpEx must produce identical expected values."""
        gross = multi_year["H1"]
        net = case.net_multi_year_scenarios(gross, annual_opex=0.0)
        for yr_g, yr_n in zip(gross.years, net.years, strict=False):
            assert yr_n.expected == pytest.approx(yr_g.expected, rel=1e-9)

    def test_original_result_immutable(self, case, multi_year):
        """Original MultiYearResult must not be mutated."""
        original_expected = [yr.expected for yr in multi_year["H1"].years]
        case.net_multi_year_scenarios(multi_year["H1"], annual_opex=99_999)
        for yr, orig_exp in zip(
            multi_year["H1"].years, original_expected, strict=False
        ):
            assert yr.expected == pytest.approx(orig_exp, rel=1e-9)


# ── T-11: roi_rows, npv_rows, irr_rows ───────────────────────────────────────


class TestRoiRowsWithOpEx:
    def test_six_columns(self, case, year1):
        rows = case.roi_rows(year1)
        assert all(len(row) == 6 for row in rows)

    def test_one_row_per_feature(self, case, year1, features):
        rows = case.roi_rows(year1)
        assert len(rows) == len(features)

    def test_opex_column_value(self, case, year1):
        """Third column must contain the feature's annual operating cost."""
        rows = case.roi_rows(year1)
        # H1 opex = 25,000
        h1_row = next(r for r in rows if r[0].startswith("H1"))
        assert "25,000" in h1_row[2]

    def test_gross_roi_column(self, case, year1):
        """Column 5 (index 4) = gross ROI — should be a percentage string."""
        rows = case.roi_rows(year1)
        for row in rows:
            assert "%" in row[4]

    def test_net_roi_column(self, case, year1):
        """Column 6 (index 5) = net ROI (after OpEx) — must be a percentage string."""
        rows = case.roi_rows(year1)
        for row in rows:
            assert "%" in row[5]

    def test_net_roi_lower_than_gross(self, case, year1):
        """Net ROI must be strictly lower than gross ROI (OpEx > 0)."""
        rows = case.roi_rows(year1)
        for row in rows:
            gross = float(row[4].replace("%", "").replace(",", ""))
            net = float(row[5].replace("%", "").replace(",", "").replace("−", "-"))
            assert net < gross


class TestNpvRowsWithOpEx:
    def test_five_columns(self, case, year1, multi_year, features):
        rows = case.npv_rows(multi_year, features, discount_rate=0.10)
        assert all(len(row) == 5 for row in rows)

    def test_one_row_per_feature(self, case, year1, multi_year, features):
        rows = case.npv_rows(multi_year, features, discount_rate=0.10)
        assert len(rows) == len(features)

    def test_npv_lower_with_opex_than_gross(self, case, multi_year, features):
        """NPV with OpEx must be lower than NPV without OpEx (same investment)."""
        from fhs.core.services import FinancialCalculator

        for key, feature in features.items():
            gross_npv = FinancialCalculator.result_npv(
                multi_year[key], feature.development_cost, 0.10
            )
            net_result = case.net_multi_year_scenarios(
                multi_year[key], feature.annual_operating_cost
            )
            net_npv = FinancialCalculator.result_npv(
                net_result, feature.development_cost, 0.10
            )
            assert net_npv.expected < gross_npv.expected

    def test_npv_rows_return_eur_strings(self, case, multi_year, features):
        rows = case.npv_rows(multi_year, features, discount_rate=0.10)
        for row in rows:
            # columns 3-5 are NPV figures: must contain €
            for col in row[2:5]:
                assert "€" in col or col.startswith("-") or col.startswith("−")


class TestIrrRowsWithOpEx:
    def test_five_columns(self, case, multi_year, features):
        rows = case.irr_rows(multi_year, features)
        assert all(len(row) == 5 for row in rows)

    def test_one_row_per_feature(self, case, multi_year, features):
        rows = case.irr_rows(multi_year, features)
        assert len(rows) == len(features)

    def test_irr_rows_return_percentage_strings(self, case, multi_year, features):
        rows = case.irr_rows(multi_year, features)
        for row in rows:
            # columns 3-5 are IRR figures: must contain %
            for col in row[2:5]:
                assert "%" in col

    def test_irr_lower_with_opex_than_gross(self, case, multi_year, features):
        """IRR with OpEx must be lower than IRR without OpEx."""
        from fhs.core.services import FinancialCalculator

        for key, feature in features.items():
            gross_irr = FinancialCalculator.result_irr(
                multi_year[key], feature.development_cost
            )
            net_result = case.net_multi_year_scenarios(
                multi_year[key], feature.annual_operating_cost
            )
            net_irr = FinancialCalculator.result_irr(
                net_result, feature.development_cost
            )
            assert net_irr.expected < gross_irr.expected


class TestTotalAnnualOpex:
    def test_sums_all_features(self, case, features):
        total = case.total_annual_opex(features)
        # H1=25k + H2=40k + H3=3k = 68k
        assert total == pytest.approx(68_000, abs=1)

    def test_empty_returns_zero(self, case):
        assert case.total_annual_opex({}) == pytest.approx(0.0)
