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

"""Tests for fhs.core.services.simulation._validation — parameter validation helpers."""

import numpy as np
import pytest

from fhs.core.model.exceptions import CorrelationMatrixError, ValidationError

# noinspection PyProtectedMember
from fhs.core.services.simulation._validation import (
    beta_params_from_mean_uncertainty,
    ensure_psd,
    lognorm_params_from_mean_uncertainty,
    validate_scenarios,
    validate_uncertainty,
)


class TestValidateScenarios:
    def test_valid(self):
        validate_scenarios(1000)  # should not raise

    def test_too_few(self):
        with pytest.raises(ValidationError, match="scenarios"):
            validate_scenarios(1)


class TestValidateUncertainty:
    def test_valid(self):
        validate_uncertainty(0.5)

    def test_negative(self):
        with pytest.raises(ValidationError, match="Uncertainty"):
            validate_uncertainty(-0.1)

    def test_above_one(self):
        with pytest.raises(ValidationError, match="Uncertainty"):
            validate_uncertainty(1.1)

    def test_boundary_zero(self):
        validate_uncertainty(0.0)

    def test_boundary_one(self):
        validate_uncertainty(1.0)


class TestBetaParams:
    def test_typical(self):
        alpha, beta = beta_params_from_mean_uncertainty(0.5, 0.3)
        assert alpha > 0
        assert beta > 0

    def test_mean_near_zero(self):
        alpha, beta = beta_params_from_mean_uncertainty(0.01, 0.5)
        assert alpha > 0
        assert beta > 0

    def test_mean_near_one(self):
        alpha, beta = beta_params_from_mean_uncertainty(0.99, 0.5)
        assert alpha > 0
        assert beta > 0

    def test_mean_zero_raises(self):
        with pytest.raises(ValidationError, match="Beta"):
            beta_params_from_mean_uncertainty(0.0, 0.3)

    def test_mean_one_raises(self):
        with pytest.raises(ValidationError, match="Beta"):
            beta_params_from_mean_uncertainty(1.0, 0.3)

    def test_mean_negative_raises(self):
        with pytest.raises(ValidationError, match="Beta"):
            beta_params_from_mean_uncertainty(-0.1, 0.3)

    def test_high_uncertainty(self):
        alpha, beta = beta_params_from_mean_uncertainty(0.5, 0.99)
        assert alpha > 0
        assert beta > 0

    def test_low_uncertainty(self):
        alpha, beta = beta_params_from_mean_uncertainty(0.5, 0.01)
        assert alpha > 0
        assert beta > 0


class TestLognormParams:
    def test_typical(self):
        mu, sigma = lognorm_params_from_mean_uncertainty(100.0, 0.3)
        assert sigma > 0
        # mu_log should be close to log(100)
        assert abs(mu - np.log(100)) < 1.0

    def test_mean_zero_raises(self):
        with pytest.raises(ValidationError, match="Log-Normal"):
            lognorm_params_from_mean_uncertainty(0.0, 0.3)

    def test_mean_negative_raises(self):
        with pytest.raises(ValidationError, match="Log-Normal"):
            lognorm_params_from_mean_uncertainty(-10.0, 0.3)


class TestEnsurePSD:
    def test_already_psd(self):
        corr = np.eye(3)
        result = ensure_psd(corr)
        np.testing.assert_array_equal(result, corr)

    def test_valid_correlation_matrix(self):
        corr = np.array(
            [
                [1.0, 0.5, 0.3],
                [0.5, 1.0, 0.2],
                [0.3, 0.2, 1.0],
            ]
        )
        result = ensure_psd(corr)
        np.testing.assert_array_almost_equal(result, corr)

    def test_not_psd_no_repair_raises(self):
        # Build a non-PSD matrix
        corr = np.array(
            [
                [1.0, 0.9, 0.9],
                [0.9, 1.0, -0.9],
                [0.9, -0.9, 1.0],
            ]
        )
        with pytest.raises(CorrelationMatrixError, match="not positive semi-definite"):
            ensure_psd(corr, repair=False)

    def test_not_psd_with_repair(self):
        corr = np.array(
            [
                [1.0, 0.9, 0.9],
                [0.9, 1.0, -0.9],
                [0.9, -0.9, 1.0],
            ]
        )
        result = ensure_psd(corr, repair=True)
        # Result should be PSD (cholesky should succeed)
        np.linalg.cholesky(result)
        # Diagonal should be 1.0
        np.testing.assert_array_almost_equal(np.diag(result), [1.0, 1.0, 1.0])

    def test_not_psd_with_repair_returns_symmetric_matrix(self):
        corr = np.array(
            [
                [1.0, 0.85, -0.95],
                [0.85, 1.0, 0.85],
                [-0.95, 0.85, 1.0],
            ]
        )
        result = ensure_psd(corr, repair=True)

        np.testing.assert_allclose(result, result.T, atol=1e-10)
        min_eigenvalue = np.min(np.linalg.eigvalsh(result))
        assert min_eigenvalue >= -1e-10
