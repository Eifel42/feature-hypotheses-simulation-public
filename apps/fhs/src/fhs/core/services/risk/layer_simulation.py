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

"""Risk Layer Simulation Service — Domain Service for risk-layer calculations.

Extracted from AdvancedPortfolioService (Phase 2.1 of DDD Refactoring).
"""

from __future__ import annotations

import numpy as np

from fhs.core.model import (
    Feature,
    FeatureRiskProfile,
    PortfolioPnLLayers,
    PortfolioRiskLayers,
    PortfolioRiskMeta,
    RiskHitRates,
    RiskLayerStats,
    RiskProbabilities,
    ScenarioRiskModel,
    SimulationResult,
)
from fhs.core.model.value_objects.risk_simulation_state import RiskSimulationState
from fhs.core.services.risk.calculator import RiskCalculator
from fhs.core.typing_utils import NDArrayFloat, to_float_array


class RiskLayerSimulationService:
    """Domain Service for simulating risk layers on features and portfolios.

    Responsibilities:
    - Prepare risk simulation state (delivery gates, market/global hits, clusters)
    - Simulate feature-level risk layers (base → risk1 → risk2 → component → risk3)
    - Simulate portfolio-level risk layers
    - Simulate portfolio P&L layers

    All calculations are pure domain logic with no orchestration concerns.
    """

    def __init__(self, risk_calculator: RiskCalculator):
        """Initialize with risk calculator dependency.

        Args:
            risk_calculator: RiskCalculator for VaR/CVaR calculations
        """
        self.risk_calculator = risk_calculator

    @staticmethod
    def _fallback_business_value_draws(
        feature: Feature,
        rng: np.random.Generator,
        n_sim: int,
    ) -> NDArrayFloat:
        """Fallback business value scenarios when no simulation result is available."""
        base = feature.get_base_annual_business_value()  # pragma: no cover - defensive
        std = base * feature.uncertainty  # pragma: no cover - defensive
        draws = rng.normal(
            loc=base, scale=std, size=n_sim
        )  # pragma: no cover - defensive
        return to_float_array(np.clip(draws, 0.0, None))  # pragma: no cover - defensive

    def prepare_year1_state(
        self,
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        risk_model: ScenarioRiskModel,
        rng: np.random.Generator,
    ) -> RiskSimulationState:
        """Prepare simulation state for year-1 risk analysis.

        Consolidates the duplicated risk-model setup code from 3 methods
        (simulate_portfolio_risk_layers, simulate_portfolio_pnl_layers,
        simulate_portfolio_pnl_multi_year).

        Args:
            features: Selected features
            sim_results: Simulation results dict
            risk_model: ScenarioRiskModel with risk probabilities
            rng: NumPy random generator

        Returns:
            RiskSimulationState with delivery gates, hits, and base scenarios
        """
        selected = tuple(f.name for f in features)
        n_sim = next(
            (
                len(result.results_array)
                for feature in features
                if (result := sim_results.get(feature.name)) is not None
                and len(result.results_array) > 0
            ),
            10_000,
        )

        # Normalize risk probabilities
        prob_market = min(0.95, max(0.0, risk_model.risk_2_market_probability))
        prob_global = min(0.95, max(0.0, risk_model.risk_3_global_probability))

        # Generate delivery outcomes: True means delivered in this scenario path
        delivery_gates: dict[str, np.ndarray] = {}
        for f in features:
            llp = min(0.95, max(0.0, float(f.likelihood_of_non_delivery)))
            delivery_gates[f.name] = np.asarray(rng.random(n_sim) >= llp)

        # Generate market and global risk hits
        market_hits = np.asarray(rng.random(n_sim) < prob_market)
        global_hits = np.asarray(rng.random(n_sim) < prob_global)

        # Generate cluster hits
        cluster_hits: dict[str, np.ndarray] = {}
        cluster_probabilities: dict[str, float] = {}
        clusters = {f.dependency_cluster or "Independent" for f in features}
        for cluster in clusters:
            prob_component = float(
                risk_model.component_risk_by_cluster.get(
                    cluster,
                    risk_model.default_component_probability,
                )
            )
            prob_component = min(0.95, max(0.0, prob_component))
            cluster_probabilities[cluster] = prob_component
            cluster_hits[cluster] = np.asarray(rng.random(n_sim) < prob_component)

        # Generate base scenarios (before risk impacts)
        base_scenarios: dict[str, NDArrayFloat] = {}
        for f in features:
            result = sim_results.get(f.name)
            if result is not None and len(result.results_array) > 0:
                values = to_float_array(
                    result.results_array * f.business_value_per_conversion
                )
                if len(values) != n_sim:
                    values = to_float_array(
                        np.resize(values, n_sim)
                    )  # pragma: no cover - defensive
                base_scenarios[f.name] = values
            else:
                base_scenarios[f.name] = (
                    self._fallback_business_value_draws(  # pragma: no cover - defensive
                        f, rng, n_sim
                    )
                )

        return RiskSimulationState(
            selected=selected,
            risk_model=risk_model,
            rng=rng,
            delivery_gates=delivery_gates,
            market_hits=market_hits,
            global_hits=global_hits,
            cluster_hits=cluster_hits,
            base_scenarios=base_scenarios,
            p2=prob_market,
            p3=prob_global,
            cluster_probabilities=cluster_probabilities,
            n_scenarios=n_sim,
        )

    def simulate_feature_layers(
        self,
        feature: Feature,
        sim_result: SimulationResult,
        risk_model: ScenarioRiskModel,
        seed: int = 42,
    ) -> FeatureRiskProfile:
        """Simulate risk layers for a single feature.

        Layers progression:
        1. Base (no risks)
        2. After Risk 1 (Delivery Risk)
        3. After Risk 2 (Market Risk)
        4. After Component Risk
        5. After Risk 3 (Global Crisis)

        Args:
            feature: Feature entity
            sim_result: SimulationResult for this feature
            risk_model: ScenarioRiskModel with risk probabilities
            seed: Random seed

        Returns:
            FeatureRiskProfile with all risk layers
        """
        rng = np.random.default_rng(seed)

        # Get base scenarios
        if len(sim_result.results_array) > 0:
            base = to_float_array(
                sim_result.results_array * feature.business_value_per_conversion
            )
        else:
            base = self._fallback_business_value_draws(
                feature, rng, 10_000
            )  # pragma: no cover - defensive
        n_sim = len(base)

        # Delivery gate scenarios
        delivered = np.asarray(
            rng.random(n_sim)
            >= min(0.95, max(0.0, float(feature.likelihood_of_non_delivery)))
        )

        # Risk 1 — Delivery blocked (probability from risk_model)
        prob_blocked = min(0.95, max(0.0, float(feature.likelihood_of_non_delivery)))
        blocked = ~delivered
        after_risk1 = np.where(np.asarray(blocked), 0.0, base)
        blocked_pct = float(np.mean(np.asarray(blocked)))

        # Risk 2 — Market downturn
        prob_market = min(0.95, max(0.0, risk_model.risk_2_market_probability))
        market_hits = np.asarray(rng.random(n_sim) < prob_market)
        market_multiplier = risk_model.risk_2_market_multiplier
        after_risk2 = np.where(
            np.asarray(market_hits), after_risk1 * market_multiplier, after_risk1
        )
        market_hit_pct = float(np.mean(np.asarray(market_hits)))

        # Component Risk
        cluster = feature.dependency_cluster or "Independent"
        prob_component = min(
            0.95,
            max(
                0.0,
                float(
                    risk_model.component_risk_by_cluster.get(
                        cluster,
                        risk_model.default_component_probability,
                    )
                ),
            ),
        )
        component_hits = np.asarray(rng.random(n_sim) < prob_component)
        component_multiplier = risk_model.component_risk_multiplier
        after_component = np.where(
            np.asarray(component_hits), after_risk2 * component_multiplier, after_risk2
        )
        component_hit_pct = float(np.mean(np.asarray(component_hits)))

        # Risk 3 — Global crisis
        prob_global = min(0.95, max(0.0, risk_model.risk_3_global_probability))
        global_hits = np.asarray(rng.random(n_sim) < prob_global)
        global_multiplier = risk_model.risk_3_global_multiplier
        after_risk3 = np.where(
            np.asarray(global_hits),
            after_component * global_multiplier,
            after_component,
        )
        global_hit_pct = float(np.mean(np.asarray(global_hits)))

        return FeatureRiskProfile(
            feature=feature.name,
            cluster=feature.dependency_cluster or "Independent",
            probabilities=RiskProbabilities(
                risk_1=prob_blocked,
                risk_2=prob_market,
                risk_3=prob_global,
                component=prob_component,
            ),
            base=RiskLayerStats.from_scenarios(base),
            after_risk_1=RiskLayerStats.from_scenarios(after_risk1),
            after_risk_2=RiskLayerStats.from_scenarios(after_risk2),
            after_component=RiskLayerStats.from_scenarios(after_component),
            after_risk_3=RiskLayerStats.from_scenarios(after_risk3),
            hit_rates=RiskHitRates(
                risk_1_blocked_pct=blocked_pct,
                risk_2_hit_pct=market_hit_pct,
                component_hit_pct=component_hit_pct,
                risk_3_hit_pct=global_hit_pct,
            ),
        )

    def all_feature_profiles(
        self,
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        risk_model: ScenarioRiskModel,
        seed: int = 42,
    ) -> dict[str, FeatureRiskProfile]:
        """Simulate risk layer profiles for all features.

        Args:
            features: List of features
            sim_results: Simulation results dict
            risk_model: ScenarioRiskModel
            seed: Random seed

        Returns:
            Dict mapping feature name → FeatureRiskProfile
        """
        profiles = {}
        for i, feature in enumerate(features):
            sim_result = sim_results.get(feature.name)
            if sim_result is None:
                sim_result = SimulationResult(  # pragma: no cover - defensive
                    feature_name=feature.name,
                    results=np.array([], dtype=float),
                    expected_value=0.0,
                    business_value_per_conversion=feature.business_value_per_conversion,
                    development_cost=feature.development_cost,
                )
            assert sim_result is not None
            profiles[feature.name] = self.simulate_feature_layers(
                feature,
                sim_result,
                risk_model,
                seed=seed + i,
            )
        return profiles

    def simulate_portfolio_layers(
        self,
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        risk_model: ScenarioRiskModel,
        seed: int = 42,
    ) -> PortfolioRiskLayers:
        """Simulate portfolio-level risk layers (business value view).

        Args:
            features: Selected features
            sim_results: Simulation results dict
            risk_model: ScenarioRiskModel
            seed: Random seed

        Returns:
            PortfolioRiskLayers with layered risk statistics
        """
        rng = np.random.default_rng(seed)
        state = self.prepare_year1_state(features, sim_results, risk_model, rng)
        delivery_gates = state.delivery_gates
        if not state.selected:
            empty = RiskLayerStats.from_scenarios(
                np.array([], dtype=float)
            )  # pragma: no cover - defensive
            return PortfolioRiskLayers(  # pragma: no cover - defensive
                base=empty,
                after_risk_1=empty,
                after_risk_2=empty,
                after_component=empty,
                after_risk_3=empty,
                meta=PortfolioRiskMeta(
                    market_hit_pct=0.0,
                    global_hit_pct=0.0,
                    cluster_hit_pct={},
                    selected=(),
                    risk_2_probability=0.0,
                    risk_3_probability=0.0,
                ),
            )

        # Base — sum all features
        base = np.sum(
            [to_float_array(state.base_scenarios[name]) for name in state.selected],
            axis=0,
        )

        # After Risk 1 — delivery blocked
        after_risk1_arrays = []
        for name in state.selected:
            delivered = np.asarray(delivery_gates[name])
            after_risk1_arrays.append(
                np.where(delivered, to_float_array(state.base_scenarios[name]), 0.0)
            )
        after_risk1 = np.sum(after_risk1_arrays, axis=0)

        # After Risk 2 — market downturn
        market_multiplier = risk_model.risk_2_market_multiplier
        after_risk2_arrays = []
        for arr in after_risk1_arrays:
            after_risk2_arrays.append(
                np.where(np.asarray(state.market_hits), arr * market_multiplier, arr)
            )
        after_risk2 = np.sum(after_risk2_arrays, axis=0)

        # After Component Risk — cluster failures
        after_component_arrays = []
        feature_by_name = {feature.name: feature for feature in features}
        for idx, name in enumerate(state.selected):
            feature = feature_by_name[name]
            arr = after_risk2_arrays[idx]

            cluster = feature.dependency_cluster or "Independent"
            cluster_hit = np.asarray(state.cluster_hits[cluster])
            arr = np.where(cluster_hit, arr * risk_model.component_risk_multiplier, arr)

            after_component_arrays.append(arr)
        after_component = np.sum(after_component_arrays, axis=0)

        # After Risk 3 — global crisis
        global_multiplier = risk_model.risk_3_global_multiplier
        after_risk3 = np.where(
            np.asarray(state.global_hits),
            after_component * global_multiplier,
            after_component,
        )

        # Calculate metadata
        market_hit_pct = float(np.mean(np.asarray(state.market_hits)))
        global_hit_pct = float(np.mean(np.asarray(state.global_hits)))
        cluster_hit_pcts = {
            cluster: float(np.mean(np.asarray(hits)))
            for cluster, hits in state.cluster_hits.items()
        }

        return PortfolioRiskLayers(
            base=RiskLayerStats.from_scenarios(base),
            after_risk_1=RiskLayerStats.from_scenarios(after_risk1),
            after_risk_2=RiskLayerStats.from_scenarios(after_risk2),
            after_component=RiskLayerStats.from_scenarios(after_component),
            after_risk_3=RiskLayerStats.from_scenarios(after_risk3),
            meta=PortfolioRiskMeta(
                market_hit_pct=market_hit_pct,
                global_hit_pct=global_hit_pct,
                cluster_hit_pct=cluster_hit_pcts,
                selected=state.selected,
                risk_2_probability=risk_model.risk_2_market_probability,
                risk_3_probability=risk_model.risk_3_global_probability,
            ),
        )

    def simulate_portfolio_pnl(
        self,
        features: list[Feature],
        sim_results: dict[str, SimulationResult],
        risk_model: ScenarioRiskModel,
        seed: int = 42,
    ) -> PortfolioPnLLayers:
        """Simulate portfolio P&L layers (net business value - investment).

        Args:
            features: Selected features
            sim_results: Simulation results dict
            risk_model: ScenarioRiskModel
            seed: Random seed

        Returns:
            PortfolioPnLLayers with layered P&L statistics
        """
        # First get business value layers
        business_value_layers = self.simulate_portfolio_layers(
            features, sim_results, risk_model, seed
        )

        # Calculate total investment
        total_investment = sum(float(f.development_cost) for f in features)

        # Convert business value layers to P&L (business value - investment)
        def to_pnl(stats: RiskLayerStats) -> RiskLayerStats:
            return RiskLayerStats(
                expected=stats.expected - total_investment,
                var_95=stats.var_95 - total_investment,
                cvar_95=stats.cvar_95 - total_investment,
                std=stats.std,  # std unchanged (investment is constant)
            )

        return PortfolioPnLLayers(
            base=to_pnl(business_value_layers.base),
            after_risk_1=to_pnl(business_value_layers.after_risk_1),
            after_risk_2=to_pnl(business_value_layers.after_risk_2),
            after_component=to_pnl(business_value_layers.after_component),
            after_risk_3=to_pnl(business_value_layers.after_risk_3),
            meta=business_value_layers.meta,
        )
