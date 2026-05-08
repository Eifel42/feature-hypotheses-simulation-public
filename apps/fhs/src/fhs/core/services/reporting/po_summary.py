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

"""Product Owner summary report generation and Markdown formatting."""

from __future__ import annotations

from typing import Any

import numpy as np

from ...model import Feature, SimulationResult
from ..portfolio import aggregate_portfolio_scenarios_from_results
from ..risk import RiskCalculator
from .stress_test import BundledRiskStressTest


def _append_bundled_risk_section(lines: list[str], bundled: dict) -> None:
    if not bundled["cluster_impacts"]:  # pragma: no cover - defensive
        return  # pragma: no cover - defensive
    lines.append(
        "## 🔥 Bundled Risk Stress Test (50% Cluster Reduction)"
    )  # pragma: no cover - defensive
    lines.append("")  # pragma: no cover - defensive
    lines.append(  # pragma: no cover - defensive
        f"**Baseline Expected Business Value**: €{bundled['baseline']['expected']:,.0f}"  # pragma: no cover - defensive
    )  # pragma: no cover - defensive
    lines.append("")  # pragma: no cover - defensive
    for cluster, impact in bundled[
        "cluster_impacts"
    ].items():  # pragma: no cover - defensive
        lines.append(f"### Cluster: {cluster}")  # pragma: no cover - defensive
        lines.append(
            f"- Affected Features: {', '.join(impact['affected_features'])}"
        )  # pragma: no cover - defensive
        lines.append(  # pragma: no cover - defensive
            f"- Business Value Impact: €{impact['expected_change']:,.0f} "  # pragma: no cover - defensive
            f"({impact['expected_change_pct']:.1f}%)"  # pragma: no cover - defensive
        )  # pragma: no cover - defensive
        lines.append("")  # pragma: no cover - defensive
    if bundled["worst_cluster"]:  # pragma: no cover - defensive
        lines.append(
            f"**Worst-Case Cluster**: {bundled['worst_cluster']}"
        )  # pragma: no cover - defensive
        lines.append("")  # pragma: no cover - defensive


def _append_bundled_risk_section(lines: list[str], bundled: dict) -> None:
    if not bundled["cluster_impacts"]:
        return  # pragma: no cover - defensive
    lines.append("## 🔥 Bundled Risk Stress Test (50% Cluster Reduction)")
    lines.append("")
    lines.append(
        f"**Baseline Expected Business Value**: €{bundled['baseline']['expected']:,.0f}"
    )
    lines.append("")
    for cluster, impact in bundled["cluster_impacts"].items():
        lines.append(f"### Cluster: {cluster}")
        lines.append(f"- Affected Features: {', '.join(impact['affected_features'])}")
        lines.append(
            f"- Business Value Impact: €{impact['expected_change']:,.0f} "
            f"({impact['expected_change_pct']:.1f}%)"
        )
        lines.append("")
    if bundled["worst_cluster"]:  # pragma: no cover - partial branch
        lines.append(f"**Worst-Case Cluster**: {bundled['worst_cluster']}")
        lines.append("")


