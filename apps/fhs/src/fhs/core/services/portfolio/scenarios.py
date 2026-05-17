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
Scenario Analysis Service for Feature Portfolio Analysis

Provides stress testing and scenario analysis for feature portfolios.
Answers: "What happens in the worst case?"
"""

import logging
from typing import Any

import numpy as np

from ...model import Feature, SimulationResult
from ..risk import RiskCalculator
from .utils import aggregate_portfolio_scenarios_from_results

logger = logging.getLogger("fhs.scenario_analysis")


class ScenarioAnalysisService:
    """Service for portfolio stress testing and scenario analysis.

    Simulates various adverse scenarios to understand portfolio resilience:
    - Market crash scenarios (all features underperform)
    - Feature failure scenarios (key feature fails)
    - Custom stress scenarios with specific multipliers
    """

    def __init__(self, calculator: RiskCalculator):
        """
        Initialize Stress Test Service.

        Args:
            calculator: Risk calculator for VaR/CVaR computations
        """
        self.calculator = calculator

    def stress_test(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        scenario: str = "market_crash",
        custom_multipliers: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        Run stress test on the feature portfolio.

        Answers: "What happens in the worst case?"

        Args:
            features: List of features in the portfolio
            simulation_results: Dictionary mapping feature names to simulation results
            scenario: Predefined scenario name or "custom"
                - "market_crash": All features at 50%
                - "feature_failure": Worst feature at 20%
                - "best_case": All features at 150%
                - "custom": Use custom_multipliers
            custom_multipliers: Feature name -> multiplier (for "custom" scenario)

        Returns:
            Dictionary with stress test results including:
                - scenario: Scenario name
                - multipliers: Applied multipliers per feature
                - baseline: Baseline expected business value and VaR
                - stressed: Stressed expected business value and VaR
                - impact: Change in business value and VaR (absolute and percentage)
        """
        feature_names = [f.name for f in features]

        # Build scenario multipliers
        if scenario == "custom":
            if not custom_multipliers:
                raise ValueError("custom_multipliers required for 'custom' scenario")
            multipliers = custom_multipliers
            scenario_name = "Custom"
        elif scenario == "market_crash":
            multipliers = dict.fromkeys(feature_names, 0.5)
            scenario_name = "Market Crash (50%)"
        elif scenario == "feature_failure":
            # Find the feature with highest expected business value
            top_feature = max(
                features,
                key=lambda f: (
                    simulation_results[f.name].expected_value
                    * f.business_value_per_conversion
                ),
            )
            multipliers = {top_feature.name: 0.2}
            scenario_name = f"Feature Failure: {top_feature.name} (20%)"
        elif scenario == "best_case":
            multipliers = dict.fromkeys(feature_names, 1.5)
            scenario_name = "Best Case (150%)"
        else:
            raise ValueError(
                f"Unknown scenario: {scenario}. "
                f"Use 'market_crash', 'feature_failure', 'best_case', or 'custom'"
            )

        # Calculate baseline
        baseline_scenarios = self._sum_portfolio_scenarios(simulation_results)
        baseline_expected = float(np.mean(baseline_scenarios))
        baseline_var = self.calculator.calculate_var(baseline_scenarios, 0.95)

        # Apply stress multipliers
        stressed_results: dict[str, SimulationResult] = {}
        for name, result in simulation_results.items():
            mult = multipliers.get(name, 1.0)
            if not np.isclose(mult, 1.0):
                stressed_arr = result.results_array * mult
                stressed_results[name] = SimulationResult(
                    feature_name=name,
                    results=stressed_arr,
                    scenarios=len(stressed_arr),
                    expected_value=result.expected_value * mult,
                    business_value_per_conversion=result.business_value_per_conversion,
                    development_cost=result.development_cost,
                )
            else:
                stressed_results[name] = result

        stressed_scenarios = self._sum_portfolio_scenarios(stressed_results)
        stressed_expected = float(np.mean(stressed_scenarios))
        stressed_var = self.calculator.calculate_var(stressed_scenarios, 0.95)

        return {
            "scenario": scenario_name,
            "multipliers": multipliers,
            "baseline": {
                "expected_business_value": baseline_expected,
                "var_95_business_value": baseline_var,
            },
            "stressed": {
                "expected_business_value": stressed_expected,
                "var_95_business_value": stressed_var,
            },
            "impact": {
                "expected_change": stressed_expected - baseline_expected,
                "expected_change_pct": (
                    (stressed_expected / baseline_expected - 1) * 100
                    if baseline_expected != 0
                    else 0
                ),
                "var_change": stressed_var - baseline_var,
                "var_change_pct": (
                    (stressed_var / baseline_var - 1) * 100 if baseline_var != 0 else 0
                ),
            },
        }

    def stress_test_multiple(
        self,
        simulation_results: dict[str, SimulationResult],
        scenarios: list[dict[str, Any]],
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        Run multiple stress test scenarios on a portfolio.

        Consolidates the batch stress testing logic from PortfolioRiskAnalyzer.

        Args:
            simulation_results: Dictionary mapping feature names to SimulationResults
            scenarios: List of stress scenarios, each a dict with:
                - "name": Scenario name (e.g., "Market Crash")
                - "multipliers": Dict of feature_name -> multiplier
            weights: Optional weights for each feature (default: equal weights)

        Returns:
            Dictionary with:
                - baseline_metrics: Baseline VaR, CVaR, expected_value
                - stress_results: List of scenario results with metrics and impact
        """
        if not simulation_results:
            raise ValueError(
                "No simulation results provided"
            )  # pragma: no cover - defensive

        feature_names = list(simulation_results.keys())

        # Default to equal weights
        if weights is None:
            weights = {
                name: 1.0 / len(feature_names) for name in feature_names
            }  # pragma: no cover - defensive

        # Calculate baseline portfolio
        baseline_scenarios = self._sum_portfolio_scenarios(simulation_results, weights)
        baseline_metrics = {
            "var_95": self.calculator.calculate_var(baseline_scenarios, 0.95),
            "cvar_95": self.calculator.calculate_cvar(baseline_scenarios, 0.95),
            "expected_value": float(np.mean(baseline_scenarios)),
        }

        # Run stress scenarios
        stress_results = []
        for scenario in scenarios:
            multipliers = scenario.get("multipliers", {})
            scenario_name = scenario.get("name", "Unnamed Scenario")

            # Apply multipliers to results
            stressed_arrays = {}
            for name in feature_names:
                multiplier = multipliers.get(name, 1.0)
                stressed_arrays[name] = (
                    simulation_results[name].results_array * multiplier
                )

            # Calculate stressed portfolio
            stressed_scenarios = self._calculate_weighted_portfolio(
                stressed_arrays, weights
            )

            stressed_metrics = {
                "var_95": self.calculator.calculate_var(stressed_scenarios, 0.95),
                "cvar_95": self.calculator.calculate_cvar(stressed_scenarios, 0.95),
                "expected_value": float(np.mean(stressed_scenarios)),
            }

            # Calculate impact
            impact = {
                "var_95_change": stressed_metrics["var_95"]
                - baseline_metrics["var_95"],
                "var_95_change_pct": (
                    (stressed_metrics["var_95"] / baseline_metrics["var_95"] - 1) * 100
                    if baseline_metrics["var_95"] != 0
                    else 0
                ),
                "expected_value_change": (
                    stressed_metrics["expected_value"]
                    - baseline_metrics["expected_value"]
                ),
            }

            stress_results.append(
                {
                    "scenario": scenario_name,
                    "multipliers": multipliers,
                    "stressed_metrics": stressed_metrics,
                    "impact": impact,
                }
            )

        return {
            "baseline_metrics": baseline_metrics,
            "stress_results": stress_results,
        }

    def _sum_portfolio_scenarios(
        self,
        results: dict[str, SimulationResult],
        weights: dict[str, float] | None = None,
    ) -> np.ndarray:
        """Sum scenario arrays across all features to get portfolio totals.

        Args:
            results: Dictionary mapping feature names to SimulationResults
            weights: Optional weights for each feature (default: simple sum)

        Returns:
            Array of portfolio scenarios
        """
        if weights is None:
            # Simple sum (backward compatible behavior)
            return aggregate_portfolio_scenarios_from_results(results)
        else:
            # Weighted sum
            results_arrays = {name: res.results_array for name, res in results.items()}
            return self._calculate_weighted_portfolio(results_arrays, weights)

    @staticmethod
    def _calculate_weighted_portfolio(
        results_arrays: dict[str, np.ndarray],
        weights: dict[str, float],
    ) -> np.ndarray:
        """
        Calculate weighted portfolio scenarios.

        Args:
            results_arrays: Dictionary mapping feature names to result arrays
            weights: Dictionary mapping feature names to weights

        Returns:
            Array of weighted portfolio scenarios
        """
        total_scenarios = None
        for name, arr in results_arrays.items():
            weight = weights.get(name, 0.0)
            if total_scenarios is None:
                total_scenarios = arr * weight
            else:
                total_scenarios += arr * weight
        return total_scenarios if total_scenarios is not None else np.array([])
