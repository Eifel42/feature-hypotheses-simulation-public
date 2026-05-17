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
Portfolio Optimization Solver Protocol (DDD Domain Layer)

Defines the contract that all solver implementations must satisfy.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget, OptimizationStrategy
from fhs.core.services.optimization.domain.portfolio_result import PortfolioResult


@runtime_checkable
class PortfolioSolver(Protocol):
    """
    Protocol for portfolio optimization solvers.

    All concrete solver implementations (Exact, Greedy, ILP) must implement
    this interface to ensure consistent behavior and testability.
    """

    # noinspection PyTypeHintsInspection
    def optimize(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        budget: float | Budget,
        strategy: str | OptimizationStrategy,
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        **kwargs,
    ) -> PortfolioResult:
        """
        Find optimal feature portfolio within budget constraint.

        Args:
            features: List of Feature objects to select from
            simulation_results: Mapping of feature name to SimulationResult
            budget: Maximum development budget (float or Budget value object)
            strategy: Optimization criterion (var_floor, expected, sharpe)
            sum_portfolio_scenarios_fn: Optional callback for portfolio aggregation
                with correlation effects. If None, assumes feature independence.
            **kwargs: Solver-specific parameters (e.g., k_candidates for greedy)

        Returns:
            PortfolioResult containing selected features and performance metrics

        Raises:
            ValueError: If inputs are invalid (negative budget, unknown strategy, etc.)
        """
        ...

    @property
    def name(self) -> str:
        """Solver name for logging and reporting (e.g., 'exact', 'ilp')."""
        ...
