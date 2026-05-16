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

"""Tests for application DTOs."""

from __future__ import annotations

import numpy as np

from fhs.application.dtos import ScenarioContext
from fhs.core.model import Feature


def test_scenario_context_features_by_key():
    """Test ScenarioContext.features_by_key property."""
    features = [
        Feature(
            name="H1: Feature A",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.2,
            business_value_per_conversion=10.0,
            development_cost=5000.0,
        ),
        Feature(
            name="H2: Feature B",
            expected_users=500,
            conversion_rate=0.3,
            uncertainty=0.1,
            business_value_per_conversion=20.0,
            development_cost=2000.0,
        ),
    ]

    context = ScenarioContext(
        scenario_id="test",
        features=features,
        budget=10000.0,
        discount_rate=0.1,
        strategy={},
        weights={},
        dependency_matrix=np.array([]),
        config_path="/test/path",
        config_source="test",
        exam_report={},
    )

    by_key = context.features_by_key

    assert "H1" in by_key
    assert "H2" in by_key
    assert by_key["H1"] == features[0]


def test_scenario_context_biz_values():
    """Test ScenarioContext.biz_values property."""
    features = [
        Feature(
            name="H1: Feature A",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.2,
            business_value_per_conversion=10.0,
            development_cost=5000.0,
        ),
        Feature(
            name="H2: Feature B",
            expected_users=500,
            conversion_rate=0.3,
            uncertainty=0.1,
            business_value_per_conversion=20.0,
            development_cost=2000.0,
        ),
    ]

    context = ScenarioContext(
        scenario_id="test",
        features=features,
        budget=10000.0,
        discount_rate=0.1,
        strategy={},
        weights={},
        dependency_matrix=np.array([]),
        config_path="/test/path",
        config_source="test",
        exam_report={},
    )

    biz_values = context.biz_values

    assert "H1" in biz_values
    assert "H2" in biz_values
    assert biz_values["H1"] == 10.0
    assert biz_values["H2"] == 20.0
