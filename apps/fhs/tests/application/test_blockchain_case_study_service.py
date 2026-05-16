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

"""Targeted tests for BlockchainCaseStudyService core capital-budgeting methods.

Covers high-risk methods called out in refactoring tasks:
- net_multi_year_scenarios
- roi_rows
- npv_rows
- irr_rows
- irr_dual_rows
- year1_overview_rows
- financing_recommendation
"""

from __future__ import annotations

import math

import pytest

from fhs.application import BlockchainCaseStudyService
from fhs.core.model import Feature
from fhs.core.model.value_objects import IrrSummary, NpvSummary
from fhs.core.services import FinancialCalculator


@pytest.fixture
def service() -> BlockchainCaseStudyService:
    return BlockchainCaseStudyService(seed=42, scenarios=4_000)


@pytest.fixture
def features_by_key() -> dict[str, Feature]:
    return {
        "H1": Feature(
            name="H1: Simplified UI",
            expected_users=100_000,
            conversion_rate=0.26,
            uncertainty=0.20,
            business_value_per_conversion=4.7,
            development_cost=75_000.0,
            installment_years=3,
            annual_growth_rate=0.05,
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
            annual_growth_rate=0.05,
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
            annual_growth_rate=0.15,
            annual_operating_cost=3_000.0,
        ),
    }


@pytest.fixture
def year1(service: BlockchainCaseStudyService, features_by_key: dict[str, Feature]):
    return service.simulate_year1(features_by_key)


@pytest.fixture
def multi_year(
    service: BlockchainCaseStudyService, features_by_key: dict[str, Feature]
):
    return service.simulate_multi_year(features_by_key, discount_rate=0.08, years=3)


@pytest.fixture
def portfolio(service: BlockchainCaseStudyService, year1):
    return service.portfolio_year1(year1)


def test_net_multi_year_scenarios_reduces_each_year_expected(
    service: BlockchainCaseStudyService, multi_year
):
    gross = multi_year["H1"]
    net = service.net_multi_year_scenarios(gross, annual_opex=25_000.0)

    assert len(net.years) == len(gross.years)
    for gross_year, net_year in zip(gross.years, net.years, strict=False):
        assert net_year.year == gross_year.year
        assert net_year.expected == pytest.approx(
            gross_year.expected - 25_000.0, rel=1e-6
        )


def test_roi_rows_returns_expected_columns_and_net_formula(
    service: BlockchainCaseStudyService,
    year1,
):
    rows = service.roi_rows(year1)

    assert len(rows) == 3
    assert all(len(row) == 6 for row in rows)

    # Row order is key-sorted (H1, H2, H3); verify net ROI formula for H1.
    h1 = year1["H1"]
    expected_net_roi = (
        h1.expected_eur - h1.feature.development_cost - h1.feature.annual_operating_cost
    ) / h1.feature.development_cost
    assert rows[0][0] == h1.feature.name
    assert rows[0][5] == f"{expected_net_roi:.1%}"


def test_npv_rows_are_net_of_opex(
    service: BlockchainCaseStudyService,
    multi_year,
    features_by_key,
):
    rows = service.npv_rows(multi_year, features_by_key, discount_rate=0.08)

    assert len(rows) == len(features_by_key)
    assert all(len(row) == 5 for row in rows)

    # Net NPV must be lower than gross NPV for positive annual OpEx.
    feature = features_by_key["H1"]
    gross_npv = FinancialCalculator.result_npv(
        multi_year["H1"], feature.development_cost, 0.08
    )
    net_result = service.net_multi_year_scenarios(
        multi_year["H1"], feature.annual_operating_cost
    )
    net_npv = FinancialCalculator.result_npv(net_result, feature.development_cost, 0.08)
    assert net_npv.expected < gross_npv.expected


def test_irr_rows_are_net_of_opex(
    service: BlockchainCaseStudyService,
    multi_year,
    features_by_key,
):
    rows = service.irr_rows(multi_year, features_by_key)

    assert len(rows) == len(features_by_key)
    assert all(len(row) == 5 for row in rows)
    assert all("%" in col for row in rows for col in row[2:5])

    feature = features_by_key["H2"]
    gross_irr = FinancialCalculator.result_irr(
        multi_year["H2"], feature.development_cost
    )
    net_result = service.net_multi_year_scenarios(
        multi_year["H2"], feature.annual_operating_cost
    )
    net_irr = FinancialCalculator.result_irr(net_result, feature.development_cost)
    if not math.isnan(gross_irr.expected) and not math.isnan(net_irr.expected):
        assert net_irr.expected < gross_irr.expected


def test_irr_dual_rows_shape_and_installment_math(
    service: BlockchainCaseStudyService,
    multi_year,
    features_by_key,
):
    rows = service.irr_dual_rows(multi_year, features_by_key)

    assert len(rows) == len(features_by_key)
    assert all(len(row) == 10 for row in rows)

    # name, dev_cost, installment, installment_years, ...
    h1_row = rows[0]
    assert h1_row[0] == "Simplified UI"
    assert h1_row[2] == pytest.approx(h1_row[1] / h1_row[3], rel=1e-9)


