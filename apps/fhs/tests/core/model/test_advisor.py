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

"""Tests for advisor value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import (
    BudgetRiskRow,
    FeatureRanking,
    NegativeScoreComparisonRow,
    NegativeScoreFeature,
    StrategyCategoryCostRow,
)


def test_feature_ranking_is_immutable() -> None:
    row = FeatureRanking(
        feature="H1: Feature One",
        expected_business_value=120_000.0,
        var_95_business_value=85_000.0,
        risk_ratio=0.29,
        llp=0.15,
        cost=45_000.0,
    )

    with pytest.raises(FrozenInstanceError):
        row.feature = "H9"


def test_negative_score_feature_fields() -> None:
    row = NegativeScoreFeature(
        feature="H2: Feature Two",
        cost=60_000.0,
        var_95_business_value=55_000.0,
        var_floor_score=-5_000.0,
        ilp_considers=False,
    )

    assert row.var_floor_score < 0
    assert row.ilp_considers is False


def test_negative_score_comparison_row_fields() -> None:
    row = NegativeScoreComparisonRow(
        candidate_set="All features",
        solver="EXACT",
        selected_features=("H1: Feature One",),
        selected_count=1,
        portfolio_var_95=95_000.0,
        total_cost=45_000.0,
    )

    assert row.solver == "EXACT"
    assert row.selected_count == len(row.selected_features)


def test_strategy_category_cost_row_share() -> None:
    row = StrategyCategoryCostRow(category="Growth", cost=80_000.0, share=0.40)
    assert row.category == "Growth"
    assert 0.0 <= row.share <= 1.0


def test_budget_risk_row_fields() -> None:
    row = BudgetRiskRow(
        label="50% Budget",
        budget=200_000.0,
        selected_count=3,
        investment=140_000.0,
        l1_floor=180_000.0,
        l2_floor=160_000.0,
        l3_floor=130_000.0,
        l3_safety_buffer=-10_000.0,
        risk_class="High",
    )

    assert row.selected_count == 3
    assert row.risk_class == "High"
