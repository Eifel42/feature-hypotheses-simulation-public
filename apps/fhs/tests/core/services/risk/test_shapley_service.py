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

"""Tests for ShapleyAttributionService."""

import pytest

from fhs.core.model.value_objects import RiskFactorShapley
from fhs.core.services.risk.shapley import ShapleyAttributionService


def test_attribute_returns_typed_shapley_result() -> None:
    result = ShapleyAttributionService.attribute(
        metric="cvar_loss",
        confidence=0.95,
        selected=("H1", "H2"),
        baseline_value_eur=12_000.0,
        contributions={
            "delivery": 11_000.0,
            "market": 7_000.0,
            "global": 4_000.0,
        },
        subset_values_eur={"none": 12_000.0},
    )

    assert isinstance(result, RiskFactorShapley)
    assert result.total_risk_eur == pytest.approx(22_000.0)
    assert result.full_value_eur == pytest.approx(34_000.0)
    assert result.contributions[0].risk == "delivery"


def test_attribute_validates_inputs() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        ShapleyAttributionService.attribute(
            metric="",
            confidence=0.95,
            selected=(),
            baseline_value_eur=0.0,
            contributions={},
        )

    with pytest.raises(ValueError, match="between 0 and 1"):
        ShapleyAttributionService.attribute(
            metric="cvar_loss",
            confidence=1.2,
            selected=(),
            baseline_value_eur=0.0,
            contributions={},
        )


def test_attribute_from_subset_value_function_builds_result() -> None:
    values = {
        frozenset(): 0.0,
        frozenset({"delivery"}): 10.0,
        frozenset({"market"}): 20.0,
        frozenset({"delivery", "market"}): 30.0,
    }

    result = ShapleyAttributionService.attribute_from_subset_value_function(
        metric="expected_loss",
        selected=("H1",),
        risks=("delivery", "market"),
        value_function=lambda subset: values[subset],
        confidence=0.95,
    )

    assert isinstance(result, RiskFactorShapley)
    assert result.total_risk_eur == pytest.approx(30.0)
    assert result.full_value_eur == pytest.approx(30.0)
    assert result.subset_values_eur["none"] == pytest.approx(0.0)
    assert result.subset_values_eur["delivery+market"] == pytest.approx(30.0)


def test_attribute_from_subset_value_function_validates_metric() -> None:
    with pytest.raises(ValueError, match="Unknown metric"):
        ShapleyAttributionService.attribute_from_subset_value_function(
            metric="unknown_metric",
            selected=("H1",),
            value_function=lambda _: 0.0,
        )
