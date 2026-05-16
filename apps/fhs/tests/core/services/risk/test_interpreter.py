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

"""Tests for fhs.core.services.risk.interpreter — RiskInterpreter and RiskLevel."""

import pytest

from fhs.core.model.exceptions import ValidationError
from fhs.core.services.risk.interpreter import (
    DEFAULT_RISK_INTERPRETER,
    RiskInterpreter,
    RiskLevel,
    categorize_likelihood,
)


class TestRiskLevel:
    def test_low_constants(self):
        assert RiskLevel.LOW.label == "Low risk"
        assert RiskLevel.LOW.color == "green"

    def test_medium_constants(self):
        assert RiskLevel.MEDIUM.label == "Medium risk"
        assert RiskLevel.MEDIUM.color == "yellow"

    def test_high_constants(self):
        assert RiskLevel.HIGH.label == "High risk"
        assert RiskLevel.HIGH.color == "red"

    def test_str(self):
        assert str(RiskLevel.LOW) == "Low risk"

    def test_enum_immutable(self):
        attr_name = "label"
        with pytest.raises(AttributeError):
            setattr(RiskLevel.LOW, attr_name, "changed")


class TestRiskInterpreter:
    def test_default_thresholds(self):
        ri = RiskInterpreter()
        assert ri.low_threshold == 0.2
        assert ri.high_threshold == 0.4

    def test_custom_thresholds(self):
        ri = RiskInterpreter(low_threshold=0.1, high_threshold=0.3)
        assert ri.low_threshold == 0.1
        assert ri.high_threshold == 0.3

    def test_invalid_thresholds_low_gte_high(self):
        with pytest.raises(ValidationError, match="thresholds"):
            RiskInterpreter(low_threshold=0.5, high_threshold=0.3)

    def test_invalid_thresholds_equal(self):
        with pytest.raises(ValidationError, match="thresholds"):
            RiskInterpreter(low_threshold=0.3, high_threshold=0.3)

    def test_invalid_thresholds_negative(self):
        with pytest.raises(ValidationError, match="thresholds"):
            RiskInterpreter(low_threshold=-0.1, high_threshold=0.3)

    def test_invalid_thresholds_above_one(self):
        with pytest.raises(ValidationError, match="thresholds"):
            RiskInterpreter(low_threshold=0.2, high_threshold=1.1)


class TestClassifyRisk:
    def test_low(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(0.1) is RiskLevel.LOW

    def test_medium(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(0.3) is RiskLevel.MEDIUM

    def test_high(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(0.5) is RiskLevel.HIGH

    def test_boundary_low_medium(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(0.2) is RiskLevel.MEDIUM  # >= threshold

    def test_boundary_medium_high(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(0.4) is RiskLevel.HIGH  # >= threshold

    def test_zero(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(0.0) is RiskLevel.LOW

    def test_one(self):
        ri = RiskInterpreter()
        assert ri.classify_risk(1.0) is RiskLevel.HIGH


class TestGenerateRecommendation:
    def test_low_risk_text(self):
        ri = RiskInterpreter()
        text = ri.generate_recommendation(0.1)
        assert "Low risk" in text
        assert "90%" in text

    def test_high_risk_text(self):
        ri = RiskInterpreter()
        text = ri.generate_recommendation(0.5)
        assert "High risk" in text

    def test_custom_confidence(self):
        ri = RiskInterpreter()
        text = ri.generate_recommendation(0.1, confidence_level=0.99)
        assert "99%" in text


class TestGenerateDetailedRecommendation:
    def test_structure(self):
        ri = RiskInterpreter()
        result = ri.generate_detailed_recommendation(
            risk_ratio=0.25,
            expected_value=100000,
            var_95=75000,
        )
        assert result["level"] is RiskLevel.MEDIUM
        assert result["risk_ratio"] == 0.25
        assert result["expected_value"] == 100000
        assert result["var_95"] == 75000
        assert result["worst_case_loss"] == 25000
        assert "text" in result

    def test_low_risk(self):
        ri = RiskInterpreter()
        result = ri.generate_detailed_recommendation(0.05, 1000, 950)
        assert result["level"] is RiskLevel.LOW


class TestCategorizeLikelihood:
    def test_low(self):
        assert categorize_likelihood(0.1) == "Low"

    def test_medium(self):
        assert categorize_likelihood(0.5) == "Medium"

    def test_high(self):
        assert categorize_likelihood(0.8) == "High"

    def test_custom_thresholds(self):
        assert (
            categorize_likelihood(0.25, low_threshold=0.2, high_threshold=0.5)
            == "Medium"
        )

    def test_boundary_low_medium(self):
        assert categorize_likelihood(0.3) == "Medium"  # >= default low_threshold

    def test_boundary_medium_high(self):
        assert categorize_likelihood(0.7) == "High"  # >= default high_threshold


class TestDefaultInterpreter:
    def test_is_instance(self):
        assert isinstance(DEFAULT_RISK_INTERPRETER, RiskInterpreter)

    def test_default_thresholds(self):
        assert DEFAULT_RISK_INTERPRETER.low_threshold == 0.2
        assert DEFAULT_RISK_INTERPRETER.high_threshold == 0.4


class TestRiskLevelProperties:
    """Test all RiskLevel properties for coverage."""

    def test_description_property(self):
        """Test description property access for all levels."""
        assert (
            RiskLevel.LOW.description
            == "Minimal downside risk - feature delivers consistently"
        )
        assert (
            RiskLevel.MEDIUM.description
            == "Moderate downside risk - significant but manageable uncertainty"
        )
        assert (
            RiskLevel.HIGH.description
            == "Significant downside risk - large uncertainty in outcomes"
        )

    def test_min_ratio_property(self):
        """Test min_ratio property access for all levels."""
        assert RiskLevel.LOW.min_ratio == 0.0
        assert RiskLevel.MEDIUM.min_ratio == 0.2
        assert RiskLevel.HIGH.min_ratio == 0.4

    def test_max_ratio_property(self):
        """Test max_ratio property access for all levels."""
        assert RiskLevel.LOW.max_ratio == 0.2
        assert RiskLevel.MEDIUM.max_ratio == 0.4
        assert RiskLevel.HIGH.max_ratio == 1.0
