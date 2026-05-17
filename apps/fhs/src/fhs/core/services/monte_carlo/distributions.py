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

"""Distribution Strategy implementations (§10.3-10.5 DDD Refactoring).

Each distribution implements the DistributionStrategy Protocol.
"""

from __future__ import annotations

from typing import ClassVar, Protocol, cast, runtime_checkable

import numpy as np
from scipy import stats

from fhs.core.model import DEFAULT_CONFIG
from fhs.core.typing_utils import NDArrayFloat, to_float_array

from ...model.exceptions import ValidationError

# noinspection PyProtectedMember
from ..simulation._validation import (
    beta_params_from_mean_uncertainty,
    lognorm_params_from_mean_uncertainty,
)


@runtime_checkable
class DistributionStrategy(Protocol):
    """Contract for a single-feature sampling strategy."""

    @property
    def name(self) -> str: ...

    def sample(
        self,
        rng: np.random.Generator,
        mean: float,
        uncertainty: float,
        n: int,
        lower: float | None = None,
        upper: float | None = None,
    ) -> NDArrayFloat:
        """Return *n* samples in rate-space [0, 1]."""
        ...

    def transform_correlated(
        self,
        z_scores: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> NDArrayFloat:
        """Transform standard-normal z-scores to this distribution."""
        ...

    def inverse_cdf(
        self,
        u: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> NDArrayFloat:
        """Inverse CDF for copula marginals (U[0,1] → rate-space)."""
        ...


class NormalDistribution:
    """Normal (Gaussian) distribution strategy."""

    @property
    def name(self) -> str:
        return "normal"

    @staticmethod
    def sample(
        rng: np.random.Generator,
        mean: float,
        uncertainty: float,
        n: int,
        _lower: float | None = None,
        _upper: float | None = None,
    ) -> np.ndarray:
        std_dev = mean * uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        return to_float_array(rng.normal(mean, std_dev, n))

    @staticmethod
    def transform_correlated(
        z_scores: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        std_dev = mean * uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        return to_float_array(mean + std_dev * np.asarray(z_scores))

    @staticmethod
    def inverse_cdf(
        u: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        std = mean * uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        return to_float_array(stats.norm.ppf(u, loc=mean, scale=std))


class LognormalDistribution:
    """Log-normal distribution strategy."""

    @property
    def name(self) -> str:
        return "lognormal"

    @staticmethod
    def sample(
        rng: np.random.Generator,
        mean: float,
        uncertainty: float,
        n: int,
        _lower: float | None = None,
        _upper: float | None = None,
    ) -> np.ndarray:
        mu_log, sigma_log = lognorm_params_from_mean_uncertainty(mean, uncertainty)
        return to_float_array(rng.lognormal(mu_log, sigma_log, n))

    @staticmethod
    def transform_correlated(
        z_scores: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        sigma_log = uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        mu_log = np.log(mean) - 0.5 * sigma_log**2
        return to_float_array(np.exp(mu_log + sigma_log * np.asarray(z_scores)))

    @staticmethod
    def inverse_cdf(
        u: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        if mean <= 0:
            raise ValidationError(
                "Lognormal marginal requires mean > 0",
                field="mean",
                value=mean,
            )
        sigma_log = (
            uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        )  # pragma: no cover - defensive
        mu_log = np.log(mean) - 0.5 * sigma_log**2  # pragma: no cover - defensive
        return to_float_array(
            stats.lognorm.ppf(u, s=sigma_log, scale=np.exp(mu_log))
        )  # pragma: no cover - defensive


class BetaDistribution:
    """Beta distribution strategy (bounded [0, 1])."""

    @property
    def name(self) -> str:
        return "beta"

    @staticmethod
    def sample(
        rng: np.random.Generator,
        mean: float,
        uncertainty: float,
        n: int,
        _lower: float | None = None,
        _upper: float | None = None,
    ) -> np.ndarray:
        alpha, beta_param = beta_params_from_mean_uncertainty(mean, uncertainty)
        return to_float_array(
            stats.beta.rvs(alpha, beta_param, size=n, random_state=rng)
        )

    def transform_correlated(
        self,
        z_scores: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        # Beta doesn't have a direct z-score transform; use CDF approach
        u = stats.norm.cdf(np.asarray(z_scores))
        return self.inverse_cdf(u, mean, uncertainty)

    @staticmethod
    def inverse_cdf(
        u: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        if not 0 < mean < 1:
            raise ValidationError(
                "Beta marginal requires 0 < mean < 1",
                field="mean",
                value=mean,
            )
        std = mean * uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        var = min(std**2, 0.999 * mean * (1 - mean))
        k = mean * (1 - mean) / var - 1
        alpha = max(mean * k, 1e-6)
        beta_param = max((1 - mean) * k, 1e-6)
        return to_float_array(stats.beta.ppf(np.asarray(u), alpha, beta_param))


class UniformDistribution:
    """Uniform distribution strategy."""

    @property
    def name(self) -> str:
        return "uniform"

    @staticmethod
    def sample(
        rng: np.random.Generator,
        mean: float,
        uncertainty: float,
        n: int,
        _lower: float | None = None,
        _upper: float | None = None,
    ) -> np.ndarray:
        min_val = mean * (1 - uncertainty)
        max_val = mean * (1 + uncertainty)
        return to_float_array(rng.uniform(min_val, max_val, n))

    def transform_correlated(
        self,
        z_scores: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        u = stats.norm.cdf(np.asarray(z_scores))
        return self.inverse_cdf(u, mean, uncertainty)

    @staticmethod
    def inverse_cdf(
        u: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        return to_float_array(
            stats.uniform.ppf(
                np.asarray(u),
                loc=mean * (1 - uncertainty),
                scale=2 * mean * uncertainty,
            )
        )


class TruncatedNormalDistribution:
    """Truncated normal distribution strategy (bounded)."""

    @property
    def name(self) -> str:
        return "truncnorm"

    @staticmethod
    def sample(
        rng: np.random.Generator,
        mean: float,
        uncertainty: float,
        n: int,
        lower: float | None = None,
        upper: float | None = None,
    ) -> np.ndarray:
        lower_bound = 0.0 if lower is None else float(lower)
        upper_bound = 1.0 if upper is None else float(upper)
        std_dev = mean * uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        if std_dev == 0:
            return to_float_array(np.full(n, mean))
        a = (lower_bound - mean) / std_dev
        b = (upper_bound - mean) / std_dev
        return to_float_array(
            stats.truncnorm.rvs(a, b, loc=mean, scale=std_dev, size=n, random_state=rng)
        )

    def transform_correlated(
        self,
        z_scores: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        u = stats.norm.cdf(np.asarray(z_scores))
        return self.inverse_cdf(u, mean, uncertainty)

    @staticmethod
    def inverse_cdf(
        u: np.ndarray,
        mean: float,
        uncertainty: float,
    ) -> np.ndarray:
        std = mean * uncertainty / DEFAULT_CONFIG.UNCERTAINTY_SIGMA_RANGE
        if std == 0:
            return to_float_array(np.full_like(u, mean))
        a = (0.0 - mean) / std
        b = (1.0 - mean) / std
        return to_float_array(
            stats.truncnorm.ppf(np.asarray(u), a, b, loc=mean, scale=std)
        )


class DistributionFactory:
    """Factory for creating distribution strategies."""

    _STRATEGIES: ClassVar[dict[str, type]] = {
        "normal": NormalDistribution,
        "lognormal": LognormalDistribution,
        "beta": BetaDistribution,
        "uniform": UniformDistribution,
        "truncnorm": TruncatedNormalDistribution,
    }

    @classmethod
    def create(cls, name: str) -> DistributionStrategy:
        """Create a distribution strategy by name."""
        strategy_class = cls._STRATEGIES.get(name)
        if strategy_class is None:
            raise ValidationError(
                f"Unknown distribution '{name}'. Supported: {cls.supported()}",
                field="distribution",
                value=name,
            )
        return cast(DistributionStrategy, strategy_class())

    @classmethod
    def supported(cls) -> list[str]:
        """List supported distribution names."""
        return list(cls._STRATEGIES.keys())
