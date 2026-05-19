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

"""Tests for simulation configuration value objects."""

from __future__ import annotations

from fhs.core.model.value_objects.simulation_config import SimulationConfig


def test_simulation_config_post_init_sets_defaults():
    """Test that __post_init__ sets ALLOWED_DISTRIBUTIONS when None."""
    config = SimulationConfig()
    assert config.ALLOWED_DISTRIBUTIONS is not None
    assert "normal" in config.ALLOWED_DISTRIBUTIONS
    assert "uniform" in config.ALLOWED_DISTRIBUTIONS


def test_simulation_config_post_init_preserves_custom():
    """Test that __post_init__ preserves custom ALLOWED_DISTRIBUTIONS."""
    custom = ["normal", "lognormal"]
    config = SimulationConfig(ALLOWED_DISTRIBUTIONS=custom)
    assert custom == config.ALLOWED_DISTRIBUTIONS
