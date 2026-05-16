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

"""Component risk domain service."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

import numpy as np

from fhs.core.model.value_objects import ClusterRisk, ComponentRiskResult

CONFIDENCE_ERROR = "Confidence must be between 0 and 1."


def _to_float(value: object, default: float = 0.0) -> float:
    """Safe float narrowing for loosely typed payload values."""
    if isinstance(value, int | float):
        return float(value)
    return default  # pragma: no cover - defensive


class ComponentRiskService:
    """Construct component-risk summaries from precomputed cluster metrics."""

    @staticmethod
    def simulate(
        *,
        selected: Iterable[str],
        cluster_payload: dict[str, dict[str, object]],
        confidence: float = 0.95,
    ) -> ComponentRiskResult:
        """Create a typed ComponentRiskResult from cluster-level payload data."""
        if not 0.0 < confidence < 1.0:
            raise ValueError(CONFIDENCE_ERROR)  # pragma: no cover - defensive

        cluster_risks: list[ClusterRisk] = []
        analytical_no_hit = 1.0
        simulated_no_hit = 1.0

        for cluster, payload in cluster_payload.items():
            configured_probability = _to_float(
                payload.get("configured_probability", 0.0)
            )
            simulated_probability = _to_float(payload.get("simulated_probability", 0.0))
            expected_incremental_loss_eur = _to_float(
                payload.get("expected_incremental_loss_eur", 0.0)
            )
            var_incremental_loss_eur = _to_float(
                payload.get("var_incremental_loss_eur", 0.0)
            )
            cvar_incremental_loss_eur = _to_float(
                payload.get("cvar_incremental_loss_eur", 0.0)
            )
            features_raw = payload.get("features", ())
            features = (
                tuple(features_raw) if isinstance(features_raw, list | tuple) else ()
            )

            cluster_risks.append(
                ClusterRisk(
                    cluster=cluster,
                    features=features,
                    configured_probability=configured_probability,
                    simulated_probability=simulated_probability,
                    expected_incremental_loss_eur=expected_incremental_loss_eur,
                    var_incremental_loss_eur=var_incremental_loss_eur,
                    cvar_incremental_loss_eur=cvar_incremental_loss_eur,
                )
            )

            analytical_no_hit *= 1.0 - configured_probability
            simulated_no_hit *= 1.0 - simulated_probability

        portfolio_component_probability_analytical = 1.0 - analytical_no_hit
        portfolio_component_probability = 1.0 - simulated_no_hit

        expected_total = float(
            sum(r.expected_incremental_loss_eur for r in cluster_risks)
        )
        var_total = float(sum(r.var_incremental_loss_eur for r in cluster_risks))
        cvar_total = float(sum(r.cvar_incremental_loss_eur for r in cluster_risks))

        # Conservative, bounded approximation for the confidence band.
        ci_half_width = 0.02
        ci95 = (
            max(0.0, portfolio_component_probability - ci_half_width),
            min(1.0, portfolio_component_probability + ci_half_width),
        )

        return ComponentRiskResult(
            confidence=float(confidence),
            selected=tuple(selected),
            cluster_risks=tuple(cluster_risks),
            portfolio_component_probability=portfolio_component_probability,
            portfolio_component_probability_analytical=portfolio_component_probability_analytical,
            portfolio_component_probability_ci95=ci95,
            portfolio_expected_incremental_loss_eur=expected_total,
            portfolio_var_incremental_loss_eur=var_total,
            portfolio_cvar_incremental_loss_eur=cvar_total,
        )

    @staticmethod
    def summary(result: ComponentRiskResult) -> dict[str, float]:
        """Create a compact summary dictionary for presentation-level consumers."""
        return {
            "clusters_at_risk": float(len(result.cluster_risks)),
            "portfolio_component_probability": result.portfolio_component_probability,
            "portfolio_expected_incremental_loss_eur": (
                result.portfolio_expected_incremental_loss_eur
            ),
            "portfolio_var_incremental_loss_eur": result.portfolio_var_incremental_loss_eur,
            "portfolio_cvar_incremental_loss_eur": result.portfolio_cvar_incremental_loss_eur,
        }

    @staticmethod
    def simulated_from_distributions(
        *,
        selected: Iterable[str],
        cluster_hits: dict[str, np.ndarray],
        cluster_probabilities: dict[str, float],
        cluster_features: dict[str, tuple[str, ...]],
        incremental_losses: np.ndarray,
        cluster_incremental_losses: dict[str, np.ndarray],
        confidence: float = 0.95,
    ) -> ComponentRiskResult:
        """Build ComponentRiskResult from simulation distributions.

        This method keeps statistical result construction in the domain layer.
        """
        if not 0.0 < confidence < 1.0:
            raise ValueError(CONFIDENCE_ERROR)

        selected_tuple = tuple(selected)
        if not selected_tuple:
            return ComponentRiskResult(
                confidence=float(confidence),
                selected=(),
                cluster_risks=(),
                portfolio_component_probability=0.0,
                portfolio_component_probability_analytical=0.0,
                portfolio_component_probability_ci95=(0.0, 0.0),
                portfolio_expected_incremental_loss_eur=0.0,
                portfolio_var_incremental_loss_eur=0.0,
                portfolio_cvar_incremental_loss_eur=0.0,
            )

        if len(incremental_losses) == 0:
            return ComponentRiskResult(
                confidence=float(confidence),
                selected=selected_tuple,
                cluster_risks=(),
                portfolio_component_probability=0.0,
                portfolio_component_probability_analytical=0.0,
                portfolio_component_probability_ci95=(0.0, 0.0),
                portfolio_expected_incremental_loss_eur=0.0,
                portfolio_var_incremental_loss_eur=0.0,
                portfolio_cvar_incremental_loss_eur=0.0,
            )

        alpha = float(confidence)
        var_inc = float(np.percentile(incremental_losses, alpha * 100.0))
        tail_inc = incremental_losses[incremental_losses >= var_inc]
        cvar_inc = float(np.mean(tail_inc)) if len(tail_inc) > 0 else var_inc

        clusters = sorted(cluster_hits)
        any_cluster_hit = (
            np.logical_or.reduce([cluster_hits[c] for c in clusters])
            if clusters
            else np.zeros(len(incremental_losses), dtype=bool)
        )
        portfolio_prob = float(np.mean(any_cluster_hit))

        configured_probs = list(cluster_probabilities.values())
        analytical_prob = 1.0 - float(np.prod([1.0 - p for p in configured_probs]))

        n = max(1, len(incremental_losses))
        se = np.sqrt(portfolio_prob * (1.0 - portfolio_prob) / n)
        z_95 = 1.959963984540054
        ci_low = float(max(0.0, portfolio_prob - z_95 * se))
        ci_high = float(min(1.0, portfolio_prob + z_95 * se))

        cluster_risks: list[ClusterRisk] = []
        for cluster in clusters:
            losses = cluster_incremental_losses.get(cluster, np.array([], dtype=float))
            if len(losses) == 0:
                cluster_var = 0.0
                cluster_cvar = 0.0
                expected_loss = 0.0
            else:
                cluster_var = float(np.percentile(losses, alpha * 100.0))
                cluster_tail = losses[losses >= cluster_var]
                cluster_cvar = (
                    float(np.mean(cluster_tail))
                    if len(cluster_tail) > 0
                    else cluster_var
                )
                expected_loss = float(np.mean(losses))

            cluster_risks.append(
                ClusterRisk(
                    cluster=cluster,
                    features=cluster_features.get(cluster, ()),
                    configured_probability=float(cluster_probabilities[cluster]),
                    simulated_probability=float(np.mean(cluster_hits[cluster])),
                    expected_incremental_loss_eur=expected_loss,
                    var_incremental_loss_eur=cluster_var,
                    cvar_incremental_loss_eur=cluster_cvar,
                )
            )

        return ComponentRiskResult(
            confidence=alpha,
            selected=selected_tuple,
            cluster_risks=tuple(cluster_risks),
            portfolio_component_probability=portfolio_prob,
            portfolio_component_probability_analytical=analytical_prob,
            portfolio_component_probability_ci95=(ci_low, ci_high),
            portfolio_expected_incremental_loss_eur=float(np.mean(incremental_losses)),
            portfolio_var_incremental_loss_eur=var_inc,
            portfolio_cvar_incremental_loss_eur=cvar_inc,
        )

    @staticmethod
    def simulated_from_component_pnl_function(
        *,
        selected: Iterable[str],
        cluster_hits: dict[str, np.ndarray],
        cluster_probabilities: dict[str, float],
        feature_cluster_by_name: Mapping[str, str],
        pnl_function: Callable[[bool, set[str] | None], np.ndarray],
        confidence: float = 0.95,
    ) -> ComponentRiskResult:
        """Build simulation-based component risk from a counterfactual P&L callback."""
        if not 0.0 < confidence < 1.0:
            raise ValueError(CONFIDENCE_ERROR)  # pragma: no cover - defensive

        selected_tuple = tuple(selected)
        if not selected_tuple:
            return ComponentRiskService.simulated_from_distributions(  # pragma: no cover - defensive
                selected=(),
                cluster_hits={},
                cluster_probabilities={},
                cluster_features={},
                incremental_losses=np.array([], dtype=float),
                cluster_incremental_losses={},
                confidence=confidence,
            )

        full_pnl = np.asarray(pnl_function(True, None), dtype=float)
        no_component_pnl = np.asarray(pnl_function(False, None), dtype=float)
        incremental_losses = np.clip(no_component_pnl - full_pnl, 0.0, None)

        clusters = sorted(cluster_hits)
        all_clusters = set(clusters)
        cluster_incremental_losses: dict[str, np.ndarray] = {}

        for cluster in clusters:
            enabled_clusters = all_clusters - {cluster}
            pnl_without_cluster = np.asarray(
                pnl_function(True, enabled_clusters),
                dtype=float,
            )
            cluster_incremental_losses[cluster] = np.clip(
                pnl_without_cluster - full_pnl,
                0.0,
                None,
            )

        cluster_features = {
            cluster: tuple(
                name.split(": ", 1)[-1]
                for name in selected_tuple
                if feature_cluster_by_name.get(name, "Independent") == cluster
            )
            for cluster in clusters
        }

        return ComponentRiskService.simulated_from_distributions(
            selected=selected_tuple,
            cluster_hits=cluster_hits,
            cluster_probabilities=cluster_probabilities,
            cluster_features=cluster_features,
            incremental_losses=incremental_losses,
            cluster_incremental_losses=cluster_incremental_losses,
            confidence=confidence,
        )

    @staticmethod
    def analytical_from_cluster_business_value_function(
        *,
        selected: Iterable[str],
        feature_cluster_by_name: Mapping[str, str],
        cluster_probabilities: Mapping[str, float],
        cluster_business_value_function: Callable[
            [str, tuple[str, ...]], tuple[float, float]
        ],
        expected_loss_multiplier: float = 1.0,
        var_loss_multiplier: float = 1.0,
        confidence: float = 0.95,
    ) -> ComponentRiskResult:
        """Build analytical component risk using a cluster-level business value callback.

        The callback returns `(expected_business_value, var_business_value)` for each cluster.
        """
        if not 0.0 < confidence < 1.0:
            raise ValueError(CONFIDENCE_ERROR)

        selected_tuple = tuple(selected)
        if not selected_tuple:
            return ComponentRiskService.analytical_from_cluster_estimates(
                selected=(),
                cluster_features={},
                cluster_probabilities={},
                expected_losses={},
                var_losses={},
                cvar_losses={},
                confidence=confidence,
            )

        cluster_features_raw: dict[str, list[str]] = {}
        for name in selected_tuple:
            cluster = feature_cluster_by_name.get(name, "Independent")
            cluster_features_raw.setdefault(cluster, []).append(name)

        cluster_features: dict[str, tuple[str, ...]] = {}
        resolved_cluster_probabilities: dict[str, float] = {}
        expected_losses: dict[str, float] = {}
        var_losses: dict[str, float] = {}

        for cluster in sorted(cluster_features_raw):
            names = tuple(cluster_features_raw[cluster])
            probability = float(cluster_probabilities.get(cluster, 0.0))
            expected_business_value, var_business_value = (
                cluster_business_value_function(cluster, names)
            )

            cluster_features[cluster] = tuple(
                name.split(": ", 1)[-1] for name in cluster_features_raw[cluster]
            )
            resolved_cluster_probabilities[cluster] = probability
            expected_losses[cluster] = (
                float(expected_business_value) * probability * expected_loss_multiplier
            )
            var_losses[cluster] = (
                float(var_business_value) * probability * var_loss_multiplier
            )

        return ComponentRiskService.analytical_from_cluster_estimates(
            selected=selected_tuple,
            cluster_features=cluster_features,
            cluster_probabilities=resolved_cluster_probabilities,
            expected_losses=expected_losses,
            var_losses=var_losses,
            cvar_losses=var_losses,
            confidence=confidence,
        )

    @staticmethod
    def analytical_from_cluster_estimates(
        *,
        selected: Iterable[str],
        cluster_features: dict[str, tuple[str, ...]],
        cluster_probabilities: dict[str, float],
        expected_losses: dict[str, float],
        var_losses: dict[str, float],
        cvar_losses: dict[str, float],
        confidence: float = 0.95,
    ) -> ComponentRiskResult:
        """Build ComponentRiskResult from analytical cluster-level estimates."""
        if not 0.0 < confidence < 1.0:
            raise ValueError(CONFIDENCE_ERROR)

        selected_tuple = tuple(selected)
        if not selected_tuple:
            return ComponentRiskResult(
                confidence=float(confidence),
                selected=(),
                cluster_risks=(),
                portfolio_component_probability=0.0,
                portfolio_component_probability_analytical=0.0,
                portfolio_component_probability_ci95=(0.0, 0.0),
                portfolio_expected_incremental_loss_eur=0.0,
                portfolio_var_incremental_loss_eur=0.0,
                portfolio_cvar_incremental_loss_eur=0.0,
            )

        cluster_risks: list[ClusterRisk] = []
        no_hit_probability = 1.0

        for cluster in sorted(cluster_features):
            probability = float(cluster_probabilities[cluster])
            cluster_risks.append(
                ClusterRisk(
                    cluster=cluster,
                    features=cluster_features[cluster],
                    configured_probability=probability,
                    simulated_probability=probability,
                    expected_incremental_loss_eur=float(expected_losses[cluster]),
                    var_incremental_loss_eur=float(var_losses[cluster]),
                    cvar_incremental_loss_eur=float(cvar_losses[cluster]),
                )
            )
            no_hit_probability *= 1.0 - probability

        portfolio_prob = float(1.0 - no_hit_probability)
        return ComponentRiskResult(
            confidence=float(confidence),
            selected=selected_tuple,
            cluster_risks=tuple(cluster_risks),
            portfolio_component_probability=portfolio_prob,
            portfolio_component_probability_analytical=portfolio_prob,
            portfolio_component_probability_ci95=(portfolio_prob, portfolio_prob),
            portfolio_expected_incremental_loss_eur=float(
                sum(r.expected_incremental_loss_eur for r in cluster_risks)
            ),
            portfolio_var_incremental_loss_eur=float(
                sum(r.var_incremental_loss_eur for r in cluster_risks)
            ),
            portfolio_cvar_incremental_loss_eur=float(
                sum(r.cvar_incremental_loss_eur for r in cluster_risks)
            ),
        )
