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

"""Tests for Feature entity validation."""

from __future__ import annotations

import pytest

from fhs.core.model.entities.feature import Feature


class TestFeatureValidation:
    """Tests for Feature validation logic."""

    def test_acceptance_model_invalid_raises(self):
        """Invalid acceptance_model raises ValueError."""
        with pytest.raises(ValueError, match="acceptance_model must be one of"):
            Feature(
                name="Test Feature",
                development_cost=100_000,
                planned_sprints=5,
                business_value_per_conversion=1000,
                expected_conversions=100,
                uncertainty_conversions=0.2,
                acceptance_model="invalid_model",
            )
