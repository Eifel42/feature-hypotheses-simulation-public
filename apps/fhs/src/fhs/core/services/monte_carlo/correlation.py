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

"""Correlation Strategy implementations (§10.6 DDD Refactoring).

Provides pluggable algorithms for correlated multi-feature simulation.
"""

from __future__ import annotations

import logging
import warnings
from typing import Protocol, runtime_checkable

import numpy as np
from statsmodels.distributions.copula.api import (
    ClaytonCopula,
    FrankCopula,
    GaussianCopula,
    GumbelCopula,
)

from fhs.core.model import DEFAULT_CONFIG

from ...model import Feature
from ...model.exceptions import CorrelationMatrixError, SimulationError, ValidationError

# noinspection PyProtectedMember
from ..simulation._validation import ensure_psd, validate_scenarios
from ._helpers import apply_acceptance_model, apply_bounds
from .distributions import DistributionStrategy

logger = logging.getLogger("fhs.monte_carlo")


@runtime_checkable
class CorrelationStrategy(Protocol):
    """Contract for multi-feature correlated simulation."""

    @property
    def name(self) -> str:
        """Return strategy name."""
        ...

    def simulate(
        self,
        features: list[Feature],
        correlation_matrix: np.ndarray,
        distribution: DistributionStrategy,
        rng: np.random.Generator,
        n: int,
    ) -> dict[str, np.ndarray]:
        """Return {feature_name: samples} with preserved correlations."""
        ...


class CholeskyCorrelator:
    """Cholesky decomposition-based correlation (Gaussian copula implicit).

    Uses Cholesky decomposition to generate correlated standard normal
    samples, then transforms them to the target distribution.
    """

    def __init__(self, repair: bool = False, repair_threshold: float = 1e-8):
        """
        Initialize Cholesky correlator.

        Args:
            repair: If True, repair non-PSD correlation matrices
            repair_threshold: Eigenvalue threshold for PSD check
        """
        self._repair = repair
        self._repair_threshold = repair_threshold

    @property
    def name(self) -> str:
        return "cholesky"  # pragma: no cover - defensive

    def simulate(
        self,
        features: list[Feature],
        correlation_matrix: np.ndarray,
        distribution: DistributionStrategy,
        rng: np.random.Generator,
        n: int,
    ) -> dict[str, np.ndarray]:
        """
        Simulate correlated features via Cholesky decomposition.

        Args:
            features: List of Feature objects to simulate
            correlation_matrix: n×n correlation matrix (must be PSD)
            distribution: DistributionStrategy for marginal transforms
            rng: Random number generator
            n: Number of scenarios

        Returns:
            Dictionary mapping feature names to arrays of simulated conversions

        Raises:
            ValueError: If correlation matrix is invalid
            SimulationError: If simulation produces non-finite values
        """
        num_features = len(features)

        # Validate correlation matrix
        if correlation_matrix.shape != (num_features, num_features):
            raise CorrelationMatrixError(
                f"Correlation matrix shape {correlation_matrix.shape} "
                f"does not match {num_features} features",
                issue="shape_mismatch",
            )

        if not np.allclose(correlation_matrix, correlation_matrix.T):
            raise CorrelationMatrixError(
                "Correlation matrix must be symmetric",
                issue="not_symmetric",
            )

        diag = np.diag(correlation_matrix)
        if not np.allclose(diag, 1.0):
            raise CorrelationMatrixError(
                "Correlation matrix diagonal must be 1.0",
                issue="invalid_diag",
            )

        if np.any(correlation_matrix < -1) or np.any(correlation_matrix > 1):
            raise CorrelationMatrixError(
                "Correlation values must be between -1 and 1",
                issue="invalid_values",
            )

        validate_scenarios(n)

        logger.info(
            f"Cholesky: Generating {n} correlated scenarios for {num_features} features"
        )

        # Ensure PSD and optionally repair
        corr = ensure_psd(
            correlation_matrix,
            repair=self._repair,
            threshold=self._repair_threshold,
        )
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        corr = np.clip(corr, -1.0, 1.0)
        np.fill_diagonal(corr, 1.0)
        if not np.allclose(corr, correlation_matrix) and self._repair:
            logger.warning(  # pragma: no cover - defensive
                "Correlation matrix was not PSD and has been repaired via cov_nearest; "
                "consider supplying a PSD matrix to avoid distortion."
            )

        # Generate correlated standard normal samples
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            correlated_samples = rng.multivariate_normal(
                mean=np.zeros(num_features),
                cov=corr,
                size=n,
                check_valid="ignore",
            ).T

        if np.any(~np.isfinite(correlated_samples)):
            raise SimulationError(
                "Correlated simulation produced non-finite values. "
                "Check correlation matrix and feature parameters."
            )

        # Transform to target distribution and scale to conversions
        results: dict[str, np.ndarray] = {}
        for i, feature in enumerate(features):
            z = correlated_samples[i]

            if np.isclose(feature.uncertainty, 0.0):
                samples = np.asarray(
                    np.full(
                        n,
                        feature.conversion_rate * feature.expected_users,
                    ),
                    dtype=float,
                )
            else:
                rates = distribution.transform_correlated(
                    z, feature.conversion_rate, feature.uncertainty
                )
                rates = apply_bounds(rates, 0.0, 1.0)
                samples = np.asarray(rates * feature.expected_users, dtype=float)

            results[feature.name] = samples

            logger.debug(
                f"Feature '{feature.name}': mean={float(np.mean(samples)):.2f}, "
                f"std={float(np.std(samples)):.2f}"
            )

        return results


