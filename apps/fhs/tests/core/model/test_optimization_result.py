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

"""Tests for OptimizationResult value object."""

from dataclasses import FrozenInstanceError

import pytest

from fhs.core.model.value_objects import OptimizationResult


def test_optimization_result_construction() -> None:
    result = OptimizationResult(
        recommended_features=("Feature A", "Feature B"),
        total_cost=120_000.0,
        portfolio_expected=220_000.0,
        portfolio_var_95=160_000.0,
        portfolio_cvar_95=145_000.0,
        portfolio_std_dev=35_000.0,
        budget=150_000.0,
        budget_remaining=30_000.0,
        computation_time_sec=0.12,
        combinations_evaluated=32,
        solver="ilp",
        strategy="var_floor",
        portfolio_roi=0.8333,
        roi=0.8333,
        safety_buffer=40_000.0,
        message="ok",
        metadata={"status": "optimal"},
    )
    assert result.recommended_features == ("Feature A", "Feature B")
    assert result.budget_remaining == 30_000.0
    assert result.portfolio_var_95 > result.total_cost


def test_optimization_result_is_immutable() -> None:
    result = OptimizationResult(
        recommended_features=(),
        total_cost=0.0,
        portfolio_expected=0.0,
        portfolio_var_95=0.0,
        portfolio_cvar_95=0.0,
        portfolio_std_dev=0.0,
        budget=0.0,
        budget_remaining=0.0,
        computation_time_sec=0.0,
        combinations_evaluated=0,
        solver="not_run",
        strategy="var_floor",
        portfolio_roi=0.0,
        roi=0.0,
        safety_buffer=0.0,
        message="empty",
        metadata={"status": "skipped"},
    )
    with pytest.raises(FrozenInstanceError):
        result.solver = "ilp"
