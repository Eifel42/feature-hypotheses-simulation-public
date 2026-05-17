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

"""Sprint-overrun simulation service.

Simulates development duration overruns using Monte Carlo,
computes actual costs, cancellation events, and profitability.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
from scipy.stats import truncnorm

from fhs.core.model import (
    DeliverySimulationResult,
    Feature,
    PortfolioProfitabilityResult,
    ProfitabilityResult,
    SprintPlan,
)
from fhs.core.model.config import DeliveryRiskConfig


class SprintOverrunService:
    """Monte Carlo simulation over sprint durations and costs.

    Given a DeliveryRiskConfig, this service:
    1. Computes planned sprints per feature from development_weeks.
    2. Draws a delay factor per scenario from a lognormal distribution.
    3. Computes actual cost = actual_sprints × burn_rate × overhead.
    4. Applies cancellation logic when overrun exceeds threshold.
    5. Combines with business-value-after-risk to produce profitability metrics.
    """

    @staticmethod
    def planned_sprints_for_weeks(
        development_weeks: float,
        sprint_length_weeks: float = 2.0,
    ) -> int:
        """Convert estimated development weeks to planned sprints.

        Sprint length is defined by delivery configuration.
        Partial sprints are rounded up so a 5-week effort
        reserves 3 sprints.
        """
        sprint_weeks = float(sprint_length_weeks)
        if sprint_weeks <= 0:
            raise ValueError("sprint_length_weeks must be > 0")
        return max(1, math.ceil(float(development_weeks) / sprint_weeks))

    @staticmethod
    def compute_sprint_plans(
        features: Sequence[Feature],
        config: DeliveryRiskConfig | None = None,
    ) -> dict[str, SprintPlan]:
        """Compute planned sprints for each feature.

        Features without development_weeks are skipped with a warning.
        """
        sprint_length_weeks = float(
            config.sprint_length_weeks if config is not None else 2.0
        )
        plans: dict[str, SprintPlan] = {}
        for feature in features:
            if feature.development_weeks is None:
                continue
            planned = SprintOverrunService.planned_sprints_for_weeks(
                feature.development_weeks,
                sprint_length_weeks=sprint_length_weeks,
            )
            plans[feature.name] = SprintPlan(
                feature_name=feature.name,
                planned_sprints=planned,
                sprint_length_weeks=sprint_length_weeks,
            )
        return plans

    @staticmethod
    def simulate_delivery(
        *,
        feature: Feature,
        sprint_plan: SprintPlan,
        business_value_after_risk: np.ndarray,
        config: DeliveryRiskConfig,
        seed: int = 42,
    ) -> DeliverySimulationResult:
        """Run Monte Carlo simulation for one feature's delivery risk.

        Uses truncated lognormal distribution for mathematically sound modeling
        of sprint duration uncertainty:

        For each scenario:
        1. Draw actual sprints from Lognormal(μ, σ) truncated to [1, sprint_ceiling].
           - Lower bound: 1.0 (no sprint finishes faster than planned)
           - Upper bound: planned_sprints × sprint_ceiling
           - σ (volatility) = sprint_uncertainty × planned_sprints (as decimal)
        2. Compute cost via feature burndown:
           weekly_burn = development_cost / development_weeks
           cost_per_sprint = weekly_burn × sprint_length_weeks
        3. If overrun > max_sprints_over_plan: evaluate cancellation.
           On cancellation: business_value = 0, cost = cost up to cancellation point.
        """
        n_scenarios = len(business_value_after_risk)
        rng = np.random.default_rng(seed)
        planned = sprint_plan.planned_sprints
        dm = config.delay_model
        cancel = config.cancellation

        # ────────────────────────────────────────────────────────────────────
        # Truncated Lognormal Distribution
        # ────────────────────────────────────────────────────────────────────
        mean_sprints = float(planned)
        std_sprints = float(dm.get_uncertainty_decimal()) * mean_sprints
        max_actual_sprints = planned * dm.sprint_ceiling

        if std_sprints > 0 and mean_sprints > 0:
            # Lognormal parameters: fit to mean and std
            sigma_sq = np.log(1 + (std_sprints / mean_sprints) ** 2)
            sigma = np.sqrt(sigma_sq)
            mu = np.log(mean_sprints) - sigma_sq / 2

            # Truncation bounds in standardized normal space (Z-scores)
            a = (np.log(1.0) - mu) / sigma  # Lower: 1 sprint
            b = (np.log(max_actual_sprints) - mu) / sigma  # Upper: cap

            # Sample from truncated standard normal
            z = truncnorm.rvs(a=a, b=b, size=n_scenarios, random_state=rng)
            # Transform back to lognormal
            actual_sprints_float = np.exp(mu + sigma * z)
        else:
            # No variation: all scenarios use planned duration
            actual_sprints_float = np.full(n_scenarios, mean_sprints)

        # Round up to whole sprints (minimum 1)
        actual_sprints = np.maximum(1, np.ceil(actual_sprints_float)).astype(int)
        # Clip to max (redundant due to truncation, but safety measure)
        actual_sprints = np.minimum(actual_sprints, int(np.ceil(max_actual_sprints)))

        # ────────────────────────────────────────────────────────────────────
        # Cancellation Logic
        # ────────────────────────────────────────────────────────────────────
        overrun = actual_sprints - planned
        overrun_exceeds = overrun > cancel.max_sprints_over_plan
        cancel_draws = rng.random(n_scenarios) < cancel.cancellation_probability
        cancelled = overrun_exceeds & cancel_draws

        # For cancelled features: cost accrues up to cancellation point
        # (planned + max_sprints_over_plan sprints before decision)
        cancel_point_sprints = planned + cancel.max_sprints_over_plan
        effective_sprints = np.where(cancelled, cancel_point_sprints, actual_sprints)

        # ────────────────────────────────────────────────────────────────────
        # Cost Calculation
        # ────────────────────────────────────────────────────────────────────
        development_weeks = float(feature.development_weeks or 0.0)
        if development_weeks > 0:
            weekly_burn = float(feature.development_cost) / development_weeks
        else:
            weekly_burn = 0.0  # pragma: no cover - defensive
        cost_per_sprint = weekly_burn * float(config.sprint_length_weeks)
        actual_cost = effective_sprints * cost_per_sprint

        # ────────────────────────────────────────────────────────────────────
        # Profitability: Business Value
        # ────────────────────────────────────────────────────────────────────
        # Business value: zero if cancelled
        effective_business_value = np.where(cancelled, 0.0, business_value_after_risk)

        return DeliverySimulationResult(
            feature_name=feature.name,
            planned_sprints=planned,
            actual_sprints=actual_sprints,
            actual_cost=actual_cost,
            cancelled=cancelled,
            business_value_after_risk=effective_business_value,
        )

    @staticmethod
    def simulate_all(
        *,
        features: Sequence[Feature],
        sprint_plans: Mapping[str, SprintPlan],
        business_value_after_risk: Mapping[str, np.ndarray],
        config: DeliveryRiskConfig,
        seed: int = 42,
    ) -> dict[str, DeliverySimulationResult]:
        """Simulate delivery risk for all features with sprint plans."""
        results: dict[str, DeliverySimulationResult] = {}
        for i, feature in enumerate(features):
            if feature.name not in sprint_plans:
                continue
            results[feature.name] = SprintOverrunService.simulate_delivery(
                feature=feature,
                sprint_plan=sprint_plans[feature.name],
                business_value_after_risk=business_value_after_risk[feature.name],
                config=config,
                seed=seed + i,  # Different seed per feature
            )
        return results

    @staticmethod
    # noinspection PyTypeHintsInspection
    def compute_profitability(
        delivery_results: Mapping[str, DeliverySimulationResult],
        features: Sequence[Feature],
    ) -> PortfolioProfitabilityResult:
        """Compute per-feature and portfolio profitability from delivery simulation."""
        feature_results: list[ProfitabilityResult] = []
        portfolio_profit: np.ndarray | None = None

        for feature in features:
            if feature.name not in delivery_results:
                continue  # pragma: no cover - defensive
            dr = delivery_results[feature.name]
            profit = dr.profit  # business_value_after_risk - actual_cost

            result = ProfitabilityResult(
                feature_name=feature.name,
                profit_distribution=profit,
                planned_cost=feature.development_cost,
                expected_business_value=float(np.mean(dr.business_value_after_risk)),
                expected_cost=float(np.mean(dr.actual_cost)),
            )
            feature_results.append(result)

            if portfolio_profit is None:
                portfolio_profit = profit.copy()
            else:
                portfolio_profit += profit

        if portfolio_profit is None:
            portfolio_profit = np.array([0.0])  # pragma: no cover - defensive

        total_investment = sum(
            f.development_cost for f in features if f.name in delivery_results
        )

        return PortfolioProfitabilityResult(
            feature_results=tuple(feature_results),
            portfolio_profit=portfolio_profit,
            total_investment=total_investment,
        )
