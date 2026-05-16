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

"""Tests for BoardRecommendationService and BoardRecommendation."""

import pytest

from fhs.application.board_recommendation_service import (
    BoardRecommendation,
    BoardRecommendationService,
)
from fhs.core.model import Feature
from fhs.core.model.value_objects.multi_year_result import MultiYearResult


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
            annual_growth_rate=0.05,
            likelihood_of_non_delivery=0.2,
        ),
        Feature(
            name="H2: Traceability",
            expected_users=69_700,
            conversion_rate=0.55,
            uncertainty=0.20,
            business_value_per_conversion=1.77,
            development_cost=50_000.0,
            installment_years=3,
            annual_growth_rate=0.05,
            likelihood_of_non_delivery=0.5,
        ),
        Feature(
            name="H3: Expiry Alerts",
            expected_users=50_000,
            conversion_rate=0.40,
            uncertainty=0.25,
            business_value_per_conversion=1.0,
            development_cost=20_000.0,
            installment_years=1,
            annual_growth_rate=0.03,
            likelihood_of_non_delivery=0.1,
        ),
    ]


@pytest.fixture
def recommendation(features: list[Feature]) -> BoardRecommendation:
    service = BoardRecommendationService(seed=42, scenarios=2_000)
    return service.generate_recommendation(features, discount_rate=0.08)


class TestBoardRecommendationService:
    def test_returns_recommendation(self, recommendation: BoardRecommendation) -> None:
        assert isinstance(recommendation, BoardRecommendation)

    def test_ranked_features_ordered_by_expected(
        self, recommendation: BoardRecommendation
    ) -> None:
        values = [f.expected_eur for f in recommendation.ranked_features]
        assert values == sorted(values, reverse=True)

    def test_go_decision_is_valid_value(
        self, recommendation: BoardRecommendation
    ) -> None:
        assert recommendation.go_decision in {"GO", "CONDITIONAL_GO", "REVIEW"}

    def test_total_cost_matches_feature_sum(
        self, features: list[Feature], recommendation: BoardRecommendation
    ) -> None:
        expected_cost = sum(f.development_cost for f in features)
        assert recommendation.total_cost == expected_cost


class TestBoardRecommendationProperties:
    def test_kpi_phase_data_length_matches_features(
        self, recommendation: BoardRecommendation
    ) -> None:
        assert len(recommendation.kpi_phase_data) == len(recommendation.ranked_features)

    def test_kpi_phase_data_contains_phase_label(
        self, recommendation: BoardRecommendation
    ) -> None:
        labels = [label for _, label in recommendation.kpi_phase_data]
        assert all("Phase" in label for label in labels)

    def test_portfolio_kpi_rows_has_four_entries(
        self, recommendation: BoardRecommendation
    ) -> None:
        assert len(recommendation.portfolio_kpi_rows) == 4

    def test_portfolio_kpi_rows_contains_expected_value(
        self, recommendation: BoardRecommendation
    ) -> None:
        labels = [row[0] for row in recommendation.portfolio_kpi_rows]
        assert "Investment — Full commitment" in labels
        assert "Investment — Year-1 P&L charge" in labels
        assert "Portfolio Expected (Year 1)" in labels
        assert "Portfolio Floor (BVF 95%)" in labels

    def test_portfolio_kpi_rows_values_are_eur_formatted(
        self, recommendation: BoardRecommendation
    ) -> None:
        for _, value, _ in recommendation.portfolio_kpi_rows:
            assert value.startswith("€")

    def test_portfolio_kpi_rows_color_is_none(
        self, recommendation: BoardRecommendation
    ) -> None:
        for _, _, color in recommendation.portfolio_kpi_rows:
            assert color is None

    def test_decision_level_success_for_go(self) -> None:
        rec = _make_recommendation(go_decision="GO")
        assert rec.decision_level == "success"

    def test_decision_level_warning_for_conditional_go(self) -> None:
        rec = _make_recommendation(go_decision="CONDITIONAL_GO")
        assert rec.decision_level == "warning"

    def test_decision_level_warning_for_review(self) -> None:
        rec = _make_recommendation(go_decision="REVIEW")
        assert rec.decision_level == "warning"

    def test_decision_message_includes_reason(self) -> None:
        rec = _make_recommendation(go_decision="GO", go_reason="floor exceeds cost")
        assert "floor exceeds cost" in rec.decision_message


# ── helpers ──────────────────────────────────────────────────────────


def _make_recommendation(
    go_decision: str = "GO",
    go_reason: str = "test reason",
) -> BoardRecommendation:
    return BoardRecommendation(
        portfolio_multi_year=MultiYearResult(
            feature_name="Portfolio", years=[], discount_rate=0.08
        ),
        ranked_features=[],
        go_decision=go_decision,
        go_reason=go_reason,
        total_portfolio_expected=200_000.0,
        total_portfolio_var95=120_000.0,
        total_cost=145_000.0,
        total_annual_installment=61_667.0,
    )
