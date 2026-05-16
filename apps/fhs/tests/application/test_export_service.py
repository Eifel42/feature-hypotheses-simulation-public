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
Tests for Portfolio Export Utilities (CSV/JSON)
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from fhs.application.export_service import (
    PortfolioExporter,
    export_portfolio_to_csv,
    export_portfolio_to_json,
)
from fhs.core.model import Feature


@pytest.fixture
def sample_features():
    """Create sample features for testing."""
    return [
        Feature(
            name="Enterprise SSO",
            expected_users=5_000,
            conversion_rate=0.25,
            uncertainty=0.15,
            business_value_per_conversion=120.0,
            development_cost=45_000,
            dependency_cluster="Team Auth",
            annual_growth_rate=0.20,
        ),
        Feature(
            name="AI Search",
            expected_users=12_000,
            conversion_rate=0.18,
            uncertainty=0.30,
            business_value_per_conversion=80.0,
            development_cost=60_000,
            dependency_cluster="Team ML",
            annual_growth_rate=0.30,
        ),
    ]


@pytest.fixture
def sample_optimization_result():
    """Create sample optimization result."""
    return {
        "solver": "exact",
        "strategy": "var_floor",
        "computation_time_sec": 0.0012,
        "combinations_evaluated": 3,
        "budget": 100_000,
        "total_cost": 45_000,
        "budget_remaining": 55_000,
        "portfolio_expected": 150_000,
        "portfolio_var_95": 130_000,
        "portfolio_cvar_95": 125_000,
        "portfolio_std_dev": 15_000,
        "recommended_features": ["Enterprise SSO"],
    }


class TestPortfolioExporter:
    """Test PortfolioExporter class."""

    def test_export_3y_forecast_csv(self, sample_features, tmp_path):
        """Test CSV export of 3-year forecasts."""
        exporter = PortfolioExporter(sample_features)
        filepath = tmp_path / "forecast.csv"

        result_path = exporter.export_3y_forecast_csv(filepath)

        assert Path(result_path).exists()
        assert Path(result_path) == filepath.absolute()

        # Verify CSV content
        with open(filepath) as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Check header
        assert rows[0][0] == "Feature"
        assert "Year 1 Business Value" in rows[0][2]

        # Check first feature
        assert rows[1][0] == "Enterprise SSO"
        assert float(rows[1][1]) == 45_000  # Cost

        # Check portfolio total row exists
        portfolio_total_found = any(
            "PORTFOLIO TOTAL" in row[0] for row in rows if len(row) > 0
        )
        assert portfolio_total_found

    def test_export_3y_forecast_csv_selected_only(self, sample_features, tmp_path):
        """Test CSV export with feature selection."""
        exporter = PortfolioExporter(sample_features)
        filepath = tmp_path / "selected.csv"

        exporter.export_3y_forecast_csv(filepath, selected_features=["Enterprise SSO"])

        with open(filepath) as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Should only have 1 feature + header + total
        feature_rows = [
            r
            for r in rows
            if r
            and r[0]
            not in [
                "",
                "Feature",
                "PORTFOLIO TOTAL",
                "Business Metrics",
                "3-Year ROI (%)",
                "Export Date",
            ]
        ]
        assert len(feature_rows) == 1
        assert feature_rows[0][0] == "Enterprise SSO"

    def test_export_optimization_result_csv(self, sample_optimization_result, tmp_path):
        """Test CSV export of optimization result."""
        exporter = PortfolioExporter([])
        filepath = tmp_path / "result.csv"

        result_path = exporter.export_optimization_result_csv(
            sample_optimization_result, filepath
        )

        assert Path(result_path).exists()

        with open(filepath) as f:
            content = f.read()

        # Verify key content
        assert "exact" in content
        assert "var_floor" in content
        assert "Enterprise SSO" in content
        assert "100000.00" in content  # Budget

    def test_export_3y_forecast_json(self, sample_features, tmp_path):
        """Test JSON export of 3-year forecasts."""
        exporter = PortfolioExporter(sample_features)
        filepath = tmp_path / "forecast.json"

        result_path = exporter.export_3y_forecast_json(filepath)

        assert Path(result_path).exists()

        with open(filepath) as f:
            data = json.load(f)

        assert "portfolio_forecast_3y" in data
        assert "features" in data["portfolio_forecast_3y"]
        assert len(data["portfolio_forecast_3y"]["features"]) == 2

        # Check first feature
        feature = data["portfolio_forecast_3y"]["features"][0]
        assert feature["name"] == "Enterprise SSO"
        assert feature["development_cost"] == 45_000
        assert "business_value_forecast" in feature
        assert feature["business_value_forecast"]["year_1"] == 150_000

        # Check portfolio totals
        totals = data["portfolio_forecast_3y"]["portfolio_totals"]
        assert "total_development_cost" in totals
        assert "total_3y_business_value" in totals

        # Check business metrics
        metrics = data["portfolio_forecast_3y"]["business_metrics"]
        assert "roi_3y_percent" in metrics
        assert metrics["discount_rate"] == 0.10
        assert "npv" in metrics

    def test_export_3y_forecast_json_uses_configured_discount_rate(
        self, sample_features, tmp_path
    ):
        """Test JSON export uses the configured discount rate for NPV."""
        exporter = PortfolioExporter(sample_features, discount_rate=0.08)
        filepath = tmp_path / "forecast_discount.json"

        exporter.export_3y_forecast_json(filepath)

        with open(filepath) as f:
            data = json.load(f)

        metrics = data["portfolio_forecast_3y"]["business_metrics"]
        assert metrics["discount_rate"] == 0.08
        assert metrics["npv"] == pytest.approx(944094.6502057613)

    def test_export_3y_forecast_json_selected_only(self, sample_features, tmp_path):
        """Test JSON export with feature selection."""
        exporter = PortfolioExporter(sample_features)
        filepath = tmp_path / "selected.json"

        exporter.export_3y_forecast_json(filepath, selected_features=["AI Search"])

        with open(filepath) as f:
            data = json.load(f)

        features = data["portfolio_forecast_3y"]["features"]
        assert len(features) == 1
        assert features[0]["name"] == "AI Search"

    def test_export_optimization_result_json(
        self, sample_optimization_result, tmp_path
    ):
        """Test JSON export of optimization result."""
        exporter = PortfolioExporter([])
        filepath = tmp_path / "result.json"

        result_path = exporter.export_optimization_result_json(
            sample_optimization_result, filepath
        )

        assert Path(result_path).exists()

        with open(filepath) as f:
            data = json.load(f)

        assert "solver_info" in data
        assert data["solver_info"]["solver"] == "exact"
        assert data["solver_info"]["strategy"] == "var_floor"

        assert "budget" in data
        assert data["budget"]["total_budget"] == 100_000

        assert "portfolio_metrics" in data
        assert data["portfolio_metrics"]["expected_business_value"] == 150_000

        assert "selected_features" in data
        assert "Enterprise SSO" in data["selected_features"]


