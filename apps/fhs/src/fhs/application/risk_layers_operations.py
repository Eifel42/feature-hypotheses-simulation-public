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

"""Risk-layer operations with explicit portfolio context."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from fhs.application.portfolio_context import PortfolioContext
from fhs.core.model import (
    FeatureRiskProfile,
    FeatureSensitivityResult,
    PortfolioPnLLayers,
    PortfolioRiskLayers,
    PortfolioSensitivityRow,
    RetentionMatrix,
    ScenarioRiskModel,
)
from fhs.core.services.risk import PortfolioLayerRiskService


@dataclass(frozen=True)
class FeatureRiskLayerTables:
    """Tabular notebook-ready representation of feature risk layers."""

    expected_headers: tuple[str, ...]
    expected_rows: tuple[tuple[str, ...], ...]
    prob_headers: tuple[str, ...]
    probability_rows: tuple[tuple[str, ...], ...]
    retention_headers: tuple[str, ...]
    retention_rows: tuple[tuple[str, ...], ...]


class RiskLayersOperations:
    """Composed risk-layer operations with explicit context dependency."""

    def __init__(self, context: PortfolioContext):
        self._context = context

    # noinspection PyTypeHintsInspection
    def simulate_feature_risk_layers(
        self,
        feature_name: str,
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk1_probability: float | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        component_probability: float | None = None,
        seed: int = 42,
    ) -> FeatureRiskProfile:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioLayerRiskService.simulate_feature_risk_layers(
            feature_name,
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            risk1_probability=risk1_probability,
            risk2_probability=risk2_probability,
            risk3_probability=risk3_probability,
            component_probability=component_probability,
            seed=seed,
        )

    # noinspection PyTypeHintsInspection
    def feature_layer_profiles(
        self,
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        feature_names: Iterable[str] | None = None,
        seed: int = 42,
    ) -> dict[str, FeatureRiskProfile]:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioLayerRiskService.feature_layer_profiles(
            selected=sorted(self._context.resolve_names(feature_names)),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            seed=seed,
        )

    @staticmethod
    def feature_risk_retention(
        profiles: dict[str, FeatureRiskProfile] | Iterable[FeatureRiskProfile],
    ) -> RetentionMatrix:
        return PortfolioLayerRiskService.feature_risk_retention(profiles)

    @staticmethod
    def feature_risk_layer_tables(
        profiles: dict[str, FeatureRiskProfile] | Iterable[FeatureRiskProfile],
    ) -> FeatureRiskLayerTables:
        if isinstance(profiles, dict):
            ordered_profiles = [profiles[name] for name in sorted(profiles)]
        else:
            ordered_profiles = sorted(
                profiles, key=lambda profile: profile.feature
            )  # pragma: no cover - defensive

        expected_rows = tuple(
            (
                profile.feature.split(": ", 1)[-1],
                f"EUR {profile.base.expected:,.0f}",
                f"EUR {profile.after_risk_1.expected:,.0f}",
                f"EUR {profile.after_risk_2.expected:,.0f}",
                f"EUR {profile.after_component.expected:,.0f}",
                f"EUR {profile.after_risk_3.expected:,.0f}",
            )
            for profile in ordered_profiles
        )

        probability_rows = tuple(
            (
                profile.feature.split(": ", 1)[-1],
                profile.cluster,
                f"{profile.probabilities.risk_1:.0%}",
                f"{profile.hit_rates.risk_1_blocked_pct:.1%}",
                f"{profile.probabilities.risk_2:.0%}",
                f"{profile.probabilities.component:.0%}",
                f"{profile.probabilities.risk_3:.0%}",
            )
            for profile in ordered_profiles
        )

        retention = PortfolioLayerRiskService.feature_risk_retention(ordered_profiles)
        retention_rows = tuple(
            (
                row.feature.split(": ", 1)[-1],
                f"{row.expected_retention_pct * 100:.1f}%",
                f"EUR {row.after_risk_3_expected - row.base_expected:,.0f}",
            )
            for row in retention.rows
        )

        return FeatureRiskLayerTables(
            expected_headers=(
                "Feature",
                "Base",
                "After Delivery",
                "After Market",
                "After Component",
                "After Global",
            ),
            expected_rows=expected_rows,
            prob_headers=(
                "Feature",
                "Cluster",
                "Delivery LLP",
                "Blocked %",
                "Market Prob",
                "Component Prob",
                "Global Prob",
            ),
            probability_rows=probability_rows,
            retention_headers=(
                "Feature",
                "Business value retained (Base → After Global)",
                "Expected value delta (EUR)",
            ),
            retention_rows=retention_rows,
        )

    # noinspection PyTypeHintsInspection
    def feature_sensitivity(
        self,
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        feature_names: Iterable[str] | None = None,
        low_factor: float = 0.5,
        high_factor: float = 1.5,
        seed: int = 42,
    ) -> FeatureSensitivityResult:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioLayerRiskService.feature_sensitivity(
            selected=sorted(self._context.resolve_names(feature_names)),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            low_factor=low_factor,
            high_factor=high_factor,
            seed=seed,
        )

    # noinspection PyTypeHintsInspection
    def simulate_portfolio_risk_layers(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk1_factor: float | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        component_probability_by_cluster: dict[str, float] | None = None,
        seed: int = 42,
    ) -> PortfolioRiskLayers:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioLayerRiskService.simulate_portfolio_risk_layers(
            selected=self._context.resolve_names(feature_names),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            risk1_factor=risk1_factor,
            risk2_probability=risk2_probability,
            risk3_probability=risk3_probability,
            component_probability_by_cluster=component_probability_by_cluster,
            seed=seed,
        )

    # noinspection PyTypeHintsInspection
    def simulate_portfolio_pnl_layers(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        risk2_probability: float | None = None,
        risk3_probability: float | None = None,
        seed: int = 42,
    ) -> PortfolioPnLLayers:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioLayerRiskService.simulate_portfolio_pnl_layers(
            selected=self._context.resolve_names(feature_names),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            risk2_probability=risk2_probability,
            risk3_probability=risk3_probability,
            seed=seed,
        )

    # noinspection PyTypeHintsInspection
    def portfolio_sensitivity(
        self,
        feature_names: Iterable[str],
        *,
        risk_model: ScenarioRiskModel | dict[str, Any] | None = None,
        low_factor: float = 0.5,
        high_factor: float = 1.5,
        seed: int = 42,
    ) -> list[PortfolioSensitivityRow]:
        feature_by_name = {f.name: f for f in self._context.features}
        return PortfolioLayerRiskService.portfolio_sensitivity(
            selected=self._context.resolve_names(feature_names),
            feature_by_name=feature_by_name,
            simulation_results=self._context.simulation_results,
            risk_model=risk_model,
            low_factor=low_factor,
            high_factor=high_factor,
            seed=seed,
        )

    @staticmethod
    def _probability_sensitivity_rows(
        sensitivity_results: Mapping[float, PortfolioRiskLayers],
        *,
        levels: Iterable[float] | None = None,
        probability_format: str = ".0%",
    ) -> list[tuple[str, str]]:
        ordered_levels = (
            list(levels) if levels is not None else sorted(sensitivity_results)
        )
        return [
            (
                format(probability, probability_format),
                f"EUR {sensitivity_results[probability].after_risk_3.expected:,.0f}",
            )
            for probability in ordered_levels
        ]

    @staticmethod
    def market_sensitivity_rows(
        sensitivity_results: Mapping[float, PortfolioRiskLayers],
        *,
        levels: Iterable[float] | None = None,
    ) -> list[tuple[str, str]]:
        """Notebook-ready rows for market-probability sensitivity tables."""
        return RiskLayersOperations._probability_sensitivity_rows(
            sensitivity_results,
            levels=levels,
            probability_format=".0%",
        )

    @staticmethod
    def global_sensitivity_rows(
        sensitivity_results: Mapping[float, PortfolioRiskLayers],
        *,
        levels: Iterable[float] | None = None,
    ) -> list[tuple[str, str]]:
        """Notebook-ready rows for global-probability sensitivity tables."""
        return RiskLayersOperations._probability_sensitivity_rows(
            sensitivity_results,
            levels=levels,
            probability_format=".1%",
        )

    @staticmethod
    def component_sensitivity_rows(
        comp_expected: dict[str, list[tuple[float, float]]],
        factor_labels: Iterable[str] | None = None,
    ) -> list[tuple[str, ...]]:
        """Notebook-ready rows for cluster-level component sensitivity."""
        labels = tuple(
            factor_labels or ("x0.5 (low risk)", "x1.0 (base)", "x1.5 (high risk)")
        )
        rows: list[tuple[str, ...]] = []
        for cluster_name, points in sorted(comp_expected.items()):
            for (test_prob, expected), label in zip(points, labels, strict=False):
                rows.append(
                    (
                        cluster_name,
                        f"{test_prob:.0%} ({label})",
                        f"EUR {expected:,.0f}",
                    )
                )
        return rows
