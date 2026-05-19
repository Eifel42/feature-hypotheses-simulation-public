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
Monte Carlo Engine for Feature Hypotheses Simulation

Thin orchestrator that delegates to DistributionStrategy and
CorrelationStrategy implementations (§10.7 DDD Refactoring).
"""

from __future__ import annotations

import logging

import numpy as np

from fhs.core.model import DEFAULT_CONFIG
from fhs.core.typing_utils import NDArrayFloat, to_float_array

from ...model import Feature

# noinspection PyProtectedMember
from ..simulation._validation import (
    validate_scenarios,
    validate_uncertainty,
)
from ._helpers import apply_acceptance_model, apply_bounds, auto_select_distribution
from .correlation import CorrelationFactory
from .distributions import (
    DistributionFactory,
    DistributionStrategy,
    TruncatedNormalDistribution,
)

logger = logging.getLogger("fhs.monte_carlo")


class MonteCarloEngine:
    """Monte Carlo simulation engine with Strategy-based distributions.

    Generates random scenarios for feature conversion rates using configurable
    probability distributions.  Supports correlated multi-feature simulation
    via Cholesky decomposition and copulas.
    """

    # noinspection PyTypeHintsInspection
    def __init__(self, seed: int | None = None, rng: np.random.Generator | None = None):
        """
        Initialize Monte Carlo Engine

        Args:
            seed: Random seed for reproducible results
            rng: Optional numpy Generator to use instead of creating a new one
        """
        self.seed = seed
        self.rng = rng if rng is not None else np.random.default_rng(seed)

    @staticmethod
    def _resolve_feature_input(
        feature,
        uncertainty: float | None,
    ) -> tuple[float, float, Feature | None]:
        if isinstance(feature, Feature):
            resolved_uncertainty = (
                feature.uncertainty if uncertainty is None else uncertainty
            )
            return feature.conversion_rate, float(resolved_uncertainty), feature
        if uncertainty is None:
            raise ValueError(
                "Uncertainty must be provided when not using Feature object"
            )
        return float(feature), float(uncertainty), None

    @staticmethod
    def _zero_uncertainty_values(
        *,
        base_value: float,
        scenarios: int,
        feature: Feature | None,
    ) -> NDArrayFloat:
        scale = feature.expected_users if feature is not None else 1
        return np.full(scenarios, base_value * scale)

    def _sample_distribution(
        self,
        *,
        distribution: str,
        base_value: float,
        uncertainty: float,
        scenarios: int,
        feature: Feature | None = None,
        lower: float = 0.0,
        upper: float | None = None,
    ) -> NDArrayFloat:
        if distribution == "truncnorm" and feature is not None:
            dist_strategy: DistributionStrategy = (
                TruncatedNormalDistribution()
            )  # pragma: no cover - defensive
            return dist_strategy.sample(  # pragma: no cover - defensive
                self.rng,
                base_value,
                uncertainty,
                scenarios,
                lower=lower,
                upper=1.0 if upper is None else upper,
            )

        dist_strategy = DistributionFactory.create(distribution)
        if distribution == "truncnorm":
            return dist_strategy.sample(  # pragma: no cover - defensive
                self.rng,
                base_value,
                uncertainty,
                scenarios,
                lower=lower,
                upper=np.inf if upper is None else upper,
            )
        return dist_strategy.sample(self.rng, base_value, uncertainty, scenarios)

    def simulate(
        self,
        feature,
        uncertainty: float | None = None,
        scenarios: int = 10000,
        distribution: str = "normal",
    ) -> NDArrayFloat:
        """
        Simulate values with uncertainty.

        Args:
            feature: Feature object or base value
            uncertainty: Relative uncertainty (0.3 = ±30%)
            scenarios: Number of simulations
            distribution: One of DEFAULT_CONFIG.ALLOWED_DISTRIBUTIONS

        Returns:
            Array of simulated values

        Note:
            When *feature* is a ``Feature`` object the simulated conversion
            rates are clipped to [0, 1] before scaling to absolute
            conversions.  At high uncertainty (> ~0.5) the clipping
            truncates the distribution tails, which slightly inflates the
            simulated mean.  Prefer ``distribution='beta'`` or
            ``distribution='truncnorm'`` to avoid that bias for rates.

        Raises:
            ValueError: If parameters are invalid
        """
        validate_scenarios(scenarios)
        base_value, uncertainty_value, feature_context = self._resolve_feature_input(
            feature,
            uncertainty,
        )
        validate_uncertainty(uncertainty_value)

        if base_value < 0:
            raise ValueError(f"Base value cannot be negative. Got {base_value}.")

        # Auto-switch distribution for high uncertainty
        original_dist = distribution
        distribution = auto_select_distribution(
            distribution,
            uncertainty_value,
            base_value,
        )
        if distribution != original_dist:
            logger.info(
                f"Uncertainty {uncertainty_value:.2f} >= 0.3: Auto-switching to '{distribution}' "
                "to avoid clipping bias (equivalent to Beta for unbounded ranges)."
            )

        # Handle zero uncertainty
        if np.isclose(uncertainty_value, 0.0):
            logger.debug("Zero uncertainty: returning constant values")
            return self._zero_uncertainty_values(
                base_value=base_value,
                scenarios=scenarios,
                feature=feature_context,
            )

        allowed = DEFAULT_CONFIG.ALLOWED_DISTRIBUTIONS or []
        if distribution not in allowed:
            raise ValueError(
                f"Distribution must be one of {DEFAULT_CONFIG.ALLOWED_DISTRIBUTIONS}. "
                f"Got {distribution}."
            )

        # Use Strategy pattern for distribution sampling
        samples = self._sample_distribution(
            distribution=distribution,
            base_value=base_value,
            uncertainty=uncertainty_value,
            scenarios=scenarios,
            feature=feature_context,
        )

        # For Feature objects, bound conversion rates and scale to acceptance counts
        if feature_context is not None:
            clipped_count = int(
                np.sum((np.asarray(samples) < 0.0) | (np.asarray(samples) > 1.0))
            )
            if clipped_count / scenarios > 0.01:
                logger.warning(
                    f"Clipping bias: {clipped_count / scenarios:.1%} of samples for "
                    f"'{feature_context.name}' were clipped to [0, 1]. "
                    f"Consider using distribution='lognormal', 'beta' or 'truncnorm' "
                    f"for conversion rates with high uncertainty."
                )
            samples = apply_bounds(samples, 0.0, 1.0)
            return apply_acceptance_model(samples, feature_context, self.rng)

        return to_float_array(samples)

    def simulate_bounded(
        self,
        feature,
        uncertainty: float | None = None,
        lower_bound: float = 0.0,
        upper_bound: float | None = None,
        min_bound: float | None = None,
        max_bound: float | None = None,
        scenarios: int = 10000,
        distribution: str = "normal",
    ) -> NDArrayFloat:
        """
        Simulate values with bounds (e.g., conversion rates between 0 and 1).

        Args:
            feature: Feature object or base value
            uncertainty: Relative uncertainty
            lower_bound: Minimum allowed value
            upper_bound: Maximum allowed value (None for no upper bound)
            min_bound: Deprecated alias for lower_bound
            max_bound: Deprecated alias for upper_bound
            scenarios: Number of scenarios
            distribution: Distribution type

        Returns:
            Array of bounded simulated values
        """
        validate_scenarios(scenarios)

        lb = lower_bound if min_bound is None else min_bound
        ub = upper_bound if max_bound is None else max_bound

        if ub is not None and lb > ub:
            raise ValueError(f"Lower bound ({lb}) must be less than upper bound ({ub})")

        logger.debug(
            f"Bounded simulation: bounds=[{lb}, {ub}], "
            f"uncertainty={uncertainty}, scenarios={scenarios}"
        )
        base_value, base_uncertainty, feature_context = self._resolve_feature_input(
            feature,
            uncertainty,
        )
        if feature_context is not None and np.isclose(base_uncertainty, 0.0):
            logger.debug("Zero uncertainty in bounded simulation")
            return np.full(scenarios, base_value)

        if base_value < 0:
            raise ValueError(
                f"Base value cannot be negative. Got {base_value}."
            )  # pragma: no cover - defensive

        # Use Strategy for bounded-friendly sampling
        if distribution in {"beta", "truncnorm"}:
            raw_values = self._sample_distribution(  # pragma: no cover - defensive
                distribution=distribution,
                base_value=base_value,
                uncertainty=float(base_uncertainty),
                scenarios=scenarios,
                feature=feature_context,
                lower=lb,
                upper=ub,
            )
        else:
            raw_values = self.simulate(
                base_value,
                uncertainty=base_uncertainty,
                scenarios=scenarios,
                distribution=distribution,
            )

        upper = ub if ub is not None else float(np.inf)
        return apply_bounds(raw_values, lb, upper)

    def simulate_correlated(
        self,
        features: list[Feature],
        correlation_matrix: np.ndarray,
        scenarios: int = 10000,
        distribution: str = "normal",
        repair_correlation: bool = False,
        repair_threshold: float = 1e-8,
    ) -> dict[str, NDArrayFloat]:
        """
        Simulate multiple features with correlated outcomes.

        Uses CorrelationStrategy (Cholesky decomposition by default) to generate
        correlated samples, then transforms them using the DistributionStrategy.

        Args:
            features: List of Feature objects to simulate
            correlation_matrix: n×n correlation matrix (must be positive semi-definite)
            scenarios: Number of simulation scenarios
            distribution: Distribution type ("normal" or "lognormal")
            repair_correlation: If True, repair non-PSD matrices
            repair_threshold: Eigenvalue threshold for PSD check

        Returns:
            Dictionary mapping feature names to arrays of simulated absolute conversions
        """
        validate_scenarios(scenarios)

        # Use CorrelationStrategy (Cholesky) via factory
        correlator = CorrelationFactory.create(
            "cholesky",
            repair=repair_correlation,
            repair_threshold=repair_threshold,
        )

        # Use DistributionStrategy for marginal transforms
        dist_strategy = DistributionFactory.create(distribution)

        result = correlator.simulate(
            features, correlation_matrix, dist_strategy, self.rng, scenarios
        )
        # Ensure numeric arrays are float64
        return {k: to_float_array(v) for k, v in result.items()}

    # noinspection PyTypeHintsInspection
    def simulate_copula(
        self,
        features: list[Feature],
        scenarios: int = 10000,
        marginal_distribution: str = "beta",
        copula_type: str = "gaussian",
        theta: float | None = None,
        correlation_matrix: np.ndarray | None = None,
    ) -> dict[str, NDArrayFloat]:
        """
        Simulate correlated features via statsmodels copulas.

        Uses CorrelationStrategy (CopulaCorrelator) with DistributionStrategy
        for marginal transforms.

        Args:
            features: List of Feature objects (conversion rates in [0,1])
            scenarios: Number of simulations
            marginal_distribution: one of {"beta","lognormal","normal","truncnorm","uniform"}
            copula_type: {"gaussian","frank","clayton","gumbel"}
            theta: Cop parameter for Archimedean copulas
            correlation_matrix: required for gaussian copula (n x n, PSD)

        Returns:
            Dictionary mapping feature names to arrays of simulated conversions
        """
        validate_scenarios(scenarios)

        # Use CorrelationStrategy (Copula) via factory
        correlator = CorrelationFactory.create(
            "copula",
            copula_type=copula_type,
            theta=theta,
        )

        # Use DistributionStrategy for marginal transforms
        dist_strategy = DistributionFactory.create(marginal_distribution)

        result = correlator.simulate(
            features,
            (
                correlation_matrix
                if correlation_matrix is not None
                else np.eye(len(features))
            ),
            dist_strategy,
            self.rng,
            scenarios,
        )
        return {k: to_float_array(v) for k, v in result.items()}

    def sample_distribution(
        self,
        dist_type: str,
        params: dict[str, float],
        n: int,
    ) -> np.ndarray:
        """Sample from a single distribution for tutorial/teaching use-cases.

        Args:
            dist_type: Distribution name supported by DistributionFactory
            params: Parameters for the distribution. Requires ``mean`` and
                ``uncertainty``; ``lower``/``upper`` are supported for
                ``truncnorm``.
            n: Number of samples

        Returns:
            Array of sampled values
        """
        if n <= 0:
            raise ValueError(f"Number of samples must be positive. Got {n}.")

        mean = params.get("mean")
        uncertainty = params.get("uncertainty")

        if mean is None or uncertainty is None:
            raise ValueError("Parameters must include 'mean' and 'uncertainty'.")

        if mean < 0:
            raise ValueError(
                f"Mean cannot be negative. Got {mean}."
            )  # pragma: no cover - defensive

        validate_uncertainty(uncertainty)

        strategy = DistributionFactory.create(dist_type)

        if dist_type == "truncnorm":
            lower = params.get("lower", 0.0)
            upper = params.get("upper", 1.0)
            return to_float_array(
                TruncatedNormalDistribution().sample(
                    self.rng,
                    mean,
                    uncertainty,
                    n,
                    lower=lower,
                    upper=upper,
                )
            )

        return to_float_array(strategy.sample(self.rng, mean, uncertainty, n))
