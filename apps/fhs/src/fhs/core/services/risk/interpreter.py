#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
Risk Interpretation Service

Interprets financial risk metrics and generates business-friendly recommendations.
Eliminates 3 duplicated implementations across portfolio_advisor, feature_assessment,
and ranking modules.
"""

from enum import Enum
from typing import Any

from fhs.core.model.exceptions import ValidationError


class RiskLevel(Enum):
    """
    Risk level value object with threshold-based classification.

    Enum-based risk category with associated metadata.
    """

    LOW = (
        "Low risk",
        "green",
        "Minimal downside risk - feature delivers consistently",
        0.0,
        0.2,
    )
    MEDIUM = (
        "Medium risk",
        "yellow",
        "Moderate downside risk - significant but manageable uncertainty",
        0.2,
        0.4,
    )
    HIGH = (
        "High risk",
        "red",
        "Significant downside risk - large uncertainty in outcomes",
        0.4,
        1.0,
    )

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def color(self) -> str:
        return self.value[1]

    @property
    def description(self) -> str:
        return self.value[2]

    @property
    def min_ratio(self) -> float:
        return self.value[3]

    @property
    def max_ratio(self) -> float:
        return self.value[4]

    def __str__(self) -> str:
        return self.label


class RiskInterpreter:
    """
    Interprets risk ratios with configurable thresholds.

    Provides consistent risk categorization and recommendation text generation
    across the codebase. Replaces 3 duplicated implementations.
    """

    def __init__(
        self,
        low_threshold: float = 0.2,
        high_threshold: float = 0.4,
    ):
        """
        Initialize risk interpreter with custom thresholds.

        Args:
            low_threshold: Upper bound for low risk (default: 0.2 = 20%)
            high_threshold: Upper bound for medium risk (default: 0.4 = 40%)

        Raises:
            ValueError: If thresholds are invalid
        """
        if not 0 <= low_threshold < high_threshold <= 1:
            raise ValidationError(
                f"Invalid thresholds: must be 0 <= low ({low_threshold}) "
                f"< high ({high_threshold}) <= 1",
                field="thresholds",
                value={"low": low_threshold, "high": high_threshold},
            )

        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def classify_risk(self, risk_ratio: float) -> RiskLevel:
        """
        Classify risk ratio into Low/Medium/High category.

        Args:
            risk_ratio: Risk ratio from RiskCalculator.calculate_risk_ratio()
                       (0.0 = no risk, 1.0 = total risk)

        Returns:
            RiskLevel instance

        Example:
            >>> interpreter = RiskInterpreter()
            >>> level = interpreter.classify_risk(0.15)
            >>> level.label
            'Low risk'
            >>> level.color
            'green'
        """
        if risk_ratio < self.low_threshold:
            return RiskLevel.LOW
        elif risk_ratio < self.high_threshold:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def generate_recommendation(
        self,
        risk_ratio: float,
        confidence_level: float = 0.95,
    ) -> str:
        """
        Generate human-readable recommendation text from risk ratio.

        Args:
            risk_ratio: Risk ratio (0.0 to 1.0)
            confidence_level: Confidence level used (default: 0.95 = 95%)

        Returns:
            Recommendation text string

        Example:
            >>> interpreter = RiskInterpreter()
            >>> interpreter.generate_recommendation(0.15)
            'Low risk — Feature delivers at least 85% of expected value with 95% confidence'
        """
        level = self.classify_risk(risk_ratio)
        confidence_pct = (1 - risk_ratio) * 100
        confidence_level_pct = confidence_level * 100

        return (
            f"{level.label} — Feature delivers at least "
            f"{confidence_pct:.0f}% of expected value "
            f"with {confidence_level_pct:.0f}% confidence"
        )

    def generate_detailed_recommendation(
        self,
        risk_ratio: float,
        expected_value: float,
        var_95: float,
        confidence_level: float = 0.95,
    ) -> dict[str, Any]:
        """
        Generate detailed recommendation with metrics.

        Args:
            risk_ratio: Risk ratio (0.0 to 1.0)
            expected_value: Expected value (mean)
            var_95: Value at Risk (95% percentile)
            confidence_level: Confidence level (default: 0.95)

        Returns:
            Dictionary with recommendation details

        Example:
            >>> interpreter = RiskInterpreter()
            >>> result = interpreter.generate_detailed_recommendation(
            ...     risk_ratio=0.25,
            ...     expected_value=100000,
            ...     var_95=75000
            ... )
            >>> result['level'].label
            'Medium risk'
            >>> result['worst_case_loss']
            25000
        """
        level = self.classify_risk(risk_ratio)

        return {
            "level": level,
            "risk_ratio": risk_ratio,
            "expected_value": expected_value,
            "var_95": var_95,
            "worst_case_loss": expected_value - var_95,
            "confidence_pct": (1 - risk_ratio) * 100,
            "text": self.generate_recommendation(risk_ratio, confidence_level),
        }


# Default interpreter instance
DEFAULT_RISK_INTERPRETER = RiskInterpreter(
    low_threshold=0.2,
    high_threshold=0.4,
)


def categorize_likelihood(
    value: float,
    low_threshold: float = 0.3,
    high_threshold: float = 0.7,
) -> str:
    """
    Categorize likelihood/probability into Low/Medium/High.

    Utility function for simple likelihood categorization without full
    risk interpretation. Used for non-delivery risk, adoption likelihood, etc.

    This replaces duplicated implementations in portfolio_reporting.

    Args:
        value: Probability value (0.0 to 1.0)
        low_threshold: Upper bound for low category (default: 0.3)
        high_threshold: Upper bound for medium category (default: 0.7)

    Returns:
        Category string: "Low", "Medium", or "High"

    Example:
        >>> categorize_likelihood(0.2)
        'Low'
        >>> categorize_likelihood(0.5)
        'Medium'
        >>> categorize_likelihood(0.8)
        'High'
    """
    if value < low_threshold:
        return "Low"
    elif value < high_threshold:
        return "Medium"
    else:
        return "High"
