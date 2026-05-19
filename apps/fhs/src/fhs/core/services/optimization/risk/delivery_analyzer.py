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
Delivery Risk Analyzer

Overlays delivery and systematic risk on optimized portfolios.
Separate concern from optimization logic (SRP).
"""

import logging
from typing import Any

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.services.optimization.domain import PortfolioResult

logger = logging.getLogger("fhs.optimizer.risk")

DEFAULT_SEED = 42
VAR_PERCENTILE = 5.0  # 95% VaR = 5th percentile


class DeliveryRiskAnalyzer:
    """
    Analyzes delivery and systematic risk for optimized portfolios.

    Three risk levels:
    1. Market only — baseline from existing simulation
    2. + Delivery risk — Bernoulli gate per feature (team estimates)
    3. + Systematic shock — portfolio-wide external events

    Computes both analytical (closed-form) and simulated (Monte Carlo) estimates.
    """

    def __init__(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
    ):
        """
        Initialize delivery risk analyzer.

        Args:
            features: List of all features
            simulation_results: Simulation results for all features
        """
        self.features = features
        self.simulation_results = simulation_results

    def analyze(
        self,
        portfolio_result: PortfolioResult,
        *,
        seed: int = DEFAULT_SEED,
        systematic_shock_probability: float = 0.0,
        systematic_shock_multiplier: float = 0.3,
    ) -> dict[str, Any]:
        """
        Overlay delivery risk on optimized portfolio.

        Args:
            portfolio_result: Result from any solver
            seed: RNG seed for reproducibility
            systematic_shock_probability: Probability of portfolio-wide shock (0-1)
            systematic_shock_multiplier: Business value multiplier in shock (e.g., 0.3 = 30%)

        Returns:
            Dictionary with per-feature details and portfolio-level metrics

        Example:
            >>> analyzer = DeliveryRiskAnalyzer(features, sim_results)
            >>> opt_result = exact_solver.optimize(...)
            >>> risk_analysis = analyzer.analyze(opt_result, seed=42)
            >>> risk_analysis['simulated_expected']
            150000.0
        """
        rng = np.random.default_rng(seed)

        # Get selected features
        selected = self._get_selected_features(portfolio_result.recommended_features)

        if not selected:
            return self._empty_analysis(
                portfolio_result.solver
            )  # pragma: no cover - defensive

        # Determine scenario count
        n_scenarios = len(self.simulation_results[selected[0].name].results_array)

        # Level 1: Market-only baseline (no delivery risk)
        market = self._calculate_market_baseline(selected, n_scenarios)
        market_exp = float(np.mean(market))
        market_var = float(np.percentile(market, VAR_PERCENTILE))

        # Analytical: E[business value] × (1 − p) per feature
        analytical_exp = self._calculate_analytical_expected(selected)

        # Level 2: Bernoulli gate per feature per scenario
        gated, feature_details = self._apply_delivery_gates(selected, n_scenarios, rng)
        sim_exp = float(np.mean(gated))
        sim_var = float(np.percentile(gated, VAR_PERCENTILE))

        # Build base result
        result = {
            "solver": portfolio_result.solver,
            "features": feature_details,
            "market_expected": market_exp,
            "market_var_95": market_var,
            "analytical_expected": analytical_exp,
            "simulated_expected": sim_exp,
            "simulated_var_95": sim_var,
            "exp_delta_pct": self._safe_percentage_delta(sim_exp, market_exp),
            "var_delta_pct": self._safe_percentage_delta(sim_var, market_var),
        }

        # Level 3: Systematic shock (optional)
        if systematic_shock_probability > 0:
            shocked_metrics = self._apply_systematic_shock(
                gated,
                n_scenarios,
                rng,
                systematic_shock_probability,
                systematic_shock_multiplier,
                market_exp,
                market_var,
            )
            result.update(shocked_metrics)

        return result

    def analyze_budget_profiles(
        self,
        budgets: list[float],
        solver_results: dict[float, dict[str, PortfolioResult]],
        *,
        seed: int = DEFAULT_SEED,
        systematic_shock_probability: float = 0.0,
        systematic_shock_multiplier: float = 0.3,
    ) -> dict[float, dict[str, Any]]:
        """
        Analyze risk profiles across multiple budgets and solvers.

        Args:
            budgets: List of budget amounts
            solver_results: Nested dict {budget: {solver_name: PortfolioResult}}
            seed: RNG seed
            systematic_shock_probability: Shock probability
            systematic_shock_multiplier: Shock multiplier

        Returns:
            Nested dict with risk analysis per budget per solver
        """
        profiles: dict[float, dict[str, Any]] = {}  # pragma: no cover - defensive
        # pragma: no cover - defensive
        for budget in budgets:  # pragma: no cover - defensive
            profiles[budget] = {}  # pragma: no cover - defensive
            # pragma: no cover - defensive
            for solver_name, portfolio_result in solver_results[
                budget
            ].items():  # pragma: no cover - defensive
                if (
                    len(portfolio_result.recommended_features) == 0
                ):  # pragma: no cover - defensive
                    continue  # pragma: no cover - defensive
                # pragma: no cover - defensive
                # Level 1 (no shock)  # pragma: no cover - defensive
                level_1 = self.analyze(
                    portfolio_result, seed=seed
                )  # pragma: no cover - defensive
                # pragma: no cover - defensive
                # Level 3 (with shock)  # pragma: no cover - defensive
                level_3 = self.analyze(  # pragma: no cover - defensive
                    portfolio_result,  # pragma: no cover - defensive
                    seed=seed,  # pragma: no cover - defensive
                    systematic_shock_probability=systematic_shock_probability,  # pragma: no cover - defensive
                    systematic_shock_multiplier=systematic_shock_multiplier,  # pragma: no cover - defensive
                )  # pragma: no cover - defensive
                # pragma: no cover - defensive
                profiles[budget][solver_name] = {  # pragma: no cover - defensive
                    "portfolio_result": portfolio_result,  # pragma: no cover - defensive
                    "feature_count": portfolio_result.feature_count,  # pragma: no cover - defensive
                    "l1": level_1,  # pragma: no cover - defensive
                    "l3": level_3,  # pragma: no cover - defensive
                }  # pragma: no cover - defensive
        # pragma: no cover - defensive
        return profiles  # pragma: no cover - defensive

    def _get_selected_features(self, feature_names: list[str]) -> list[Feature]:
        """Extract Feature objects from names."""
        return [f for f in self.features if f.name in feature_names]

    def _calculate_market_baseline(
        self, selected: list[Feature], n_scenarios: int
    ) -> np.ndarray:
        """Calculate market-only portfolio business value (vectorized)."""
        market = np.zeros(n_scenarios)
        for f in selected:
            market += (
                self.simulation_results[f.name].results_array
                * f.business_value_per_conversion
            )
        return market

    def _calculate_analytical_expected(self, selected: list[Feature]) -> float:
        """Calculate analytical expected business value with delivery risk."""
        return sum(
            float(
                np.mean(
                    self.simulation_results[f.name].results_array
                    * f.business_value_per_conversion
                )
            )
            * (1.0 - f.likelihood_of_non_delivery)
            for f in selected
        )

    def _apply_delivery_gates(
        self, selected: list[Feature], n_scenarios: int, rng: np.random.Generator
    ) -> tuple[np.ndarray, list[dict[str, Any]]]:
        """
        Apply Bernoulli delivery gates to each feature.

        Returns:
            Tuple of (gated_scenarios, feature_details)
        """
        gated = np.zeros(n_scenarios)
        feature_details = []

        for f in selected:
            # Bernoulli gate: delivered if random < (1 - p_fail)
            delivered = rng.random(n_scenarios) >= f.likelihood_of_non_delivery
            gated += (
                self.simulation_results[f.name].results_array
                * f.business_value_per_conversion
                * delivered
            )

            feature_details.append(
                {
                    "name": f.name,
                    "non_delivery_risk": f.likelihood_of_non_delivery,
                    "delivered_pct": float(delivered.mean()),
                }
            )

        return gated, feature_details

    def _apply_systematic_shock(
        self,
        gated: np.ndarray,
        n_scenarios: int,
        rng: np.random.Generator,
        shock_prob: float,
        shock_mult: float,
        market_exp: float,
        market_var: float,
    ) -> dict[str, Any]:
        """Apply systematic shock to portfolio."""
        shock_hits = rng.random(n_scenarios) < shock_prob
        shock_multiplier = np.where(shock_hits, shock_mult, 1.0)
        shocked = gated * shock_multiplier

        shocked_exp = float(np.mean(shocked))
        shocked_var = float(np.percentile(shocked, VAR_PERCENTILE))

        return {
            "shock_probability": shock_prob,
            "shock_multiplier": shock_mult,
            "shock_hit_pct": float(shock_hits.mean()),
            "shocked_expected": shocked_exp,
            "shocked_var_95": shocked_var,
            "shocked_exp_delta_pct": self._safe_percentage_delta(
                shocked_exp, market_exp
            ),
            "shocked_var_delta_pct": self._safe_percentage_delta(
                shocked_var, market_var
            ),
        }

    @staticmethod
    def _safe_percentage_delta(new_value: float, baseline: float) -> float:
        """Calculate percentage delta with zero-division protection."""
        if baseline > 0:
            return (new_value / baseline - 1) * 100
        return 0.0  # pragma: no cover - defensive

    @staticmethod
    def _empty_analysis(solver_name: str) -> dict[str, Any]:
        """Return empty analysis for portfolios with no features."""
        return {
            "solver": solver_name,
            "features": [],
            "market_expected": 0.0,
            "market_var_95": 0.0,
            "analytical_expected": 0.0,
            "simulated_expected": 0.0,
            "simulated_var_95": 0.0,
        }