class CopulaCorrelator:
    """Copula-based correlation with flexible marginals.

    Supports Gaussian, Frank, Clayton, and Gumbel copulas for modeling
    non-linear dependencies between features.
    """

    def __init__(
        self,
        copula_type: str = "gaussian",
        theta: float | None = None,
    ):
        """
        Initialize copula correlator.

        Args:
            copula_type: One of "gaussian", "frank", "clayton", "gumbel"
            theta: Copula parameter for Archimedean copulas (ignored for Gaussian)
        """
        self._copula_type = copula_type.lower()
        self._theta = theta

    @property
    def name(self) -> str:
        return f"copula-{self._copula_type}"  # pragma: no cover - defensive

    def _gaussian_copula(
        self,
        correlation_matrix: np.ndarray,
        num_features: int,
    ) -> GaussianCopula:
        if correlation_matrix is None:
            raise CorrelationMatrixError(  # pragma: no cover - defensive
                "Gaussian copula requires correlation_matrix",
                issue="missing",
            )
        if correlation_matrix.shape != (num_features, num_features):
            raise CorrelationMatrixError(  # pragma: no cover - defensive
                f"Correlation matrix shape {correlation_matrix.shape} "
                f"does not match {num_features} features",
                issue="shape_mismatch",
            )
        if self._theta is not None:
            logger.warning(
                "theta is ignored for Gaussian copula."
            )  # pragma: no cover - defensive
        corr = ensure_psd(correlation_matrix, repair=True, threshold=1e-8)
        return GaussianCopula(corr)

    def _validate_theta(self) -> None:
        if (
            self._copula_type == "clayton"
            and self._theta is not None
            and self._theta <= 0
        ):
            raise ValidationError(  # pragma: no cover - defensive
                "Clayton copula requires theta > 0. "
                f"Got theta={self._theta}. "
                "Typical range: (0, 20]. Larger values mean stronger tail dependence.",
                field="theta",
                value=self._theta,
            )
        if (
            self._copula_type == "gumbel"
            and self._theta is not None
            and self._theta < 1
        ):
            raise ValidationError(  # pragma: no cover - defensive
                "Gumbel copula requires theta >= 1. "
                f"Got theta={self._theta}. "
                "theta=1 means independence; larger values mean stronger upper tail dependence.",
                field="theta",
                value=self._theta,
            )

    def _build_copula(
        self,
        correlation_matrix: np.ndarray,
        num_features: int,
    ) -> GaussianCopula | FrankCopula | ClaytonCopula | GumbelCopula:
        if self._copula_type == "gaussian":
            return self._gaussian_copula(correlation_matrix, num_features)

        self._validate_theta()
        if self._copula_type == "frank":
            return (
                FrankCopula(theta=self._theta)
                if self._theta is not None
                else FrankCopula()
            )
        if self._copula_type == "clayton":  # pragma: no cover - scipy fallback
            return (  # pragma: no cover - scipy fallback
                ClaytonCopula(theta=self._theta)  # pragma: no cover - scipy fallback
                if self._theta is not None  # pragma: no cover - scipy fallback
                else ClaytonCopula()  # pragma: no cover - scipy fallback
            )  # pragma: no cover - scipy fallback
        if self._copula_type == "gumbel":  # pragma: no cover - scipy fallback
            return (  # pragma: no cover - scipy fallback
                GumbelCopula(theta=self._theta)  # pragma: no cover - scipy fallback
                if self._theta is not None  # pragma: no cover - scipy fallback
                else GumbelCopula()  # pragma: no cover - scipy fallback
            )  # pragma: no cover - scipy fallback
        raise ValidationError(  # pragma: no cover - scipy fallback
            f"Unsupported copula_type '{self._copula_type}'",
            field="copula_type",
            value=self._copula_type,
        )

    def simulate(
        self,
        features: list[Feature],
        correlation_matrix: np.ndarray,
        distribution: DistributionStrategy,
        rng: np.random.Generator,
        n: int,
    ) -> dict[str, np.ndarray]:
        """
        Simulate correlated features via copula.

        Args:
            features: List of Feature objects
            correlation_matrix: n×n correlation matrix (required for Gaussian copula)
            distribution: DistributionStrategy for marginal transforms
            rng: Random number generator
            n: Number of scenarios

        Returns:
            Dictionary mapping feature names to arrays of simulated conversions

        Raises:
            ValueError: If parameters are invalid
        """
        num_features = len(features)
        if num_features == 0:
            return {}  # pragma: no cover - defensive

        if n < DEFAULT_CONFIG.MIN_SCENARIOS:
            raise ValidationError(  # pragma: no cover - defensive
                f"Minimum {DEFAULT_CONFIG.MIN_SCENARIOS} scenarios required. Got {n}.",
                field="scenarios",
                value=n,
            )

        copula = self._build_copula(correlation_matrix, num_features)

        # Sample from copula (returns uniform [0,1] marginals)
        # Suppress scipy's internal RuntimeWarnings (divide by zero, overflow)
        # as we sanitize the output immediately after
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, module="scipy")
            u = copula.rvs(n, random_state=rng)
        u = np.clip(u, 1e-12, 1 - 1e-12)

        # Transform each marginal using distribution's inverse CDF
        results: dict[str, np.ndarray] = {}
        for j, feature in enumerate(features):
            u_col = u[:, j]
            rates = distribution.inverse_cdf(
                u_col, feature.conversion_rate, feature.uncertainty
            )
            rates = apply_bounds(rates, 0.0, 1.0)
            conversions = apply_acceptance_model(rates, feature, rng)
            results[feature.name] = conversions

        return results


class CorrelationFactory:
    """Factory for creating correlation strategies."""

    @classmethod
    def create(cls, method: str, **kwargs) -> CorrelationStrategy:
        """
        Create a correlation strategy by method name.

        Args:
            method: "cholesky" or "copula"
            **kwargs: Strategy-specific parameters
                For cholesky: repair=bool, repair_threshold=float
                For copula: copula_type=str, theta=float

        Returns:
            CorrelationStrategy instance

        Raises:
            ValueError: If method is unknown
        """
        if method == "cholesky":
            return CholeskyCorrelator(
                repair=kwargs.get("repair", False),
                repair_threshold=kwargs.get("repair_threshold", 1e-8),
            )
        elif method == "copula":
            return CopulaCorrelator(
                copula_type=kwargs.get("copula_type", "gaussian"),
                theta=kwargs.get("theta"),
            )
        else:
            raise ValidationError(  # pragma: no cover - defensive
                f"Unknown correlation method '{method}'. Supported: ['cholesky', 'copula']",
                field="method",
                value=method,
            )
