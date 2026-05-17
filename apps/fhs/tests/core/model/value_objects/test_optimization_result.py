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

from __future__ import annotations

from fhs.core.model.value_objects.optimization_result import OptimizationResult


class TestOptimizationResult:
    """Tests for OptimizationResult value object."""

    def test_getitem(self):
        """__getitem__ returns attribute value."""
        result = OptimizationResult(
            recommended_features=("Feature A",),
            total_cost=100_000.0,
            portfolio_expected=150_000.0,
            portfolio_var_95=80_000.0,
            portfolio_cvar_95=70_000.0,
            portfolio_std_dev=20_000.0,
            budget=200_000.0,
            budget_remaining=100_000.0,
            computation_time_sec=1.5,
            combinations_evaluated=100,
            solver="ilp",
            strategy="var_floor",
            portfolio_roi=0.5,
            roi=0.5,
            safety_buffer=-20_000.0,
            message="Optimal",
            metadata={},
        )
        assert result["total_cost"] == 100_000.0
        assert result["solver"] == "ilp"

    def test_get_with_existing_key(self):
        """get() returns attribute value for existing key."""
        result = OptimizationResult(
            recommended_features=("Feature A",),
            total_cost=100_000.0,
            portfolio_expected=150_000.0,
            portfolio_var_95=80_000.0,
            portfolio_cvar_95=70_000.0,
            portfolio_std_dev=20_000.0,
            budget=200_000.0,
            budget_remaining=100_000.0,
            computation_time_sec=1.5,
            combinations_evaluated=100,
            solver="ilp",
            strategy="var_floor",
            portfolio_roi=0.5,
            roi=0.5,
            safety_buffer=-20_000.0,
            message="Optimal",
            metadata={},
        )
        assert result.get("solver") == "ilp"

    def test_get_with_missing_key(self):
        """get() returns default for missing key."""
        result = OptimizationResult(
            recommended_features=("Feature A",),
            total_cost=100_000.0,
            portfolio_expected=150_000.0,
            portfolio_var_95=80_000.0,
            portfolio_cvar_95=70_000.0,
            portfolio_std_dev=20_000.0,
            budget=200_000.0,
            budget_remaining=100_000.0,
            computation_time_sec=1.5,
            combinations_evaluated=100,
            solver="ilp",
            strategy="var_floor",
            portfolio_roi=0.5,
            roi=0.5,
            safety_buffer=-20_000.0,
            message="Optimal",
            metadata={},
        )
        assert result.get("nonexistent", "default") == "default"
        assert result.get("nonexistent") is None
