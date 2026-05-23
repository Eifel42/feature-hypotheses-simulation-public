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
Ranking Service

Domain service for ranking and comparing features.
Extracted from PortfolioAdvisor to follow Single Responsibility Principle.

§11.3 DDD Refactoring: Strategy pattern for pluggable sort keys.
§11.4 DDD Refactoring: Delegates recommendation text to RiskInterpreter.
"""

import logging
from typing import Any, Protocol

from ...model import Feature, SimulationResult
from ...model.exceptions import ValidationError
from ..risk import RiskCalculator, RiskInterpreter

logger = logging.getLogger("fhs.ranking")


# ── Ranking Strategies (§11.3) ───────────────────────────────────────────


class RankingStrategy(Protocol):
    """Protocol for pluggable ranking sort keys."""

    def sort_key(self, feature: str, result: SimulationResult) -> float: ...


class ExpectedValueRanking:
    """Rank by expected business value (default)."""

    @staticmethod
    def sort_key(_feature: str, result: SimulationResult) -> float:
        return result.expected_business_value


class VaRRanking:
    """Rank by business value at risk (95%)."""

    @staticmethod
    def sort_key(_feature: str, result: SimulationResult) -> float:
        return result.business_value_at_risk_95


class CVaRRanking:
    """Rank by conditional VaR (95%) business value."""

    @staticmethod
    def sort_key(_feature: str, result: SimulationResult) -> float:
        return result.cvar_95 * result.business_value_per_conversion


class ROIRanking:
    """Rank by return on investment."""

    @staticmethod
    def sort_key(_feature: str, result: SimulationResult) -> float:
        return result.roi


# Mapping from string names to strategy instances (backward compatibility)
_RANKING_STRATEGIES: dict[str, RankingStrategy] = {
    "expected": ExpectedValueRanking(),
    "var_95": VaRRanking(),
    "cvar_95": CVaRRanking(),
    "roi": ROIRanking(),
}


# ── RankingService ───────────────────────────────────────────────────────


class RankingService:
    """
    Ranks features by various criteria and analyzes risk concentration.

    Responsibilities:
    - Rank features by expected value, VaR, CVaR
    - Calculate risk concentration
    - Identify top/bottom performers
    """

    def __init__(
        self,
        calculator: RiskCalculator | None = None,
        risk_interpreter: RiskInterpreter | None = None,
    ):
        """
        Initialize ranking service.

        Args:
            calculator: RiskCalculator instance (if None, creates new one)
            risk_interpreter: RiskInterpreter for recommendation text (§11.4)
        """
        self.calculator = calculator or RiskCalculator()
        self.risk_interpreter = risk_interpreter or RiskInterpreter()

    def rank_features(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        by: str = "expected",
        strategy: RankingStrategy | None = None,
    ) -> dict[str, Any]:
        """
        Rank features by specified criterion.

        Args:
            features: List of features to rank
            simulation_results: Simulation results for each feature
            by: Ranking criterion (backward-compatible string):
                - "expected": Expected business value (default)
                - "var_95": Value at Risk (95%)
                - "cvar_95": Conditional Value at Risk (95%)
                - "roi": Return on Investment
            strategy: Optional RankingStrategy instance (overrides ``by``)

        Returns:
            Dictionary with:
                - ranking: List of dicts with feature data, sorted descending
                - criterion: Ranking criterion used
        """
        # Resolve strategy: explicit strategy wins over string ``by``
        if strategy is None:
            valid_criteria = tuple(_RANKING_STRATEGIES.keys())
            if by not in valid_criteria:
                raise ValidationError(
                    f"Invalid criterion '{by}'. Valid: {valid_criteria}",
                    field="by",
                    value=by,
                )
            strategy = _RANKING_STRATEGIES[by]

        ranking_data: list[dict[str, Any]] = []
        for feature in features:
            result = simulation_results[feature.name]

            bv = feature.business_value_per_conversion
            expected_conversions = result.expected_value
            var_95_conversions = result.var_95
            expected_business_value = expected_conversions * bv
            var_95_business_value = var_95_conversions * bv
            risk_ratio = self.calculator.calculate_risk_ratio(
                expected_business_value, var_95_business_value, clamp=True
            )

            # §11.4: Delegate recommendation text to RiskInterpreter
            recommendation = self.risk_interpreter.generate_recommendation(risk_ratio)

            ranking_data.append(
                {
                    "feature": feature.name,
                    "expected_business_value": expected_business_value,
                    "var_95_business_value": var_95_business_value,
                    "risk_ratio": risk_ratio,
                    "uncertainty": feature.uncertainty,
                    "recommendation": recommendation,
                    "_sort_value": strategy.sort_key(feature.name, result),
                }
            )

        # Sort descending by strategy sort key
        ranking_data.sort(key=lambda x: float(x["_sort_value"]), reverse=True)

        # Remove internal sort key from output
        for item in ranking_data:
            del item["_sort_value"]

        return {
            "rankings": ranking_data,
            "metadata": {},
        }

    def get_risk_concentration(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
    ) -> dict[str, Any]:
        """
        Analyze risk concentration in the portfolio.

        Answers: "Are we betting everything on one feature?"

        Args:
            features: List of features
            simulation_results: Simulation results for each feature

        Returns:
            Dictionary with:
                - total_expected_business_value: Sum of expected business values
                - feature_contributions: List of features with their contribution %
                - top_3_concentration: % of total business value from top 3 features
                - herfindahl_index: Herfindahl-Hirschman Index (0-1, higher = more concentrated)
        """
        # Calculate total expected business value
        total_expected = sum(
            simulation_results[f.name].expected_business_value for f in features
        )

        # Calculate each feature's contribution
        contributions: list[dict[str, Any]] = []
        for feature in features:
            expected_business_value = simulation_results[
                feature.name
            ].expected_business_value
            contribution_pct = (
                (expected_business_value / total_expected * 100)
                if total_expected > 0
                else 0.0
            )
            contributions.append(
                {
                    "feature_name": feature.name,
                    "expected_business_value": expected_business_value,
                    "contribution_pct": contribution_pct,
                }
            )

        # Sort by contribution descending
        contributions.sort(key=lambda x: float(x["contribution_pct"]), reverse=True)

        # Top 3 concentration
        top_3_concentration = sum(
            float(c["contribution_pct"]) for c in contributions[:3]
        )

        # Herfindahl-Hirschman Index (HHI) via centralized calculator
        shares = [float(c["contribution_pct"]) / 100 for c in contributions]
        hhi = self.calculator.calculate_hhi(shares)

        return {
            "total_expected_business_value": total_expected,
            "feature_contributions": contributions,
            "top_3_concentration": top_3_concentration,
            "herfindahl_index": hhi,
            "concentration_level": self._concentration_level(hhi),
        }

    @staticmethod
    def _concentration_level(hhi: float) -> str:
        """
        Classify concentration level based on HHI.

        Args:
            hhi: Herfindahl-Hirschman Index (0-1)

        Returns:
            Textual classification
        """
        if hhi < 0.15:
            return "Low concentration (diversified portfolio)"
        elif hhi < 0.25:
            return "Moderate concentration"
        else:
            return "High concentration (risky, dominated by few features)"
