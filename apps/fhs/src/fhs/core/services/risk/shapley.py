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

"""Shapley attribution domain service."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import combinations
from math import factorial

import numpy as np

from fhs.core.model.value_objects import RiskFactorContribution, RiskFactorShapley


class ShapleyAttributionService:
    """Build typed Shapley-attribution outputs for risk-factor decomposition."""

    SUPPORTED_LOSS_METRICS = frozenset({"expected_loss", "var_loss", "cvar_loss"})

    @staticmethod
    def _powerset(items: tuple[str, ...]) -> list[frozenset[str]]:
        """Generate all subsets for a small tuple of risk names."""
        subsets: list[frozenset[str]] = []
        for size in range(len(items) + 1):
            for combo in combinations(items, size):
                subsets.append(frozenset(combo))
        return subsets

    @staticmethod
    def _subset_key(subset: frozenset[str]) -> str:
        """Canonical key for risk subset labels."""
        return "+".join(sorted(subset)) if subset else "none"

    @staticmethod
    def calculate_shapley_values(
        *,
        risks: tuple[str, ...],
        value_function: Callable[[frozenset[str]], float],
    ) -> dict[str, float]:
        """Calculate Shapley values for given risk factors.

        Args:
            risks: Tuple of risk factor names
            value_function: Function that returns the value for a given subset of risks

        Returns:
            Dictionary mapping risk names to their Shapley contributions
        """
        n = len(risks)
        denom = factorial(n)
        contributions: dict[str, float] = dict.fromkeys(risks, 0.0)
        risk_set = set(risks)

        for risk in risks:
            others = tuple(sorted(risk_set - {risk}))
            for subset in ShapleyAttributionService._powerset(others):
                size = len(subset)
                weight = factorial(size) * factorial(n - size - 1) / denom
                with_risk = subset | {risk}
                marginal = value_function(frozenset(with_risk)) - value_function(subset)
                contributions[risk] += weight * marginal

        return contributions

    @staticmethod
    def attribute(
        *,
        metric: str,
        contributions: dict[str, float],
        selected: Iterable[str],
        baseline_value_eur: float,
        confidence: float = 0.95,
        subset_values_eur: dict[str, float] | None = None,
    ) -> RiskFactorShapley:
        """Create a typed RiskFactorShapley result from factor contributions."""
        if not metric:
            raise ValueError("Metric must be a non-empty string.")
        if not 0.0 < confidence < 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

        contribution_objs = [
            RiskFactorContribution(
                risk=risk, contribution_eur=float(value), share_of_total=0.0
            )
            for risk, value in contributions.items()
        ]

        total_risk = float(sum(item.contribution_eur for item in contribution_objs))
        full_value = float(baseline_value_eur) + total_risk

        if not np.isclose(total_risk, 0.0):  # pragma: no cover - partial branch
            contribution_objs = [
                RiskFactorContribution(
                    risk=item.risk,
                    contribution_eur=item.contribution_eur,
                    share_of_total=item.contribution_eur / total_risk,
                )
                for item in contribution_objs
            ]

        contribution_objs.sort(
            key=lambda item: abs(item.contribution_eur), reverse=True
        )

        contribution_sum = float(
            sum(item.contribution_eur for item in contribution_objs)
        )
        interaction_residual = total_risk - contribution_sum

        return RiskFactorShapley(
            metric=metric,
            confidence=float(confidence),
            selected=tuple(selected),
            baseline_value_eur=float(baseline_value_eur),
            full_value_eur=full_value,
            total_risk_eur=total_risk,
            contributions=tuple(contribution_objs),
            interaction_residual_eur=float(interaction_residual),
            subset_values_eur=dict(subset_values_eur or {}),
        )

    @staticmethod
    def attribute_from_subset_value_function(
        *,
        metric: str,
        selected: Iterable[str],
        value_function: Callable[[frozenset[str]], float],
        risks: tuple[str, ...] = ("delivery", "market", "component", "global"),
        confidence: float = 0.95,
    ) -> RiskFactorShapley:
        """Build full Shapley attribution from subset value function.

        The method handles metric validation, subset-value caching, contribution
        calculation, and typed result assembly.
        """
        if metric not in ShapleyAttributionService.SUPPORTED_LOSS_METRICS:
            supported = ", ".join(
                sorted(ShapleyAttributionService.SUPPORTED_LOSS_METRICS)
            )
            raise ValueError(f"Unknown metric '{metric}'. Use one of: {supported}")

        subset_values: dict[frozenset[str], float] = {}

        def cached_value(subset: frozenset[str]) -> float:
            if subset in subset_values:
                return subset_values[subset]

            value = float(value_function(subset))
            subset_values[subset] = value
            return value

        contributions = ShapleyAttributionService.calculate_shapley_values(
            risks=risks,
            value_function=cached_value,
        )

        empty_value = cached_value(frozenset())
        _ = cached_value(frozenset(risks))

        subset_values_str = {
            ShapleyAttributionService._subset_key(subset): value
            for subset, value in subset_values.items()
        }

        return ShapleyAttributionService.attribute(
            metric=metric,
            contributions=contributions,
            selected=selected,
            baseline_value_eur=empty_value,
            confidence=confidence,
            subset_values_eur=subset_values_str,
        )
