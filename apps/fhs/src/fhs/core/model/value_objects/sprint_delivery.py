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

"""Value objects for sprint-based delivery risk simulation."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SprintPlan:
    """Planned sprint allocation for a single feature."""

    feature_name: str
    planned_sprints: int
    sprint_length_weeks: float = 2.0

    @property
    def planned_weeks(self) -> int:
        """Planned duration in calendar weeks."""
        return int(self.planned_sprints * self.sprint_length_weeks)


@dataclass(frozen=True)
class DeliverySimulationResult:
    """Monte Carlo result for one feature's sprint delivery simulation.

    Each array has one entry per simulation scenario.
    """

    feature_name: str
    planned_sprints: int
    actual_sprints: np.ndarray  # int per scenario
    actual_cost: np.ndarray  # EUR per scenario
    cancelled: np.ndarray  # bool per scenario
    business_value_after_risk: np.ndarray  # EUR per scenario (from existing risk sim)

    @property
    def cancelled_pct(self) -> float:
        """Percentage of scenarios where the feature was cancelled."""
        return float(np.mean(self.cancelled)) if len(self.cancelled) > 0 else 0.0

    @property
    def sunk_cost_if_cancelled(self) -> float:
        """Expected sunk cost in cancellation scenarios."""
        mask = self.cancelled
        if not np.any(mask):
            return 0.0
        return float(np.mean(self.actual_cost[mask]))

    @property
    def expected_actual_sprints(self) -> float:
        """Expected number of actual sprints."""
        return float(np.mean(self.actual_sprints))

    @property
    def expected_actual_cost(self) -> float:
        """Expected actual development cost (EUR)."""
        return float(np.mean(self.actual_cost))

    @property
    def sprints_p50(self) -> int:
        """Median actual sprints, always rounded up to whole sprints."""
        return math.ceil(float(np.percentile(self.actual_sprints, 50)))

    @property
    def sprints_p75(self) -> int:
        """75th percentile of actual sprints, always rounded up."""
        return math.ceil(float(np.percentile(self.actual_sprints, 75)))

    @property
    def sprints_p95(self) -> int:
        """95th percentile of actual sprints, always rounded up."""
        return math.ceil(float(np.percentile(self.actual_sprints, 95)))

    @property
    def max_actual_sprints(self) -> int:
        """Maximum observed actual sprints across all scenarios."""
        return int(np.max(self.actual_sprints))

    @property
    def cost_p95(self) -> float:
        """95th percentile of actual cost (EUR)."""
        return float(np.percentile(self.actual_cost, 95))

    @property
    def cost_cvar(self) -> float:
        """CVaR (Expected Shortfall) at 95%: average cost in the worst 5% of scenarios."""
        threshold = self.cost_p95
        tail = self.actual_cost[self.actual_cost >= threshold]
        return float(np.mean(tail)) if len(tail) > 0 else threshold

    @property
    def cost_uplift(self) -> float:
        """Expected cost uplift ratio vs planned (0.0 = on-time)."""
        if self.planned_sprints <= 0:
            return 0.0
        return self.expected_actual_sprints / self.planned_sprints - 1.0

    @property
    def profit(self) -> np.ndarray:
        """Profit distribution: business value after risk minus actual cost."""
        return np.asarray(
            self.business_value_after_risk - self.actual_cost, dtype=float
        )


@dataclass(frozen=True)
class ProfitabilityResult:
    """Profitability analysis for a single feature."""

    feature_name: str
    profit_distribution: np.ndarray  # EUR per scenario
    planned_cost: float  # EUR (deterministic)
    expected_business_value: float  # EUR (mean of business_value_after_risk)
    expected_cost: float  # EUR (mean of actual_cost)

    @property
    def break_even_probability(self) -> float:
        """Percentage of scenarios where profit > 0."""
        if len(self.profit_distribution) == 0:
            return 0.0
        return float(np.mean(self.profit_distribution > 0))

    @property
    def expected_profit(self) -> float:
        """Expected profit (EUR)."""
        return float(np.mean(self.profit_distribution))

    @property
    def expected_loss(self) -> float:
        """Expected loss given loss (EUR, positive value)."""
        losses = self.profit_distribution[self.profit_distribution < 0]
        if len(losses) == 0:
            return 0.0
        return float(-np.mean(losses))

    @property
    def loss_at_risk_95(self) -> float:
        """95th percentile of losses (EUR, positive = loss)."""
        if len(self.profit_distribution) == 0:
            return 0.0
        p5 = float(np.percentile(self.profit_distribution, 5))
        return max(0.0, -p5)

    @property
    def profit_margin(self) -> float:
        """Expected profit margin (%)."""
        if self.expected_cost <= 0:
            return 0.0
        return self.expected_profit / self.expected_cost


@dataclass(frozen=True)
class PortfolioProfitabilityResult:
    """Aggregated profitability result for the entire portfolio."""

    feature_results: tuple[ProfitabilityResult, ...]
    portfolio_profit: np.ndarray  # EUR per scenario (sum of all features)
    total_investment: float  # EUR (sum of planned costs)

    @property
    def portfolio_break_even_probability(self) -> float:
        """Percentage of scenarios where portfolio profit > 0."""
        if len(self.portfolio_profit) == 0:
            return 0.0
        return float(np.mean(self.portfolio_profit > 0))

    @property
    def expected_portfolio_profit(self) -> float:
        """Expected portfolio profit (EUR)."""
        return float(np.mean(self.portfolio_profit))

    @property
    def portfolio_loss_at_risk_95(self) -> float:
        """95th percentile of portfolio losses (EUR, positive = loss)."""
        if len(self.portfolio_profit) == 0:
            return 0.0
        p5 = float(np.percentile(self.portfolio_profit, 5))
        return max(0.0, -p5)

    @property
    def portfolio_profit_p5(self) -> float:
        """5th percentile of portfolio profit (EUR)."""
        if len(self.portfolio_profit) == 0:
            return 0.0
        return float(np.percentile(self.portfolio_profit, 5))

    @property
    def portfolio_expected_loss(self) -> float:
        """Expected loss given loss for the portfolio (EUR, positive)."""
        losses = self.portfolio_profit[self.portfolio_profit < 0]
        if len(losses) == 0:
            return 0.0
        return float(-np.mean(losses))
