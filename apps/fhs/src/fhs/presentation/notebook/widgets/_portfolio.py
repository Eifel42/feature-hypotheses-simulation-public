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

"""Portfolio and decision-support methods."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fhs.application.decision_operations import FeatureSelectionView
    from fhs.core.model import DeliveryRiskConfig
    from fhs.core.model.value_objects.multi_year_result import MultiYearResult

from ..formatters import format_budget_status, format_multi_year_result
from .cards import (
    feature_risk_card,
    feature_scorecard,
    portfolio_summary_card,
)
from .comparison import solver_comparison_card
from .portfolio import optimizer_results_card, selection_card
from .primitives import (
    kpi_card,
    kpi_row,
)
from .tables import (
    backlog_table,
    comparison_table,
)

PLANNED_SPRINTS_LABEL = "Planned sprints"
PLANNED_INVESTMENT_LABEL = "Planned investment"
FLOOR_BVF_95_LABEL = "Floor (BVF 95%)"
EXPECTED_BUSINESS_VALUE_LABEL = "Expected Business Value"


class _PortfolioMixin:
    # Lightweight stubs to help static type checkers. The real host class that
    # mixes in _PortfolioMixin provides concrete implementations for these
    # methods; these definitions only exist to make mypy happy and are no-ops.
    # noinspection PyUnusedLocal
    def __call__(self, html: str) -> None:  # pragma: no cover - stub for typing
        """Callable host stub used by mixin methods that emit HTML blocks."""
        del html

    # noinspection PyUnusedLocal
    @staticmethod
    def metrics(
        rows: list[tuple], *, title: str = ""
    ) -> None:  # pragma: no cover - stub
        del rows, title

    # noinspection PyUnusedLocal
    @staticmethod
    def danger(msg: str) -> None:  # pragma: no cover - stub
        del msg

    # noinspection PyUnusedLocal
    @staticmethod
    def warning(msg: str) -> None:  # pragma: no cover - stub
        del msg

    # noinspection PyUnusedLocal
    @staticmethod
    def success(msg: str) -> None:  # pragma: no cover - stub
        del msg

    # noinspection PyUnusedLocal
    @staticmethod
    def note(msg: str, *, compact: bool = False) -> None:  # pragma: no cover - stub
        del msg, compact

    # noinspection PyUnusedLocal
    def sensitivity(
        self,
        rows: list[tuple[Any, ...]],
        headers: tuple[str, ...],
        *,
        title: str,
    ) -> None:  # pragma: no cover - stub
        del rows, headers, title

    # noinspection PyUnusedLocal
    def sensitivity_html(
        self,
        rows: list[tuple[Any, ...]],
        headers: tuple[str, ...],
        *,
        title: str,
    ) -> str:  # pragma: no cover - stub
        del rows, headers, title
        return ""

    # noinspection PyUnusedLocal
    @staticmethod
    def info(msg: str) -> None:  # pragma: no cover - stub
        del msg

    # noinspection PyUnusedLocal
    @staticmethod
    def grid(items: list[dict], *, title: str = "") -> None:  # pragma: no cover - stub
        del items, title

    def portfolio(
        self,
        expected: float,
        var95: float,
        std: float,
        *,
        cvar95: float | None = None,
        title: str = "Portfolio Summary",
    ) -> None:
        self(portfolio_summary_card(expected, var95, std, cvar95=cvar95, title=title))

    def kpi(self, *cards: str) -> None:
        self(kpi_row(*cards))

    @staticmethod
    def kpi_card(value: str, label: str, *, color: str | None = None) -> str:
        """Return a KPI card HTML fragment for use in composite rows."""
        return kpi_card(value, label, color=color)

    @staticmethod
    def feature_risk_card(
        name: str,
        expected_eur: float,
        var95_eur: float,
        risk_ratio: float,
        *,
        cvar95_eur: float = 0.0,
        icon: str = "📊",
        color: str | None = None,
    ) -> str:
        """Return a feature-risk card HTML fragment for scorecards."""
        return feature_risk_card(
            name,
            expected_eur,
            var95_eur,
            risk_ratio,
            cvar95_eur=cvar95_eur,
            icon=icon,
            color=color,
        )

    def comparison(
        self,
        rows: list[tuple[str, float, float, float]],
        *,
        headers: tuple[str, str, str, str] = ("Feature", "Expected", "VaR95", "CVaR95"),
        title: str = "Risk Comparison",
    ) -> None:
        self(comparison_table(rows, headers=headers, title=title))

    def budget_status(
        self,
        budget: float,
        features: list,
        *,
        source: str | None = None,
        scenarios: int | None = None,
        title: str = "Budget Check",
    ) -> None:
        summary = format_budget_status(
            features,
            budget,
            source=source,
            scenarios=scenarios,
        )
        self.metrics(summary["rows"], title=title)
        if summary["level"] == "danger":
            self.danger(summary["message"])
        elif summary["level"] == "warning":
            self.warning(summary["message"])
        else:
            self.success(summary["message"])

        if summary.get("note"):
            self.note(summary["note"], compact=True)

    def multi_year(
        self,
        result: MultiYearResult,
        annual_installment: float = 0.0,
        installment_years: int = 0,
        development_cost: float = 0.0,
    ) -> None:
        """Display a multi-year simulation result card.

        Parameters
        ----------
        result:
            ``MultiYearResult`` object.
        annual_installment:
            Annual installment charge in EUR. When > 0, an additional
            "Annual Installment" row is shown in the result card.
        installment_years:
            Installment period in years. When > 1, the row label includes
            the period (e.g. "Installment (3 yrs)").
        development_cost:
            Total development cost in EUR. When > 0, a "Total Investment" row
            is shown with the year-1 charge share.
        """
        self(
            format_multi_year_result(
                result,
                annual_installment=annual_installment,
                installment_years=installment_years,
                development_cost=development_cost,
            )
        )

    def backlog(
        self,
        features: list,
        strategy: dict,
        *,
        title: str = "Feature Backlog",
        expected_business_value_func: Callable[[Any], float] | None = None,
        standalone_roi_func: Callable[[Any], float] | None = None,
    ) -> None:
        self(
            backlog_table(
                features,
                strategy,
                title=title,
                expected_business_value_func=expected_business_value_func,
                standalone_roi_func=standalone_roi_func,
            )
        )

    def selection(
        self,
        selected_features: list[str],
        metrics: dict,
        *,
        title: str = "Recommended Selection",
        accent: str | None = None,
        excluded_features: list | None = None,
    ) -> None:
        self(
            selection_card(
                selected_features,
                metrics,
                title=title,
                accent=accent,
                excluded_features=excluded_features,
            )
        )

    def optimizer(
        self,
        selected: list[str],
        total_cost: float,
        expected_business_value: float,
        var95: float,
        budget_remaining: float,
        *,
        title: str = "Optimization Results",
        roi: float | None = None,
        net_value: float | None = None,
        cvar95: float | None = None,
        budget_pressure: float | None = None,
        objective: str | None = None,
        accent: str | None = None,
    ) -> None:
        self(
            optimizer_results_card(
                selected,
                total_cost,
                expected_business_value,
                var95,
                budget_remaining,
                title=title,
                roi=roi,
                net_value=net_value,
                cvar95=cvar95,
                budget_pressure=budget_pressure,
                objective=objective,
                accent=accent,
            )
        )

    def scorecard(
        self, cards: list[str], *, title: str = "Executive Scorecard"
    ) -> None:
        self(feature_scorecard(cards, title=title))

    def solver_compare(self, *solvers: dict, **kwargs: Any) -> None:
        self(solver_comparison_card(*solvers, **kwargs))

    @staticmethod
    def _sprint_plan_rows(
        features: Iterable[Any],
        _delivery_config: DeliveryRiskConfig,
    ) -> list[tuple[str, ...]]:
        """Compute sprint plan rows without displaying."""
        rows: list[tuple[str, ...]] = []
        sprint_length_weeks = float(_delivery_config.sprint_length_weeks)
        for feature in features:
            planned_weeks = float(getattr(feature, "development_weeks", 0.0) or 0.0)
            planned_sprints = max(1, math.ceil(planned_weeks / sprint_length_weeks))
            rows.append(
                (
                    str(feature.name).split(": ", 1)[-1],
                    f"{planned_weeks:.1f}",
                    str(planned_sprints),
                    f"EUR {float(feature.development_cost):,.0f}",
                )
            )
        return rows

    def sprint_plan(
        self,
        features: Iterable[Any],
        delivery_config: DeliveryRiskConfig,
        *,
        title: str = "Sprint Plan per Feature",
    ) -> list[tuple[str, ...]]:
        """Render a standardized sprint-plan table and return its rows."""
        rows = self._sprint_plan_rows(features, delivery_config)
        self.sensitivity(
            rows=rows,
            headers=(
                "Feature",
                "Planned weeks",
                PLANNED_SPRINTS_LABEL,
                PLANNED_INVESTMENT_LABEL,
            ),
            title=title,
        )
        return rows

    def sprint_plan_html(
        self,
        features: Iterable[Any],
        delivery_config: DeliveryRiskConfig,
        *,
        title: str = "Sprint Plan per Feature",
    ) -> tuple[str, list[tuple[str, ...]]]:
        """Return (html, rows) for the sprint-plan table without displaying.

        Use with ``show.columns()`` to place the table beside another block::

            sprint_html, plan_rows = show.sprint_plan_html(features, delivery_config)
            show.columns(sprint_html, show.metrics_html([...]))
        """
        rows = self._sprint_plan_rows(features, delivery_config)
        html = self.sensitivity_html(
            rows,
            (
                "Feature",
                "Planned weeks",
                PLANNED_SPRINTS_LABEL,
                PLANNED_INVESTMENT_LABEL,
            ),
            title=title,
        )
        return html, rows

    def delay_summary(
        self,
        delivery_results: dict[str, Any],
        *,
        feature_names: Iterable[str] | None = None,
        title: str = "Sprint Overrun Summary",
    ) -> None:
        """Render a standardized sprint-overrun summary table and return its rows."""
        ordered_names = (
            [name for name in feature_names if name in delivery_results]
            if feature_names is not None
            else sorted(delivery_results)
        )

        rows = [
            (
                name.split(": ", 1)[-1],
                str(delivery_results[name].planned_sprints),
                str(delivery_results[name].sprints_p50),
                str(delivery_results[name].sprints_p75),
                str(delivery_results[name].sprints_p95),
                f"+{delivery_results[name].sprints_p50 - delivery_results[name].planned_sprints}",
                f"+{delivery_results[name].sprints_p75 - delivery_results[name].planned_sprints}",
                f"+{delivery_results[name].sprints_p95 - delivery_results[name].planned_sprints}",
                f"{delivery_results[name].cancelled_pct:.1%}",
            )
            for name in ordered_names
        ]

        self.sensitivity(
            rows=rows,
            headers=(
                "Feature",
                PLANNED_SPRINTS_LABEL,
                "P50 actual",
                "P75 actual",
                "P95 actual",
                "P50 overrun",
                "P75 overrun",
                "P95 overrun",
                "Cancelled %",
            ),
            title=title,
        )

    def cost_comparison(
        self,
        features: Iterable[Any],
        delivery_results: dict[str, Any],
        *,
        title: str = "Feature Investment vs Development Burn Cost",
    ) -> None:
        """Render a standardized cost-comparison table and return its rows."""
        rows: list[tuple[str, ...]] = []
        for feature in features:
            result = delivery_results.get(feature.name)
            if result is None:
                continue
            planned_investment = float(feature.development_cost)
            cost_uplift = float(getattr(result, "cost_uplift", 0.0))
            planned_delivery = (
                float(result.expected_actual_cost) / (1.0 + cost_uplift)
                if (1.0 + cost_uplift) > 0
                else 0.0
            )
            expected = float(result.expected_actual_cost)
            p95 = float(result.cost_p95)
            uplift = (
                (expected / planned_delivery - 1.0) if planned_delivery > 0 else 0.0
            )
            rows.append(
                (
                    str(feature.name).split(": ", 1)[-1],
                    f"EUR {planned_investment:,.0f}",
                    f"EUR {planned_delivery:,.0f}",
                    f"EUR {expected:,.0f}",
                    f"EUR {p95:,.0f}",
                    f"{uplift:+.1%}",
                )
            )

        self.sensitivity(
            rows=rows,
            headers=(
                "Feature",
                "Planned feature investment",
                "Planned development burn",
                "Expected development burn",
                "P95 development burn",
                "Burn uplift vs plan",
            ),
            title=title,
        )

    def delivery_cost_risk(
        self,
        features: Iterable[Any],
        delivery_results: dict[str, Any],
        *,
        title: str = "Development Cost Risk — Cost at Risk (CaR) & CVaR",
    ) -> None:
        """Render a VaR/CVaR development cost risk table.

        Columns: Feature | Planned investment | Expected cost |
                 Cost at Risk 95% (CaR) | CVaR (worst-5% avg) |
                 Uplift vs plan | Cancelled %
        """
        rows: list[tuple[str, ...]] = []
        for feature in features:
            result = delivery_results.get(feature.name)
            if result is None:
                continue
            planned = float(feature.development_cost)
            expected = float(result.expected_actual_cost)
            car95 = float(result.cost_p95)
            cvar = float(getattr(result, "cost_cvar", car95))
            uplift = (expected / planned - 1.0) if planned > 0 else 0.0
            cancelled = float(getattr(result, "cancelled_pct", 0.0))
            rows.append(
                (
                    str(feature.name).split(": ", 1)[-1],
                    f"EUR {planned:,.0f}",
                    f"EUR {expected:,.0f}",
                    f"EUR {car95:,.0f}",
                    f"EUR {cvar:,.0f}",
                    f"{uplift:+.1%}",
                    f"{cancelled:.1%}",
                )
            )
        self.sensitivity(
            rows=rows,
            headers=(
                "Feature",
                PLANNED_INVESTMENT_LABEL,
                "Expected cost",
                "Cost at Risk 95% (CaR)",
                "CVaR (worst 5% avg)",
                "Uplift vs plan",
                "Cancelled %",
            ),
            title=title,
        )

    def solver_results(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Optimization Result Table",
    ) -> None:
        """Render the standardized solver-comparison result table."""
        self.sensitivity(
            rows,
            (
                "Method",
                "Num Features",
                "Cost",
                "Expected",
                FLOOR_BVF_95_LABEL,
                "ROI",
                "Safety Buffer",
                "Runtime",
            ),
            title=title,
        )

    def selected_portfolio_details(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Selected Portfolio Details",
    ) -> None:
        """Render standardized selected-portfolio detail rows."""
        self.sensitivity(
            rows,
            (
                "Selected Feature",
                "Strategy Category",
                "Cost",
                EXPECTED_BUSINESS_VALUE_LABEL,
                FLOOR_BVF_95_LABEL,
            ),
            title=title,
        )

    def practical_decision_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Practical Decision Table",
    ) -> None:
        """Render the standard practical decision table for budget-level actions."""
        self.sensitivity(
            rows,
            (
                "Budget Level",
                "Budget",
                "ILP Selection",
                "Selection Note",
                "Backlog Guidance",
                "Expected",
                FLOOR_BVF_95_LABEL,
                "Safety Buffer",
                "Remaining Budget",
                "Suggested Action",
            ),
            title=title,
        )

    def feature_value_risk_baseline(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Blockchain Features - Value and Outage Risk Baseline",
    ) -> None:
        """Render the standard baseline table with cost/business-value/floor/LLP columns."""
        self.sensitivity(
            rows,
            (
                "Key",
                "Feature",
                "Cost",
                EXPECTED_BUSINESS_VALUE_LABEL,
                "Business Value Floor (BVF 95%)",
                "LLP",
                "Risk Zone",
            ),
            title=title,
        )

    def ilp_selection_explanation(
        self,
        selection: FeatureSelectionView,
        *,
        title: str = "Why ILP may skip affordable features",
    ) -> None:
        """Render the ILP selection explanation table from feature_selection_view output."""
        rows = list(selection.rows)
        headers = tuple(selection.headers)
        self.sensitivity(
            rows,
            headers,
            title=title,
        )

    def feature_profitability_matrix(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Feature Profitability Matrix",
    ) -> None:
        """Render the standard development-risk profitability matrix per feature."""
        self.sensitivity(
            rows,
            (
                "Feature",
                "Break-even probability",
                "Expected profit",
                "Expected loss",
                "Loss at Risk 95%",
                "Profit margin",
            ),
            title=title,
        )

    def feature_ranking_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Feature Ranking Table",
    ) -> None:
        """Render the standard feature ranking table used in advanced advisor views."""
        self.sensitivity(
            rows,
            (
                "Rank",
                "Feature",
                "Cost",
                EXPECTED_BUSINESS_VALUE_LABEL,
                "Business Value Floor (BVF 95%)",
                "LLP",
            ),
            title=title,
        )

    def npv_comparison(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "Feature NPV Comparison",
    ) -> None:
        """Render the feature-level NPV comparison table with PI."""
        self.sensitivity(
            rows,
            (
                "Feature",
                "Upfront Investment",
                "NPV (Year 1)",
                "NPV (3 Years)",
                "PI (3Y)",
            ),
            title=title,
        )

    def npv_decision_table(
        self,
        rows: list[tuple[str, ...]],
        *,
        title: str = "NPV Decision Table",
    ) -> None:
        """Render the NPV-based decision table with budget x horizon view."""
        self.sensitivity(
            rows,
            (
                "Budget Level",
                "Budget (EUR)",
                "Horizon",
                "ILP Selection",
                "Portfolio NPV",
                "Suggested Action",
            ),
            title=title,
        )

    def feature_overview(
        self,
        features: list,
        strategy: dict,
        *,
        config_path: str | None = None,
        colors: dict[str, str] | None = None,
        grid_title: str = "Hypothesis details (live from YAML)",
        backlog_title: str = "Table view (live from YAML)",
        expected_business_value_func: Callable[[Any], float] | None = None,
        standalone_roi_func: Callable[[Any], float] | None = None,
    ) -> None:
        """Display feature overview grid and backlog table.

        Combines a visual grid of feature details with a tabular backlog view.
        All formatting is handled internally — no format strings needed in notebooks.

        Args:
            features: Feature objects to display.
            strategy: Strategy config dict (maps feature name to strategy info dict).
            config_path: Path to the config file, shown as a header info box.
            colors: Optional dict mapping feature key (e.g. "H1") to a color string.
            grid_title: Title for the grid widget.
            backlog_title: Title for the backlog table.
            expected_business_value_func: Optional callable for expected business value per feature.
            standalone_roi_func: Optional callable for standalone ROI per feature.
        """
        if config_path:
            self.info(f"📂 Config source: {config_path}")

        config_name = config_path.split("/")[-1] if config_path else "config"
        _colors = colors or {}
        grid_items = []

        for feature in features:
            key = (
                feature.name.split(":")[0].strip()
                if ":" in feature.name
                else feature.name
            )
            short = (
                feature.name.split(": ", 1)[-1]
                if ": " in feature.name
                else feature.name
            )
            strategy_info = strategy.get(feature.name, {})
            grid_items.append(
                {
                    "title": f"{key} — {short}",
                    "color": _colors.get(key),
                    "description": f"Live from {config_name}",
                    "bullets": [
                        f"📋 Strategy: {strategy_info.get('category', 'Unknown')}",
                        f"👥 Expected users: {feature.expected_users:,}",
                        f"✅ Conversion: {feature.conversion_rate:.0%} ({feature.acceptance_model} model)",
                        f"💶 Value per conversion: €{feature.business_value_per_conversion:,.2f}",
                        f"🤷 Uncertainty: ±{feature.uncertainty:.0%}",
                        f"💰 Dev cost: €{feature.development_cost:,.0f}",
                        f"🛡️ Non-completion risk: {feature.likelihood_of_non_delivery:.0%}",
                        f"🔗 Dependency: {feature.dependency_cluster or '—'}",
                        f"📆 Release: {feature.planned_release or '—'}",
                        f"📉 Installment: {feature.installment_years} year{'s' if feature.installment_years != 1 else ''} (€{feature.annual_installment:,.0f}/yr)",
                        f"💣 Year-1 development risk: €{feature.year1_business_value_at_risk:,.0f}",
                    ],
                    "rule": strategy_info.get("reason"),
                }
            )

        self.grid(grid_items, title=grid_title)
        self.backlog(
            features,
            strategy,
            title=backlog_title,
            expected_business_value_func=expected_business_value_func,
            standalone_roi_func=standalone_roi_func,
        )
