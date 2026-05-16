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

"""Tests for reporting metrics module (Year1RiskReporter)."""

from fhs.core.model import Feature
from fhs.core.services.reporting.year1_risk import Year1RiskReporter


class TestYear1RiskReporter:
    def test_generate_report_contains_expected_sections(self):
        reporter = Year1RiskReporter()
        features = [
            Feature(
                name="A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                business_value_per_conversion=5000.0,
                development_cost=40000.0,
                likelihood_of_non_delivery=0.5,
                planned_release="R1",
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="B",
                expected_users=200,
                conversion_rate=0.3,
                uncertainty=0.2,
                business_value_per_conversion=1333.33,
                development_cost=30000.0,
                likelihood_of_non_delivery=0.25,
                planned_release="R2",
            ),
        ]

        report = reporter.generate_report(features)

        assert "feature_details" in report
        assert "summary" in report
        assert "risk_categories" in report
        assert report["summary"]["total_features"] == 2
        assert report["summary"]["total_y1_business_value_at_risk"] > 0

    def test_format_table_includes_header_and_summary(self):
        reporter = Year1RiskReporter()
        feature = Feature(
            name="A",
            expected_users=100,
            conversion_rate=0.2,
            uncertainty=0.1,
            business_value_per_conversion=5000.0,
            development_cost=40000.0,
            likelihood_of_non_delivery=0.5,
            planned_release="R1",
            dependency_cluster="Team Alpha",
        )
        report = reporter.generate_report([feature])

        text = reporter.format_table(report)

        assert "Year-1 Business Value at Risk (Y1 BVaR) Report" in text
        assert "Summary:" in text
        assert "Total Y1 Business Value at Risk" in text
