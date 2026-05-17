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
Free-Format Export Utilities (CSV + JSON)

Exports portfolio optimization results and 3-year forecasts to open formats:
- CSV: Human-readable, Excel/LibreOffice compatible
- JSON: Machine-readable, API-friendly
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import numpy_financial as npf
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    npf = None

from fhs.core.model import Feature


class PortfolioExporter:
    """Export portfolio optimization results to free formats (CSV/JSON)."""

    def __init__(self, features: list[Feature], discount_rate: float = 0.10):
        """
        Initialize exporter.

        Args:
            features: List of Feature objects
            discount_rate: Annual discount rate for NPV calculations
        """
        self.features = features
        self.discount_rate = discount_rate

    def export_3y_forecast_csv(
        self, filepath: str | Path, selected_features: list[str] | None = None
    ) -> str:
        """
        Export 3-year business value forecasts to CSV.

        Args:
            filepath: Output file path (e.g., "portfolio_forecast.csv")
            selected_features: Optional list of feature names to include
                (if None, exports all features)

        Returns:
            Absolute path to created CSV file
        """
        filepath = Path(filepath)
        features_to_export = (
            [f for f in self.features if f.name in selected_features]
            if selected_features
            else self.features
        )

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Feature",
                    "Development Cost (EUR)",
                    "Year 1 Business Value (EUR)",
                    "Year 2 Business Value (EUR)",
                    "Year 3 Business Value (EUR)",
                    "Total 3Y Business Value (EUR)",
                    "Annual Growth Rate",
                    "Dependency Cluster",
                ]
            )

            # Data rows
            total_cost = 0.0
            total_y1, total_y2, total_y3 = 0.0, 0.0, 0.0

            for feature in features_to_export:
                base = feature.get_base_annual_business_value()
                growth = feature.annual_growth_rate
                forecast = [base * (1 + growth) ** yr for yr in range(3)]
                total_3y = sum(forecast)

                writer.writerow(
                    [
                        feature.name,
                        f"{feature.development_cost:.2f}",
                        f"{forecast[0]:.2f}",
                        f"{forecast[1]:.2f}",
                        f"{forecast[2]:.2f}",
                        f"{total_3y:.2f}",
                        f"{feature.annual_growth_rate:.2%}",
                        feature.dependency_cluster or "Independent",
                    ]
                )

                total_cost += feature.development_cost
                total_y1 += forecast[0]
                total_y2 += forecast[1]
                total_y3 += forecast[2]

            # Summary row
            writer.writerow([])
            writer.writerow(
                [
                    "PORTFOLIO TOTAL",
                    f"{total_cost:.2f}",
                    f"{total_y1:.2f}",
                    f"{total_y2:.2f}",
                    f"{total_y3:.2f}",
                    f"{total_y1 + total_y2 + total_y3:.2f}",
                    "",
                    "",
                ]
            )

            # Business metrics
            total_business_value_3y = total_y1 + total_y2 + total_y3
            roi_3y = (
                (total_business_value_3y - total_cost) / total_cost * 100
                if total_cost > 0
                else 0.0
            )

            writer.writerow([])
            writer.writerow(["Business Metrics", ""])
            writer.writerow(["3-Year ROI (%)", f"{roi_3y:.2f}"])
            writer.writerow(
                [
                    "Export Date",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return str(filepath.absolute())

    @staticmethod
    def export_optimization_result_csv(
        result: dict[str, Any], filepath: str | Path
    ) -> str:
        """
        Export optimization result to CSV.

        Args:
            result: Optimization result dictionary from PortfolioOptimizer
            filepath: Output file path

        Returns:
            Absolute path to created CSV file
        """
        filepath = Path(filepath)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(["Portfolio Optimization Result"])
            writer.writerow([])

            # Solver info
            writer.writerow(["Solver", result.get("solver", "unknown")])
            writer.writerow(["Strategy", result.get("strategy", "unknown")])
            writer.writerow(
                [
                    "Computation Time (seconds)",
                    f"{result.get('computation_time_sec', 0):.4f}",
                ]
            )
            if "combinations_evaluated" in result:  # pragma: no cover - partial branch
                writer.writerow(
                    ["Combinations Evaluated", result["combinations_evaluated"]]
                )
            if "candidates_evaluated" in result:
                writer.writerow(  # pragma: no cover - defensive
                    ["Candidates Evaluated", result["candidates_evaluated"]]
                )

            writer.writerow([])

            # Budget
            writer.writerow(["Budget (EUR)", f"{result.get('budget', 0):.2f}"])
            writer.writerow(["Total Cost (EUR)", f"{result.get('total_cost', 0):.2f}"])
            writer.writerow(
                [
                    "Budget Remaining (EUR)",
                    f"{result.get('budget_remaining', 0):.2f}",
                ]
            )

            writer.writerow([])

            # Portfolio metrics
            writer.writerow(["Portfolio Metrics", ""])
            writer.writerow(
                [
                    "Expected Business Value (EUR)",
                    f"{result.get('portfolio_expected', 0):.2f}",
                ]
            )
            writer.writerow(
                [
                    "VaR95 Floor (EUR)",
                    f"{result.get('portfolio_var_95', 0):.2f}",
                ]
            )
            writer.writerow(
                [
                    "CVaR95 (EUR)",
                    f"{result.get('portfolio_cvar_95', 0):.2f}",
                ]
            )
            writer.writerow(
                [
                    "Standard Deviation (EUR)",
                    f"{result.get('portfolio_std_dev', 0):.2f}",
                ]
            )

            writer.writerow([])

            # Selected features
            writer.writerow(["Selected Features"])
            for feature_name in result.get("recommended_features", []):
                writer.writerow([feature_name])

            writer.writerow([])
            writer.writerow(
                [
                    "Export Date",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return str(filepath.absolute())

    def export_3y_forecast_json(
        self, filepath: str | Path, selected_features: list[str] | None = None
    ) -> str:
        """
        Export 3-year business value forecasts to JSON.

        Args:
            filepath: Output file path (e.g., "portfolio_forecast.json")
            selected_features: Optional list of feature names to include

        Returns:
            Absolute path to created JSON file
        """
        filepath = Path(filepath)
        features_to_export = (
            [f for f in self.features if f.name in selected_features]
            if selected_features
            else self.features
        )

        # Build JSON structure
        features_data = []
        total_cost = 0.0
        total_y1, total_y2, total_y3 = 0.0, 0.0, 0.0

        for feature in features_to_export:
            base = feature.get_base_annual_business_value()
            growth = feature.annual_growth_rate
            forecast = [base * (1 + growth) ** yr for yr in range(3)]

            features_data.append(
                {
                    "name": feature.name,
                    "development_cost": feature.development_cost,
                    "business_value_forecast": {
                        "year_1": forecast[0],
                        "year_2": forecast[1],
                        "year_3": forecast[2],
                        "total_3y": sum(forecast),
                    },
                    "annual_growth_rate": feature.annual_growth_rate,
                    "dependency_cluster": feature.dependency_cluster,
                    "expected_users": feature.expected_users,
                    "conversion_rate": feature.conversion_rate,
                    "uncertainty": feature.uncertainty,
                    "business_value_per_conversion": feature.business_value_per_conversion,
                }
            )

            total_cost += feature.development_cost
            total_y1 += forecast[0]
            total_y2 += forecast[1]
            total_y3 += forecast[2]

        total_business_value_3y = total_y1 + total_y2 + total_y3
        roi_3y = (
            (total_business_value_3y - total_cost) / total_cost * 100
            if total_cost > 0
            else 0.0
        )

        if npf is not None:
            npv = float(
                npf.npv(
                    self.discount_rate,
                    [-total_cost, total_y1, total_y2, total_y3],
                )
            )
        else:
            npv = -total_cost + (  # pragma: no cover - defensive
                total_y1 / ((1 + self.discount_rate) ** 1)
                + total_y2 / ((1 + self.discount_rate) ** 2)
                + total_y3 / ((1 + self.discount_rate) ** 3)
            )

        output = {
            "portfolio_forecast_3y": {
                "features": features_data,
                "portfolio_totals": {
                    "total_development_cost": total_cost,
                    "year_1_business_value": total_y1,
                    "year_2_business_value": total_y2,
                    "year_3_business_value": total_y3,
                    "total_3y_business_value": total_business_value_3y,
                },
                "business_metrics": {
                    "roi_3y_percent": roi_3y,
                    "discount_rate": self.discount_rate,
                    "npv": npv,
                },
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "feature_count": len(features_to_export),
                },
            }
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        return str(filepath.absolute())

    @staticmethod
    def export_optimization_result_json(
        result: dict[str, Any], filepath: str | Path
    ) -> str:
        """
        Export optimization result to JSON.

        Args:
            result: Optimization result dictionary from PortfolioOptimizer
            filepath: Output file path

        Returns:
            Absolute path to created JSON file
        """
        filepath = Path(filepath)

        # Clean up result dict (remove non-serializable items)
        clean_result = {
            "solver_info": {
                "solver": result.get("solver", "unknown"),
                "strategy": result.get("strategy", "unknown"),
                "computation_time_sec": result.get("computation_time_sec", 0),
                "combinations_evaluated": result.get("combinations_evaluated"),
                "candidates_evaluated": result.get("candidates_evaluated"),
            },
            "budget": {
                "total_budget": result.get("budget", 0),
                "total_cost": result.get("total_cost", 0),
                "budget_remaining": result.get("budget_remaining", 0),
            },
            "portfolio_metrics": {
                "expected_business_value": result.get("portfolio_expected", 0),
                "var_95_floor": result.get("portfolio_var_95", 0),
                "cvar_95": result.get("portfolio_cvar_95", 0),
                "standard_deviation": result.get("portfolio_std_dev", 0),
            },
            "selected_features": result.get("recommended_features", []),
            "metadata": {
                "export_date": datetime.now().isoformat(),
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(clean_result, f, indent=2, ensure_ascii=False)

        return str(filepath.absolute())


def export_portfolio_to_csv(
    features: list[Feature],
    optimization_result: dict[str, Any] | None = None,
    output_dir: str | Path = ".",
    discount_rate: float = 0.10,
) -> dict[str, str]:
    """
    Convenience function: Export portfolio to CSV files.

    Creates two CSV files:
    1. 3-year forecast for selected features
    2. Optimization result summary (if provided)

    Args:
        features: List of Feature objects
        optimization_result: Optional optimization result dict
        output_dir: Output directory (default: current directory)
        discount_rate: Annual discount rate for NPV calculations

    Returns:
        Dictionary with paths to created files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exporter = PortfolioExporter(features, discount_rate=discount_rate)
    created_files = {}

    # Export 3Y forecast
    if optimization_result and "recommended_features" in optimization_result:
        selected = optimization_result["recommended_features"]
    else:
        selected = None

    forecast_path = exporter.export_3y_forecast_csv(
        output_dir / "portfolio_forecast_3y.csv", selected_features=selected
    )
    created_files["forecast_csv"] = forecast_path

    # Export optimization result
    if optimization_result:
        result_path = exporter.export_optimization_result_csv(
            optimization_result, output_dir / "optimization_result.csv"
        )
        created_files["result_csv"] = result_path

    return created_files


def export_portfolio_to_json(
    features: list[Feature],
    optimization_result: dict[str, Any] | None = None,
    output_dir: str | Path = ".",
    discount_rate: float = 0.10,
) -> dict[str, str]:
    """
    Convenience function: Export portfolio to JSON files.

    Creates two JSON files:
    1. 3-year forecast for selected features
    2. Optimization result summary (if provided)

    Args:
        features: List of Feature objects
        optimization_result: Optional optimization result dict
        output_dir: Output directory (default: current directory)
        discount_rate: Annual discount rate for NPV calculations

    Returns:
        Dictionary with paths to created files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exporter = PortfolioExporter(features, discount_rate=discount_rate)
    created_files = {}

    # Export 3Y forecast
    if optimization_result and "recommended_features" in optimization_result:
        selected = optimization_result["recommended_features"]
    else:
        selected = None

    forecast_path = exporter.export_3y_forecast_json(
        output_dir / "portfolio_forecast_3y.json", selected_features=selected
    )
    created_files["forecast_json"] = forecast_path

    # Export optimization result
    if optimization_result:
        result_path = exporter.export_optimization_result_json(
            optimization_result, output_dir / "optimization_result.json"
        )
        created_files["result_json"] = result_path

    return created_files
