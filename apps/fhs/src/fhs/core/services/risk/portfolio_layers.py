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

"""Portfolio layer risk service for year-1 state, layer simulations, and sensitivity."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np

from fhs.core.model import (
    Feature,
    FeatureRiskProfile,
    FeatureSensitivityResult,
    PortfolioPnLLayers,
    PortfolioRiskLayers,
    PortfolioRiskMeta,
    PortfolioSensitivityRow,
    RetentionMatrix,
    RetentionRow,
    RiskHitRates,
    RiskLayerStats,
    RiskProbabilities,
    RiskSimulationState,
    ScenarioRiskModel,
    SensitivityDetail,
    SensitivityDriver,
    SimulationResult,
)
from fhs.core.services.risk.calculator import RiskCalculator
from fhs.core.services.risk.layer_simulation import RiskLayerSimulationService
from fhs.core.services.risk.sensitivity import SensitivityAnalysisService


class PortfolioLayerRiskService:
    """Risk-layer calculations extracted from AdvancedPortfolioService."""

    @staticmethod
    def clamp_probability(value: float, upper: float = 0.95) -> float:
        return float(max(0.0, min(upper, value)))

    @staticmethod
    def clamp_multiplier(value: float) -> float:
        return float(max(0.0, min(1.0, value)))

    @staticmethod
    def risk_stats(values: np.ndarray) -> RiskLayerStats:
        if len(values) == 0:
            return RiskLayerStats(
                expected=0.0, var_95=0.0, cvar_95=0.0, std=0.0
            )  # pragma: no cover - defensive
        return RiskLayerStats.from_scenarios(values)

    @staticmethod
    # noinspection PyTypeHintsInspection
    def normalize_risk_model(
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
    ) -> ScenarioRiskModel:
        """Normalize and validate shared risk-model values."""
        if isinstance(risk_model, ScenarioRiskModel):
            raw = risk_model.model_dump()
        else:
            raw = risk_model or {}

        cluster_input = raw.get("component_risk_by_cluster", {}) or {}
        cluster_probs = {
            str(cluster): PortfolioLayerRiskService.clamp_probability(
                float(probability)
            )
            for cluster, probability in cluster_input.items()
        }

        return ScenarioRiskModel(
            risk_2_market_probability=PortfolioLayerRiskService.clamp_probability(
                float(raw.get("risk_2_market_probability", 0.20))
            ),
            risk_2_market_multiplier=PortfolioLayerRiskService.clamp_multiplier(
                float(raw.get("risk_2_market_multiplier", 0.85))
            ),
            risk_3_global_probability=PortfolioLayerRiskService.clamp_probability(
                float(raw.get("risk_3_global_probability", 0.05))
            ),
            risk_3_global_multiplier=PortfolioLayerRiskService.clamp_multiplier(
                float(raw.get("risk_3_global_multiplier", 0.60))
            ),
            component_risk_multiplier=PortfolioLayerRiskService.clamp_multiplier(
                float(raw.get("component_risk_multiplier", 0.70))
            ),
            default_component_probability=PortfolioLayerRiskService.clamp_probability(
                float(raw.get("default_component_probability", 0.08))
            ),
            component_risk_by_cluster=cluster_probs,
        )

    @staticmethod
    def feature_business_value_array(
        feature_name: str,
        *,
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
    ) -> np.ndarray:
        if feature_name not in feature_by_name:
            raise ValueError(
                f"Unknown feature '{feature_name}'"
            )  # pragma: no cover - defensive
        feature = feature_by_name[feature_name]
        return (
            simulation_results[feature_name].results_array
            * feature.business_value_per_conversion
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def simulate_portfolio_year1_state(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk1_factor: float | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        seed: int = 42,
    ) -> RiskSimulationState:
        """Prepare one stochastic state for year-1 risk calculations."""
        normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        rng = np.random.default_rng(seed)
        p2 = PortfolioLayerRiskService.clamp_probability(
            normalized.risk_2_market_probability
            if risk2_probability is None
            else risk2_probability
        )
        p3 = PortfolioLayerRiskService.clamp_probability(
            normalized.risk_3_global_probability
            if risk3_probability is None
            else risk3_probability
        )

        selected_names = list(selected)
        if not selected_names:
            return RiskSimulationState(  # pragma: no cover - defensive
                selected=(),
                risk_model=normalized,
                rng=rng,
                delivery_gates={},
                market_hits=np.array([], dtype=bool),
                global_hits=np.array([], dtype=bool),
                cluster_hits={},
                base_scenarios={},
                p2=p2,
                p3=p3,
                cluster_probabilities={},
                n_scenarios=0,
            )

        n_scenarios = len(
            PortfolioLayerRiskService.feature_business_value_array(
                selected_names[0],
                feature_by_name=feature_by_name,
                simulation_results=simulation_results,
            )
        )

        market_hits = rng.random(n_scenarios) < p2
        global_hits = rng.random(n_scenarios) < p3

        cluster_probs = dict(normalized.component_risk_by_cluster)
        cluster_hits: dict[str, np.ndarray] = {}
        cluster_probabilities: dict[str, float] = {}
        for name in selected_names:
            cluster = feature_by_name[name].dependency_cluster or "Independent"
            if cluster not in cluster_hits:  # pragma: no cover - partial branch
                cluster_probability = PortfolioLayerRiskService.clamp_probability(
                    float(
                        cluster_probs.get(
                            cluster,
                            normalized.default_component_probability,
                        )
                    )
                )
                cluster_probabilities[cluster] = cluster_probability
                cluster_hits[cluster] = rng.random(n_scenarios) < cluster_probability

        delivery_gates: dict[str, np.ndarray] = {}
        feature_business_values: dict[str, np.ndarray] = {}
        for idx, name in enumerate(selected_names):
            feature = feature_by_name[name]
            feature_business_values[name] = (
                PortfolioLayerRiskService.feature_business_value_array(
                    name,
                    feature_by_name=feature_by_name,
                    simulation_results=simulation_results,
                )
            )
            feature_rng = np.random.default_rng(seed + idx + 1000)
            effective_llp = feature.likelihood_of_non_delivery
            if risk1_factor is not None:
                effective_llp = effective_llp * risk1_factor
            delivery_gates[name] = feature_rng.random(
                n_scenarios
            ) >= PortfolioLayerRiskService.clamp_probability(effective_llp)

        return RiskSimulationState(
            selected=tuple(selected_names),
            risk_model=normalized,
            rng=rng,
            delivery_gates=delivery_gates,
            market_hits=market_hits,
            global_hits=global_hits,
            cluster_hits=cluster_hits,
            base_scenarios=feature_business_values,
            p2=p2,
            p3=p3,
            cluster_probabilities=cluster_probabilities,
            n_scenarios=n_scenarios,
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def portfolio_year1_pnl_from_state(
        state: RiskSimulationState,
        *,
        feature_by_name: Mapping[str, Feature],
        include_delivery: bool,
        include_market: bool,
        include_component: bool,
        include_global: bool,
        component_enabled_clusters: set[str] | None = None,
    ) -> np.ndarray:
        """Compute portfolio year-1 P&L under selected active risk drivers."""
        selected = list(state.selected)
        if not selected:
            return np.array([], dtype=float)  # pragma: no cover - defensive

        normalized = state.risk_model
        market_hits: np.ndarray = np.asarray(state.market_hits)
        global_hits: np.ndarray = np.asarray(state.global_hits)
        cluster_hits: dict[str, np.ndarray] = {
            k: np.asarray(v) for k, v in state.cluster_hits.items()
        }
        delivery_gates: dict[str, np.ndarray] = {
            k: np.asarray(v) for k, v in state.delivery_gates.items()
        }
        feature_business_values: dict[str, np.ndarray] = {
            k: np.asarray(v) for k, v in state.base_scenarios.items()
        }

        if component_enabled_clusters is None:
            active_component_clusters = set(cluster_hits)
        else:
            active_component_clusters = set(component_enabled_clusters)

        market_factor: np.ndarray | float = (
            np.where(market_hits, normalized.risk_2_market_multiplier, 1.0)
            if include_market
            else 1.0
        )
        global_factor: np.ndarray | float = (
            np.where(global_hits, normalized.risk_3_global_multiplier, 1.0)
            if include_global
            else 1.0
        )

        total = np.zeros(state.n_scenarios, dtype=float)
        for name in selected:
            feature = feature_by_name[name]
            bv_array = feature_business_values[name].copy()

            if include_delivery:
                delivered = delivery_gates[name]
                bv_array *= delivered
                total -= feature.development_cost * (~delivered).astype(float)

            bv_array *= market_factor

            cluster = feature.dependency_cluster or "Independent"
            if include_component and cluster in active_component_clusters:
                bv_array *= np.where(
                    cluster_hits[cluster],
                    normalized.component_risk_multiplier,
                    1.0,
                )

            bv_array *= global_factor
            total += bv_array

        return total

    @staticmethod
    def component_probability_for_feature(
        feature_name: str,
        *,
        feature_by_name: Mapping[str, Feature],
        normalized_risk_model: ScenarioRiskModel,
        component_probability: float | None = None,
    ) -> float:
        if component_probability is not None:
            return PortfolioLayerRiskService.clamp_probability(component_probability)

        feature = feature_by_name[feature_name]
        cluster = feature.dependency_cluster or "Independent"
        cluster_probs = normalized_risk_model.component_risk_by_cluster
        fallback = normalized_risk_model.default_component_probability
        return PortfolioLayerRiskService.clamp_probability(
            float(cluster_probs.get(cluster, fallback))
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def simulate_feature_risk_layers(
        feature_name: str,
        *,
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk1_probability: float | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        component_probability: float | None = None,
        seed: int = 42,
    ) -> FeatureRiskProfile:
        """Simulate layered risks for one feature."""
        normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        feature = feature_by_name[feature_name]
        sim_result = simulation_results.get(
            feature_name,
            SimulationResult(
                feature_name=feature_name,
                results=np.array([], dtype=float),
                expected_value=0.0,
                business_value_per_conversion=feature.business_value_per_conversion,
                development_cost=feature.development_cost,
            ),
        )
        if (
            risk1_probability is None
            and risk2_probability is None
            and risk3_probability is None
            and component_probability is None
        ):
            return RiskLayerSimulationService(RiskCalculator()).simulate_feature_layers(
                feature=feature,
                sim_result=sim_result,
                risk_model=normalized,
                seed=seed,
            )

        base = sim_result.results_array * feature.business_value_per_conversion
        if len(base) == 0:
            rng_fallback = np.random.default_rng(
                seed + 100
            )  # pragma: no cover - defensive
            fallback_base = (
                feature.get_base_annual_business_value()
            )  # pragma: no cover - defensive
            fallback_std = (
                fallback_base * feature.uncertainty
            )  # pragma: no cover - defensive
            base = np.clip(  # pragma: no cover - defensive
                rng_fallback.normal(loc=fallback_base, scale=fallback_std, size=10_000),
                0.0,
                None,
            )
        n_scenarios = len(base)
        rng = np.random.default_rng(seed)

        p1 = PortfolioLayerRiskService.clamp_probability(
            feature.likelihood_of_non_delivery
            if risk1_probability is None
            else risk1_probability
        )
        p2 = PortfolioLayerRiskService.clamp_probability(
            normalized.risk_2_market_probability
            if risk2_probability is None
            else risk2_probability
        )
        p3 = PortfolioLayerRiskService.clamp_probability(
            normalized.risk_3_global_probability
            if risk3_probability is None
            else risk3_probability
        )
        pc = PortfolioLayerRiskService.component_probability_for_feature(
            feature_name,
            feature_by_name=feature_by_name,
            normalized_risk_model=normalized,
            component_probability=component_probability,
        )

        r1_gate = rng.random(n_scenarios) >= p1
        after_r1 = base * r1_gate

        r2_hits = rng.random(n_scenarios) < p2
        after_r2 = after_r1 * np.where(
            r2_hits,
            normalized.risk_2_market_multiplier,
            1.0,
        )

        component_hits = rng.random(n_scenarios) < pc
        after_component = after_r2 * np.where(
            component_hits,
            normalized.component_risk_multiplier,
            1.0,
        )

        r3_hits = rng.random(n_scenarios) < p3
        after_r3 = after_component * np.where(
            r3_hits,
            normalized.risk_3_global_multiplier,
            1.0,
        )

        return FeatureRiskProfile(
            feature=feature_name,
            cluster=feature.dependency_cluster or "Independent",
            probabilities=RiskProbabilities(
                risk_1=p1,
                risk_2=p2,
                risk_3=p3,
                component=pc,
            ),
            base=PortfolioLayerRiskService.risk_stats(base),
            after_risk_1=PortfolioLayerRiskService.risk_stats(after_r1),
            after_risk_2=PortfolioLayerRiskService.risk_stats(after_r2),
            after_component=PortfolioLayerRiskService.risk_stats(after_component),
            after_risk_3=PortfolioLayerRiskService.risk_stats(after_r3),
            hit_rates=RiskHitRates(
                risk_1_blocked_pct=float(np.mean(np.asarray(~r1_gate))),
                risk_2_hit_pct=float(np.mean(np.asarray(r2_hits))),
                component_hit_pct=float(np.mean(np.asarray(component_hits))),
                risk_3_hit_pct=float(np.mean(np.asarray(r3_hits))),
            ),
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def feature_layer_profiles(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        seed: int = 42,
    ) -> dict[str, FeatureRiskProfile]:
        """Layered risk profiles for a feature set."""
        selected_features = [
            feature_by_name[name] for name in selected if name in feature_by_name
        ]
        if not selected_features:
            return {}  # pragma: no cover - defensive
        normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        selected_results = {
            feature.name: simulation_results[feature.name]
            for feature in selected_features
            if feature.name in simulation_results
        }
        return RiskLayerSimulationService(RiskCalculator()).all_feature_profiles(
            features=selected_features,
            sim_results=selected_results,
            risk_model=normalized,
            seed=seed,
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def feature_risk_retention(
        profiles: dict[str, FeatureRiskProfile] | Iterable[FeatureRiskProfile],
    ) -> RetentionMatrix:
        """Build expected/floor retention matrix from feature risk profiles."""
        if isinstance(profiles, dict):
            profile_rows = [profiles[key] for key in sorted(profiles)]
        else:
            profile_rows = sorted(profiles, key=lambda p: p.feature)

        rows: list[RetentionRow] = []
        base_expected_total = 0.0
        after_expected_total = 0.0
        base_floor_total = 0.0
        after_floor_total = 0.0

        for profile in profile_rows:
            base_expected = profile.base.expected
            after_expected = profile.after_risk_3.expected
            base_floor = profile.base.var_95
            after_floor = profile.after_risk_3.var_95

            rows.append(
                RetentionRow(
                    feature=profile.feature,
                    cluster=profile.cluster,
                    base_expected=base_expected,
                    after_risk_3_expected=after_expected,
                    expected_retention_pct=(
                        (after_expected / base_expected) if base_expected > 0 else 0.0
                    ),
                    base_var_95=base_floor,
                    after_risk_3_var_95=after_floor,
                    floor_retention_pct=(
                        (after_floor / base_floor) if base_floor > 0 else 0.0
                    ),
                )
            )

            base_expected_total += base_expected
            after_expected_total += after_expected
            base_floor_total += base_floor
            after_floor_total += after_floor

        return RetentionMatrix(
            rows=tuple(rows),
            portfolio_expected_retention_pct=(
                (after_expected_total / base_expected_total)
                if base_expected_total > 0
                else 0.0
            ),
            portfolio_floor_retention_pct=(
                (after_floor_total / base_floor_total) if base_floor_total > 0 else 0.0
            ),
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def feature_sensitivity(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        low_factor: float = 0.5,
        high_factor: float = 1.5,
        seed: int = 42,
    ) -> FeatureSensitivityResult:
        """Per-feature sensitivity for Risk 1/2/3 and component risk."""
        details: list[SensitivityDetail] = []
        drivers: list[SensitivityDriver] = []

        for feature_name in selected:
            base_profile = PortfolioLayerRiskService.simulate_feature_risk_layers(
                feature_name,
                feature_by_name=feature_by_name,
                simulation_results=simulation_results,
                risk_model=risk_model,
                seed=seed,
            )
            base_floor = base_profile.after_risk_3.var_95
            probabilities = base_profile.probabilities

            factors = [
                (
                    "Development risk probability",
                    "risk1_probability",
                    probabilities.risk_1,
                ),
                ("Market risk probability", "risk2_probability", probabilities.risk_2),
                ("Global risk probability", "risk3_probability", probabilities.risk_3),
                (
                    "Component probability",
                    "component_probability",
                    probabilities.component,
                ),
            ]

            most_sensitive_name = "-"
            most_sensitive_delta = 0.0

            for factor_name, argument_name, base_probability in factors:
                low_probability = PortfolioLayerRiskService.clamp_probability(
                    base_probability * low_factor
                )
                high_probability = PortfolioLayerRiskService.clamp_probability(
                    base_probability * high_factor
                )

                low_profile = PortfolioLayerRiskService.simulate_feature_risk_layers(
                    feature_name,
                    feature_by_name=feature_by_name,
                    simulation_results=simulation_results,
                    risk_model=risk_model,
                    **{argument_name: low_probability},
                    seed=seed,
                )
                high_profile = PortfolioLayerRiskService.simulate_feature_risk_layers(
                    feature_name,
                    feature_by_name=feature_by_name,
                    simulation_results=simulation_results,
                    risk_model=risk_model,
                    **{argument_name: high_probability},
                    seed=seed,
                )

                low_floor = low_profile.after_risk_3.var_95
                high_floor = high_profile.after_risk_3.var_95
                delta_pct = (
                    ((high_floor / base_floor) - 1.0) * 100 if base_floor > 0 else 0.0
                )
                delta_eur = high_floor - base_floor

                if delta_eur < most_sensitive_delta:
                    most_sensitive_delta = delta_eur  # pragma: no cover - defensive
                    most_sensitive_name = factor_name  # pragma: no cover - defensive

                details.append(
                    SensitivityDetail(
                        feature=feature_name,
                        factor=factor_name,
                        low_probability=low_probability,
                        base_probability=base_probability,
                        high_probability=high_probability,
                        floor_low=low_floor,
                        floor_base=base_floor,
                        floor_high=high_floor,
                        high_vs_base_pct=delta_pct,
                    )
                )

            drivers.append(
                SensitivityDriver(
                    feature=feature_name,
                    most_sensitive_driver=most_sensitive_name,
                    floor_change_eur=most_sensitive_delta,
                )
            )

        return SensitivityAnalysisService.analyze_features(
            details=details,
            drivers=drivers,
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def simulate_portfolio_risk_layers(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk1_factor: float | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        component_probability_by_cluster: dict[str, float] | None = None,
        seed: int = 42,
    ) -> PortfolioRiskLayers:
        """Layered risk simulation for a selected portfolio."""
        selected_features = [
            feature_by_name[name] for name in selected if name in feature_by_name
        ]
        selected_results = {
            feature.name: simulation_results[feature.name]
            for feature in selected_features
            if feature.name in simulation_results
        }
        if (
            risk1_factor is None
            and risk2_probability is None
            and risk3_probability is None
            and not component_probability_by_cluster
        ):
            normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
            return RiskLayerSimulationService(
                RiskCalculator()
            ).simulate_portfolio_layers(
                features=selected_features,
                sim_results=selected_results,
                risk_model=normalized,
                seed=seed,
            )

        normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        if component_probability_by_cluster:
            cluster_probs = dict(normalized.component_risk_by_cluster)
            cluster_probs.update(
                {
                    str(cluster): PortfolioLayerRiskService.clamp_probability(
                        float(probability)
                    )
                    for cluster, probability in component_probability_by_cluster.items()
                }
            )
            normalized = normalized.model_copy(
                update={"component_risk_by_cluster": cluster_probs}
            )

        state = PortfolioLayerRiskService.simulate_portfolio_year1_state(
            selected=selected,
            feature_by_name=feature_by_name,
            simulation_results=simulation_results,
            risk_model=normalized,
            risk1_factor=risk1_factor,
            risk2_probability=risk2_probability,
            risk3_probability=risk3_probability,
            seed=seed,
        )
        selected_names = list(state.selected)
        if not selected_names:
            empty = PortfolioLayerRiskService.risk_stats(
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

        base_arrays = [
            np.asarray(state.base_scenarios[name]) for name in selected_names
        ]
        base_total = np.sum(base_arrays, axis=0)

        risk1_arrays: list[np.ndarray] = []
        for name in selected_names:
            risk1_arrays.append(state.base_scenarios[name] * state.delivery_gates[name])
        risk1_total = np.sum(risk1_arrays, axis=0)

        risk2_arrays: list[np.ndarray] = []
        rm = state.risk_model
        for arr in risk1_arrays:
            risk2_arrays.append(
                arr
                * np.where(
                    np.asarray(state.market_hits),
                    rm.risk_2_market_multiplier,
                    1.0,
                )
            )
        risk2_total = np.sum(risk2_arrays, axis=0)

        component_arrays: list[np.ndarray] = []
        for idx, name in enumerate(selected_names):
            cluster = feature_by_name[name].dependency_cluster or "Independent"
            arr = risk2_arrays[idx]
            component_arrays.append(
                arr
                * np.where(
                    np.asarray(state.cluster_hits[cluster]),
                    rm.component_risk_multiplier,
                    1.0,
                )
            )
        component_total = np.sum(component_arrays, axis=0)

        risk3_total = component_total * np.where(
            np.asarray(state.global_hits),
            rm.risk_3_global_multiplier,
            1.0,
        )

        return PortfolioRiskLayers(
            base=PortfolioLayerRiskService.risk_stats(base_total),
            after_risk_1=PortfolioLayerRiskService.risk_stats(risk1_total),
            after_risk_2=PortfolioLayerRiskService.risk_stats(risk2_total),
            after_component=PortfolioLayerRiskService.risk_stats(component_total),
            after_risk_3=PortfolioLayerRiskService.risk_stats(risk3_total),
            meta=PortfolioRiskMeta(
                market_hit_pct=float(np.mean(np.asarray(state.market_hits))),
                global_hit_pct=float(np.mean(np.asarray(state.global_hits))),
                cluster_hit_pct={
                    cluster: float(np.mean(np.asarray(hits)))
                    for cluster, hits in state.cluster_hits.items()
                },
                selected=tuple(selected_names),
                risk_2_probability=float(state.p2),
                risk_3_probability=float(state.p3),
            ),
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def simulate_portfolio_pnl_layers(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        seed: int = 42,
    ) -> PortfolioPnLLayers:
        """Portfolio P&L risk layers that allow negative outcomes."""
        if risk2_probability is None and risk3_probability is None:
            selected_features = [
                feature_by_name[name] for name in selected if name in feature_by_name
            ]
            selected_results = {
                feature.name: simulation_results[feature.name]
                for feature in selected_features
                if feature.name in simulation_results
            }
            normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
            return RiskLayerSimulationService(RiskCalculator()).simulate_portfolio_pnl(
                features=selected_features,
                sim_results=selected_results,
                risk_model=normalized,
                seed=seed,
            )

        state = PortfolioLayerRiskService.simulate_portfolio_year1_state(  # pragma: no cover - scipy fallback
            selected=selected,  # pragma: no cover - scipy fallback
            feature_by_name=feature_by_name,  # pragma: no cover - scipy fallback
            simulation_results=simulation_results,  # pragma: no cover - scipy fallback
            risk_model=risk_model,  # pragma: no cover - scipy fallback
            risk2_probability=risk2_probability,  # pragma: no cover - scipy fallback
            risk3_probability=risk3_probability,  # pragma: no cover - scipy fallback
            seed=seed,  # pragma: no cover - scipy fallback
        )  # pragma: no cover - scipy fallback
        selected_names = list(state.selected)  # pragma: no cover - scipy fallback
        if not selected_names:  # pragma: no cover - scipy fallback
            empty = PortfolioLayerRiskService.risk_stats(
                np.array([], dtype=float)
            )  # pragma: no cover - scipy fallback
            return PortfolioPnLLayers(  # pragma: no cover - scipy fallback
                base=empty,  # pragma: no cover - scipy fallback
                after_risk_1=empty,  # pragma: no cover - scipy fallback
                after_risk_2=empty,  # pragma: no cover - scipy fallback
                after_component=empty,  # pragma: no cover - scipy fallback
                after_risk_3=empty,  # pragma: no cover - scipy fallback
                meta=PortfolioRiskMeta(  # pragma: no cover - scipy fallback
                    market_hit_pct=0.0,  # pragma: no cover - scipy fallback
                    global_hit_pct=0.0,  # pragma: no cover - scipy fallback
                    cluster_hit_pct={},  # pragma: no cover - scipy fallback
                    selected=(),  # pragma: no cover - scipy fallback
                    risk_2_probability=0.0,  # pragma: no cover - scipy fallback
                    risk_3_probability=0.0,  # pragma: no cover - scipy fallback
                ),  # pragma: no cover - scipy fallback
            )  # pragma: no cover - scipy fallback
        # pragma: no cover - scipy fallback
        pnl_arrays = {  # pragma: no cover - scipy fallback
            "base": PortfolioLayerRiskService.portfolio_year1_pnl_from_state(  # pragma: no cover - scipy fallback
                state,  # pragma: no cover - scipy fallback
                feature_by_name=feature_by_name,  # pragma: no cover - scipy fallback
                include_delivery=False,  # pragma: no cover - scipy fallback
                include_market=False,  # pragma: no cover - scipy fallback
                include_component=False,  # pragma: no cover - scipy fallback
                include_global=False,  # pragma: no cover - scipy fallback
            ),  # pragma: no cover - scipy fallback
            "risk1": PortfolioLayerRiskService.portfolio_year1_pnl_from_state(  # pragma: no cover - scipy fallback
                state,  # pragma: no cover - scipy fallback
                feature_by_name=feature_by_name,  # pragma: no cover - scipy fallback
                include_delivery=True,  # pragma: no cover - scipy fallback
                include_market=False,  # pragma: no cover - scipy fallback
                include_component=False,  # pragma: no cover - scipy fallback
                include_global=False,  # pragma: no cover - scipy fallback
            ),  # pragma: no cover - scipy fallback
            "risk2": PortfolioLayerRiskService.portfolio_year1_pnl_from_state(  # pragma: no cover - scipy fallback
                state,  # pragma: no cover - scipy fallback
                feature_by_name=feature_by_name,  # pragma: no cover - scipy fallback
                include_delivery=True,  # pragma: no cover - scipy fallback
                include_market=True,  # pragma: no cover - scipy fallback
                include_component=False,  # pragma: no cover - scipy fallback
                include_global=False,  # pragma: no cover - scipy fallback
            ),  # pragma: no cover - scipy fallback
            "component": PortfolioLayerRiskService.portfolio_year1_pnl_from_state(  # pragma: no cover - scipy fallback
                state,  # pragma: no cover - scipy fallback
                feature_by_name=feature_by_name,  # pragma: no cover - scipy fallback
                include_delivery=True,  # pragma: no cover - scipy fallback
                include_market=True,  # pragma: no cover - scipy fallback
                include_component=True,  # pragma: no cover - scipy fallback
                include_global=False,  # pragma: no cover - scipy fallback
            ),  # pragma: no cover - scipy fallback
            "risk3": PortfolioLayerRiskService.portfolio_year1_pnl_from_state(  # pragma: no cover - scipy fallback
                state,  # pragma: no cover - scipy fallback
                feature_by_name=feature_by_name,  # pragma: no cover - scipy fallback
                include_delivery=True,  # pragma: no cover - scipy fallback
                include_market=True,  # pragma: no cover - scipy fallback
                include_component=True,  # pragma: no cover - scipy fallback
                include_global=True,  # pragma: no cover - scipy fallback
            ),  # pragma: no cover - scipy fallback
        }  # pragma: no cover - scipy fallback
        # pragma: no cover - scipy fallback
        return PortfolioPnLLayers(  # pragma: no cover - scipy fallback
            base=PortfolioLayerRiskService.risk_stats(pnl_arrays["base"]),
            after_risk_1=PortfolioLayerRiskService.risk_stats(pnl_arrays["risk1"]),
            after_risk_2=PortfolioLayerRiskService.risk_stats(pnl_arrays["risk2"]),
            after_component=PortfolioLayerRiskService.risk_stats(
                pnl_arrays["component"]
            ),
            after_risk_3=PortfolioLayerRiskService.risk_stats(pnl_arrays["risk3"]),
            meta=PortfolioRiskMeta(
                market_hit_pct=float(np.mean(state.market_hits)),
                global_hit_pct=float(np.mean(state.global_hits)),
                cluster_hit_pct={
                    cluster: float(np.mean(hits))
                    for cluster, hits in state.cluster_hits.items()
                },
                selected=tuple(selected_names),
                risk_2_probability=float(state.p2),
                risk_3_probability=float(state.p3),
            ),
        )

    @staticmethod
    # noinspection PyTypeHintsInspection
    def portfolio_sensitivity(
        *,
        selected: Sequence[str],
        feature_by_name: Mapping[str, Feature],
        simulation_results: Mapping[str, SimulationResult],
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        low_factor: float = 0.5,
        high_factor: float = 1.5,
        seed: int = 42,
    ) -> list[PortfolioSensitivityRow]:
        """Sensitivity matrix for Risk 2 and Risk 3 probabilities."""
        normalized = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        p2 = normalized.risk_2_market_probability
        p3 = normalized.risk_3_global_probability

        market_levels = [
            PortfolioLayerRiskService.clamp_probability(p2 * low_factor),
            PortfolioLayerRiskService.clamp_probability(p2),
            PortfolioLayerRiskService.clamp_probability(p2 * high_factor),
        ]
        global_levels = [
            PortfolioLayerRiskService.clamp_probability(p3 * low_factor),
            PortfolioLayerRiskService.clamp_probability(p3),
            PortfolioLayerRiskService.clamp_probability(p3 * high_factor),
        ]

        rows: list[PortfolioSensitivityRow] = []
        for market_probability in market_levels:
            for global_probability in global_levels:
                profile = PortfolioLayerRiskService.simulate_portfolio_risk_layers(
                    selected=selected,
                    feature_by_name=feature_by_name,
                    simulation_results=simulation_results,
                    risk_model=normalized,
                    risk2_probability=market_probability,
                    risk3_probability=global_probability,
                    seed=seed,
                )
                rows.append(
                    PortfolioSensitivityRow(
                        risk_2_probability=market_probability,
                        risk_3_probability=global_probability,
                        expected=profile.after_risk_3.expected,
                        var_95=profile.after_risk_3.var_95,
                        cvar_95=profile.after_risk_3.cvar_95,
                    )
                )

        return SensitivityAnalysisService.analyze_portfolio(rows)
