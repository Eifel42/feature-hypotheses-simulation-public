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
Tests for Year-1 Business Value at Risk (Y1 BVaR) and Year-1 Profit at Risk (Y1 PaR).

Tests:
- Y1 RaR and Y1 PaR calculations
- Dependency cluster correlation matrix building
- Year-1 risk reporting
"""

import numpy as np
import pytest

from fhs.core.model import Feature
from fhs.core.services import (
    build_correlation_matrix_from_clusters,
)
from fhs.core.services.reporting import PortfolioReportingService


class TestFeatureYear1Extensions:
    """Test Feature model Year-1 calculations"""

    def test_feature_creation(self):
        """Test creating a feature"""
        feature = Feature(
            name="Automated Reports",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.2,
            likelihood_of_non_delivery=0.5,
            planned_release="R3",
            dependency_cluster="Team Alpha",
        )

        assert feature.likelihood_of_non_delivery == 0.5
        assert feature.planned_release == "R3"
        assert feature.dependency_cluster == "Team Alpha"

    def test_year1_business_value_at_risk_calculation(self):
        """Test Y1 BVaR calculation: base business value × likelihood."""
        feature = Feature(
            name="Premium Dashboard",
            expected_users=500,
            conversion_rate=0.4,
            uncertainty=0.3,
            business_value_per_conversion=1200.0,
            likelihood_of_non_delivery=0.5,
        )

        # Base business value = 500 × 0.4 × 1200 = 240,000
        # Y1 RaR = 240,000 × 0.5 = 120,000
        assert feature.year1_business_value_at_risk == 120000

    def test_year1_profit_at_risk_calculation(self):
        """Test Y1 PaR calculation: (base business value - dev cost) × likelihood."""
        feature = Feature(
            name="Advanced Analytics",
            expected_users=800,
            conversion_rate=0.6,
            uncertainty=0.25,
            business_value_per_conversion=312.5,
            development_cost=90000.0,
            likelihood_of_non_delivery=0.3,
        )

        # Base business value = 800 × 0.6 × 312.5 = 150,000
        # Profit = 150,000 - 90,000 = 60,000
        # Y1 PaR = 60,000 × 0.3 = 18,000
        assert feature.year1_profit_at_risk == 18000

    def test_year1_bvar_calculation_from_base_business_value(self):
        """Test Y1 BVaR is calculated from base business value."""
        feature = Feature(
            name="Basic Feature",
            expected_users=100,
            conversion_rate=0.2,
            uncertainty=0.1,
            business_value_per_conversion=100.0,
            likelihood_of_non_delivery=0.8,
        )

        # Base business value = 100 × 0.2 × 100 = 2,000
        # Y1 RaR = 2,000 × 0.8 = 1,600
        assert feature.year1_business_value_at_risk == 1600.0

    def test_year1_par_calculation_from_base_business_value(self):
        """Test Y1 PaR is calculated from base business value minus dev cost."""
        feature = Feature(
            name="Basic Feature",
            expected_users=100,
            conversion_rate=0.2,
            uncertainty=0.1,
            business_value_per_conversion=100.0,
            development_cost=50.0,
            likelihood_of_non_delivery=0.8,
        )

        # Base business value = 100 × 0.2 × 100 = 2,000
        # Profit = 2,000 - 50 = 1,950
        # Y1 PaR = 1,950 × 0.8 = 1,560
        assert feature.year1_profit_at_risk == 1560.0

    def test_risk_category_low(self):
        """Test risk category classification: Low"""
        feature = Feature(
            name="Low Risk Feature",
            expected_users=100,
            conversion_rate=0.2,
            uncertainty=0.1,
            business_value_per_conversion=400.0,
            likelihood_of_non_delivery=0.2,
        )

        # Base business value = 100 × 0.2 × 400 = 8,000
        # Y1 RaR = 8,000 × 0.2 = 1,600 → Low
        assert feature.get_risk_category("business_value") == "Low"

    def test_risk_category_medium(self):
        """Test risk category classification: Medium"""
        feature = Feature(
            name="Medium Risk Feature",
            expected_users=500,
            conversion_rate=0.4,
            uncertainty=0.2,
            business_value_per_conversion=1000.0,
            likelihood_of_non_delivery=0.5,
        )

        # Base business value = 500 × 0.4 × 1000 = 200,000
        # Y1 RaR = 200,000 × 0.5 = 100,000 → Medium
        assert feature.get_risk_category("business_value") == "Medium"

    def test_risk_category_high(self):
        """Test risk category classification: High"""
        feature = Feature(
            name="High Risk Feature",
            expected_users=625,
            conversion_rate=0.4,
            uncertainty=0.3,
            business_value_per_conversion=2000.0,
            likelihood_of_non_delivery=0.8,
        )

        # Base business value = 625 × 0.4 × 2000 = 500,000
        # Y1 RaR = 500,000 × 0.8 = 400,000 → High
        assert feature.get_risk_category("business_value") == "High"

    def test_likelihood_validation_bounds(self):
        """Test likelihood_of_non_delivery must be between 0 and 1"""
        with pytest.raises(ValueError):
            Feature(
                name="Invalid",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                likelihood_of_non_delivery=1.5,  # Invalid
            )

        with pytest.raises(ValueError):
            Feature(
                name="Invalid",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                likelihood_of_non_delivery=-0.1,  # Invalid
            )


class TestDependencyClusterCorrelation:
    """Test dependency cluster correlation matrix building"""

    def test_build_correlation_matrix_no_clusters(self):
        """Test correlation matrix for independent features (no clusters)"""
        features = [
            Feature(
                name="Feature A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
            ),
            Feature(
                name="Feature B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
            ),
        ]

        corr_matrix = build_correlation_matrix_from_clusters(features)

        # Should be identity matrix (no correlation)
        expected = np.eye(2)
        np.testing.assert_array_equal(corr_matrix, expected)

    def test_build_correlation_matrix_shared_team(self):
        """Test correlation matrix for features sharing a team"""
        features = [
            Feature(
                name="Feature A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Feature B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
                dependency_cluster="Team Alpha",
            ),
        ]

        corr_matrix = build_correlation_matrix_from_clusters(features)

        # Diagonal should be 1, off-diagonal should be 0.5 (shared team)
        assert corr_matrix[0, 0] == 1.0
        assert corr_matrix[1, 1] == 1.0
        assert corr_matrix[0, 1] == 0.5
        assert corr_matrix[1, 0] == 0.5

    def test_build_correlation_matrix_technical_dependency(self):
        """Test correlation matrix for features with technical dependency"""
        features = [
            Feature(
                name="Feature A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Payment API",
            ),
            Feature(
                name="Feature B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
                dependency_cluster="Payment API",
            ),
        ]

        corr_matrix = build_correlation_matrix_from_clusters(features)

        # Technical dependency → correlation = 0.8
        assert corr_matrix[0, 1] == 0.8
        assert corr_matrix[1, 0] == 0.8

    def test_build_correlation_matrix_same_user_segment(self):
        """Test correlation matrix for features targeting same user segment"""
        features = [
            Feature(
                name="Feature A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Power Users",
            ),
            Feature(
                name="Feature B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
                dependency_cluster="Power Users",
            ),
        ]

        corr_matrix = build_correlation_matrix_from_clusters(features)

        # Same user segment → correlation = 0.3
        assert corr_matrix[0, 1] == 0.3
        assert corr_matrix[1, 0] == 0.3

    def test_build_correlation_matrix_mixed_clusters(self):
        """Test correlation matrix with multiple dependency clusters"""
        features = [
            Feature(
                name="Feature A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Feature B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Feature C",
                expected_users=300,
                conversion_rate=0.4,
                uncertainty=0.3,
                dependency_cluster="Team Beta",
            ),
        ]

        corr_matrix = build_correlation_matrix_from_clusters(features)

        # A and B share Team Alpha → 0.5
        assert corr_matrix[0, 1] == 0.5
        assert corr_matrix[1, 0] == 0.5

        # A and C are in different teams → 0.0
        assert corr_matrix[0, 2] == 0.0
        assert corr_matrix[2, 0] == 0.0

        # B and C are in different teams → 0.0
        assert corr_matrix[1, 2] == 0.0
        assert corr_matrix[2, 1] == 0.0


class TestYear1RiskReporting:
    """Test Year-1 Risk Report generation"""

    def test_generate_year1_risk_report_structure(self):
        """Test that Year-1 risk report has correct structure"""
        features = [
            Feature(
                name="Automated Reports",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=240.0,
                development_cost=60000.0,
                likelihood_of_non_delivery=0.5,
                planned_release="R3",
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Advanced Analytics",
                expected_users=800,
                conversion_rate=0.6,
                uncertainty=0.25,
                business_value_per_conversion=625.0,
                development_cost=80000.0,
                likelihood_of_non_delivery=0.3,
                planned_release="R4",
                dependency_cluster="Team Beta",
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        # Check structure
        assert "feature_details" in report
        assert "summary" in report
        assert "risk_categories" in report
        assert "dependency_clusters" in report
        assert "glossary" in report
        assert "legend" in report

        # Check feature details
        assert len(report["feature_details"]) == 2

        # Check summary
        summary = report["summary"]
        assert summary["total_features"] == 2
        # Business value exposure: (1000 × 0.5 × 240) + (800 × 0.6 × 625) = 120,000 + 300,000 = 420,000
        assert summary["total_business_value_exposure_year1"] == 420000
        # Profit exposure: (120,000 - 60,000) + (300,000 - 80,000) = 60,000 + 220,000 = 280,000
        assert summary["total_profit_exposure_year1"] == 280000

        # Check glossary
        assert "Year-1 Business Value at Risk (Y1 BVaR)" in report["glossary"]
        assert "Year-1 Profit at Risk (Y1 PaR)" in report["glossary"]

    def test_generate_year1_risk_report_calculations(self):
        """Test Y1 RaR/PaR calculations in report"""
        features = [
            Feature(
                name="Feature A",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=240.0,
                likelihood_of_non_delivery=0.5,
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        detail = report["feature_details"][0]
        # Base business value = 1000 × 0.5 × 240 = 120,000
        # Y1 RaR = 120,000 × 0.5 = 60,000
        assert detail["y1_business_value_at_risk"] == 60000

    def test_format_year1_risk_table(self):
        """Test Year-1 risk table formatting"""
        features = [
            Feature(
                name="Automated Reports",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=240.0,
                likelihood_of_non_delivery=0.5,
                planned_release="R3",
            ),
        ]

        reporting = PortfolioReportingService()
        report = reporting.generate_year1_risk_report(features)
        table = reporting.format_year1_risk_table(report)

        # Check that table contains key elements
        assert "Year-1 Business Value at Risk (Y1 BVaR) Report" in table
        assert "Automated Reports" in table
        assert "R3" in table
        assert "Summary:" in table
        assert "Legend:" in table
        # Base business value = 1000 × 0.5 × 240 = 120,000
        # Y1 RaR = 120,000 × 0.5 = 60,000
        assert "$60,000" in table

    def test_risk_categories_grouping(self):
        """Test features are correctly grouped by risk category"""
        features = [
            Feature(
                name="Low Risk",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                business_value_per_conversion=400.0,
                likelihood_of_non_delivery=0.2,  # Base: 8k, Y1 RaR = 1,600 → Low
            ),
            Feature(
                name="Medium Risk",
                expected_users=500,
                conversion_rate=0.4,
                uncertainty=0.2,
                business_value_per_conversion=1000.0,
                likelihood_of_non_delivery=0.5,  # Base: 200k, Y1 RaR = 100,000 → Medium
            ),
            Feature(
                name="High Risk",
                expected_users=625,
                conversion_rate=0.4,
                uncertainty=0.3,
                business_value_per_conversion=2000.0,
                likelihood_of_non_delivery=0.8,  # Base: 500k, Y1 RaR = 400,000 → High
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        categories = report["risk_categories"]
        assert "Low Risk" in categories["Low"]
        assert "Medium Risk" in categories["Medium"]
        assert "High Risk" in categories["High"]

    def test_dependency_clusters_grouping(self):
        """Test features are correctly grouped by dependency cluster"""
        features = [
            Feature(
                name="Feature A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Feature B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Feature C",
                expected_users=300,
                conversion_rate=0.4,
                uncertainty=0.3,
                dependency_cluster="Team Beta",
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        clusters = report["dependency_clusters"]
        assert "Feature A" in clusters["Team Alpha"]
        assert "Feature B" in clusters["Team Alpha"]
        assert "Feature C" in clusters["Team Beta"]


class TestYear1RiskVisualizations:
    """Test Year-1 Risk Report visualizations"""

    def test_plot_year1_risk_heatmap(self):
        """Test Year-1 risk heatmap creation"""
        from fhs.plotting.reporting import Reporter

        features = [
            Feature(
                name="Feature A",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=240.0,
                likelihood_of_non_delivery=0.5,
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        # Should create figure without errors
        fig = Reporter.plot_year1_risk_heatmap(report)
        assert fig is not None
        assert "Year-1 Business Value at Risk" in fig.layout.title.text

    def test_plot_year1_risk_by_cluster(self):
        """Test Year-1 risk by cluster visualization"""
        from fhs.plotting.reporting import Reporter

        features = [
            Feature(
                name="Feature A",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=240.0,
                likelihood_of_non_delivery=0.5,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="Feature B",
                expected_users=800,
                conversion_rate=0.6,
                uncertainty=0.25,
                business_value_per_conversion=625.0,
                likelihood_of_non_delivery=0.3,
                dependency_cluster="Team Beta",
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        # Should create figure without errors
        fig = Reporter.plot_year1_risk_by_cluster(report)
        assert fig is not None
        assert "Dependency Cluster" in fig.layout.title.text

    def test_create_year1_risk_summary_table(self):
        """Test Year-1 risk summary table creation"""
        from fhs.plotting.reporting import Reporter

        features = [
            Feature(
                name="Automated Reports",
                expected_users=1000,
                conversion_rate=0.5,
                uncertainty=0.2,
                business_value_per_conversion=240.0,
                development_cost=60000.0,
                likelihood_of_non_delivery=0.5,
                planned_release="R3",
                dependency_cluster="Team Alpha",
            ),
        ]

        report = PortfolioReportingService().generate_year1_risk_report(features)

        # Should create DataFrame with required columns
        df = Reporter.create_year1_risk_summary_table(report)
        assert df is not None
        assert len(df) == 1

        # Check required columns from business-improvements.md
        required_columns = [
            "Feature",
            "Planned Release",
            "Business Value Exposure (Year 1)",
            "Likelihood of Non-Delivery",
            "Y1 Business Value at Risk",
        ]
        for col in required_columns:
            assert col in df.columns

        # Check optional columns
        assert "Y1 Profit at Risk" in df.columns
        assert "Dependency Cluster" in df.columns
