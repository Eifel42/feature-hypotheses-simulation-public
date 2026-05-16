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
Portfolio Utility Functions

Centralized portfolio calculation functions to eliminate code duplication
across portfolio_advisor, portfolio_facade, scenario_analysis, and optimization_service.
"""

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.exceptions import InsufficientDataError
from fhs.core.typing_utils import to_float_array


def aggregate_portfolio_scenarios(
    simulation_results: dict[str, SimulationResult],
    features: list[Feature],
) -> np.ndarray:
    """
    Aggregate scenario arrays across features to get portfolio totals.

    This is the canonical implementation of portfolio scenario aggregation,
    replacing 4 duplicated implementations across the codebase.

    Args:
        simulation_results: Dict mapping feature name to SimulationResult
        features: List of Feature objects to include in portfolio

    Returns:
        NumPy array of portfolio total scenarios (one value per simulation)

    Example:
        >>> results = {"A": sim_result_a, "B": sim_result_b}
        >>> feat_list = [feature_a, feature_b]
        >>> portfolio = aggregate_portfolio_scenarios(results, feat_list)
        >>> portfolio.shape
        (10000,)  # One value per simulation
    """
    arrays = [
        simulation_results[f.name].results_array * f.business_value_per_conversion
        for f in features
        if f.name in simulation_results
    ]

    if not arrays:
        raise InsufficientDataError(
            "No valid features found in simulation results",
            required=1,
            provided=0,
        )

    # Sum across features (axis=0) to get portfolio totals per scenario
    return to_float_array(np.sum(arrays, axis=0))


def aggregate_portfolio_scenarios_from_results(
    results: dict[str, SimulationResult],
) -> np.ndarray:
    """
    Aggregate scenario arrays using business_value from SimulationResult.

    Each SimulationResult carries its own ``business_value_per_conversion``;
    this variant reads it directly instead of requiring a separate features list.

    Args:
        results: Dict mapping feature name to SimulationResult

    Returns:
        NumPy array of portfolio business value scenarios (one value per simulation)
    """
    arrays = [
        result.results_array * result.business_value_per_conversion
        for result in results.values()
    ]

    if not arrays:
        raise InsufficientDataError(
            "No simulation results provided",
            required=1,
            provided=0,
        )

    return to_float_array(np.sum(arrays, axis=0))


def calculate_feature_contribution(
    _feature: Feature,
    simulation_result: SimulationResult,
    portfolio_total: float,
) -> float:
    """
    Calculate a feature's percentage contribution to portfolio.

    Args:
        _feature: Feature object (unused, kept for API consistency)
        simulation_result: Simulation result for the feature
        portfolio_total: Total portfolio expected value

    Returns:
        Contribution as percentage (0.0 to 100.0)

    Example:
        >>> contribution = calculate_feature_contribution(
        ...     feature_a,
        ...     sim_result_a,
        ...     portfolio_total=500000
        ... )
        >>> contribution
        35.2  # Feature contributes 35.2% of portfolio value
    """
    if portfolio_total == 0:
        return 0.0

    feature_value = simulation_result.expected_business_value
    return (feature_value / portfolio_total) * 100


def calculate_portfolio_concentration(
    features: list[Feature],
    simulation_results: dict[str, SimulationResult],
) -> dict[str, float]:
    """
    Calculate concentration (share) of each feature in portfolio.

    Args:
        features: List of features in portfolio
        simulation_results: Simulation results for all features

    Returns:
        Dict mapping feature name to concentration (0.0 to 1.0)

    Example:
        >>> concentration = calculate_portfolio_concentration(features, results)
        >>> concentration
        {"Feature A": 0.45, "Feature B": 0.35, "Feature C": 0.20}
        >>> sum(concentration.values())
        1.0
    """
    total_expected = sum(
        simulation_results[f.name].expected_business_value
        for f in features
        if f.name in simulation_results
    )

    if total_expected == 0:
        # Equal distribution for zero-value portfolio
        n = len(features)
        return {f.name: 1.0 / n for f in features}

    return {
        f.name: simulation_results[f.name].expected_business_value / total_expected
        for f in features
        if f.name in simulation_results
    }
