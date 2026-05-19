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

"""Tests for reporting formatter module (POSummaryReporter)."""

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.services.reporting.po_summary import POSummaryReporter


class TestPOSummaryReporter:
    @staticmethod
    def _sample_inputs():
        features = [
            Feature(
                name="A",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Team Alpha",
            ),
            Feature(
                name="B",
                expected_users=80,
                conversion_rate=0.15,
                uncertainty=0.2,
            ),
        ]
        simulation_results = {
            "A": SimulationResult(
                feature_name="A",
                results=np.array([10.0, 12.0, 11.0, 9.0]),
                scenarios=4,
                expected_value=10.5,
            ),
            "B": SimulationResult(
                feature_name="B",
                results=np.array([6.0, 7.0, 8.0, 6.5]),
                scenarios=4,
                expected_value=6.875,
            ),
        }
        ranking_result = {
            "rankings": [
                {
                    "feature": "A",
                    "expected_business_value": 10.5,
                    "var_95_business_value": 9.0,
                    "risk_ratio": 0.15,
                    "recommendation": "Low risk",
                },
                {
                    "feature": "B",
                    "expected_business_value": 6.875,
                    "var_95_business_value": 6.0,
                    "risk_ratio": 0.2,
                    "recommendation": "Low risk",
                },
            ]
        }
        concentration = {
            "hhi": 0.55,
            "is_concentrated": True,
            "warnings": [
                "A accounts for 60% of total expected value - high concentration risk"
            ],
        }
        robustness_variants = {
            "Independent": {"expected": 17.0, "var_95": 14.0},
            "Cluster (Standard)": {"expected": 16.5, "var_95": 13.8},
            "High-Coupling Stress": {"expected": 15.0, "var_95": 12.0},
        }
        metadata = {
            "timestamp": "2026-03-10 10:00:00",
            "scenarios": 1000,
            "distribution": "normal",
            "correlation_source": "clusters",
        }
        return (
            features,
            simulation_results,
            ranking_result,
            concentration,
            robustness_variants,
            metadata,
        )

    def test_generate_summary_contains_expected_keys(self):
        reporter = POSummaryReporter()
        (
            features,
            simulation_results,
            ranking_result,
            concentration,
            robustness_variants,
            metadata,
        ) = self._sample_inputs()

        summary = reporter.generate_summary(
            features,
            simulation_results,
            ranking_result,
            concentration,
            robustness_variants,
            metadata,
        )

        assert "top_3_features" in summary
        assert "portfolio_metrics" in summary
        assert "bundled_risk_impact" in summary
        assert "metadata" in summary

    def test_format_markdown_contains_sections(self):
        reporter = POSummaryReporter()
        (
            features,
            simulation_results,
            ranking_result,
            concentration,
            robustness_variants,
            metadata,
        ) = self._sample_inputs()

        summary = reporter.generate_summary(
            features,
            simulation_results,
            ranking_result,
            concentration,
            robustness_variants,
            metadata,
        )
        markdown = reporter.format_markdown(summary, budget=50000)

        assert "# Product Owner Feature Prioritization Report" in markdown
        assert "## 🛡️ Robustness Check (Portfolio Variants)" in markdown
        assert "## 📊 Portfolio Overview" in markdown