def test_year1_overview_rows_include_total_and_consistent_totals(
    service: BlockchainCaseStudyService,
    year1,
    portfolio,
):
    rows = service.year1_overview_rows(year1, portfolio)

    # One row per feature + one portfolio total row.
    assert len(rows) == len(year1) + 1

    total_row = rows[-1]
    assert total_row[0] == "Portfolio Total"
    assert total_row[9] is True

    # expected / var / cvar come directly from portfolio snapshot
    assert total_row[1] == pytest.approx(portfolio.expected, rel=1e-12)
    assert total_row[2] == pytest.approx(portfolio.var_95, rel=1e-12)
    assert total_row[3] == pytest.approx(portfolio.cvar_95, rel=1e-12)

    # investment / opex / installment totals match feature sums
    expected_total_invest = sum(
        item.feature.development_cost for item in year1.values()
    )
    expected_total_opex = sum(
        item.feature.annual_operating_cost for item in year1.values()
    )
    expected_total_installment = sum(
        item.feature.annual_installment for item in year1.values()
    )
    assert total_row[4] == pytest.approx(expected_total_invest, rel=1e-12)
    assert total_row[5] == pytest.approx(expected_total_opex, rel=1e-12)
    assert total_row[7] == pytest.approx(expected_total_installment, rel=1e-12)


def test_financing_recommendation_prefers_installment_when_better():
    npv_a = NpvSummary(expected=50_000.0, var_95=-10_000.0, p95=95_000.0, std=20_000.0)
    npv_b = NpvSummary(expected=63_000.0, var_95=4_000.0, p95=102_000.0, std=18_000.0)
    irr_a = IrrSummary(expected=0.15, floor=0.05, ceiling=0.30)
    irr_b = IrrSummary(expected=0.22, floor=0.09, ceiling=0.35)

    recommendation = BlockchainCaseStudyService.financing_recommendation(
        npv_a=npv_a,
        npv_b=npv_b,
        irr_a=irr_a,
        irr_b=irr_b,
        total_investment=145_000.0,
        total_annual_installment=60_000.0,
        installment_years=3,
        discount_rate=0.08,
    )

    assert "Option B (installment) produces a higher expected NPV" in recommendation
    assert "IRR (Option B: 22%) exceeds IRR (Option A: 15%)" in recommendation
    assert "downside floor (BVF 95%) is negative under Option A" in recommendation


def test_financing_recommendation_handles_nan_installment_irr():
    npv_a = NpvSummary(expected=45_000.0, var_95=-3_000.0, p95=80_000.0, std=14_000.0)
    npv_b = NpvSummary(expected=55_000.0, var_95=2_000.0, p95=90_000.0, std=13_000.0)
    irr_a = IrrSummary(expected=0.18, floor=0.06, ceiling=0.30)
    irr_b = IrrSummary(expected=float("nan"), floor=float("nan"), ceiling=float("nan"))

    recommendation = BlockchainCaseStudyService.financing_recommendation(
        npv_a=npv_a,
        npv_b=npv_b,
        irr_a=irr_a,
        irr_b=irr_b,
        total_investment=100_000.0,
        total_annual_installment=35_000.0,
        installment_years=3,
        discount_rate=0.08,
    )

    assert "Option B IRR is undefined" in recommendation
    assert "favourable sign" in recommendation


def test_financing_recommendation_describes_mixed_installment_schedule():
    npv_a = NpvSummary(
        expected=3_938_666.0, var_95=3_100_000.0, p95=4_700_000.0, std=250_000.0
    )
    npv_b = NpvSummary(
        expected=3_968_021.0, var_95=3_150_000.0, p95=4_730_000.0, std=240_000.0
    )
    irr_a = IrrSummary(expected=1.87, floor=1.20, ceiling=2.40)
    irr_b = IrrSummary(expected=2.71, floor=1.80, ceiling=3.20)

    recommendation = BlockchainCaseStudyService.financing_recommendation(
        npv_a=npv_a,
        npv_b=npv_b,
        irr_a=irr_a,
        irr_b=irr_b,
        total_investment=865_000.0,
        total_annual_installment=515_000.0,
        installment_years=3,
        discount_rate=0.08,
        installment_schedule=[515_000.0, 300_000.0, 50_000.0],
    )

    assert "declining installment schedule" in recommendation
    assert "Year 0: €515,000" in recommendation
    assert "Year 2: €50,000" in recommendation
    assert "starts at €515,000 in Year 0" in recommendation


def test_cost_variant_rows_returns_one_row_per_feature(
    service: BlockchainCaseStudyService,
    year1,
):
    rows = service.cost_variant_rows(year1)
    assert len(rows) == len(year1)
    assert all(len(row) == 7 for row in rows)
    assert all(isinstance(row[0], str) for row in rows)
