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

"""Tests for DeliveryRiskConfig validation."""

from __future__ import annotations

import warnings

import pytest

from fhs.core.model.config.delivery import DelayModelConfig


class TestDeliveryRiskConfigValidation:
    """Tests for DeliveryRiskConfig validation logic."""

    def test_sprint_uncertainty_as_string_percent(self):
        """Sprint uncertainty accepts string percentage format."""
        config = DelayModelConfig(
            sprint_uncertainty="30%",
            sprint_ceiling=3.0,
        )
        assert config.sprint_uncertainty == 0.30

    def test_sprint_uncertainty_above_one_normalizes(self):
        """Sprint uncertainty > 1.0 is treated as percentage."""
        config = DelayModelConfig(
            sprint_uncertainty=30.0,
            sprint_ceiling=3.0,
        )
        assert config.sprint_uncertainty == 0.30

    def test_sprint_uncertainty_negative_raises(self):
        """Negative sprint uncertainty raises ValueError."""
        with pytest.raises(ValueError, match="sprint_uncertainty must be ≥ 0%"):
            DelayModelConfig(
                sprint_uncertainty=-0.1,
                sprint_ceiling=3.0,
            )

    def test_sprint_uncertainty_above_100_percent_raises(self):
        """Sprint uncertainty > 100% raises ValueError."""
        with pytest.raises(ValueError, match="sprint_uncertainty must be ≤ 100%"):
            DelayModelConfig(
                sprint_uncertainty=150.0,
                sprint_ceiling=3.0,
            )

    def test_sprint_ceiling_at_one_raises(self):
        """Sprint ceiling at 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="greater than 1"):
            DelayModelConfig(
                sprint_uncertainty=0.30,
                sprint_ceiling=1.0,
            )

    def test_sprint_ceiling_above_ten_raises(self):
        """Sprint ceiling > 10.0 raises ValueError."""
        with pytest.raises(ValueError, match="less than or equal to 10"):
            DelayModelConfig(
                sprint_uncertainty=0.30,
                sprint_ceiling=11.0,
            )

    def test_sprint_ceiling_clips_probability_mass_warns(self):
        """Low sprint ceiling emits warning about clipping."""
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            DelayModelConfig(
                sprint_uncertainty=0.50,
                sprint_ceiling=1.5,
            )
            assert len(caught_warnings) > 0
            assert "sprint_ceiling" in str(caught_warnings[0].message)
