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

"""Tests for shapley value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import (
    RiskFactorContribution,
    RiskFactorShapley,
    ShapleyAttribution,
    ShapleyContribution,
)


def test_shapley_contribution_is_immutable() -> None:
    contribution = ShapleyContribution(
        feature="H1: Feature One",
        marginal_risk=20_000.0,
        shapley_value=18_500.0,
        risk_share_pct=0.37,
    )

    with pytest.raises(FrozenInstanceError):
        contribution.feature = "H9"


def test_shapley_attribution_fields() -> None:
    attribution = ShapleyAttribution(
        total_risk=50_000.0,
        risk_metric="cvar_95",
        contributions=(
            ShapleyContribution(
                feature="H1: Feature One",
                marginal_risk=20_000.0,
                shapley_value=18_500.0,
                risk_share_pct=0.37,
            ),
            ShapleyContribution(
                feature="H2: Feature Two",
                marginal_risk=31_500.0,
                shapley_value=31_500.0,
                risk_share_pct=0.63,
            ),
        ),
        selected_features=("H1: Feature One", "H2: Feature Two"),
    )

    assert attribution.total_risk == pytest.approx(50_000.0)
    assert len(attribution.contributions) == 2


def test_risk_factor_shapley_fields() -> None:
    result = RiskFactorShapley(
        metric="cvar_loss",
        confidence=0.95,
        selected=("H1", "H2"),
        baseline_value_eur=12_000.0,
        full_value_eur=40_000.0,
        total_risk_eur=28_000.0,
        contributions=(
            RiskFactorContribution(
                risk="delivery",
                contribution_eur=16_000.0,
                share_of_total=16_000.0 / 28_000.0,
            ),
        ),
        interaction_residual_eur=0.0,
        subset_values_eur={"none": 12_000.0, "delivery": 28_000.0},
    )

    assert result.metric == "cvar_loss"
    assert result.contributions[0].risk == "delivery"
