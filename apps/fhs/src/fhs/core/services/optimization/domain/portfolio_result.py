#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""
Portfolio Optimization Result Value Object (DDD Domain Layer)

Immutable result container for optimization outcomes.
"""

from typing import Any

from pydantic import BaseModel, Field


class PortfolioResult(BaseModel):
    """
    Value Object representing portfolio optimization result.

    Immutable container for solver output. All solvers return this
    standardized structure for consistency across algorithms.
    """

    # Selected Features
    recommended_features: list[str] = Field(
        ..., description="List of selected feature names"
    )
    total_cost: float = Field(..., ge=0.0, description="Total development cost")

    # Portfolio Metrics
    portfolio_expected: float = Field(
        ..., description="Expected portfolio business value"
    )
    portfolio_var_95: float = Field(..., description="Value at Risk (95%)")
    portfolio_cvar_95: float = Field(..., description="Conditional VaR (95%)")
    portfolio_std_dev: float = Field(..., ge=0.0, description="Portfolio volatility")

    # Budget Information
    budget: float = Field(..., ge=0.0, description="Budget constraint used")
    budget_remaining: float = Field(..., ge=0.0, description="Unused budget")

    # Solver Metadata
    solver: str = Field(..., description="Solver name (exact, greedy, ilp)")
    strategy: str = Field(..., description="Optimization strategy used")
    computation_time_sec: float = Field(..., ge=0.0, description="Solver runtime")
    combinations_evaluated: int = Field(
        ..., ge=0, description="Number of combinations evaluated"
    )

    # Optional Fields
    message: str | None = Field(
        default=None, description="Optional status/warning message"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Solver-specific metadata"
    )

    model_config = {"frozen": True}  # Immutable

    @property
    def feature_count(self) -> int:
        """Number of selected features."""
        return len(self.recommended_features)

    @property
    def budget_utilization(self) -> float:
        """Budget utilization ratio (0.0 to 1.0)."""
        if self.budget <= 0:
            return 0.0  # pragma: no cover - defensive
        return self.total_cost / self.budget

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (for backwards compatibility)."""
        return self.model_dump(exclude_none=True)  # pragma: no cover - defensive

    def __getitem__(self, key: str) -> Any:
        """Dict-style access for backward compatibility."""
        return getattr(self, key)  # pragma: no cover - defensive

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style get for backward compatibility."""
        return getattr(self, key, default)  # pragma: no cover - defensive

    def __contains__(self, key: object) -> bool:
        """Support `"field" in result` checks used by legacy callers/tests."""
        if not isinstance(key, str):
            return False  # pragma: no cover - defensive
        return key in self.model_dump(exclude_none=False)
