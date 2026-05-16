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

"""Risk attribution orchestration service for portfolio-level loss/component views."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

import numpy as np

from fhs.core.model import (
    ComponentRiskResult,
    Feature,
    LossMetrics,
    RiskFactorShapley,
    ScenarioRiskModel,
    SimulationResult,
)
from fhs.core.services.risk.component_risk import ComponentRiskService
from fhs.core.services.risk.loss_metrics import LossMetricsService
from fhs.core.services.risk.portfolio_layers import PortfolioLayerRiskService
from fhs.core.services.risk.shapley import ShapleyAttributionService


class PortfolioRiskAttributionService:
    """Orchestrate portfolio loss and component risk attribution outputs."""

    @staticmethod
    # noinspection PyTypeHintsInspection
    def loss_metrics(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        confidence: float = 0.95,
        seed: int = 42,
        normalize_confidence: Callable[[float], float],
        loss_profile_function: Callable[[np.ndarray, float], Any],
    ) -> LossMetrics:
        """Year-1 loss-space metrics with catastrophe decomposition."""
        state = PortfolioLayerRiskService.simulate_portfolio_year1_state(
            selected=selected,
            feature_by_name=feature_by_name,
            simulation_results=simulation_results,
            risk_model=risk_model,
            seed=seed,
        )

        alpha = normalize_confidence(confidence)
        selected_names = list(state.selected)
        delivery_gates = cast(Mapping[str, np.ndarray], state.delivery_gates)

        return LossMetricsService.from_subset_pnl_function(
            selected=selected_names,
            delivery_gates=delivery_gates,
            development_cost_by_feature={
                name: float(feature_by_name[name].development_cost)
                for name in selected_names
            },
            pnl_function=lambda: (
                PortfolioLayerRiskService.portfolio_year1_pnl_from_state(
                    state,
                    feature_by_name=feature_by_name,
                    include_delivery=True,
                    include_market=True,
                    include_component=True,
                    include_global=True,
                )
            ),
            loss_profile_function=loss_profile_function,
            confidence=alpha,
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def risk_contributions_shapley(
        *,
        metric: str,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        confidence: float = 0.95,
        seed: int = 42,
        normalize_confidence: Callable[[float], float],
        loss_profile_function: Callable[[np.ndarray, float], Any],
    ) -> RiskFactorShapley:
        """Shapley risk attribution on year-1 loss metrics."""
        state = PortfolioLayerRiskService.simulate_portfolio_year1_state(
            selected=selected,
            feature_by_name=feature_by_name,
            simulation_results=simulation_results,
            risk_model=risk_model,
            seed=seed,
        )
        selected_names = list(state.selected)

        alpha = normalize_confidence(confidence)
        if not selected_names:
            return RiskFactorShapley(  # pragma: no cover - defensive
                metric=metric,
                confidence=alpha,
                selected=(),
                baseline_value_eur=0.0,
                full_value_eur=0.0,
                total_risk_eur=0.0,
                contributions=(),
                interaction_residual_eur=0.0,
                subset_values_eur={"none": 0.0},
            )

        def value_function(subset: frozenset[str]) -> float:
            pnl = PortfolioLayerRiskService.portfolio_year1_pnl_from_state(
                state,
                feature_by_name=feature_by_name,
                include_delivery="delivery" in subset,
                include_market="market" in subset,
                include_component="component" in subset,
                include_global="global" in subset,
            )
            profile = loss_profile_function(pnl, alpha)

            if metric == "expected_loss":
                return float(profile.loss_expected)  # pragma: no cover - defensive
            if metric == "var_loss":
                return float(profile.loss_var)  # pragma: no cover - defensive
            return float(profile.loss_cvar)

        return ShapleyAttributionService.attribute_from_subset_value_function(
            metric=metric,
            selected=selected_names,
            value_function=value_function,
            confidence=alpha,
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def component_risk_simulated(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        confidence: float = 0.95,
        seed: int = 42,
        normalize_confidence: Callable[[float], float],
    ) -> ComponentRiskResult:
        """Simulation-based component risk metrics with counterfactual losses."""
        state = PortfolioLayerRiskService.simulate_portfolio_year1_state(
            selected=selected,
            feature_by_name=feature_by_name,
            simulation_results=simulation_results,
            risk_model=risk_model,
            seed=seed,
        )
        selected_names = list(state.selected)
        alpha = normalize_confidence(confidence)
        feature_cluster_by_name = {
            name: feature_by_name[name].dependency_cluster or "Independent"
            for name in selected_names
        }

        def component_pnl(
            include_component: bool,
            component_enabled_clusters: set[str] | None,
        ) -> np.ndarray:
            return PortfolioLayerRiskService.portfolio_year1_pnl_from_state(
                state,
                feature_by_name=feature_by_name,
                include_delivery=True,
                include_market=True,
                include_component=include_component,
                include_global=True,
                component_enabled_clusters=component_enabled_clusters,
            )

        return ComponentRiskService.simulated_from_component_pnl_function(
            selected=selected_names,
            cluster_hits=state.cluster_hits,
            cluster_probabilities=state.cluster_probabilities,
            feature_cluster_by_name=feature_cluster_by_name,
            pnl_function=component_pnl,
            confidence=alpha,
        )

    @staticmethod
    def portfolio_component_risk_summary(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        normalized_risk_model: ScenarioRiskModel,
        clamp_probability: Callable[[float], float],
    ) -> ComponentRiskResult:
        """Named portfolio-level component risk metrics."""
        cluster_probs = normalized_risk_model.component_risk_by_cluster
        multiplier = normalized_risk_model.component_risk_multiplier
        fallback = normalized_risk_model.default_component_probability

        feature_cluster_by_name = {
            name: feature_by_name[name].dependency_cluster or "Independent"
            for name in selected
        }
        active_clusters = sorted(set(feature_cluster_by_name.values()))
        cluster_probabilities = {
            cluster: clamp_probability(float(cluster_probs.get(cluster, fallback)))
            for cluster in active_clusters
        }

        def cluster_business_value(
            _cluster: str,
            feat_names: tuple[str, ...],
        ) -> tuple[float, float]:
            business_value = float(
                sum(
                    float(simulation_results[name].expected_business_value)
                    for name in feat_names
                )
            )
            return business_value, business_value

        return ComponentRiskService.analytical_from_cluster_business_value_function(
            selected=selected,
            feature_cluster_by_name=feature_cluster_by_name,
            cluster_probabilities=cluster_probabilities,
            cluster_business_value_function=cluster_business_value,
            expected_loss_multiplier=(1.0 - multiplier),
            confidence=0.95,
        )

    @staticmethod
    def portfolio_component_risk_summary_multi_year(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        normalized_risk_model: ScenarioRiskModel,
        cluster_business_value_function: Callable[
            [tuple[str, ...]], tuple[float, float]
        ],
        clamp_probability: Callable[[float], float],
    ) -> ComponentRiskResult:
        """Named component risk metrics across a multi-year horizon."""
        cluster_probs = normalized_risk_model.component_risk_by_cluster
        multiplier = normalized_risk_model.component_risk_multiplier
        fallback = normalized_risk_model.default_component_probability

        feature_cluster_by_name = {
            name: feature_by_name[name].dependency_cluster or "Independent"
            for name in selected
        }
        active_clusters = sorted(set(feature_cluster_by_name.values()))
        cluster_probabilities = {
            cluster: clamp_probability(float(cluster_probs.get(cluster, fallback)))
            for cluster in active_clusters
        }

        def cluster_business_value(
            _cluster: str,
            feat_names: tuple[str, ...],
        ) -> tuple[float, float]:
            return cluster_business_value_function(feat_names)

        return ComponentRiskService.analytical_from_cluster_business_value_function(
            selected=selected,
            feature_cluster_by_name=feature_cluster_by_name,
            cluster_probabilities=cluster_probabilities,
            cluster_business_value_function=cluster_business_value,
            expected_loss_multiplier=(1.0 - multiplier),
            var_loss_multiplier=(1.0 - multiplier),
            confidence=0.95,
        )
