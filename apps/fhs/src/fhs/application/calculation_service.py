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

"""Feature calculation service — business metrics for features.

This service provides domain-agnostic calculations for feature metrics.
Replaces inline helper functions in notebooks.
"""

from __future__ import annotations

from collections.abc import Iterable

from fhs.core.model.entities import Feature
from fhs.core.model.value_objects import (
    BudgetCheckResult,
    FeatureBudgetCheckRow,
    SimulationResult,
)


class FeatureCalculationService:
    """Calculate feature metrics: business value, ROI, cost-benefit ratios."""

    @staticmethod
    def simulate_feature(
        feature: Feature,
        *,
        scenarios: int = 10_000,
        seed: int | None = None,
    ) -> SimulationResult:
        """Run a Monte Carlo simulation for a single feature.

        Delegates to the core FeatureSimulator via ServiceFactory.

        Args:
            feature: Feature to simulate.
            scenarios: Number of Monte Carlo draws.
            seed: Random seed for reproducibility.

        Returns:
            SimulationResult with distribution statistics.
        """
        from fhs.application.service_factory import ServiceFactory

        sim = ServiceFactory(seed=seed).create_feature_simulator()
        return sim.simulate_feature(feature, scenarios=scenarios)  # type: ignore[return-value]

    @staticmethod
    def calculate_expected_business_value(feature: Feature) -> float:
        """Expected annual business value from feature adoption.

        Formula: expected_users × conversion_rate × value_per_conversion

        Args:
            feature: Feature with user expectations and value metrics

        Returns:
            Annual business value in currency units (usually EUR)
        """
        return (
            feature.expected_users
            * feature.conversion_rate
            * feature.business_value_per_conversion
        )

    @staticmethod
    def calculate_roi(feature: Feature) -> float:
        """Return on investment (absolute, year 1).

        Formula: (expected_business_value - annual_installment) / annual_installment

        Uses annual_installment (= development_cost / installment_years) so that
        multi-year features are compared fairly on a per-year basis.

        Args:
            feature: Feature with business value and cost metrics

        Returns:
            ROI multiple (e.g., 2.5 = 250% ROI = 2.5× payback)
            Returns inf if annual_installment ≤ 0
        """
        if feature.annual_installment <= 0:
            return float("inf")  # pragma: no cover - defensive

        business_value = FeatureCalculationService.calculate_expected_business_value(
            feature
        )
        return (
            business_value - feature.annual_installment
        ) / feature.annual_installment

    @staticmethod
    def calculate_roi_percentage(feature: Feature) -> float:
        """Return on investment as percentage.

        Formula: ROI × 100%

        Args:
            feature: Feature with business value and cost metrics

        Returns:
            ROI as percentage (e.g., 250 for 250%)
        """
        roi = FeatureCalculationService.calculate_roi(
            feature
        )  # pragma: no cover - defensive
        return (
            roi * 100 if roi != float("inf") else float("inf")
        )  # pragma: no cover - defensive

    @staticmethod
    def calculate_break_even_users(feature: Feature) -> float:
        """Users needed to break even on development cost.

        Formula: development_cost / (conversion_rate × value_per_conversion)

        Args:
            feature: Feature with cost and value metrics

        Returns:
            Number of users needed to break even (may exceed expected_users)
        """
        denominator = (
            feature.conversion_rate * feature.business_value_per_conversion
        )  # pragma: no cover - defensive
        if denominator <= 0:  # pragma: no cover - defensive
            return float("inf")  # pragma: no cover - defensive
        return feature.development_cost / denominator  # pragma: no cover - defensive

    @staticmethod
    def is_profitable(feature: Feature) -> bool:
        """Check if feature expected business value exceeds development cost.

        Args:
            feature: Feature with business value and cost metrics

        Returns:
            True if expected_business_value > annual_installment
        """
        business_value = FeatureCalculationService.calculate_expected_business_value(  # pragma: no cover - defensive
            feature  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        return (
            business_value > feature.annual_installment
        )  # pragma: no cover - defensive

    @staticmethod
    def net_value_full_cost_year1(feature: Feature, expected_bv: float) -> float:
        """Net business value after deducting full investment and year-1 operating cost.

        Variant 1 — cash-flow view: treats the entire development cost as an
        immediate outflow in year 1, plus the annual operating cost.

        Formula:
            net = expected_bv − development_cost − annual_operating_cost

        Args:
            feature: Feature with cost and operating cost fields.
            expected_bv: Simulated expected business value (EUR).

        Returns:
            Net value in EUR. Negative means the feature does not pay back in year 1.
        """
        return expected_bv - feature.development_cost - feature.annual_operating_cost

    @staticmethod
    def net_value_pl_year1(feature: Feature, expected_bv: float) -> float:
        """Net business value after deducting year-1 P&L charges.

        Variant 2 — accounting view: uses straight-line annual installment
        (development_cost / installment_years) plus the annual operating cost.

        Formula:
            net = expected_bv − annual_installment − annual_operating_cost

        Args:
            feature: Feature with cost, installment, and operating cost fields.
            expected_bv: Simulated expected business value (EUR).

        Returns:
            Net value in EUR. Negative means the feature does not cover its
            year-1 P&L charges.
        """
        return expected_bv - feature.annual_installment - feature.annual_operating_cost

    @staticmethod
    def budget_check(
        features: Iterable[Feature],
        budget: float,
        *,
        small_buffer_threshold: float = 0.10,
    ) -> BudgetCheckResult:
        """Check whether selected features fit into the available budget."""
        feature_list = list(features)
        budget_value = float(budget)
        total_cost = float(sum(feature.development_cost for feature in feature_list))
        budget_left = budget_value - total_cost

        rows = []
        for feature in feature_list:
            feature_key = feature.name.split(":", 1)[0].strip()
            short_name = feature.name.split(": ", 1)[-1]
            development_cost = float(feature.development_cost)
            rows.append(
                FeatureBudgetCheckRow(
                    feature_key=feature_key,
                    feature_name=feature.name,
                    short_name=short_name,
                    development_cost=development_cost,
                    budget_share=(
                        (development_cost / budget_value) if budget_value > 0 else 0.0
                    ),
                    fits_budget=development_cost <= budget_value,
                )
            )

        return BudgetCheckResult(
            rows=tuple(rows),
            budget=budget_value,
            total_cost=total_cost,
            budget_left=budget_left,
            budget_share=(total_cost / budget_value) if budget_value > 0 else 0.0,
            fits_budget=budget_left >= 0,
            small_buffer=(budget_left >= 0)
            and (budget_value > 0)
            and (budget_left < small_buffer_threshold * budget_value),
        )


# Simplified factory for common use cases
def expected_business_value_fn(feature: Feature) -> float:
    """Convenience function for expected_business_value calculation."""
    return FeatureCalculationService.calculate_expected_business_value(
        feature
    )  # pragma: no cover - defensive


def roi_fn(feature: Feature) -> float:
    """Convenience function for ROI calculation."""
    return FeatureCalculationService.calculate_roi(
        feature
    )  # pragma: no cover - defensive