class TestConvenienceFunctions:
    """Test convenience export functions."""

    def test_export_portfolio_to_csv(self, sample_features, tmp_path):
        """Test CSV export convenience function."""
        files = export_portfolio_to_csv(sample_features, output_dir=tmp_path)

        assert "forecast_csv" in files
        assert Path(files["forecast_csv"]).exists()

        # Should only create forecast (no optimization result)
        assert "result_csv" not in files

    def test_export_portfolio_to_csv_with_optimization(
        self, sample_features, sample_optimization_result, tmp_path
    ):
        """Test CSV export with optimization result."""
        files = export_portfolio_to_csv(
            sample_features,
            optimization_result=sample_optimization_result,
            output_dir=tmp_path,
        )

        assert "forecast_csv" in files
        assert "result_csv" in files
        assert Path(files["forecast_csv"]).exists()
        assert Path(files["result_csv"]).exists()

    def test_export_portfolio_to_json(self, sample_features, tmp_path):
        """Test JSON export convenience function."""
        files = export_portfolio_to_json(sample_features, output_dir=tmp_path)

        assert "forecast_json" in files
        assert Path(files["forecast_json"]).exists()

    def test_export_portfolio_to_json_with_optimization(
        self, sample_features, sample_optimization_result, tmp_path
    ):
        """Test JSON export with optimization result."""
        files = export_portfolio_to_json(
            sample_features,
            optimization_result=sample_optimization_result,
            output_dir=tmp_path,
        )

        assert "forecast_json" in files
        assert "result_json" in files
        assert Path(files["forecast_json"]).exists()
        assert Path(files["result_json"]).exists()

    def test_export_creates_directory(self, sample_features):
        """Test that export creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_dir" / "subdir"
            files = export_portfolio_to_csv(sample_features, output_dir=output_dir)

            assert output_dir.exists()
            assert Path(files["forecast_csv"]).exists()
