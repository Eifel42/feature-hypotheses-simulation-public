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
Feature Simulator for Feature Hypotheses Simulation

Main simulation class that orchestrates Monte Carlo simulation and risk calculation.
"""

import logging

import numpy as np

from fhs.core.model import DEFAULT_CONFIG

from ...model import Feature, SimulationResult
from ...model.exceptions import SimulationError, ValidationError
from ...model.value_objects.multi_year_result import MultiYearResult, YearResult
from ...model.value_objects.operating_cost import (
    FeatureOperatingCostStats,
    OperatingCostResult,
)
from ..monte_carlo import MonteCarloEngine
from ..risk import RiskCalculator

logger = logging.getLogger("fhs.simulator")
DEFAULT_SIMULATION_SEED = 42


class FeatureSimulator:
    """High-level orchestrator for feature risk simulation.

    Combines :class:`MonteCarloEngine` and :class:`RiskCalculator` to run
    end-to-end simulations, analyse risk, and compare multiple features.
    """

    def __init__(self, feature: Feature | None = None, seed: int | None = None):
        """
        Initialize Feature Simulator

        Args:
            feature: Feature to simulate (optional, can be provided later)
            seed: Random seed for reproducible results
        """
        self.feature = feature
        self.seed = seed
        effective_seed = DEFAULT_SIMULATION_SEED if seed is None else seed
        self.rng = np.random.default_rng(effective_seed)
        self.engine = MonteCarloEngine(seed=seed, rng=self.rng)
        self.calculator = RiskCalculator()

    def simulate_feature(
        self, feature: Feature, scenarios: int = 10000, distribution: str = "normal"
    ) -> SimulationResult:
        """
        Perform Monte Carlo simulation on a feature.

        Args:
            feature: Feature to simulate
            scenarios: Number of simulation scenarios
            distribution: Distribution type ("normal" or "uniform")

        Returns:
            SimulationResult with all metrics

        Raises:
            ValidationError: For invalid parameters
            SimulationError: If simulation fails
        """
        try:
            # Validate scenarios
            if scenarios < DEFAULT_CONFIG.MIN_SCENARIOS:
                raise ValidationError(
                    f"Minimum {DEFAULT_CONFIG.MIN_SCENARIOS} scenarios required "
                    f"for reliable results. Got {scenarios}.",
                    field="scenarios",
                    value=scenarios,
                )

            logger.info(
                f"Starting simulation for feature '{feature.name}' "
                f"with {scenarios} scenarios"
            )

            # Re-initialize engine with seed so repeated calls
            # yield reproducible results
            if self.seed is not None:
                self.rng = np.random.default_rng(self.seed)
                self.engine = MonteCarloEngine(seed=self.seed, rng=self.rng)

            # Simulate absolute conversions for this feature
            user_scenarios = self.engine.simulate(
                feature, scenarios=scenarios, distribution=distribution
            )

            # Calculate expected value
            expected_value = feature.expected_users * feature.conversion_rate

            logger.debug(f"Simulation completed. Expected value: {expected_value:.2f}")

            # Create result object
            return SimulationResult(
                feature_name=feature.name,
                results=user_scenarios,
                scenarios=scenarios,
                expected_value=expected_value,
                business_value_per_conversion=feature.business_value_per_conversion,
                development_cost=feature.development_cost,
                installment_years=feature.installment_years,
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Simulation failed for feature '{feature.name}': {e!s}")
            raise SimulationError(
                f"Simulation failed: {e!s}",
                scenarios=scenarios,
            ) from e

    def simulate_feature_multi_year(
        self,
        feature: Feature,
        years: int = 3,
        scenarios: int = 100_000,
        discount_rate: float = 0.10,
    ) -> MultiYearResult:
        """Run Monte Carlo simulation for each year independently.

        Year 1 base = feature.get_base_annual_business_value().
        Year N base = Year (N-1) expected × (1 + annual_growth_rate).
        Each year is an independent draw — scenarios are not chained.

        Args:
            feature: Feature to simulate
            years: Number of years (default 3)
            scenarios: Scenarios per year (default 100 000)
            discount_rate: For NPV calculation (default 8 %)

        Returns:
            MultiYearResult with per-year distributions
        """
        base = feature.get_base_annual_business_value()
        growth = feature.annual_growth_rate
        uncertainty = feature.uncertainty

        effective_seed = DEFAULT_SIMULATION_SEED if self.seed is None else self.seed
        rng = np.random.default_rng(effective_seed)

        # When uncertainty is high (>= 0.3) use Lognormal instead of Normal.
        # Normal + clip(0) introduces an upward bias because the left tail is
        # truncated and mass is piled at zero.  Lognormal is naturally bounded
        # below, so it avoids this distortion and matches the single-year
        # distribution auto-switch behaviour.
        use_lognormal = uncertainty >= 0.3
        if use_lognormal:
            logger.info(
                "Multi-year simulation for '%s': using Lognormal distribution "
                "(uncertainty=%.2f >= 0.3) to avoid Normal+clip upward bias.",
                feature.name,
                uncertainty,
            )

        year_results: list[YearResult] = []
        for yr in range(1, years + 1):
            year_base = base * (1 + growth) ** (yr - 1)
            if use_lognormal and year_base > 0:
                # Moment-match: σ_log = uncertainty / UNCERTAINTY_SIGMA_RANGE
                sigma_log = uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
                mu_log = np.log(year_base) - 0.5 * sigma_log**2
                draws = rng.lognormal(mean=mu_log, sigma=sigma_log, size=scenarios)
            else:
                std = year_base * uncertainty
                draws = rng.normal(loc=year_base, scale=std, size=scenarios)
                draws = np.clip(draws, 0, None)  # business value cannot be negative

            year_results.append(YearResult.from_scenarios(year=yr, scenarios=draws))

        return MultiYearResult(
            feature_name=feature.name,
            years=year_results,
            discount_rate=discount_rate,
        )

    def analyze_risk(self, result: SimulationResult) -> dict:
        """
        Perform comprehensive risk analysis on simulation results.

        Args:
            result: The simulation result to analyze

        Returns:
            Dictionary with risk metrics including VaR, CVaR and confidence intervals

        Raises:
            SimulationError: If analysis fails
        """
        try:
            logger.debug(f"Analyzing risk for feature '{result.feature_name}'")

            # Get results as numpy array
            data = result.results_array

            if len(data) == 0:
                logger.warning(f"No results to analyze for '{result.feature_name}'")
                raise SimulationError(
                    f"No simulation results available for '{result.feature_name}'"
                )

            # Calculate risk metrics
            var_95 = self.calculator.calculate_var(data, 0.95)
            var_99 = self.calculator.calculate_var(data, 0.99)
            cvar_95 = self.calculator.calculate_cvar(data, 0.95)
            cvar_99 = self.calculator.calculate_cvar(data, 0.99)

            # Calculate confidence interval with isolated RNG for reproducibility
            rng = np.random.default_rng(self.seed) if self.seed is not None else None
            confidence_interval = self.calculator.bootstrap_confidence_interval(
                data, rng=rng
            )

            logger.debug(f"Risk metrics: VaR95={var_95:.2f}, CVaR95={cvar_95:.2f}")

            # Return comprehensive risk analysis
            return {
                # Standard keys required by tests
                "var_95": var_95,
                "var_99": var_99,
                "cvar_95": cvar_95,
                "cvar_99": cvar_99,
                "confidence_interval": confidence_interval,
                # Alternative keys (alias)
                "cvar": cvar_95,
                "mean": float(np.mean(data)),
                "median": float(np.median(data)),
                "std": float(np.std(data)),
            }

        except SimulationError:
            raise
        except Exception as e:
            logger.error(f"Risk analysis failed: {e!s}")
            raise SimulationError(f"Risk analysis failed: {e!s}") from e

    @staticmethod
    def classify_risk(result: SimulationResult) -> tuple[str, str]:
        """Classify risk level from relative spread (std / expected value)."""
        return result.risk_verdict()

    def compare_features(
        self,
        features: list[Feature],
        scenarios: int = 10000,
        distribution: str = "normal",
    ) -> dict:
        """
        Compare multiple features with risk analysis

        Args:
            features: List of features to compare
            scenarios: Number of simulation scenarios
            distribution: Distribution type

        Returns:
            Dictionary mapping feature names to their
            simulation results and risk analysis
        """
        if not features:
            # Tests expect an empty dict, not an empty list
            return {}

        # Tests expect a dictionary format where keys are feature names
        result_dict = {}

        # Simulate and analyze each feature
        for feature in features:
            # Simulate
            simulation = self.simulate_feature(feature, scenarios, distribution)

            # Analyze risk
            risk = self.analyze_risk(simulation)

            # Store results according to test expectations
            result_dict[feature.name] = {
                "simulation_result": simulation,
                "risk_analysis": risk,
            }

        return result_dict

    def simulate_operating_costs(
        self,
        features: list[Feature],
        cost_inflation_max: float = 0.25,
        scenarios: int = 10_000,
    ) -> OperatingCostResult:
        """Simulate portfolio operating costs with a shared cost inflation factor.

        One inflation factor is drawn from Uniform(0, cost_inflation_max) per
        scenario and applied to every feature's ``annual_operating_cost``.
        This reflects a shared operational environment (local or cloud):
        if infrastructure prices rise, they rise for all features equally.

        Args:
            features: Features to simulate.
            cost_inflation_max: Maximum inflation rate (0.0–1.0). Default 0.25 = 25%.
            scenarios: Number of Monte Carlo scenarios.

        Returns:
            OperatingCostResult with per-feature statistics and portfolio totals.
        """
        # One shared draw per scenario — same environment for all features.
        inflation_scenarios = self.rng.uniform(0.0, cost_inflation_max, size=scenarios)

        per_feature: dict[str, FeatureOperatingCostStats] = {}
        for feature in features:
            base = feature.annual_operating_cost
            cost_scenarios = base * (1.0 + inflation_scenarios)
            per_feature[feature.name] = FeatureOperatingCostStats(
                feature_name=feature.name,
                base_annual_cost=base,
                expected_cost=float(np.mean(cost_scenarios)),
                worst_case_cost=base * (1.0 + cost_inflation_max),
                scenarios=cost_scenarios,
            )

        return OperatingCostResult(
            inflation_max=cost_inflation_max,
            inflation_scenarios=inflation_scenarios,
            per_feature=per_feature,
        )
