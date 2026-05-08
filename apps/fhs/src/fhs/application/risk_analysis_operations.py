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

"""Risk attribution, loss metrics, and Shapley analysis operations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fhs.application.portfolio_context import PortfolioContext
from fhs.core.model import (
    ComponentRiskResult,
    LossMetrics,
    RiskFactorShapley,
    ScenarioRiskModel,
)
from fhs.core.services import RiskCalculator
from fhs.core.services.risk import (
    PortfolioLayerRiskService,
    PortfolioRiskAttributionService,
)


class RiskAnalysisOperations:
    """Risk attribution, loss metrics, and Shapley analysis with explicit context."""

    def __init__(self, context: PortfolioContext):
        self._context = context
        self._risk_calculator = RiskCalculator()

    @staticmethod
    def _normalize_confidence(confidence: float) -> float:
        """Clamp confidence level to a numerically stable range."""
        return float(max(0.5, min(0.999, confidence)))

    @staticmethod
    def _clamp_probability(value: float, upper: float = 0.95) -> float:
        return PortfolioLayerRiskService.clamp_probability(value, upper=upper)

    # noinspection PyTypeHintsInspection
    def loss_metrics(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        confidence: float = 0.95,
        seed: int = 42,
    ) -> LossMetrics:
        """Year-1 loss-space metrics with explicit catastrophe decomposition."""
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioRiskAttributionService.loss_metrics(
            selected=self._context.resolve_names(feature_names),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            confidence=confidence,
            seed=seed,
            normalize_confidence=self._normalize_confidence,
            loss_profile_function=lambda pnl, conf: self._risk_calculator.loss_profile(
                pnl, confidence=conf
            ),
        )

    # noinspection PyTypeHintsInspection
    def shapley_attribution(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        confidence: float = 0.95,
        metric: str = "cvar_loss",
        seed: int = 42,
    ) -> RiskFactorShapley:
        """Shapley risk attribution on year-1 loss metrics.

        Uses common random numbers across all counterfactual subsets so each
        contribution is comparable and noise-stable.
        """
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioRiskAttributionService.risk_contributions_shapley(
            metric=metric,
            selected=self._context.resolve_names(feature_names),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            confidence=confidence,
            seed=seed,
            normalize_confidence=self._normalize_confidence,
            loss_profile_function=lambda pnl, conf: self._risk_calculator.loss_profile(
                pnl, confidence=conf
            ),
        )

    # noinspection PyTypeHintsInspection
    def component_simulated(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        confidence: float = 0.95,
        seed: int = 42,
    ) -> ComponentRiskResult:
        """Simulation-based component risk metrics with counterfactual losses."""
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioRiskAttributionService.component_risk_simulated(
            selected=self._context.resolve_names(feature_names),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            confidence=confidence,
            seed=seed,
            normalize_confidence=self._normalize_confidence,
        )

    # noinspection PyTypeHintsInspection
    def component_summary(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
    ) -> ComponentRiskResult:
        """Named portfolio-level component risk metrics.

        Computes:
        - Per-cluster component failure probability and expected business value loss.
        - **Portfolio component probability**: P(≥1 cluster fails) =
          ``1 − ∏(1 − p_cluster)`` across all active clusters.
        - Total expected business value loss from component risks across the portfolio.

        This metric names the combined dependency-chain risk that individual
        cluster analyses present separately.
        """
        selected = self._context.resolve_names(feature_names)
        feature_by_name = {f.name: f for f in self._context.features}
        normalized_risk_model = PortfolioLayerRiskService.normalize_risk_model(
            risk_model
        )
        return PortfolioRiskAttributionService.portfolio_component_risk_summary(
            selected=selected,
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            normalized_risk_model=normalized_risk_model,
            clamp_probability=self._clamp_probability,
        )
