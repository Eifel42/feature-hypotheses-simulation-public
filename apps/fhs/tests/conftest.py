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
Pytest configuration for the FHS test suite.

Shared fixtures for reuse across test modules.
"""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult


@pytest.fixture(autouse=True)
def _reset_rng():
    """Reset NumPy global RNG state before each test for isolation."""
    np.random.seed(None)
    return


@pytest.fixture
def sample_feature():
    """A typical Feature for reuse in tests."""
    return Feature(
        name="Login",
        expected_users=1000,
        conversion_rate=0.15,
        uncertainty=0.1,
    )


@pytest.fixture
def sample_simulation_result():
    """A SimulationResult with known data for reuse in tests."""
    return SimulationResult(
        feature_name="Login",
        results=np.array([100.0, 150.0, 200.0, 250.0, 300.0]),
        scenarios=5,
        expected_value=200.0,
        var_95=120.0,
        business_value_per_conversion=10.0,
        development_cost=500.0,
    )
