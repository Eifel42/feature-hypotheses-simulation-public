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

"""Tests for fhs.core.services.assessment.feature_assessment — FeatureAssessmentService."""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.services.assessment.feature_assessment import FeatureAssessmentService
from fhs.core.services.risk import RiskCalculator


@pytest.fixture
def feature():
    return Feature(
        name="Login",
        expected_users=1000,
        conversion_rate=0.5,
        uncertainty=0.2,
        business_value_per_conversion=10.0,
        development_cost=5000.0,
    )


@pytest.fixture
def simulation_result():
    return SimulationResult(
        feature_name="Login",
        results=np.random.RandomState(42).normal(500, 50, 1000),
        expected_value=500.0,
        business_value_per_conversion=10.0,
        development_cost=5000.0,
    )


class TestFeatureAssessmentService:
    def test_init_defaults(self):
        svc = FeatureAssessmentService()
        assert isinstance(svc.calculator, RiskCalculator)

    def test_init_with_calculator(self):
        calc = RiskCalculator()
        svc = FeatureAssessmentService(calculator=calc)
        assert svc.calculator is calc

    def test_assess_feature_structure(self, feature, simulation_result):
        svc = FeatureAssessmentService()
        result = svc.assess_feature(feature, simulation_result)

        assert result["feature"] == "Login"
        assert "expected_business_value" in result
        assert "var_95_business_value" in result
        assert "risk_ratio" in result
        assert "recommendation" in result
        assert "confidence_interval" in result
        assert "downside_risk" in result

    def test_assess_feature_business_value_values(self, feature, simulation_result):
        svc = FeatureAssessmentService()
        result = svc.assess_feature(feature, simulation_result)

        # Expected business value = 500 * 10 = 5000
        assert result["expected_business_value"] == 5000.0
        assert result["var_95_business_value"] > 0

    def test_assess_feature_risk_ratio_range(self, feature, simulation_result):
        svc = FeatureAssessmentService()
        result = svc.assess_feature(feature, simulation_result)
        assert 0.0 <= result["risk_ratio"] <= 1.0

    def test_assess_feature_recommendation_text(self, feature, simulation_result):
        svc = FeatureAssessmentService()
        result = svc.assess_feature(feature, simulation_result)
        assert "risk" in result["recommendation"].lower()

    def test_assess_feature_confidence_interval(self, feature, simulation_result):
        svc = FeatureAssessmentService()
        result = svc.assess_feature(feature, simulation_result)
        ci = result["confidence_interval"]
        assert len(ci) == 2
        assert ci[0] < ci[1]
