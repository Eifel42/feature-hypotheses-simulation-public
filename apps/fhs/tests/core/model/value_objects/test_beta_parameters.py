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

"""Tests for BetaParameters value object."""

from __future__ import annotations

import pytest

from fhs.core.model.exceptions import ValidationError
from fhs.core.model.value_objects.beta_parameters import BetaParameters


class TestBetaParameters:
    """Tests for BetaParameters value object."""

    def test_from_mean_uncertainty_valid(self):
        """Valid mean and uncertainty produces beta parameters."""
        params = BetaParameters.from_mean_uncertainty(mean=0.5, uncertainty=0.2)
        assert params.alpha > 0
        assert params.beta > 0

    def test_from_mean_uncertainty_mean_zero_raises(self):
        """Mean of 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="0 < mean < 1"):
            BetaParameters.from_mean_uncertainty(mean=0.0, uncertainty=0.2)

    def test_from_mean_uncertainty_mean_one_raises(self):
        """Mean of 1 raises ValidationError."""
        with pytest.raises(ValidationError, match="0 < mean < 1"):
            BetaParameters.from_mean_uncertainty(mean=1.0, uncertainty=0.2)

    def test_from_mean_uncertainty_mean_negative_raises(self):
        """Negative mean raises ValidationError."""
        with pytest.raises(ValidationError, match="0 < mean < 1"):
            BetaParameters.from_mean_uncertainty(mean=-0.1, uncertainty=0.2)

    def test_from_mean_uncertainty_mean_above_one_raises(self):
        """Mean above 1 raises ValidationError."""
        with pytest.raises(ValidationError, match="0 < mean < 1"):
            BetaParameters.from_mean_uncertainty(mean=1.5, uncertainty=0.2)

    def test_from_mean_uncertainty_sigma_multiplier_zero_raises(self):
        """Sigma multiplier of 0 raises ValidationError."""
        with pytest.raises(ValidationError, match="sigma_multiplier must be positive"):
            BetaParameters.from_mean_uncertainty(
                mean=0.5, uncertainty=0.2, sigma_multiplier=0.0
            )

    def test_from_mean_uncertainty_sigma_multiplier_negative_raises(self):
        """Negative sigma multiplier raises ValidationError."""
        with pytest.raises(ValidationError, match="sigma_multiplier must be positive"):
            BetaParameters.from_mean_uncertainty(
                mean=0.5, uncertainty=0.2, sigma_multiplier=-1.0
            )
