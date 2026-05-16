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
Portfolio Risk Analysis for Feature Hypotheses Simulation

Provides advanced portfolio-level risk management capabilities including:
- Portfolio VaR and CVaR
- Correlation analysis between features
- Diversification benefits
- Risk contribution analysis
- Scenario stress testing
"""

import logging
from typing import Any

import numpy as np
from scipy import stats

from fhs.core.model import DEFAULT_CONFIG

from ...model import (
    CorrelationPair,
    CorrelationResult,
    CorrelationStatistics,
    DiversificationMetrics,
    IndividualRiskMetrics,
    PortfolioMetrics,
    PortfolioRiskResult,
    RiskContributionResult,
    SimulationResult,
)
from ...model.exceptions import ValidationError
from ..risk import RiskCalculator

# Backward-compatible re-exports (§3.2)
from .correlation import (  # noqa: F401
    DEPENDENCY_CORRELATION_DEFAULTS,
    build_correlation_matrix_from_clusters,
)
from .scenarios import ScenarioAnalysisService

logger = logging.getLogger("fhs.portfolio")
NO_SIMULATION_RESULTS_MESSAGE = "No simulation results provided"


def _default_weights(feature_names: list[str]) -> dict[str, float]:
    """Return equal weights for the given feature names (sum to 1.0)."""
    n = len(feature_names)
    return dict.fromkeys(feature_names, 1.0 / n)


class PortfolioRiskAnalyzer:
    """
    Portfolio-level risk analysis for multiple features.

    Extends single-feature analysis with a portfolio perspective:
    - Correlations between features
    - Diversification effects
    - Portfolio VaR/CVaR
    - Risk contribution (how much each feature contributes to total risk)
    """

    def __init__(
        self,
        seed: int | None = None,
        scenario_analysis_service: ScenarioAnalysisService | None = None,
    ):
        """
        Initialize Portfolio Risk Analyzer

        Args:
            seed: Random seed for reproducible results
            scenario_analysis_service: Optional ScenarioAnalysisService for stress testing
                (creates default if None)
        """
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.calculator = RiskCalculator()
        self._scenario_analysis_service = (
            scenario_analysis_service or ScenarioAnalysisService(self.calculator)
        )
        logger.info("Portfolio Risk Analyzer initialized")

    def calculate_portfolio_risk(
        self,
        simulation_results: dict[str, SimulationResult],
        weights: dict[str, float] | None = None,
    ) -> PortfolioRiskResult:
        """
        Calculate portfolio-level risk metrics.

        Args:
            simulation_results: Dictionary mapping feature names to SimulationResults
            weights: Optional weights for each feature (default: equal weights)

        Returns:
            Dictionary with portfolio risk metrics

        Raises:
            ValidationError: If validation fails
        """
        if not simulation_results:
            raise ValidationError(
                NO_SIMULATION_RESULTS_MESSAGE, field="simulation_results"
            )

        feature_names = list(simulation_results.keys())
        n_features = len(feature_names)

        # Default to equal weights
        if weights is None:
            weights = _default_weights(feature_names)

        # Validate weights sum to 1
        weight_sum = sum(weights.values())
        if not np.isclose(weight_sum, 1.0):
            logger.warning(f"Weights sum to {weight_sum}, normalizing to 1.0")
            weights = {name: w / weight_sum for name, w in weights.items()}

        logger.info(f"Calculating portfolio risk for {n_features} features")

        # Extract results arrays
        results_arrays = {}
        for name, result in simulation_results.items():
            results_arrays[name] = result.results_array

        # Calculate weighted portfolio returns
        portfolio_scenarios = self._calculate_portfolio_scenarios(
            results_arrays, weights
        )

        # Calculate portfolio risk metrics
        portfolio_var_95 = self.calculator.calculate_var(portfolio_scenarios, 0.95)
        portfolio_var_99 = self.calculator.calculate_var(portfolio_scenarios, 0.99)
        portfolio_cvar_95 = self.calculator.calculate_cvar(portfolio_scenarios, 0.95)
        portfolio_cvar_99 = self.calculator.calculate_cvar(portfolio_scenarios, 0.99)

        # Calculate individual feature risks for comparison
        individual_risks: dict[str, IndividualRiskMetrics] = {}
        for name, scenarios in results_arrays.items():
            individual_risks[name] = IndividualRiskMetrics(
                var_95=self.calculator.calculate_var(scenarios, 0.95),
                cvar_95=self.calculator.calculate_cvar(scenarios, 0.95),
                mean=float(np.mean(scenarios)),
                std=float(np.std(scenarios)),
            )

        # Calculate diversification benefit
        weighted_var = sum(
            weights[name] * individual_risks[name].var_95 for name in feature_names
        )
        diversification_benefit = weighted_var - portfolio_var_95

        logger.debug(
            f"Portfolio VaR95: {portfolio_var_95:.2f}, "
            f"Diversification benefit: {diversification_benefit:.2f}"
        )

        return PortfolioRiskResult(
            portfolio_metrics=PortfolioMetrics(
                var_95=float(portfolio_var_95),
                var_99=float(portfolio_var_99),
                cvar_95=float(portfolio_cvar_95),
                cvar_99=float(portfolio_cvar_99),
                expected_value=float(np.mean(portfolio_scenarios)),
                std_dev=float(np.std(portfolio_scenarios)),
            ),
            individual_risks=individual_risks,
            diversification=DiversificationMetrics(
                weighted_individual_var=float(weighted_var),
                portfolio_var=float(portfolio_var_95),
                diversification_benefit=float(diversification_benefit),
                diversification_ratio=(
                    float(diversification_benefit / weighted_var)
                    if weighted_var > 0
                    else 0.0
                ),
            ),
            weights=weights,
            n_features=n_features,
        )

    @staticmethod
    def calculate_correlation_matrix(
        simulation_results: dict[str, SimulationResult],
    ) -> CorrelationResult:
        """
        Calculate correlation matrix between features.

        Args:
            simulation_results: Dictionary mapping feature names to SimulationResults

        Returns:
            Dictionary with correlation matrix and statistics
        """
        if not simulation_results:
            raise ValidationError(
                NO_SIMULATION_RESULTS_MESSAGE, field="simulation_results"
            )

        feature_names = list(simulation_results.keys())
        n_features = len(feature_names)

        logger.info(f"Calculating correlation matrix for {n_features} features")

        # Extract results arrays
        results_arrays = [
            simulation_results[name].results_array for name in feature_names
        ]

        # Stack arrays for correlation calculation
        data_matrix = np.column_stack(results_arrays)

        # Calculate correlation matrix
        corr_matrix = np.corrcoef(data_matrix, rowvar=False)

        # Calculate p-value matrix using scipy.stats.pearsonr
        p_value_matrix = np.ones((n_features, n_features))
        for i in range(n_features):
            for j in range(i + 1, n_features):
                _, p_val = stats.pearsonr(results_arrays[i], results_arrays[j])
                p_value_matrix[i, j] = p_val
                p_value_matrix[j, i] = p_val

        # Calculate average correlation (excluding diagonal)
        mask = ~np.eye(n_features, dtype=bool)
        avg_correlation = np.mean(corr_matrix[mask])

        # Find most and least correlated pairs
        upper_triangle = np.triu(corr_matrix, k=1)
        max_corr_idx = np.unravel_index(np.argmax(upper_triangle), upper_triangle.shape)
        min_corr_idx = np.unravel_index(np.argmin(upper_triangle), upper_triangle.shape)

        logger.debug(f"Average correlation: {float(avg_correlation):.3f}")

        return CorrelationResult(
            correlation_matrix=corr_matrix.tolist(),
            p_value_matrix=p_value_matrix.tolist(),
            feature_names=feature_names,
            statistics=CorrelationStatistics(
                average_correlation=float(avg_correlation),
                max_correlation=CorrelationPair(
                    value=float(corr_matrix[max_corr_idx]),
                    features=(
                        feature_names[max_corr_idx[0]],
                        feature_names[max_corr_idx[1]],
                    ),
                ),
                min_correlation=CorrelationPair(
                    value=float(corr_matrix[min_corr_idx]),
                    features=(
                        feature_names[min_corr_idx[0]],
                        feature_names[min_corr_idx[1]],
                    ),
                ),
            ),
        )

    def calculate_risk_contribution(
        self,
        simulation_results: dict[str, SimulationResult],
        weights: dict[str, float] | None = None,
        risk_metric: str = "var_95",
    ) -> RiskContributionResult:
        """
        Calculate each feature's contribution to portfolio risk (Risk Decomposition).

        Uses marginal contribution approach: how much does portfolio risk change
        when we slightly increase a feature's weight?

        Args:
            simulation_results: Dictionary mapping feature names to SimulationResults
            weights: Optional weights for each feature
            risk_metric: Risk metric to use ("var_95", "var_99", "cvar_95", "cvar_99")

        Returns:
            Dictionary with risk contributions
        """
        if not simulation_results:
            raise ValidationError(
                NO_SIMULATION_RESULTS_MESSAGE, field="simulation_results"
            )

        feature_names = list(simulation_results.keys())
        n_features = len(feature_names)

        # Default to equal weights
        if weights is None:
            weights = _default_weights(feature_names)

        logger.info(f"Calculating risk contribution for {n_features} features")

        # Extract results arrays
        results_arrays = {
            name: simulation_results[name].results_array for name in feature_names
        }

        # Calculate baseline portfolio risk
        portfolio_scenarios = self._calculate_portfolio_scenarios(
            results_arrays, weights
        )
        baseline_risk = self._calculate_risk_metric(portfolio_scenarios, risk_metric)

        # Calculate marginal risk contribution for each feature
        epsilon = DEFAULT_CONFIG.MARGINAL_RISK_EPSILON
        risk_contributions = {}
        marginal_risks = {}

        for feature_name in feature_names:
            # Increase feature weight by epsilon
            perturbed_weights = weights.copy()
            perturbed_weights[feature_name] += epsilon

            # Normalize weights
            weight_sum = sum(perturbed_weights.values())
            perturbed_weights = {
                name: w / weight_sum for name, w in perturbed_weights.items()
            }

            # Calculate perturbed portfolio risk
            perturbed_scenarios = self._calculate_portfolio_scenarios(
                results_arrays, perturbed_weights
            )
            perturbed_risk = self._calculate_risk_metric(
                perturbed_scenarios, risk_metric
            )

            # Marginal risk = d(Risk) / d(weight)
            marginal_risk = (perturbed_risk - baseline_risk) / epsilon
            marginal_risks[feature_name] = float(marginal_risk)

            # Risk contribution = weight * marginal_risk
            risk_contributions[feature_name] = float(
                weights[feature_name] * marginal_risk
            )

        # Calculate percentage contributions
        total_contribution = sum(risk_contributions.values())
        percentage_contributions = {
            name: (contrib / total_contribution * 100 if total_contribution != 0 else 0)
            for name, contrib in risk_contributions.items()
        }

        logger.debug(
            f"Risk contributions calculated. Top contributor: "
            f"{
                max(percentage_contributions, key=lambda k: percentage_contributions[k])
            }"
        )

        return RiskContributionResult(
            baseline_risk=float(baseline_risk),
            risk_metric=risk_metric,
            risk_contributions=risk_contributions,
            marginal_risks=marginal_risks,
            percentage_contributions=percentage_contributions,
            weights=weights,
        )

    def stress_test_portfolio(
        self,
        simulation_results: dict[str, SimulationResult],
        weights: dict[str, float] | None = None,
        scenarios: list[dict[str, Any]] | None = None,
    ) -> dict:
        """
        Perform stress testing on portfolio under various scenarios.

        Delegates to ScenarioAnalysisService for consolidated stress testing logic.

        Args:
            simulation_results: Dictionary mapping feature names to SimulationResults
            weights: Optional weights for each feature
            scenarios: List of stress scenarios, each a dict
                of feature_name -> multiplier (e.g.,
                {"Premium": 0.5, "Basic": 1.5} means
                Premium drops 50%, Basic increases 50%)

        Returns:
            Dictionary with stress test results (baseline_metrics, stress_results)
        """
        if not simulation_results:
            raise ValidationError(
                NO_SIMULATION_RESULTS_MESSAGE, field="simulation_results"
            )

        feature_names = list(simulation_results.keys())

        # Default to equal weights
        if weights is None:  # pragma: no cover - partial branch
            weights = _default_weights(feature_names)

        # Default stress scenarios
        if scenarios is None:
            scenarios = [
                {
                    "name": "Market Crash",
                    "multipliers": dict.fromkeys(feature_names, 0.5),
                },
                {"name": "Feature Failure", "multipliers": {feature_names[0]: 0.2}},
                {
                    "name": "Best Case",
                    "multipliers": dict.fromkeys(feature_names, 1.5),
                },
            ]
        else:
            # Convert to expected format if needed
            formatted_scenarios = []
            for i, scenario in enumerate(scenarios):
                if isinstance(scenario, dict) and "multipliers" in scenario:
                    formatted_scenarios.append(scenario)
                else:
                    formatted_scenarios.append(
                        {"name": f"Scenario {i + 1}", "multipliers": scenario}
                    )
            scenarios = formatted_scenarios

        logger.info(f"Running {len(scenarios)} stress test scenarios")

        # Delegate to ScenarioAnalysisService (§5 DRY consolidation)
        result = self._scenario_analysis_service.stress_test_multiple(
            simulation_results, scenarios, weights
        )

        # Adapt output format for backward compatibility
        stress_results = [
            {
                "scenario_name": item["scenario"],
                "multipliers": item["multipliers"],
                "stressed_metrics": item["stressed_metrics"],
                "impact": item["impact"],
            }
            for item in result["stress_results"]
        ]

        return {
            "baseline_metrics": result["baseline_metrics"],
            "stress_scenarios": stress_results,  # Use legacy key name
            "n_scenarios": len(stress_results),
        }

    @staticmethod
    def _calculate_portfolio_scenarios(
        results_arrays: dict[str, np.ndarray], weights: dict[str, float]
    ) -> np.ndarray:
        """
        Calculate weighted portfolio scenarios via matrix multiplication.

        Args:
            results_arrays: Dictionary mapping feature names to results arrays
            weights: Dictionary mapping feature names to weights

        Returns:
            Portfolio scenarios array
        """
        names = list(results_arrays.keys())
        matrix = np.column_stack([results_arrays[n] for n in names]).astype(np.float64)
        w = np.array([weights.get(n, 0.0) for n in names], dtype=np.float64)

        # Guard against upstream non-finite values so risk metrics remain stable.
        matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
        w = np.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)

        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            scenarios = matrix @ w

        return np.nan_to_num(scenarios, nan=0.0, posinf=0.0, neginf=0.0)

    def _calculate_risk_metric(self, scenarios: np.ndarray, risk_metric: str) -> float:
        """
        Calculate specified risk metric.

        Args:
            scenarios: Scenario array
            risk_metric: Name of risk metric

        Returns:
            Risk metric value
        """
        if risk_metric == "var_95":
            return self.calculator.calculate_var(scenarios, 0.95)
        elif risk_metric == "var_99":
            return self.calculator.calculate_var(scenarios, 0.99)
        elif risk_metric == "cvar_95":
            return self.calculator.calculate_cvar(scenarios, 0.95)
        elif risk_metric == "cvar_99":
            return self.calculator.calculate_cvar(scenarios, 0.99)
        else:
            raise ValidationError(
                f"Unknown risk metric: {risk_metric}",
                field="risk_metric",
                value=risk_metric,
            )