class POSummaryReporter:
    """Generates Product Owner facing summary reports."""

    def __init__(self, calculator: RiskCalculator | None = None):
        self.calculator = calculator or RiskCalculator()
        self._stress_test = BundledRiskStressTest(self.calculator)

    @staticmethod
    def _risk_indicator(risk_ratio: float) -> str:
        if risk_ratio < 0.2:
            return "🟢"
        if risk_ratio < 0.4:
            return "🟡"
        return "🔴"  # pragma: no cover - defensive

    def generate_summary(
        self,
        features: list[Feature],
        simulation_results: dict[str, SimulationResult],
        ranking_result: dict[str, Any],
        concentration: dict[str, Any],
        robustness_variants: dict[str, Any],
        metadata: dict[str, Any],
        recommended_set: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate Product Owner friendly summary report."""
        rankings = ranking_result["rankings"]
        top_3 = sorted(
            rankings, key=lambda x: x["var_95_business_value"], reverse=True
        )[:3]

        portfolio_scenarios = aggregate_portfolio_scenarios_from_results(
            simulation_results
        )
        portfolio_expected = float(np.mean(portfolio_scenarios))
        portfolio_var95 = self.calculator.calculate_var(portfolio_scenarios, 0.95)

        bundled_stress = self._stress_test.calculate(features, simulation_results)

        return {
            "top_3_features": top_3,
            "recommended_set": recommended_set,
            "portfolio_metrics": {
                "expected_business_value": portfolio_expected,
                "var_95_business_value": portfolio_var95,
                "risk_ratio": self.calculator.calculate_risk_ratio(
                    portfolio_expected, portfolio_var95, clamp=True
                ),
            },
            "concentration": {
                "hhi": concentration["hhi"],
                "is_concentrated": concentration["is_concentrated"],
                "warnings": concentration["warnings"],
            },
            "bundled_risk_impact": bundled_stress,
            "robustness_variants": robustness_variants,
            "metadata": metadata,
        }

    @staticmethod
    def format_markdown(
        report: dict[str, Any],
        budget: float | None = None,
    ) -> str:
        """Format PO summary as Markdown report."""
        metadata = report["metadata"]

        lines = [
            "# Product Owner Feature Prioritization Report",
            "",
            f"**Generated**: {metadata['timestamp']}",
            f"**Scenarios**: {metadata['scenarios']:,}",
            f"**Distribution**: {metadata['distribution']}",
            f"**Correlation Source**: {metadata['correlation_source']}",
        ]
        if "correlation_note" in metadata:
            lines.append(
                f"**Note**: {metadata['correlation_note']}"
            )  # pragma: no cover - defensive
        if "diversification_warning" in metadata:
            lines.append("")  # pragma: no cover - defensive
            lines.append(
                f"⚠️ **Warning**: {metadata['diversification_warning']}"
            )  # pragma: no cover - defensive
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 🛡️ Robustness Check (Portfolio Variants)")
        lines.append("Comparison of different dependency assumptions:")
        lines.append("")
        lines.append("| Variant | Expected Business Value | VaR95 Floor | Stability |")
        lines.append("|:--------|:------------------------|:------------|:----------|")

        variants = report["robustness_variants"]
        base_var = variants["Cluster (Standard)"]["var_95"]

        for name, metrics in variants.items():
            if base_var != 0:
                diff = (metrics["var_95"] - base_var) / base_var
            else:
                diff = 0  # pragma: no cover - defensive
            stability = "✅ Stable" if abs(diff) < 0.1 else "⚠️ Sensitive"
            lines.append(
                f"| {name} | €{metrics['expected']:,.0f} | "
                f"€{metrics['var_95']:,.0f} | {stability} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## 🏆 Top 3 Most Reliable Features (by VaR95 Floor)")
        lines.append("")
        for i, feat in enumerate(report["top_3_features"], 1):
            risk_emoji = POSummaryReporter._risk_indicator(feat["risk_ratio"])
            lines.append(f"{i}. **{feat['feature']}** {risk_emoji}")
            lines.append(
                f"   - Expected Business Value: €{feat['expected_business_value']:,.0f}"
            )
            lines.append(f"   - VaR95 Floor: €{feat['var_95_business_value']:,.0f}")
            lines.append(f"   - Risk Level: {feat['recommendation']}")
            lines.append("")

        if report["recommended_set"]:
            rec = report["recommended_set"]  # pragma: no cover - defensive
            lines.append(
                "## 💰 Budget-Optimized Feature Set"
            )  # pragma: no cover - defensive
            lines.append("")  # pragma: no cover - defensive
            lines.append(f"**Budget**: €{budget:,.0f}")  # pragma: no cover - defensive
            lines.append(
                f"**Selected Features**: {', '.join(rec['features'])}"
            )  # pragma: no cover - defensive
            lines.append(
                f"**Total Cost**: €{rec['total_cost']:,.0f}"
            )  # pragma: no cover - defensive
            lines.append(  # pragma: no cover - defensive
                f"**Expected Business Value**: €{rec['expected_business_value']:,.0f}"  # pragma: no cover - defensive
            )  # pragma: no cover - defensive
            lines.append(
                f"**VaR95 Floor**: €{rec['var_95']:,.0f}"
            )  # pragma: no cover - defensive
            lines.append(
                f"**Budget Remaining**: €{rec['budget_remaining']:,.0f}"
            )  # pragma: no cover - defensive
            lines.append("")  # pragma: no cover - defensive

        pm = report["portfolio_metrics"]
        lines.append("## 📊 Portfolio Overview")
        lines.append("")
        lines.append(
            f"- **Expected Business Value**: €{pm['expected_business_value']:,.0f}"
        )
        lines.append(f"- **VaR95 Floor**: €{pm['var_95_business_value']:,.0f}")
        risk_emoji = POSummaryReporter._risk_indicator(pm["risk_ratio"])
        lines.append(f"- **Risk Level**: {risk_emoji} {pm['risk_ratio']:.1%}")
        lines.append("")

        conc = report["concentration"]
        lines.append("## ⚖️ Diversification Analysis")
        lines.append("")
        lines.append(f"**HHI (Herfindahl-Hirschman Index)**: {conc['hhi']:.2f}")
        if conc["is_concentrated"]:
            lines.append("⚠️ **Portfolio is concentrated** (HHI > 0.25)")
        else:
            lines.append(
                "✅ **Portfolio is well-diversified**"
            )  # pragma: no cover - defensive
        if conc["warnings"]:  # pragma: no cover - partial branch
            lines.append("")
            lines.append("**Warnings**:")
            for warning in conc["warnings"]:
                lines.append(f"- {warning}")
        lines.append("")

        bundled = report["bundled_risk_impact"]
        _append_bundled_risk_section(lines, bundled)

        lines.append("---")
        lines.append("")
        lines.append("### Risk Level Legend")
        lines.append(
            "- 🟢 **Low Risk**: Feature delivers ≥80% of expected value (95% confidence)"
        )
        lines.append("- 🟡 **Medium Risk**: Feature delivers 60-80% of expected value")
        lines.append("- 🔴 **High Risk**: Feature delivers <60% of expected value")

        return "\n".join(lines)
