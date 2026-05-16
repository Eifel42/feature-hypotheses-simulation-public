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

"""Risk-layer related value objects for advanced portfolio analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RiskLayerStats:
    """Immutable statistics for a single risk layer."""

    expected: float
    var_95: float
    cvar_95: float
    std: float

    @classmethod
    def from_scenarios(cls, scenarios: np.ndarray) -> RiskLayerStats:
        """Factory method to construct RiskLayerStats from numpy array.

        Eliminates DRY violations: VaR/CVaR calculation appears 8+ times
        across Application Services and Domain Services.

        Args:
            scenarios: Monte Carlo scenarios (numpy array)

        Returns:
            RiskLayerStats with calculated risk metrics
        """
        if len(scenarios) == 0:
            return cls(expected=0.0, var_95=0.0, cvar_95=0.0, std=0.0)

        var_95 = float(np.percentile(scenarios, 5))
        tail = scenarios[scenarios <= var_95]
        cvar_95 = float(np.mean(tail)) if len(tail) > 0 else var_95

        return cls(
            expected=float(np.mean(scenarios)),
            var_95=var_95,
            cvar_95=cvar_95,
            std=float(np.std(scenarios)),
        )


@dataclass(frozen=True)
class RiskProbabilities:
    """Configured risk probabilities for a feature or portfolio."""

    risk_1: float  # Development risk (LLP — likelihood of non-delivery)
    risk_2: float  # Market risk (portfolio-wide market shock)
    risk_3: float  # Global risk (global crisis event)
    component: float  # Component risk (platform/dependency cluster failure)


@dataclass(frozen=True)
class RiskHitRates:
    """Simulated hit rates for risk events."""

    risk_1_blocked_pct: (
        float  # Development risk — % of scenarios where feature was not delivered
    )
    risk_2_hit_pct: float  # Market risk — % of scenarios where market shock occurred
    component_hit_pct: float  # Component risk — % of scenarios where platform failed
    risk_3_hit_pct: float  # Global risk — % of scenarios where global crisis occurred


@dataclass(frozen=True)
class FeatureRiskProfile:
    """Complete risk-layer profile for one feature."""

    feature: str
    cluster: str
    probabilities: RiskProbabilities
    base: RiskLayerStats
    after_risk_1: RiskLayerStats  # After Development risk
    after_risk_2: RiskLayerStats  # After Market risk
    after_component: RiskLayerStats  # After Component risk
    after_risk_3: RiskLayerStats  # After Global risk
    hit_rates: RiskHitRates


@dataclass(frozen=True)
class RetentionRow:
    """Retention metrics from base to fully risk-adjusted layer for one feature."""

    feature: str
    cluster: str
    base_expected: float
    after_risk_3_expected: float
    expected_retention_pct: float
    base_var_95: float
    after_risk_3_var_95: float
    floor_retention_pct: float


@dataclass(frozen=True)
class RetentionMatrix:
    """Portfolio-level retention view built from feature risk profiles."""

    rows: tuple[RetentionRow, ...]
    portfolio_expected_retention_pct: float
    portfolio_floor_retention_pct: float


@dataclass(frozen=True)
class PortfolioRiskMeta:
    """Metadata for a portfolio risk simulation."""

    market_hit_pct: float
    global_hit_pct: float
    cluster_hit_pct: dict[str, float]
    selected: tuple[str, ...]
    risk_2_probability: float  # Market risk probability
    risk_3_probability: float  # Global risk probability


@dataclass(frozen=True)
class PortfolioRiskLayers:
    """Layered risk statistics for a portfolio."""

    base: RiskLayerStats
    after_risk_1: RiskLayerStats  # After Development risk
    after_risk_2: RiskLayerStats  # After Market risk
    after_component: RiskLayerStats  # After Component risk
    after_risk_3: RiskLayerStats  # After Global risk
    meta: PortfolioRiskMeta

    def waterfall_summary(self) -> WaterfallSummary:
        """Build layer-by-layer loss breakdown for waterfall visualizations."""
        rows = (
            WaterfallRow(
                layer="Base (no risk)",
                expected=self.base.expected,
                var_95=self.base.var_95,
                layer_loss=0.0,
            ),
            WaterfallRow(
                layer="After Delivery",
                expected=self.after_risk_1.expected,
                var_95=self.after_risk_1.var_95,
                layer_loss=self.base.expected - self.after_risk_1.expected,
            ),
            WaterfallRow(
                layer="After Market",
                expected=self.after_risk_2.expected,
                var_95=self.after_risk_2.var_95,
                layer_loss=self.after_risk_1.expected - self.after_risk_2.expected,
            ),
            WaterfallRow(
                layer="After Component",
                expected=self.after_component.expected,
                var_95=self.after_component.var_95,
                layer_loss=self.after_risk_2.expected - self.after_component.expected,
            ),
            WaterfallRow(
                layer="After Global (all risks)",
                expected=self.after_risk_3.expected,
                var_95=self.after_risk_3.var_95,
                layer_loss=self.after_component.expected - self.after_risk_3.expected,
            ),
        )
        total_expected_loss = self.base.expected - self.after_risk_3.expected
        return WaterfallSummary(
            rows=rows,
            total_expected_loss=total_expected_loss,
            total_expected_loss_pct=(
                (total_expected_loss / self.base.expected)
                if self.base.expected > 0
                else 0.0
            ),
        )


@dataclass(frozen=True)
class WaterfallRow:
    """One row in a layered portfolio-risk waterfall."""

    layer: str
    expected: float
    var_95: float
    layer_loss: float


@dataclass(frozen=True)
class WaterfallSummary:
    """Aggregated waterfall summary derived from PortfolioRiskLayers."""

    rows: tuple[WaterfallRow, ...]
    total_expected_loss: float
    total_expected_loss_pct: float


@dataclass(frozen=True)
class PortfolioPnLLayers:
    """Layered P&L risk statistics for a portfolio."""

    base: RiskLayerStats
    after_risk_1: RiskLayerStats
    after_risk_2: RiskLayerStats
    after_component: RiskLayerStats
    after_risk_3: RiskLayerStats
    meta: PortfolioRiskMeta


@dataclass(frozen=True)
class DeliveryStressResult:
    """Aggregated delivery stress-test result for one scenario profile."""

    prob_success: float
    prob_failure: float
    expected_delay_weeks: float
    expected_impact_eur: float
    impact_var_95_eur: float
    impact_cvar_95_eur: float


@dataclass(frozen=True)
class RiskManagementROI:
    """Financial impact of a risk-management program."""

    program_cost_eur: float
    avoided_expected_loss_eur: float
    net_expected_benefit_eur: float
    tail_risk_reduction_var_95_eur: float
