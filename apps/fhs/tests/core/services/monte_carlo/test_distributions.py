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

"""Tests for monte carlo distribution strategies."""

from __future__ import annotations

import numpy as np
import pytest

from fhs.core.model.exceptions import ValidationError
from fhs.core.services.monte_carlo.distributions import (
    BetaDistribution,
    LognormalDistribution,
    NormalDistribution,
    TruncatedNormalDistribution,
    UniformDistribution,
)


def test_normal_distribution_name():
    """Test NormalDistribution name property."""
    dist = NormalDistribution()
    assert dist.name == "normal"


def test_normal_distribution_inverse_cdf():
    """Test NormalDistribution.inverse_cdf."""
    u = np.array([0.1, 0.5, 0.9])
    result = NormalDistribution.inverse_cdf(u, mean=100.0, uncertainty=0.2)
    assert len(result) == 3
    assert result.dtype == np.float64


def test_lognormal_distribution_name():
    """Test LognormalDistribution name property."""
    dist = LognormalDistribution()
    assert dist.name == "lognormal"


def test_lognormal_distribution_inverse_cdf_negative_mean():
    """Test LognormalDistribution.inverse_cdf with negative mean raises error."""
    u = np.array([0.5])
    with pytest.raises(ValidationError, match="Lognormal marginal requires mean > 0"):
        LognormalDistribution.inverse_cdf(u, mean=-10.0, uncertainty=0.2)


def test_lognormal_distribution_inverse_cdf_zero_mean():
    """Test LognormalDistribution.inverse_cdf with zero mean raises error."""
    u = np.array([0.5])
    with pytest.raises(ValidationError, match="Lognormal marginal requires mean > 0"):
        LognormalDistribution.inverse_cdf(u, mean=0.0, uncertainty=0.2)


def test_beta_distribution_name():
    """Test BetaDistribution name property."""
    dist = BetaDistribution()
    assert dist.name == "beta"


def test_beta_distribution_sample():
    """Test BetaDistribution.sample."""
    rng = np.random.default_rng(42)
    dist = BetaDistribution()
    result = dist.sample(rng, mean=0.5, uncertainty=0.2, n=100)
    assert len(result) == 100
    assert np.all((result >= 0) & (result <= 1))


def test_beta_distribution_transform_correlated():
    """Test BetaDistribution.transform_correlated."""
    dist = BetaDistribution()
    z_scores = np.array([0.0, 1.0, -1.0])
    result = dist.transform_correlated(z_scores, mean=0.5, uncertainty=0.2)
    assert len(result) == 3
    assert np.all((result >= 0) & (result <= 1))


def test_beta_distribution_inverse_cdf_invalid_mean_below():
    """Test BetaDistribution.inverse_cdf with mean <= 0 raises error."""
    u = np.array([0.5])
    with pytest.raises(ValidationError, match="Beta marginal requires 0 < mean < 1"):
        BetaDistribution.inverse_cdf(u, mean=0.0, uncertainty=0.2)


def test_beta_distribution_inverse_cdf_invalid_mean_above():
    """Test BetaDistribution.inverse_cdf with mean >= 1 raises error."""
    u = np.array([0.5])
    with pytest.raises(ValidationError, match="Beta marginal requires 0 < mean < 1"):
        BetaDistribution.inverse_cdf(u, mean=1.0, uncertainty=0.2)


def test_uniform_distribution_name():
    """Test UniformDistribution name property."""
    dist = UniformDistribution()
    assert dist.name == "uniform"


def test_uniform_distribution_transform_correlated():
    """Test UniformDistribution.transform_correlated."""
    dist = UniformDistribution()
    z_scores = np.array([0.0, 1.0, -1.0])
    result = dist.transform_correlated(z_scores, mean=100.0, uncertainty=0.3)
    assert len(result) == 3


def test_uniform_distribution_inverse_cdf():
    """Test UniformDistribution.inverse_cdf."""
    u = np.array([0.0, 0.5, 1.0])
    result = UniformDistribution.inverse_cdf(u, mean=100.0, uncertainty=0.3)
    assert len(result) == 3


def test_truncated_normal_distribution_name():
    """Test TruncatedNormalDistribution name property."""
    dist = TruncatedNormalDistribution()
    assert dist.name == "truncnorm"


def test_truncated_normal_distribution_zero_std():
    """Test TruncatedNormalDistribution.sample with zero std dev."""
    rng = np.random.default_rng(42)
    result = TruncatedNormalDistribution.sample(rng, mean=100.0, uncertainty=0.0, n=10)
    assert len(result) == 10
    assert np.all(result == 100.0)


def test_truncated_normal_distribution_transform_correlated():
    """Test TruncatedNormalDistribution.transform_correlated."""
    dist = TruncatedNormalDistribution()
    z_scores = np.array([0.0, 1.0, -1.0])
    result = dist.transform_correlated(z_scores, mean=100.0, uncertainty=0.2)
    assert len(result) == 3


def test_truncated_normal_distribution_inverse_cdf_zero_std():
    """Test TruncatedNormalDistribution.inverse_cdf with zero std."""
    u = np.array([0.0, 0.5, 1.0])
    result = TruncatedNormalDistribution.inverse_cdf(u, mean=100.0, uncertainty=0.0)
    assert len(result) == 3
    assert np.all(result == 100.0)


def test_truncated_normal_distribution_inverse_cdf_nonzero_std():
    """Test TruncatedNormalDistribution.inverse_cdf with nonzero std."""
    u = np.array([0.0, 0.5, 1.0])
    result = TruncatedNormalDistribution.inverse_cdf(u, mean=100.0, uncertainty=0.2)
    assert len(result) == 3
