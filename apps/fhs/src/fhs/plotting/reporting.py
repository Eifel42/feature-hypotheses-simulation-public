#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""
Reporting utilities for Feature Hypotheses Simulation.
Provides clean, CIO/CFO-focused summaries and visualizations.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from fhs.core.model import PortfolioRiskResult, SimulationResult
from fhs.presentation.notebook import COLORS

EXPECTED_BUSINESS_VALUE_LABEL = "Expected Business Value"


class Reporter:
    """CIO/CFO-focused reporting and visualisation.

    All methods are ``@staticmethod`` — no instance state is needed.
    Provides summary tables (pandas), Plotly charts, and plain-text formatters.
    """

    @staticmethod
    def get_portfolio_summary(portfolio_risk: PortfolioRiskResult) -> pd.DataFrame:
        """Create a clean summary table for portfolio metrics.

        Args:
            portfolio_risk: Output of
                :meth:`PortfolioRiskAnalyzer.calculate_portfolio_risk`.

        Returns:
            DataFrame with Metric / Value columns.
        """
        metrics = portfolio_risk.portfolio_metrics
        div = portfolio_risk.diversification

        summary_data = {
            "Metric": [
                "Expected Annual Value",
                "Value at Risk (95%)",
                "Value at Risk (99%)",
                "Expected Shortfall (CVaR 95%)",
                "Portfolio Volatility",
                "Diversification Benefit",
                "Diversification Ratio",
            ],
            "Value": [
                f"€{metrics.expected_value:,.0f}",
                f"€{metrics.var_95:,.0f}",
                f"€{metrics.var_99:,.0f}",
                f"€{metrics.cvar_95:,.0f}",
                f"€{metrics.std_dev:,.0f}",
                f"€{div.diversification_benefit:,.0f}",
                f"{div.diversification_ratio:.1%}",
            ],
        }
        return pd.DataFrame(summary_data)

    @staticmethod
    def get_confidence_interval_summary(
        data: np.ndarray, confidence: float = 0.95
    ) -> dict:
        """Calculate a confidence interval using scipy *t*-distribution.

        Args:
            data: 1-D array of sample values.
            confidence: Confidence level (default 0.95).

        Returns:
            Dict with keys: mean, lower, upper, confidence.
        """
        mean = np.mean(data)
        sem = stats.sem(data)
        interval = stats.t.interval(confidence, len(data) - 1, loc=mean, scale=sem)
        return {
            "mean": mean,
            "lower": interval[0],
            "upper": interval[1],
            "confidence": confidence,
        }

    @staticmethod
    def get_feature_comparison_table(
        simulation_results: dict[str, SimulationResult],
    ) -> pd.DataFrame:
        """Create a comparative table for all simulated features.

        Args:
            simulation_results: Mapping of feature name to
                :class:`SimulationResult`.

        Returns:
            DataFrame sorted by Expected Value (descending).
        """
        rows = []
        for name, res in simulation_results.items():
            annual_installment = float(getattr(res, "annual_installment", 0.0))
            net_results = (
                res.results_array * res.business_value_per_conversion
            ) - annual_installment
            rows.append(
                {
                    "Feature": name,
                    EXPECTED_BUSINESS_VALUE_LABEL: res.expected_business_value,
                    "Annual Installment": annual_installment,
                    "Min. Net Profit (95%)": res.net_value_at_risk_95,
                    "Worst Case Profit": np.min(net_results),
                    "Success Prob. (ROI > 0)": (
                        (np.sum(net_results > 0) / len(net_results))
                        if len(net_results) > 0
                        else 0
                    ),
                }
            )

        df = pd.DataFrame(rows)

        # Sort by expected business value descending
        return df.sort_values(by=EXPECTED_BUSINESS_VALUE_LABEL, ascending=False)

    @staticmethod
    def plot_risk_distributions(simulation_results: dict[str, SimulationResult]):
        """Create a box-plot comparison of risk distributions.

        Args:
            simulation_results: Mapping of feature name to
                :class:`SimulationResult`.

        Returns:
            Plotly Figure.
        """
        fig = go.Figure()
        color_cycle = [
            COLORS.primary,
            COLORS.secondary,
            COLORS.accent,
            COLORS.danger,
            COLORS.tertiary,
        ]

        for idx, (name, res) in enumerate(simulation_results.items()):
            fig.add_trace(
                go.Box(
                    y=res.results,
                    name=name,
                    boxpoints="outliers",
                    notched=True,
                    marker_color=color_cycle[idx % len(color_cycle)],
                )
            )

        fig.update_layout(
            title="Risk Distribution Comparison (Box Plot)",
            yaxis_title="Simulated Value",
            xaxis_title="Feature",
            height=600,
            showlegend=False,
        )
        return fig

    @staticmethod
    def format_feature_assessment(assessment: dict) -> str:
        """Format a single feature assessment as readable text.

        Args:
            assessment: Output from PortfolioAdvisor.assess_feature()

        Returns:
            Formatted string for display
        """
        ci = assessment["confidence_interval"]
        return (
            f"Feature: {assessment['feature']}\n"
            f"  {EXPECTED_BUSINESS_VALUE_LABEL}:{assessment['expected_business_value']:>12,.0f}\n"
            f"  VaR (95%):             {assessment['var_95_business_value']:>12,.0f}\n"
            f"  Opportunity Cost:      {assessment['opportunity_cost']:>12,.0f}\n"
            f"  Downside Risk:         {assessment['downside_risk']:>12,.0f}\n"
            f"  Risk Ratio:            {assessment['risk_ratio']:>11.0%}\n"
            f"  Confidence Interval:   [{ci[0]:,.0f} — {ci[1]:,.0f}]\n"
            f"  {assessment['recommendation']}"
        )

    @staticmethod
    def format_portfolio_recommendation(optimization: dict) -> str:
        """Format portfolio optimization results as readable text.

        Args:
            optimization: Output from PortfolioAdvisor.optimize_portfolio()

        Returns:
            Formatted string for display
        """
        opt = optimization
        total = opt["max_features"] + len(opt["excluded_features"])
        lines = [
            f"Recommended Features ({opt['max_features']} of {total}):",
            f"  {', '.join(opt['recommended_features'])}",
            "",
            f"  Total Expected Business Value:  {opt['total_expected_business_value']:>12,.0f}",
            f"  Portfolio VaR (95%):     {opt['portfolio_var_95']:>12,.0f}",
            f"  Portfolio Risk:          {opt['portfolio_risk_ratio']:>11.0%}",
        ]

        if optimization["excluded_features"]:
            lines.append("")
            lines.append("Excluded Features:")
            for exc in optimization["excluded_features"]:
                lines.append(f"  - {exc['name']}: {exc['reason']}")

        if optimization["alternatives"]:
            lines.append("")
            lines.append("Alternatives:")
            for i, alt in enumerate(optimization["alternatives"][:3], 1):
                features_str = ", ".join(alt["features"])
                lines.append(
                    f"  {i}. [{features_str}] — "
                    f"Business Value: {alt['expected_business_value']:,.0f}, "
                    f"VaR: {alt['var_95_business_value']:,.0f}"
                )

        return "\n".join(lines)

    @staticmethod
    def plot_portfolio_optimization(optimization: dict):
        """Create a Plotly visualization of portfolio optimization results.

        Args:
            optimization: Output from PortfolioAdvisor.optimize_portfolio()

        Returns:
            Plotly figure
        """
        if not optimization.get("alternatives"):
            # Not enough data to plot
            return None

        all_combos = [
            {
                "label": ", ".join(optimization["recommended_features"]),
                "expected": optimization["total_expected_business_value"],
                "var_95": optimization["portfolio_var_95"],
                "is_best": True,
            }
        ]
        for alt in optimization["alternatives"]:
            all_combos.append(
                {
                    "label": ", ".join(alt["features"]),
                    "expected": alt["expected_business_value"],
                    "var_95": alt["var_95_business_value"],
                    "is_best": False,
                }
            )

        fig = go.Figure()

        # All alternatives
        fig.add_trace(
            go.Scatter(
                x=[c["var_95"] for c in all_combos if not c["is_best"]],
                y=[c["expected"] for c in all_combos if not c["is_best"]],
                mode="markers",
                hovertext=[c["label"] for c in all_combos if not c["is_best"]],
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    "BVF 95%: €%{x:,.0f}<br>"
                    "Expected: €%{y:,.0f}<extra></extra>"
                ),
                marker={"size": 10, "color": COLORS.primary, "opacity": 0.5},
                name="Alternatives",
            )
        )

        # Best combo
        best = [c for c in all_combos if c["is_best"]]
        fig.add_trace(
            go.Scatter(
                x=[best[0]["var_95"]],
                y=[best[0]["expected"]],
                mode="markers+text",
                text=[best[0]["label"]],
                textposition="top center",
                cliponaxis=False,
                marker={"size": 16, "color": COLORS.accent, "symbol": "star"},
                name="Recommended",
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "BVF 95%: €%{x:,.0f}<br>"
                    "Expected: €%{y:,.0f}<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            title="Portfolio Optimization: Business Value vs. Risk",
            xaxis_title="Business Value Floor 95% (Downside)",
            yaxis_title=EXPECTED_BUSINESS_VALUE_LABEL,
            height=540,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0.0,
            },
            margin={"t": 110, "b": 80, "l": 70, "r": 40},
        )
        fig.update_xaxes(automargin=True)
        fig.update_yaxes(automargin=True)
        return fig

    @staticmethod
    def plot_year1_risk_heatmap(report: dict) -> go.Figure:
        """
        Create a heatmap visualization for Year-1 Business Value at Risk.

        Args:
            report: Output from PortfolioAdvisor.generate_year1_risk_report()

        Returns:
            Plotly Figure with risk heatmap
        """
        details = report["feature_details"]

        # Extract data
        features = [d["feature"] for d in details]
        y1_rar = [d["y1_business_value_at_risk"] for d in details]
        risk_categories = [d["risk_category"] for d in details]

        # Color mapping: Green (Low), Amber (Medium), Red (High)
        color_map = {
            "Low": COLORS.secondary,
            "Medium": COLORS.warning,
            "High": COLORS.danger,
        }
        colors = [color_map[cat] for cat in risk_categories]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=features,
                y=y1_rar,
                marker={"color": colors},
                text=[f"${v:,.0f}" for v in y1_rar],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>Y1 RaR: $%{y:,.0f}<br><extra></extra>",
            )
        )

        fig.update_layout(
            title="Year-1 Business Value at Risk (Y1 BVaR) by Feature",
            xaxis_title="Feature",
            yaxis_title="Y1 Business Value at Risk ($)",
            height=540,
            showlegend=False,
            margin={"t": 120, "b": 90, "l": 70, "r": 40},
            annotations=[
                {
                    "text": "Legend: 🟢 Low Risk | 🟡 Medium Risk | 🔴 High Risk",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 1.14,
                    "showarrow": False,
                    "font": {"size": 12},
                    "xanchor": "center",
                }
            ],
        )
        fig.update_xaxes(tickangle=-24, automargin=True)
        fig.update_yaxes(automargin=True)

        return fig

    @staticmethod
    def plot_year1_risk_by_cluster(report: dict) -> go.Figure:
        """
        Create a grouped bar chart showing Y1 RaR by dependency cluster.

        Args:
            report: Output from PortfolioAdvisor.generate_year1_risk_report()

        Returns:
            Plotly Figure with clustered risk visualization
        """
        details = report["feature_details"]

        # Group by cluster
        clusters: dict[str, list[dict[str, Any]]] = {}
        for detail in details:
            cluster = detail["dependency_cluster"]
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(detail)

        fig = go.Figure()

        # Create bar for each cluster
        for cluster, items in clusters.items():
            features = [item["feature"] for item in items]
            y1_rar = [item["y1_business_value_at_risk"] for item in items]

            fig.add_trace(
                go.Bar(
                    name=cluster,
                    x=features,
                    y=y1_rar,
                    text=[f"${v:,.0f}" for v in y1_rar],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"Cluster: {cluster}<br>"
                        "Y1 BVaR: $%{y:,.0f}<br>"
                        "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title="Year-1 Business Value at Risk by Dependency Cluster",
            xaxis_title="Feature",
            yaxis_title="Y1 Business Value at Risk ($)",
            height=560,
            barmode="group",
            legend_title="Dependency Cluster",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "left",
                "x": 0.0,
            },
            margin={"t": 120, "b": 90, "l": 70, "r": 40},
        )
        fig.update_xaxes(tickangle=-24, automargin=True)
        fig.update_yaxes(automargin=True)

        return fig

    @staticmethod
    def create_year1_risk_summary_table(report: dict) -> pd.DataFrame:
        """
        Create a pandas DataFrame summary table for Year-1 Risk Report.

        Matches the required columns from business-improvements.md:
        - Feature
        - Planned Release
        - Business Value Exposure (Year 1)
        - Likelihood of Non-Delivery
        - Y1 Business Value at Risk
        - Y1 Profit at Risk (optional)
        - Dependency Cluster (optional)

        Args:
            report: Output from PortfolioAdvisor.generate_year1_risk_report()

        Returns:
            DataFrame with Year-1 risk metrics
        """
        details = report["feature_details"]

        data = []
        for detail in details:
            # Format likelihood as label
            likelihood = detail["likelihood_of_non_delivery"]
            if likelihood < 0.3:
                likelihood_label = "Low"
            elif likelihood < 0.7:
                likelihood_label = "Medium"
            else:
                likelihood_label = "High"

            row = {
                "Feature": detail["feature"],
                "Planned Release": detail["planned_release"],
                "Business Value Exposure (Year 1)": f"${detail['business_value_exposure_year1']:,.0f}",
                "Likelihood of Non-Delivery": likelihood_label,
                "Y1 Business Value at Risk": f"${detail['y1_business_value_at_risk']:,.0f}",
                "Y1 Profit at Risk": f"${detail['y1_profit_at_risk']:,.0f}",
                "Dependency Cluster": detail["dependency_cluster"],
                "Risk Category": detail["risk_category"],
            }
            data.append(row)

        return pd.DataFrame(data)
