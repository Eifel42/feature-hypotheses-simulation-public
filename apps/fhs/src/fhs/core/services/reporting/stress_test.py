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

"""Bundled risk stress testing and executive summary generation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

import numpy as np

from ...model import Feature, SimulationResult
from ..portfolio import aggregate_portfolio_scenarios_from_results
from ..risk import RiskCalculator


class BundledRiskStressTest:
    """Calculates bundled risk stress test (50% cluster reduction)."""

    def __init__(self, calculator: RiskCalculator | None = None):
        self.calculator = calculator or RiskCalculator()

    @staticmethod
    def _cluster_mapping(features: list[Feature]) -> dict[str, list[str]]:
        clusters: dict[str, list[str]] = {}
        for feature in features:
            cluster = feature.dependency_cluster or "Independent"
            clusters.setdefault(cluster, []).append(feature.name)
        return clusters

    @staticmethod
    def _stressed_result(result: SimulationResult) -> SimulationResult:
        stressed_arr = result.results_array * 0.5
        return SimulationResult(
            feature_name=result.feature_name,
            results=stressed_arr,
            scenarios=len(stressed_arr),
            expected_value=result.expected_value * 0.5,
            business_value_per_conversion=result.business_value_per_conversion,
            development_cost=result.development_cost,
        )

    def calculate(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
    ) -> dict[str, Any]:
        """
        Stress test: all features in same cluster reduced to 50%.

        Returns:
            Dictionary with stress test results per cluster.
        """
        clusters = self._cluster_mapping(features)

        baseline_scenarios = aggregate_portfolio_scenarios_from_results(
            simulation_results
        )
        baseline_expected = float(np.mean(baseline_scenarios))
        baseline_var95 = self.calculator.calculate_var(baseline_scenarios, 0.95)

        cluster_impacts = {}
        for cluster, feature_names in clusters.items():
            if cluster == "Independent":
                continue

            stressed_results = {}
            for name, result in simulation_results.items():
                if name in feature_names:
                    stressed_results[name] = self._stressed_result(result)
                else:
                    stressed_results[name] = result

            stressed_scenarios = aggregate_portfolio_scenarios_from_results(
                stressed_results
            )
            stressed_expected = float(np.mean(stressed_scenarios))

            cluster_impacts[cluster] = {
                "affected_features": feature_names,
                "expected_change": stressed_expected - baseline_expected,
                "expected_change_pct": (
                    (stressed_expected / baseline_expected - 1) * 100
                    if baseline_expected != 0
                    else 0
                ),
            }

        worst_cluster = None
        if cluster_impacts:  # pragma: no cover - partial branch
            worst_cluster = min(
                cluster_impacts.items(),
                key=lambda x: cast(float, x[1]["expected_change"]),
            )[0]

        return {
            "baseline": {"expected": baseline_expected, "var_95": baseline_var95},
            "cluster_impacts": cluster_impacts,
            "worst_cluster": worst_cluster,
        }


class ExecutiveSummaryBuilder:
    """Builds executive summary from various analysis results."""

    def __init__(self, calculator: RiskCalculator | None = None):
        self.calculator = calculator or RiskCalculator()

    # noinspection PyTypeHintsInspection
    def build(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        ranking_result: dict[str, Any],
        concentration: dict[str, Any],
        stress_crash: dict[str, Any],
        stress_failure: dict[str, Any],
        metadata: dict[str, Any],
        correlation_matrix: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Generate a comprehensive executive summary."""
        ranking = ranking_result["rankings"]

        portfolio_scenarios = aggregate_portfolio_scenarios_from_results(
            simulation_results
        )
        total_expected = float(np.mean(portfolio_scenarios))
        total_var = self.calculator.calculate_var(portfolio_scenarios, 0.95)

        ranking_by_risk = sorted(ranking, key=lambda x: x["risk_ratio"], reverse=True)

        methodology_warnings: list[str] = []
        if correlation_matrix is None:  # pragma: no cover - partial branch
            methodology_warnings.append(
                "Features are simulated independently (uncorrelated). "
                "This overstates diversification benefits. "
                "Provide a correlation_matrix for realistic portfolio risk."
            )

        return {
            "portfolio": {
                "total_expected_business_value": total_expected,
                "portfolio_var_95": total_var,
                "portfolio_risk_ratio": self.calculator.calculate_risk_ratio(
                    total_expected, total_var, clamp=True
                ),
                "n_features": len(features),
            },
            "feature_ranking": ranking,
            "highest_value_feature": ranking[0]["feature"] if ranking else None,
            "highest_risk_feature": (
                ranking_by_risk[0]["feature"] if ranking_by_risk else None
            ),
            "concentration": {
                "is_concentrated": concentration["is_concentrated"],
                "hhi": concentration["hhi"],
                "warnings": concentration["warnings"],
            },
            "stress_tests": {
                "market_crash": stress_crash,
                "feature_failure": stress_failure,
            },
            "methodology_warnings": methodology_warnings,
            "metadata": metadata,
        }


class RunMetadataBuilder:
    """Generates run metadata for transparency and reproducibility."""

    @staticmethod
    def build(
        features: list[Feature],
        scenarios: int,
        distribution: str,
        correlation_source: str,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate metadata dict."""
        independent_count = sum(1 for f in features if not f.dependency_cluster)
        independent_pct = (independent_count / len(features)) * 100 if features else 0

        metadata = {
            "distribution": distribution,
            "scenarios": scenarios,
            "correlation_source": correlation_source,
            "seed": seed,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "n_features": len(features),
            "independent_features_count": independent_count,
            "independent_features_pct": independent_pct,
        }

        if independent_pct > 30:  # pragma: no cover - partial branch
            metadata["diversification_warning"] = (
                f"{independent_pct:.0f}% of features are simulated independently. "
                f"This may overstate diversification benefits. "
                f"Consider assigning dependency_cluster attributes."
            )

        if correlation_source == "clusters":
            metadata["correlation_note"] = (  # pragma: no cover - defensive
                "Diversification calculated with cluster correlation"
            )

        return metadata
