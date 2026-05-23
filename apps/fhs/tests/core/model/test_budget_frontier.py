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

"""Tests for budget frontier value objects."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import BudgetFrontierRow


def test_budget_frontier_row_is_immutable() -> None:
    row = BudgetFrontierRow(
        budget=200_000.0,
        selected_count=4,
        expected=260_000.0,
        var_95=190_000.0,
        cost=198_000.0,
        budget_remaining=2_000.0,
        roi=0.31,
    )

    with pytest.raises(FrozenInstanceError):
        row.budget = 210_000.0


def test_budget_frontier_row_fields() -> None:
    row = BudgetFrontierRow(
        budget=200_000.0,
        selected_count=4,
        expected=260_000.0,
        var_95=190_000.0,
        cost=198_000.0,
        budget_remaining=2_000.0,
        roi=0.31,
    )

    assert row.selected_count == 4
    assert row.budget_remaining == pytest.approx(row.budget - row.cost)
