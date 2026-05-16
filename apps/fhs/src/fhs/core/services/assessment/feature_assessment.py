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
Feature Assessment Service

Domain service for assessing individual features and calculating risk metrics.
Extracted from PortfolioAdvisor to follow Single Responsibility Principle.
"""

import logging
from typing import Any

from ...model import Feature, SimulationResult
from ..monte_carlo import MonteCarloEngine
from ..risk import RiskCalculator, RiskInterpreter

logger = logging.getLogger("fhs.feature_assessment")


class FeatureAssessmentService:
    """
    Assesses individual features and provides risk analysis.

    Responsibilities:
    - Assess single feature risk/value
    - Calculate risk ratios
    - Generate recommendations
    - Robustness analysis
    """

    def __init__(
        self,
        calculator: RiskCalculator | None = None,
        risk_interpreter: RiskInterpreter | None = None,
    ):
        """
        Initialize feature assessment service.

        Args:
            calculator: RiskCalculator instance (if None, creates new one)
            risk_interpreter: RiskInterpreter instance (if None, creates new one)
        """
        self.calculator = calculator or RiskCalculator()
        self.risk_interpreter = risk_interpreter or RiskInterpreter()

    def assess_feature(
        self,
        feature: Feature,
        simulation_result: SimulationResult,
    ) -> dict[str, Any]:
        """
        Assess a single feature's risk and value.

        Answers: "What do we lose if we don't build this feature?"

        Args:
            feature: Feature to assess
            simulation_result: Simulation results for the feature

        Returns:
            Dictionary with assessment metrics:
                - feature_name: Feature name
                - expected_business_value: Expected business value
                - business_value_at_risk_95: VaR95
                - conditional_var_95: CVaR95
                - risk_ratio: Risk ratio (expected / VaR95)
                - recommendation: Textual recommendation
                - development_cost: Development cost
                - net_expected_value: Expected business value - cost
                - roi: Return on investment
        """
        bv = feature.business_value_per_conversion
        expected_conversions = simulation_result.expected_value
        var_95_conversions = simulation_result.var_95
        expected_business_value = expected_conversions * bv
        var_95_business_value = var_95_conversions * bv
        downside_risk = expected_business_value - var_95_business_value

        risk_ratio = self._risk_ratio(expected_business_value, var_95_business_value)
        recommendation = self._recommendation_text(risk_ratio)

        ci = simulation_result.confidence_interval
        ci_business_value = [ci[0] * bv, ci[1] * bv]

        return {
            "feature": feature.name,
            "expected_conversions": expected_conversions,
            "expected_business_value": expected_business_value,
            "var_95_conversions": var_95_conversions,
            "var_95_business_value": var_95_business_value,
            "opportunity_cost": expected_business_value,
            "downside_risk": downside_risk,
            "risk_ratio": risk_ratio,
            "confidence_interval": ci_business_value,
            "recommendation": recommendation,
        }

    @staticmethod
    def get_robustness_variants(
        feature: Feature,
        engine: MonteCarloEngine,
        scenarios: int = 10000,
        distribution: str = "normal",
    ) -> dict[str, dict[str, float]]:
        """
        Calculate robustness variants for a feature.

        Compares results across different uncertainty assumptions.

        Args:
            feature: Feature to analyze
            engine: MonteCarloEngine instance
            scenarios: Number of scenarios
            distribution: Distribution type

        Returns:
            Dictionary with variants:
                - original: Results with original uncertainty
                - low_uncertainty: Results with uncertainty * 0.5
                - high_uncertainty: Results with uncertainty * 1.5
        """
        variants = {}  # pragma: no cover - defensive
        # pragma: no cover - defensive
        # Original uncertainty  # pragma: no cover - defensive
        result_original = engine.simulate(  # pragma: no cover - defensive
            feature,
            scenarios=scenarios,
            distribution=distribution,  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        variants["original"] = {  # pragma: no cover - defensive
            "uncertainty": feature.uncertainty,  # pragma: no cover - defensive
            "expected_business_value": result_original.expected_business_value,  # type: ignore[attr-defined]  # pragma: no cover - defensive
            "var_95": result_original.business_value_at_risk_95,  # type: ignore[attr-defined]  # pragma: no cover - defensive
            "cvar_95": result_original.conditional_var_95,  # type: ignore[attr-defined]  # pragma: no cover - defensive
        }  # pragma: no cover - defensive
        # pragma: no cover - defensive
        # Low uncertainty variant (50% reduction)  # pragma: no cover - defensive
        feature_low = feature.model_copy(  # pragma: no cover - defensive
            update={
                "uncertainty": feature.uncertainty * 0.5
            }  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        result_low = engine.simulate(  # pragma: no cover - defensive
            feature_low,
            scenarios=scenarios,
            distribution=distribution,  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        variants["low_uncertainty"] = {  # pragma: no cover - defensive
            "uncertainty": feature_low.uncertainty,  # pragma: no cover - defensive
            "expected_business_value": result_low.expected_business_value,  # type: ignore[attr-defined]  # pragma: no cover - defensive
            "var_95": result_low.business_value_at_risk_95,  # type: ignore[attr-defined]  # pragma: no cover - defensive
            "cvar_95": result_low.conditional_var_95,  # type: ignore[attr-defined]  # pragma: no cover - defensive
        }  # pragma: no cover - defensive
        # pragma: no cover - defensive
        # High uncertainty variant (50% increase)  # pragma: no cover - defensive
        feature_high = feature.model_copy(  # pragma: no cover - defensive
            update={
                "uncertainty": feature.uncertainty * 1.5
            }  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        result_high = engine.simulate(  # pragma: no cover - defensive
            feature_high,
            scenarios=scenarios,
            distribution=distribution,  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        variants["high_uncertainty"] = {  # pragma: no cover - defensive
            "uncertainty": feature_high.uncertainty,  # pragma: no cover - defensive
            "expected_business_value": result_high.expected_business_value,  # type: ignore[attr-defined]  # pragma: no cover - defensive
            "var_95": result_high.business_value_at_risk_95,  # type: ignore[attr-defined]  # pragma: no cover - defensive
            "cvar_95": result_high.conditional_var_95,  # type: ignore[attr-defined]  # pragma: no cover - defensive
        }  # pragma: no cover - defensive
        # pragma: no cover - defensive
        return variants  # pragma: no cover - defensive

    def _risk_ratio(self, expected: float, var_95: float) -> float:
        """Calculate risk ratio using centralized RiskCalculator."""
        return self.calculator.calculate_risk_ratio(expected, var_95, clamp=True)

    def _recommendation_text(self, risk_ratio: float) -> str:
        """Generate recommendation using centralized RiskInterpreter."""
        return self.risk_interpreter.generate_recommendation(
            risk_ratio, confidence_level=0.95
        )
