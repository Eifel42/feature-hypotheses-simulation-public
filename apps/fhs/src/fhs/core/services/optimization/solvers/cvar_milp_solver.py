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

"""CVaR MILP solver using Rockafellar-Uryasev linearization."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization.domain import PortfolioResult
from fhs.core.services.optimization.risk import reduce_scenarios
from fhs.core.services.optimization.scoring import PortfolioMetricsCalculator

logger = logging.getLogger("fhs.optimizer.cvar_milp")


class CVaRMILPSolver:
    """CVaR minimization solver (Rockafellar-Uryasev + scenario reduction)."""

    # noinspection PyTypeHintsInspection
    def __init__(
        self,
        risk_calculator: RiskCalculator | None = None,
        *,
        n_scenarios: int = 300,
        seed: int = 42,
    ):
        if n_scenarios < 1:
            raise ValueError(
                f"n_scenarios must be >= 1, got {n_scenarios}"
            )  # pragma: no cover - defensive
        self.metrics_calc = PortfolioMetricsCalculator(
            risk_calculator or RiskCalculator()
        )
        self.n_scenarios = int(n_scenarios)
        self.seed = int(seed)

    @property
    def name(self) -> str:
        return "cvar_milp"

    # noinspection PyTypeHintsInspection
    def solve(
        self,
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        budget: float | Budget,
        alpha: float = 0.95,
        *,
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
    ) -> PortfolioResult:
        """Solve portfolio selection by minimizing portfolio CVaR."""
        start_time = time.time()
        budget_amount = self._normalize_budget(budget)
        self._validate_inputs(features, sim_results, budget_amount, alpha)

        logger.info(
            "CVaR-MILP solver: %s features, budget=%.0f, alpha=%.3f, reduced_scenarios=%s",
            len(features),
            budget_amount,
            alpha,
            self.n_scenarios,
        )

        names = [feature.name for feature in features]
        costs = np.array(
            [feature.development_cost for feature in features], dtype=float
        )
        full_matrix = self._build_full_scenario_matrix(features, sim_results)
        n_original = full_matrix.shape[0]

        if self.n_scenarios < n_original:
            reduced_matrix, weights = reduce_scenarios(
                {name: full_matrix[:, idx] for idx, name in enumerate(names)},
                n_reduced=self.n_scenarios,
                seed=self.seed,
            )
            reduced = True
        else:
            reduced_matrix = full_matrix
            weights = np.full(n_original, 1.0 / float(n_original), dtype=float)
            reduced = False

        result = self._solve_milp(
            scenario_matrix=reduced_matrix,
            weights=weights,
            costs=costs,
            budget=budget_amount,
            alpha=alpha,
        )

        elapsed = time.time() - start_time
        if not result.success:
            logger.warning(
                "CVaR-MILP failed: %s", result.message
            )  # pragma: no cover - defensive
            return self._failure_result(  # pragma: no cover - defensive
                budget=budget_amount,
                elapsed=elapsed,
                error_msg=str(result.message),
            )

        selected = self._extract_selected_features(features, result.x[: len(features)])
        if not selected:
            logger.warning(
                "CVaR-MILP selected no features"
            )  # pragma: no cover - defensive
            return self._empty_result(  # pragma: no cover - defensive
                budget=budget_amount,
                elapsed=elapsed,
                message="CVaR-MILP selected no features",
            )

        selected_results = {
            feature.name: sim_results[feature.name] for feature in selected
        }
        if sum_portfolio_scenarios_fn is not None:
            portfolio_scenarios = sum_portfolio_scenarios_fn(selected_results)
        else:
            portfolio_scenarios = self._simple_sum_scenarios(selected, selected_results)
        metrics = self.metrics_calc.calculate(portfolio_scenarios)

        total_cost = float(sum(feature.development_cost for feature in selected))
        logger.info(
            "CVaR-MILP completed in %.4fs, selected %s features",
            elapsed,
            len(selected),
        )

        return PortfolioResult(
            recommended_features=[feature.name for feature in selected],
            total_cost=total_cost,
            portfolio_expected=metrics.expected,
            portfolio_var_95=metrics.var_95,
            portfolio_cvar_95=metrics.cvar_95,
            portfolio_std_dev=metrics.std_dev,
            budget=budget_amount,
            budget_remaining=budget_amount - total_cost,
            computation_time_sec=elapsed,
            combinations_evaluated=1,
            solver=self.name,
            strategy=f"cvar_{round(alpha * 100)}",
            metadata={
                "alpha": alpha,
                "scenarios_original": int(n_original),
                "scenarios_optimized": int(reduced_matrix.shape[0]),
                "scenario_reduced": reduced,
                "milp_status": int(result.status),
                "milp_message": str(result.message),
            },
        )

    @staticmethod
    def _solve_milp(
        *,
        scenario_matrix: np.ndarray,
        weights: np.ndarray,
        costs: np.ndarray,
        budget: float,
        alpha: float,
    ):
        """Build and solve MILP with variables [x_1..x_J, theta, z_1..z_N]."""
        n_scenarios, n_features = scenario_matrix.shape
        theta_idx = n_features
        z_start = n_features + 1
        n_variables = n_features + 1 + n_scenarios

        c = np.zeros(n_variables, dtype=float)
        c[theta_idx] = 1.0
        denominator = (1.0 - alpha) * float(np.sum(weights))
        if denominator <= 0.0:
            raise ValueError(
                "invalid alpha/weights setup for CVaR objective"
            )  # pragma: no cover - defensive
        c[z_start:] = weights / denominator

        a_budget = np.zeros((1, n_variables), dtype=float)
        a_budget[0, :n_features] = costs
        budget_constraint = LinearConstraint(a_budget, lb=-np.inf, ub=budget)

        a_tail = np.zeros((n_scenarios, n_variables), dtype=float)
        a_tail[:, :n_features] = scenario_matrix
        a_tail[:, theta_idx] = 1.0
        a_tail[np.arange(n_scenarios), z_start + np.arange(n_scenarios)] = 1.0
        tail_constraint = LinearConstraint(
            a_tail,
            lb=np.zeros(n_scenarios, dtype=float),
            ub=np.full(n_scenarios, np.inf, dtype=float),
        )

        a_min_features = np.zeros((1, n_variables), dtype=float)
        a_min_features[0, :n_features] = 1.0
        min_features_constraint = LinearConstraint(a_min_features, lb=1.0, ub=np.inf)

        integrality = np.zeros(n_variables, dtype=int)
        integrality[:n_features] = 1

        lower = np.concatenate(
            [
                np.zeros(n_features, dtype=float),  # x_j >= 0
                np.array([-np.inf], dtype=float),  # theta unbounded
                np.zeros(n_scenarios, dtype=float),  # z_i >= 0
            ]
        )
        upper = np.concatenate(
            [
                np.ones(n_features, dtype=float),  # x_j <= 1
                np.array([np.inf], dtype=float),  # theta unbounded
                np.full(n_scenarios, np.inf, dtype=float),  # z_i unbounded above
            ]
        )
        bounds = Bounds(lb=lower, ub=upper)

        return milp(
            c=c,
            constraints=[budget_constraint, tail_constraint, min_features_constraint],
            integrality=integrality,
            bounds=bounds,
        )

    # noinspection PyTypeHintsInspection
    def solve_from_profit_scenarios(
        self,
        profit_scenarios: dict[str, np.ndarray],
        costs: dict[str, float],
        budget: float | Budget,
        alpha: float = 0.95,
    ) -> PortfolioResult:
        """Solve portfolio selection from pre-computed profit scenarios.

        Unlike ``solve()``, this method accepts profit arrays directly
        (e.g. business value-after-risk minus simulated development cost) so the
        caller controls how scenarios are built.

        Args:
            profit_scenarios: ``{feature_name: 1-D profit array}`` per feature.
            costs: ``{feature_name: development_cost}`` used for the budget constraint.
            budget: Maximum total development cost.
            alpha: CVaR confidence level (default 0.95).

        Returns:
            PortfolioResult with selected features that minimise CVaR of profit.
        """
        start_time = time.time()
        budget_amount = self._normalize_budget(budget)

        if not profit_scenarios:
            raise ValueError(
                "profit_scenarios must not be empty"
            )  # pragma: no cover - defensive
        if budget_amount < 0:
            raise ValueError(
                f"budget must be non-negative, got {budget_amount}"
            )  # pragma: no cover - defensive
        if not (0.0 < alpha < 1.0):
            raise ValueError(
                f"alpha must be in (0, 1), got {alpha}"
            )  # pragma: no cover - defensive

        names = list(profit_scenarios.keys())
        cost_array = np.array([costs[n] for n in names], dtype=float)

        # Build scenario matrix from profit arrays
        arrays: list[np.ndarray] = []
        expected_len: int | None = None
        for name in names:
            arr = np.asarray(profit_scenarios[name], dtype=float)
            if expected_len is None:
                expected_len = len(arr)
            elif len(arr) != expected_len:
                raise ValueError(
                    "all profit scenario arrays must have the same length"
                )  # pragma: no cover - defensive
            arrays.append(arr)
        full_matrix = np.column_stack(arrays)
        n_original = full_matrix.shape[0]

        logger.info(
            "CVaR-MILP profit solver: %s features, budget=%.0f, alpha=%.3f",
            len(names),
            budget_amount,
            alpha,
        )

        if self.n_scenarios < n_original:
            reduced_matrix, weights = reduce_scenarios(
                {name: full_matrix[:, idx] for idx, name in enumerate(names)},
                n_reduced=self.n_scenarios,
                seed=self.seed,
            )
            reduced = True
        else:
            reduced_matrix = full_matrix
            weights = np.full(n_original, 1.0 / float(n_original), dtype=float)
            reduced = False

        result = self._solve_milp(
            scenario_matrix=reduced_matrix,
            weights=weights,
            costs=cost_array,
            budget=budget_amount,
            alpha=alpha,
        )

        elapsed = time.time() - start_time
        if not result.success:
            logger.warning(
                "CVaR-MILP profit solver failed: %s", result.message
            )  # pragma: no cover - defensive
            return self._failure_result(  # pragma: no cover - defensive
                budget=budget_amount, elapsed=elapsed, error_msg=str(result.message)
            )

        selected_indices = np.nonzero(result.x[: len(names)] > 0.5)[0]
        selected_names = [names[i] for i in selected_indices]
        if not selected_names:
            return self._empty_result(  # pragma: no cover - defensive
                budget=budget_amount,
                elapsed=elapsed,
                message="CVaR-MILP profit solver selected no features",
            )

        # Compute portfolio metrics from selected features' profit scenarios
        portfolio_profit = np.sum([profit_scenarios[n] for n in selected_names], axis=0)
        metrics = self.metrics_calc.calculate(portfolio_profit)
        total_cost = float(sum(costs[n] for n in selected_names))

        logger.info(
            "CVaR-MILP profit solver completed in %.4fs, selected %s features",
            elapsed,
            len(selected_names),
        )

        return PortfolioResult(
            recommended_features=selected_names,
            total_cost=total_cost,
            portfolio_expected=metrics.expected,
            portfolio_var_95=metrics.var_95,
            portfolio_cvar_95=metrics.cvar_95,
            portfolio_std_dev=metrics.std_dev,
            budget=budget_amount,
            budget_remaining=budget_amount - total_cost,
            computation_time_sec=elapsed,
            combinations_evaluated=1,
            solver=self.name,
            strategy=f"cvar_profit_{round(alpha * 100)}",
            metadata={
                "alpha": alpha,
                "scenarios_original": int(n_original),
                "scenarios_optimized": int(reduced_matrix.shape[0]),
                "scenario_reduced": reduced,
                "milp_status": int(result.status),
                "milp_message": str(result.message),
                "mode": "profit",
            },
        )

    @staticmethod
    def _build_full_scenario_matrix(
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
    ) -> np.ndarray:
        arrays = []
        expected_len: int | None = None
        for feature in features:
            if feature.name not in sim_results:
                raise ValueError(  # pragma: no cover - defensive
                    f"Missing simulation result for feature '{feature.name}'"
                )
            scaled = (
                np.asarray(sim_results[feature.name].results_array, dtype=float)
                * feature.business_value_per_conversion
            )
            if expected_len is None:
                expected_len = len(scaled)
            elif len(scaled) != expected_len:
                raise ValueError(  # pragma: no cover - defensive
                    "all simulation result arrays must have the same length"
                )
            arrays.append(scaled)

        if not arrays:
            return np.empty((0, 0), dtype=float)  # pragma: no cover - defensive
        return np.column_stack(arrays)

    @staticmethod
    def _extract_selected_features(
        features: list[Feature],
        solution: np.ndarray,
    ) -> list[Feature]:
        selected_indices = np.nonzero(solution > 0.5)[0]
        return [features[idx] for idx in selected_indices]

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _simple_sum_scenarios(
        selected: list[Feature],
        selected_results: dict[str, SimulationResult],
    ) -> np.ndarray:
        arrays = [
            selected_results[feature.name].results_array
            * feature.business_value_per_conversion
            for feature in selected
        ]
        return np.asarray(np.sum(arrays, axis=0), dtype=float)

    @staticmethod
    # noinspection PyTypeHintsInspection
    def _normalize_budget(budget: float | Budget) -> float:
        return budget.amount if isinstance(budget, Budget) else float(budget)

    @staticmethod
    def _validate_inputs(
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        budget: float,
        alpha: float,
    ) -> None:
        if not features:
            raise ValueError(
                "features must not be empty"
            )  # pragma: no cover - defensive
        if budget < 0:
            raise ValueError(
                f"budget must be non-negative, got {budget}"
            )  # pragma: no cover - defensive
        if not (0.0 < alpha < 1.0):
            raise ValueError(
                f"alpha must be in (0, 1), got {alpha}"
            )  # pragma: no cover - defensive

        missing = [
            feature.name for feature in features if feature.name not in sim_results
        ]
        if missing:
            raise ValueError(
                f"Missing simulation results for features: {missing}"
            )  # pragma: no cover - defensive

    def _empty_result(
        self, budget: float, elapsed: float, message: str
    ) -> PortfolioResult:
        return PortfolioResult(  # pragma: no cover - defensive
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
            strategy="cvar_95",
            message=message,
        )

    def _failure_result(
        self,
        budget: float,
        elapsed: float,
        error_msg: str,
    ) -> PortfolioResult:
        return PortfolioResult(  # pragma: no cover - defensive
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
            strategy="cvar_95",
            message=f"CVaR-MILP solver failed: {error_msg}",
        )
