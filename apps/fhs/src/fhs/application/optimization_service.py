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
Portfolio Optimizer Facade: DDD Architecture with Four Solvers

This facade maintains backwards compatibility while delegating to the refactored
DDD architecture in core.services.optimization.

Solvers:
1. Exact Solver (Exhaustive Search): Evaluates all valid combinations — guarantees global optimum
2. Greedy Solver (Randomized + Portfolio Simulation): Fast approximation with diversity
3. ILP Solver (Integer Linear Programming): Mathematical optimisation using scipy.optimize.milp
4. CVaR-MILP Solver: Scenario-based CVaR minimization via Rockafellar-Uryasev
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.value_objects import Budget, OptimizationStrategy
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization.domain import PortfolioResult
from fhs.core.services.optimization.risk.delivery_analyzer import DeliveryRiskAnalyzer
from fhs.core.services.optimization.solvers.cvar_milp_solver import CVaRMILPSolver
from fhs.core.services.optimization.solvers.exact_solver import ExactSolver
from fhs.core.services.optimization.solvers.greedy_solver import GreedySolver
from fhs.core.services.optimization.solvers.ilp_solver import ILPSolver

logger = logging.getLogger("fhs.optimizer")


class PortfolioOptimizer:
    """
    Portfolio optimizer facade with exact, greedy, ILP, and CVaR-MILP solvers.

    This class maintains backwards compatibility with the original API while
    delegating to the refactored DDD architecture.

    For small portfolios (≤15 features), the exact solver finds the globally
    optimal solution by evaluating all valid feature combinations.

    For larger portfolios (>15 features), use the greedy or ILP solver.
    """

    # noinspection PyTypeHintsInspection
    def __init__(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        risk_calculator: RiskCalculator,
    ):
        """
        Initialize optimizer.

        Args:
            features: List of Feature objects
            simulation_results: Dict mapping feature name -> SimulationResult
            risk_calculator: RiskCalculator instance for VaR/CVaR computation
        """
        self.features = features
        self.simulation_results = simulation_results
        self.calculator = risk_calculator

        # Initialize solvers (DDD architecture)
        self._exact_solver = ExactSolver(risk_calculator)
        self._greedy_solver = GreedySolver(risk_calculator)
        self._ilp_solver = ILPSolver(risk_calculator)
        self._cvar_milp_solver: CVaRMILPSolver | None = None

        # Risk analysis delegate
        self._delivery_analyzer = DeliveryRiskAnalyzer(features, simulation_results)

    # noinspection PyTypeHintsInspection
    def optimize_exact(
        self,
        budget: float | Budget,
        strategy: str | OptimizationStrategy = "var_floor",
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        discount_rate: float = 0.08,
    ) -> PortfolioResult:
        """
        Exact solver using exhaustive combinatorial search.

        Evaluates all C(n,k) combinations that fit within budget and selects
        the one that maximizes the chosen metric.

        Args:
            budget: Maximum development budget (e.g., EUR)
            strategy: Optimization criterion:
                - "var_floor": Maximize Portfolio VaR95 (worst-case business value at 95% confidence)
                - "expected": Maximize expected portfolio business value
                - "sharpe": Maximize Sharpe ratio (expected / std_dev)
            sum_portfolio_scenarios_fn: Optional callback to sum correlated scenarios.
                Signature: (dict[str, SimulationResult]) -> np.ndarray
            discount_rate: Annual discount rate for NPV calculations.

        Returns:
            PortfolioResult with optimization results including recommended features,
            costs, portfolio metrics, and solver metadata.
        """
        return self._exact_solver.optimize(
            features=self.features,
            simulation_results=self.simulation_results,
            budget=budget,
            strategy=strategy,
            sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
            discount_rate=discount_rate,
        )

    # noinspection PyTypeHintsInspection
    def optimize_greedy(
        self,
        budget: float | Budget,
        strategy: str | OptimizationStrategy = "var_floor",
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        k: int = 10,
        seed: int | None = None,
        discount_rate: float = 0.08,
    ) -> PortfolioResult:
        """
        Greedy solver with randomized candidate generation.

        Generates K candidate solutions by perturbing feature scores and
        greedily selecting features. Returns the best portfolio after
        full simulation.

        Args:
            budget: Maximum development budget
            strategy: Optimization criterion (var_floor, expected, sharpe)
            sum_portfolio_scenarios_fn: Optional callback for correlated scenarios
            k: Number of candidate solutions to generate (default: 10)
            seed: Random seed for reproducibility
            discount_rate: Annual discount rate for NPV calculations.

        Returns:
            PortfolioResult with optimization results
        """
        return self._greedy_solver.optimize(
            features=self.features,
            simulation_results=self.simulation_results,
            budget=budget,
            strategy=strategy,
            sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
            k=k,
            seed=seed,
            discount_rate=discount_rate,
        )

    # noinspection PyTypeHintsInspection
    def optimize_ilp(
        self,
        budget: float | Budget,
        strategy: str | OptimizationStrategy = "var_floor",
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        discount_rate: float = 0.08,
    ) -> PortfolioResult:
        """
        ILP solver using scipy.optimize.milp.

        Formulates the portfolio optimization as an integer linear program
        and solves it using scipy's MIP solver.

        Args:
            budget: Maximum development budget
            strategy: Optimization criterion (var_floor, expected, sharpe)
            sum_portfolio_scenarios_fn: Optional callback for correlated scenarios
            discount_rate: Annual discount rate for NPV calculations.

        Returns:
            PortfolioResult with optimization results
        """
        return self._ilp_solver.optimize(
            features=self.features,
            simulation_results=self.simulation_results,
            budget=budget,
            strategy=strategy,
            sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
            discount_rate=discount_rate,
        )

    # noinspection PyTypeHintsInspection
    def optimize_cvar(
        self,
        budget: float | Budget,
        alpha: float = 0.95,
        n_scenarios: int = 300,
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        profit_scenarios: dict[str, np.ndarray] | None = None,
    ) -> PortfolioResult:
        """
        Scenario-based CVaR minimization via MILP.

        Args:
            budget: Maximum development budget
            alpha: CVaR confidence level (e.g., 0.95)
            n_scenarios: Reduced scenario count used inside MILP
            sum_portfolio_scenarios_fn: Optional callback for correlated scenarios
            profit_scenarios: Optional per-feature profit arrays (EUR per scenario).
                If provided, CVaR is optimized on profit instead of business value.

        Returns:
            PortfolioResult with optimization results
        """
        if (
            self._cvar_milp_solver is None
            or self._cvar_milp_solver.n_scenarios != n_scenarios
        ):
            self._cvar_milp_solver = CVaRMILPSolver(
                risk_calculator=self.calculator,
                n_scenarios=n_scenarios,
                seed=42,
            )

        solver_features = self.features
        solver_sim_results = self.simulation_results
        if profit_scenarios is not None:
            solver_features, solver_sim_results = self._build_profit_inputs(
                profit_scenarios
            )
            logger.info(
                "CVaR-MILP uses profit scenarios for %s features",
                len(solver_features),
            )

        return self._cvar_milp_solver.solve(
            features=solver_features,
            sim_results=solver_sim_results,
            budget=budget,
            alpha=alpha,
            sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
        )

    # noinspection PyTypeHintsInspection
    def _build_profit_inputs(
        self,
        profit_scenarios: dict[str, np.ndarray],
    ) -> tuple[list[Feature], dict[str, SimulationResult]]:
        """Build solver inputs that treat each scenario array as profit in EUR."""
        missing = [
            feature.name
            for feature in self.features
            if feature.name not in profit_scenarios
        ]
        if missing:
            raise ValueError(f"Missing profit scenarios for features: {missing}")

        arrays_by_name: dict[str, np.ndarray] = {
            name: np.asarray(values, dtype=float)
            for name, values in profit_scenarios.items()
        }
        lengths = {len(arrays_by_name[feature.name]) for feature in self.features}
        if len(lengths) != 1:
            raise ValueError(
                "All profit scenario arrays must have the same length"
            )  # pragma: no cover - defensive

        # Avoid double-scaling in CVaRMILPSolver (it multiplies by business_value_per_conversion).
        features = [
            feature.model_copy(update={"business_value_per_conversion": 1.0})
            for feature in self.features
        ]
        sim_results = {
            feature.name: SimulationResult(
                feature_name=feature.name,
                results=arrays_by_name[feature.name],
                scenarios=len(arrays_by_name[feature.name]),
                expected_value=(
                    float(np.mean(arrays_by_name[feature.name]))
                    if len(arrays_by_name[feature.name]) > 0
                    else 0.0
                ),
                business_value_per_conversion=1.0,
                development_cost=feature.development_cost,
            )
            for feature in self.features
        }
        return features, sim_results

    # noinspection PyTypeHintsInspection
    def optimize(
        self,
        budget: float | Budget,
        strategy: str | OptimizationStrategy = "var_floor",
        solver: str = "auto",
        sum_portfolio_scenarios_fn: (
            Callable[[dict[str, SimulationResult]], np.ndarray] | None
        ) = None,
        discount_rate: float = 0.08,
        **kwargs,
    ) -> PortfolioResult:
        """
        Optimize portfolio with automatic solver selection.

        Args:
            budget: Maximum development budget
            strategy: Optimization criterion (var_floor, expected, sharpe)
            solver: Solver to use:
                - "auto": Exact if ≤15 features, greedy otherwise
                - "exact": Exhaustive search
                - "greedy": Randomized greedy
                - "ilp": Integer linear programming
                - "cvar_milp": Scenario-based CVaR minimization
            sum_portfolio_scenarios_fn: Optional callback for correlated scenarios
            discount_rate: Annual discount rate for NPV calculations.
            **kwargs: Additional solver-specific arguments (e.g., k, seed for greedy)

        Returns:
            PortfolioResult with optimization results
        """
        n_features = len(self.features)

        if solver == "auto":
            solver = "exact" if n_features <= 15 else "greedy"
            logger.info(f"Auto-selected solver='{solver}' for {n_features} features")

        if solver == "exact":
            return self.optimize_exact(
                budget,
                strategy,
                sum_portfolio_scenarios_fn,
                discount_rate=discount_rate,
            )
        elif solver == "greedy":
            return self.optimize_greedy(  # pragma: no cover - defensive
                budget,
                strategy,
                sum_portfolio_scenarios_fn,
                discount_rate=discount_rate,
                **kwargs,
            )
        elif solver == "ilp":
            return self.optimize_ilp(  # pragma: no cover - defensive
                budget,
                strategy,
                sum_portfolio_scenarios_fn,
                discount_rate=discount_rate,
            )
        elif solver == "cvar_milp":
            alpha = float(kwargs.get("alpha", 0.95))
            n_scenarios = int(kwargs.get("n_scenarios", 300))
            profit_scenarios = kwargs.get("profit_scenarios")
            return self.optimize_cvar(
                budget=budget,
                alpha=alpha,
                n_scenarios=n_scenarios,
                sum_portfolio_scenarios_fn=sum_portfolio_scenarios_fn,
                profit_scenarios=profit_scenarios,
            )
        else:
            raise ValueError(  # pragma: no cover - defensive
                "Unknown solver "
                f"'{solver}'. Valid options: exact, greedy, ilp, cvar_milp, auto"
            )

    # noinspection PyTypeHintsInspection
    def analyze_delivery_risk(
        self,
        solver_result: PortfolioResult | dict[str, Any],
        *,
        seed: int = 42,
        systematic_shock_probability: float = 0.0,
        systematic_shock_multiplier: float = 0.3,
    ) -> dict[str, Any]:
        """
        Overlay delivery risk on a solver's recommended portfolio.

        Delegates to core ``DeliveryRiskAnalyzer``.

        Args:
            solver_result: PortfolioResult from any solver.
            seed: RNG seed for reproducibility.
            systematic_shock_probability: Probability of a portfolio-wide
                external shock per scenario (e.g. 0.05 = 5 %).
            systematic_shock_multiplier: Business value multiplier when a shock
                occurs (e.g. 0.3 = business value drops to 30 %).

        Returns:
            Dictionary with per-feature details and portfolio-level metrics
            for all computed risk levels.
        """
        if isinstance(solver_result, dict):
            if not solver_result.get("recommended_features"):
                # noinspection PyProtectedMember
                return self._delivery_analyzer._empty_analysis(
                    str(solver_result.get("solver", "unknown"))
                )
            portfolio_result = PortfolioResult(
                **solver_result
            )  # pragma: no cover - defensive
        else:
            portfolio_result = solver_result

        # Fast path: empty portfolio doesn't need full analysis
        if not portfolio_result.recommended_features:
            # noinspection PyProtectedMember
            return self._delivery_analyzer._empty_analysis(
                portfolio_result.solver
            )  # pragma: no cover - defensive

        analysis = self._delivery_analyzer.analyze(
            portfolio_result,
            seed=seed,
            systematic_shock_probability=systematic_shock_probability,
            systematic_shock_multiplier=systematic_shock_multiplier,
        )

        investment = float(portfolio_result.total_cost)
        analysis["investment"] = investment

        market_var_95 = float(analysis.get("market_var_95", 0.0))
        simulated_var_95 = float(analysis.get("simulated_var_95", 0.0))
        analysis["market_safety_buffer"] = market_var_95 - investment
        analysis["simulated_safety_buffer"] = simulated_var_95 - investment

        if "shocked_var_95" in analysis:
            shocked_var_95 = float(analysis.get("shocked_var_95", 0.0))
            analysis["shocked_safety_buffer"] = shocked_var_95 - investment

        return analysis

    # noinspection PyTypeHintsInspection
    def analyze_budget_risk_profiles(
        self,
        budgets: list[float | Budget],
        *,
        strategy: str | OptimizationStrategy = "var_floor",
        solvers: tuple[str, ...] = ("exact", "ilp"),
        seed: int = 42,
        systematic_shock_probability: float = 0.0,
        systematic_shock_multiplier: float = 0.3,
    ) -> dict[float, dict[str, Any]]:
        """
        Analyze market, delivery, and shock risk across sample budgets.

        Delegates optimization to individual solvers and risk analysis to
        core ``DeliveryRiskAnalyzer``.

        Args:
            budgets: Budget amounts to evaluate.
            strategy: Optimisation strategy used by each solver.
            solvers: Solver names to evaluate. Supported: ``exact``, ``greedy``,
                ``ilp``, and ``cvar_milp``.
            seed: RNG seed for reproducible delivery-risk overlays.
            systematic_shock_probability: Probability of a portfolio-wide shock.
            systematic_shock_multiplier: Business value multiplier applied in shock cases.

        Returns:
            Nested dictionary keyed by budget and solver. Each solver entry
            contains the solver result, risk analysis for level 1 and level 3,
            and the selected feature count.
        """

        # noinspection PyTypeHintsInspection
        def _solve_cvar(
            bgt: float,
            strat: str,
        ) -> PortfolioResult:
            _ = strat
            return self.optimize_cvar(
                budget=bgt,
                alpha=0.95,
            )

        supported_solvers: dict[str, Callable[[float, str], PortfolioResult]] = {
            "exact": self.optimize_exact,
            "greedy": self.optimize_greedy,
            "ilp": self.optimize_ilp,
            "cvar_milp": _solve_cvar,
        }

        unknown_solvers = [
            solver for solver in solvers if solver not in supported_solvers
        ]
        if unknown_solvers:
            raise ValueError(
                f"Unknown solver(s) {unknown_solvers}. Valid options: {tuple(supported_solvers)}"
            )

        results: dict[float, dict[str, Any]] = {}
        for budget in budgets:
            budget_amount = budget.amount if isinstance(budget, Budget) else budget
            results[budget_amount] = {}

            for solver_name in solvers:
                solver_fn = supported_solvers[solver_name]
                solver_result = solver_fn(budget_amount, strategy)

                feature_count = len(solver_result.recommended_features)
                if feature_count == 0:
                    continue

                level_1 = self.analyze_delivery_risk(solver_result, seed=seed)
                level_3 = self.analyze_delivery_risk(
                    solver_result,
                    seed=seed,
                    systematic_shock_probability=systematic_shock_probability,
                    systematic_shock_multiplier=systematic_shock_multiplier,
                )

                results[budget_amount][solver_name] = {
                    "solver_result": solver_result,
                    "feature_count": feature_count,
                    "l1": level_1,
                    "l3": level_3,
                }

        return results
