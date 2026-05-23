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

"""Tests for budget-check value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import BudgetCheckResult, FeatureBudgetCheckRow


def test_feature_budget_check_row_is_immutable() -> None:
    row = FeatureBudgetCheckRow(
        feature_key="H1",
        feature_name="H1: Feature One",
        short_name="Feature One",
        development_cost=50_000.0,
        budget_share=0.25,
        fits_budget=True,
    )

    with pytest.raises(FrozenInstanceError):
        row.feature_key = "H9"


def test_budget_check_result_fields() -> None:
    result = BudgetCheckResult(
        rows=(
            FeatureBudgetCheckRow(
                feature_key="H1",
                feature_name="H1: Feature One",
                short_name="Feature One",
                development_cost=50_000.0,
                budget_share=0.25,
                fits_budget=True,
            ),
        ),
        budget=200_000.0,
        total_cost=50_000.0,
        budget_left=150_000.0,
        budget_share=0.25,
        fits_budget=True,
        small_buffer=False,
    )

    assert result.rows[0].short_name == "Feature One"
    assert result.budget_left > 0
