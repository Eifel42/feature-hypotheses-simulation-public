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

"""Development-risk methods."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from fhs.application.delivery_analysis_operations import (
    DeliveryAnalysisOperations,
    ProfitOptimizationComparison,
)
from fhs.presentation.notebook.styling import COLORS

if TYPE_CHECKING:
    from fhs.core.model import DeliveryRiskConfig, DeliverySimulationResult, Feature

BUDGET_PRESSURE_LABEL = "Budget pressure"
PLANNED_INVESTMENT_LABEL = "Planned investment"


class _DeliveryMixin:
    # Host stubs for static typing; concrete implementations come from _PrimitivesMixin/facade.
    # noinspection PyUnusedLocal
    def sensitivity(
        self,
        _rows: list[tuple[Any, ...]],
        _headers: tuple[str, ...],
        **_kwargs: Any,
    ) -> None:  # pragma: no cover - typing stub
        return None

    # noinspection PyUnusedLocal
    @staticmethod
    def samples(
        headers: tuple[str, ...],
        rows: list[tuple[str, ...]],
        *,
        title: str = "Sample Data",
        description: str | None = None,
        footer: str | None = None,
    ) -> None:  # pragma: no cover - typing stub
        del headers, rows, title, description, footer

    # noinspection PyUnusedLocal
    @staticmethod
    def metrics(
        rows: list[tuple[str, str, str | None]],
        *,
        title: str = "Metrics",
        metric_header: str = "Metric",
        value_header: str = "Value",
    ) -> None:  # pragma: no cover - typing stub
        del rows, title, metric_header, value_header

    # noinspection PyUnusedLocal
    @staticmethod
    def info_html(
        text: str, *, accent: str | None = None
    ) -> str:  # pragma: no cover - typing stub
        del accent
        return text

    # noinspection PyUnusedLocal
    @staticmethod
    def metrics_html(
        rows: list[tuple[str, str, str | None]],
        *,
        title: str = "Metrics",
        metric_header: str = "Metric",
        value_header: str = "Value",
    ) -> str:  # pragma: no cover - typing stub
        del rows, title, metric_header, value_header
        return ""

    # noinspection PyUnusedLocal
    @staticmethod
    def columns(
        *html_blocks: str,
        gap: str = "16px",
        min_width: str = "250px",
    ) -> None:  # pragma: no cover - typing stub
        del html_blocks, gap, min_width

    def delivery_risk_configuration(
        self,
        delivery_config: DeliveryRiskConfig,
        *,
        title: str = "Deployment-Risk Configuration Overview",
    ) -> None:
        """Render the standard deployment-risk configuration overview table."""
        sprint_uncertainty = float(delivery_config.delay_model.sprint_uncertainty)
        if sprint_uncertainty <= 1.0:
            sprint_uncertainty = sprint_uncertainty * 100.0

        rows = [
            (
                "Sprint uncertainty",
                f"{sprint_uncertainty:.0f}%",
                "Sprint duration volatility",
            ),
            (
                "Sprint ceiling",
                f"{delivery_config.delay_model.sprint_ceiling:.1f}x",
                "Maximum sprint duration multiplier",
            ),
            (
                "Sprint length",
                f"{delivery_config.sprint_length_weeks} weeks",
                "Fixed cadence for all development plans",
            ),
            (
                "Cancellation threshold",
                f"> {delivery_config.cancellation.max_sprints_over_plan} sprints",
                "Overrun trigger",
            ),
            (
                "Cancellation probability",
                f"{delivery_config.cancellation.cancellation_probability:.0%}",
                "Chance after trigger",
            ),
        ]
        self.sensitivity(
            rows,
            ("Parameter", "Value", "Business meaning"),
            title=title,
        )

    def profit_tail_optimization_comparison(
        self,
        comparison: ProfitOptimizationComparison,
        *,
        title: str = "Profit-Tail Optimization Comparison",
    ) -> None:
        """Render the standard profit-tail optimization comparison table."""
        rows = list(comparison.rows)
        headers = tuple(comparison.headers)
        self.sensitivity(
            rows,
            headers,
            title=title,
        )

    def negative_roi_reference_comparison(
        self,
        comparison: ProfitOptimizationComparison,
        *,
        title: str = "Reference comparison when a feature has negative ROI",
    ) -> None:
        """Render the negative-ROI reference comparison table."""
        rows = list(comparison.rows)
        headers = tuple(comparison.headers)
        self.sensitivity(
            rows,
            headers,
            title=title,
        )

    def budget_fit_ranking(
        self,
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
        *,
        title: str = "Budget Fit Ranking (Lower Pressure First)",
    ) -> None:
        """Render budget-fit CVaR ranking table only.

        Uses CVaR 95% (worst-5% average) for the budget pressure metric
        because sprint-based costs are step functions — the raw CaR 95%
        percentile collapses to identical multiples.
        """
        rows = DeliveryAnalysisOperations.budget_fit_rows(features, delivery_results)
        self.samples(
            headers=(
                "Priority",
                "Feature",
                PLANNED_INVESTMENT_LABEL,
                "CVaR 95% (worst 5%)",
                BUDGET_PRESSURE_LABEL,
            ),
            rows=rows,
            title=title,
            description=f"{BUDGET_PRESSURE_LABEL} = (CVaR 95% / planned investment) − 1.",
        )

    def budget_fit_summary_cvar(
        self,
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
        budget: float,
        *,
        title: str = "Budget Summary",
    ) -> None:
        """Render portfolio-level budget summary (planned totals only)."""
        summary = DeliveryAnalysisOperations.budget_fit_summary(
            features,
            delivery_results,
            budget,
        )
        self.metrics(
            [
                ("Scenario budget", f"EUR {budget:,.0f}", COLORS.primary),
                (
                    "Portfolio planned total",
                    f"EUR {summary['planned_total']:,.0f}",
                    COLORS.primary,
                ),
            ],
            title=title,
        )

    def budget_fit_and_select(
        self,
        features: Iterable[Feature],
        delivery_results: dict[str, DeliverySimulationResult],
        budget: float,
        *,
        summary_title: str = "Budget Summary",
        selection_title: str = "Cost Risk Selection — Minimum Portfolio CVaR 95%",
        combinations_title: str = "Feasible Combination Comparison",
    ) -> None:
        """Render budget summary and cost-risk selection in a single call.

        Convenience wrapper that computes the minimum-CVaR selection internally
        so notebooks do not need to import DeliveryAnalysisOperations directly.
        Also renders a comparison table of all budget-feasible combinations.
        """
        self.budget_fit_summary_cvar(
            features, delivery_results, budget, title=summary_title
        )
        selection = DeliveryAnalysisOperations.min_cost_cvar_selection(
            features,
            delivery_results,
            budget,
        )
        self.cost_risk_selection(selection, title=selection_title)
        combination_rows = DeliveryAnalysisOperations.cost_risk_combination_rows(
            features,
            delivery_results,
            budget,
        )
        self.samples(
            headers=(
                "Rank",
                "Selected",
                "Features",
                "Combination",
                "Planned total",
                "Budget remaining",
                "Portfolio CVaR 95%",
                BUDGET_PRESSURE_LABEL,
            ),
            rows=combination_rows,
            title=combinations_title,
            description=(
                "Sorted by objective: maximise feature count, then minimise "
                "portfolio budget pressure (CVaR 95% / planned total − 1)."
            ),
        )

    def cost_risk_selection(
        self,
        result: dict,
        *,
        title: str = "Cost Risk Selection — Minimum Portfolio CVaR 95%",
        objective: str = "Minimise portfolio CVaR 95% (worst-5% average development cost) — development simulation",
    ) -> None:
        """Render cost-risk optimisation result based on development cost scenarios.

        Shows selected features and portfolio development cost risk metrics.
        No business value metrics — purely development cost view.
        """
        selected = result.get("selected", [])
        budget_pressure = result.get("budget_pressure", 0.0)

        feature_html = self.info_html(
            "<b>Selected features:</b><br>"
            + "&nbsp;&nbsp;".join(f"✅ <b>{n.split(': ', 1)[-1]}</b>" for n in selected)
            + f"<br><small style='opacity:0.7'>{objective}</small>"
        )
        metrics_html = self.metrics_html(
            [
                (
                    "Total planned cost",
                    f"EUR {result.get('total_planned_cost', 0):,.0f}",
                    COLORS.primary,
                ),
                (
                    "Budget remaining",
                    f"EUR {result.get('budget_remaining', 0):,.0f}",
                    COLORS.secondary,
                ),
                (
                    BUDGET_PRESSURE_LABEL,
                    f"{budget_pressure:+.1%}",
                    COLORS.success if budget_pressure <= 0 else COLORS.danger,
                ),
                (
                    "Expected development cost",
                    f"EUR {result.get('expected_cost', 0):,.0f}",
                    COLORS.neutral,
                ),
                (
                    "Portfolio CaR 95%",
                    f"EUR {result.get('portfolio_car', 0):,.0f}",
                    COLORS.warning,
                ),
                (
                    "Portfolio CVaR 95% ← minimised",
                    f"EUR {result.get('portfolio_cvar', 0):,.0f}",
                    COLORS.danger,
                ),
            ],
            title=title,
        )
        self.columns(feature_html, metrics_html, min_width="320px")
