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
Greedy Portfolio Solver (Heuristic)

Fast approximation using randomized greedy selection with portfolio refinement.
Suitable for large portfolios (>15 features).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget, OptimizationStrategy
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization.domain import PortfolioResult
from fhs.core.services.optimization.scoring import (
    ObjectiveFunctionFactory,
    PortfolioMetricsCalculator,
)
from fhs.core.typing_utils import to_float_array

logger = logging.getLogger("fhs.optimizer.greedy")

DEFAULT_K_CANDIDATES = 10
DEFAULT_SEED = 42
PERTURBATION_FACTOR = 0.1  # 10% random noise for diversity


class GreedySolver:
    """
    Greedy solver with randomized diversification.

    Algorithm:
    1. Score each feature individually using objective function
    2. Generate K diverse candidates via randomized greedy selection
    3. Evaluate each candidate with full portfolio simulation
    4. Return best candidate

    Complexity: O(K × n log n + K × m) where K=candidates, n=features, m=scenarios
    Recommended for n > 15 features.
    """

    def __init__(self, risk_calculator: RiskCalculator):
        """
        Initialize greedy solver.

        Args:
            risk_calculator: RiskCalculator for VaR/CVaR computation
        """
        self.metrics_calc = PortfolioMetricsCalculator(risk_calculator)

    @property
    def name(self) -> str:
        return "greedy"

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
        Find near-optimal portfolio via greedy heuristic.

        Args:
            features: List of Feature objects to select from
            simulation_results: Mapping of feature name to SimulationResult
            budget: Maximum development budget
            strategy: Optimization criterion (var_floor, expected, sharpe)
            sum_portfolio_scenarios_fn: Portfolio aggregation callback
            **kwargs: Optional parameters:
                - k_candidates (int): Number of greedy candidates (default: 10)
                - seed (int): Random seed for reproducibility (default: 42)

        Returns:
            PortfolioResult with greedy-selected features
        """
        start_time = time.time()

        # Extract kwargs
        k_candidates = kwargs.get("k_candidates", DEFAULT_K_CANDIDATES)
        seed = kwargs.get("seed", DEFAULT_SEED)

        # Validate inputs
        if k_candidates < 1:
            raise ValueError(f"k_candidates must be ≥1, got {k_candidates}")

        # Normalize inputs
        budget_amount = self._normalize_budget(budget)
        discount_rate = float(kwargs.get("discount_rate", 0.08))
        objective_fn = ObjectiveFunctionFactory.create(
            strategy,
            discount_rate=discount_rate,
        )

        logger.info(
            f"Greedy solver: {len(features)} features, "
            f"budget={budget_amount:.0f}, k_candidates={k_candidates}, "
            f"strategy={objective_fn.name}, seed={seed}"
        )

        # Phase 1: Generate K diverse candidates via greedy selection
        greedy_start = time.time()
        candidates = self._generate_candidates(
            features,
            simulation_results,
            budget_amount,
            objective_fn,
            k_candidates,
            seed,
        )
        greedy_time = time.time() - greedy_start

        if not candidates:
            elapsed = time.time() - start_time
            min_cost = min(f.development_cost for f in features)
            logger.warning(f"No valid candidates within budget {budget_amount:.0f}")
            return self._empty_result(
                budget_amount, objective_fn.name, elapsed, greedy_time, 0.0, min_cost
            )

        logger.info(
            f"Greedy phase: Generated {len(candidates)} candidates in {greedy_time:.3f}s"
        )

        # Phase 2: Portfolio simulation refinement
        sim_start = time.time()
        best_candidate, best_metrics = self._refine_candidates(
            candidates,
            simulation_results,
            objective_fn,
            sum_portfolio_scenarios_fn,
        )
        sim_time = time.time() - sim_start

        elapsed = time.time() - start_time
        total_cost = sum(f.development_cost for f in best_candidate)

        logger.info(
            f"Greedy solver completed in {elapsed:.3f}s "
            f"(greedy={greedy_time:.3f}s, simulation={sim_time:.3f}s), "
            f"evaluated {len(candidates)} candidates, "
            f"selected {len(best_candidate)} features"
        )

        return PortfolioResult(
            recommended_features=[f.name for f in best_candidate],
            total_cost=total_cost,
            portfolio_expected=best_metrics.expected,  # type: ignore[attr-defined]
            portfolio_var_95=best_metrics.var_95,  # type: ignore[attr-defined]
            portfolio_cvar_95=best_metrics.cvar_95,  # type: ignore[attr-defined]
            portfolio_std_dev=best_metrics.std_dev,  # type: ignore[attr-defined]
            budget=budget_amount,
            budget_remaining=budget_amount - total_cost,
            computation_time_sec=elapsed,
            combinations_evaluated=len(candidates),
            solver=self.name,
            strategy=objective_fn.name,
            metadata={
                "greedy_time_sec": greedy_time,
                "simulation_time_sec": sim_time,
                "k_candidates": k_candidates,
                "seed": seed,
            },
        )

    def _generate_candidates(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        budget: float,
        objective_fn,
        k: int,
        seed: int,
    ) -> list[list[Feature]]:
        """
        Generate K diverse feature portfolios using randomized greedy.

        Uses NumPy vectorization for score computation and perturbation.

        Args:
            features: List of features
            simulation_results: Simulation results dict
            budget: Budget constraint
            objective_fn: Objective function for scoring
            k: Number of candidates to generate
            seed: Random seed

        Returns:
            List of candidate portfolios (each is a list of Features)
        """
        rng = np.random.default_rng(seed)

        # Score all features using vectorized operations
        feature_scores = self._score_all_features(
            features, simulation_results, objective_fn
        )

        candidates = []
        seen_signatures = set()  # Avoid duplicate candidates

        for _iteration in range(k):
            # Add random perturbation for diversity (vectorized)
            noise = rng.normal(
                0, np.abs(feature_scores) * PERTURBATION_FACTOR, size=len(features)
            )
            perturbed_scores = feature_scores + noise

            # Sort by perturbed scores (descending)
            sorted_indices = np.argsort(perturbed_scores)[::-1]

            # Greedy selection with budget constraint
            selected = []
            remaining_budget = budget

            for idx in sorted_indices:
                feature = features[idx]
                if feature.development_cost <= remaining_budget:
                    selected.append(feature)
                    remaining_budget -= feature.development_cost

            # Add candidate if non-empty and unique
            if selected:
                signature = frozenset(f.name for f in selected)
                if signature not in seen_signatures:
                    candidates.append(selected)
                    seen_signatures.add(signature)

        return candidates

    @staticmethod
    def _score_all_features(
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        objective_fn,
    ) -> np.ndarray:
        """
        Score all features using objective function.

        Vectorized implementation for performance.

        Args:
            features: List of features
            simulation_results: Simulation results dict
            objective_fn: Objective function

        Returns:
            NumPy array of feature scores
        """
        scores = np.empty(len(features))
        for i, feature in enumerate(features):
            result = simulation_results[feature.name]
            scores[i] = objective_fn.score_feature(feature, result)

        return scores

    def _refine_candidates(
        self,
        candidates: list[list[Feature]],
        simulation_results: dict[str, SimulationResult],
        objective_fn,
        sum_portfolio_scenarios_fn,
    ) -> tuple[list[Feature], Any]:
        """
        Evaluate candidates with full portfolio simulation.

        Args:
            candidates: List of candidate portfolios
            simulation_results: Simulation results dict
            objective_fn: Objective function
            sum_portfolio_scenarios_fn: Portfolio aggregation function

        Returns:
            Tuple of (best_candidate, best_metrics)
        """
        best_score = -np.inf
        best_candidate = None
        best_metrics = None

        for candidate in candidates:
            combo_results = {f.name: simulation_results[f.name] for f in candidate}

            # Aggregate portfolio scenarios
            if sum_portfolio_scenarios_fn:
                portfolio_scenarios = sum_portfolio_scenarios_fn(combo_results)
            else:
                portfolio_scenarios = self._simple_sum_scenarios(
                    candidate, combo_results
                )

            # Calculate metrics and score
            metrics = self.metrics_calc.calculate(portfolio_scenarios)
            score = objective_fn.score_portfolio(metrics)

            if score > best_score:
                best_score = score
                best_candidate = candidate
                best_metrics = metrics

        assert best_candidate is not None
        assert best_metrics is not None
        return best_candidate, best_metrics

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _simple_sum_scenarios(
        candidate: list[Feature], combo_results: dict[str, SimulationResult]
    ) -> np.ndarray:
        """Simple portfolio aggregation (vectorized)."""
        arrays = [
            combo_results[f.name].results_array * f.business_value_per_conversion
            for f in candidate
        ]
        return to_float_array(np.sum(arrays, axis=0))

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _normalize_budget(budget: float | Budget) -> float:
        """Normalize budget to float."""
        return budget.amount if isinstance(budget, Budget) else budget

    def _empty_result(
        self,
        budget: float,
        strategy: str,
        elapsed: float,
        greedy_time: float,
        sim_time: float,
        min_cost: float,
    ) -> PortfolioResult:
        """Create empty result for infeasible problem."""
        return PortfolioResult(
            recommended_features=[],
            total_cost=0.0,
            portfolio_expected=0.0,
            portfolio_var_95=0.0,
            portfolio_cvar_95=0.0,
            portfolio_std_dev=0.0,
            budget=budget,
            budget_remaining=budget,
            computation_time_sec=elapsed,
            combinations_evaluated=0,
            solver=self.name,
            strategy=strategy,
            message=f"No features fit within budget {budget:.0f}. "
            f"Cheapest feature costs {min_cost:.0f}",
            metadata={
                "greedy_time_sec": greedy_time,
                "simulation_time_sec": sim_time,
            },
        )
