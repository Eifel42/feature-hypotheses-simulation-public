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

"""Year-1 Business Value at Risk (Y1 BVaR) report generation and formatting."""

from __future__ import annotations

from typing import Any

from ...model import Feature


class Year1RiskReporter:
    """Generates Year-1 Business Value at Risk reports.

    Year-1 exposures are calculated from the feature's base annual business value
    (expected_users × conversion_rate × business_value_per_conversion).
    """

    @staticmethod
    def _get_business_value_exposure(feature: Feature) -> float:
        """Get Year-1 business value exposure for a feature."""
        return feature.get_base_annual_business_value()

    @staticmethod
    def _get_profit_exposure(feature: Feature) -> float:
        """Get Year-1 profit exposure for a feature.

        Profit = Business Value - Development Cost
        """
        return max(
            0.0, feature.get_base_annual_business_value() - feature.annual_installment
        )

    def generate_report(self, features: list[Feature]) -> dict[str, Any]:
        """Generate Year-1 Business Value at Risk (Y1 BVaR) and Profit at Risk report."""
        feature_details: list[dict[str, Any]] = []
        total_y1_bvar = 0.0
        total_y1_par = 0.0
        total_business_value_exposure = 0.0
        total_profit_exposure = 0.0

        for feature in features:
            business_value_exposure = self._get_business_value_exposure(feature)
            profit_exposure = self._get_profit_exposure(feature)

            y1_bvar = business_value_exposure * feature.likelihood_of_non_delivery
            y1_par = profit_exposure * feature.likelihood_of_non_delivery

            risk_category = feature.get_risk_category("business_value")

            detail = {
                "feature": feature.name,
                "planned_release": feature.planned_release or "TBD",
                "business_value_exposure_year1": business_value_exposure,
                "profit_exposure_year1": profit_exposure,
                "likelihood_of_non_delivery": feature.likelihood_of_non_delivery,
                "y1_business_value_at_risk": y1_bvar,
                "y1_profit_at_risk": y1_par,
                "risk_category": risk_category,
                "dependency_cluster": feature.dependency_cluster or "Independent",
            }
            feature_details.append(detail)

            total_y1_bvar += y1_bvar
            total_y1_par += y1_par
            total_business_value_exposure += business_value_exposure
            total_profit_exposure += profit_exposure

        feature_details.sort(
            key=lambda x: float(x["y1_business_value_at_risk"]),
            reverse=True,
        )

        risk_categories: dict[str, list[str]] = {"Low": [], "Medium": [], "High": []}
        for detail in feature_details:
            category = str(detail["risk_category"])
            risk_categories[category].append(str(detail["feature"]))

        dependency_clusters: dict[str, list[str]] = {}
        for detail in feature_details:
            cluster = str(detail["dependency_cluster"])
            if cluster not in dependency_clusters:
                dependency_clusters[cluster] = []
            dependency_clusters[cluster].append(str(detail["feature"]))

        summary = {
            "total_features": len(features),
            "total_business_value_exposure_year1": total_business_value_exposure,
            "total_profit_exposure_year1": total_profit_exposure,
            "total_y1_business_value_at_risk": total_y1_bvar,
            "total_y1_profit_at_risk": total_y1_par,
            "high_risk_features_count": len(risk_categories["High"]),
            "medium_risk_features_count": len(risk_categories["Medium"]),
            "low_risk_features_count": len(risk_categories["Low"]),
        }

        glossary = {
            "Year-1 Business Value at Risk (Y1 BVaR)": (
                "Expected business value loss in the first 12 months after release "
                "if a feature is not delivered and users churn or reduce usage."
            ),
            "Year-1 Profit at Risk (Y1 PaR)": (
                "Expected profit loss in the first 12 months after release "
                "under the same scenario."
            ),
            "Feature Delivery Risk": (
                "The risk that a planned feature is not delivered on time "
                "or not delivered at all."
            ),
            "Churn-Driven Business Value Risk": (
                "Risk of business value loss caused by users leaving due to missing features."
            ),
        }

        legend = {
            "Green": "Low Risk",
            "Amber": "Medium Risk",
            "Red": "High Risk",
            "Y1": "First 12 months after release",
        }

        return {
            "feature_details": feature_details,
            "summary": summary,
            "risk_categories": risk_categories,
            "dependency_clusters": dependency_clusters,
            "glossary": glossary,
            "legend": legend,
        }

    @staticmethod
    def format_table(report: dict[str, Any]) -> str:
        """Format Year-1 Risk Report as text table."""
        details = report["feature_details"]

        lines = [
            "=" * 120,
            "Year-1 Business Value at Risk (Y1 BVaR) Report",
            "=" * 120,
            "",
        ]

        header = (
            f"{'Feature':<25} | {'Release':<8} | "
            f"{'BV Exp (Y1)':>15} | {'Likelihood':>11} | "
            f"{'Y1 BVaR':>15} | {'Risk':<8} | {'Cluster':<20}"
        )
        lines.append(header)
        lines.append("-" * 120)

        for detail in details:
            business_value_exp = detail["business_value_exposure_year1"]
            likelihood = detail["likelihood_of_non_delivery"]
            y1_bvar = detail["y1_business_value_at_risk"]

            if likelihood < 0.3:
                likelihood_label = "Low"  # pragma: no cover - defensive
            elif likelihood < 0.7:
                likelihood_label = "Medium"
            else:
                likelihood_label = "High"  # pragma: no cover - defensive

            row = (
                f"{detail['feature']:<25} | {detail['planned_release']:<8} | "
                f"${business_value_exp:>14,.0f} | {likelihood_label:>11} | "
                f"${y1_bvar:>14,.0f} | {detail['risk_category']:<8} | "
                f"{detail['dependency_cluster']:<20}"
            )
            lines.append(row)

        lines.append("=" * 120)
        lines.append("")

        summary = report["summary"]
        lines.append("Summary:")
        lines.append(
            f"  Total Y1 Business Value at Risk: ${summary['total_y1_business_value_at_risk']:,.0f}"
        )
        lines.append(f"  High Risk Features: {summary['high_risk_features_count']}")
        lines.append(f"  Medium Risk Features: {summary['medium_risk_features_count']}")
        lines.append(f"  Low Risk Features: {summary['low_risk_features_count']}")
        lines.append("")

        lines.append("Legend:")
        for key, value in report["legend"].items():
            lines.append(f"  {key}: {value}")
        lines.append("")

        return "\n".join(lines)
