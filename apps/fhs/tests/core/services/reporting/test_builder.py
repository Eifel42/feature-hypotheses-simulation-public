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

"""Tests for reporting builder module (stress test + metadata + executive summary)."""

import numpy as np

from fhs.core.model import Feature, SimulationResult
from fhs.core.services.reporting.stress_test import (
    BundledRiskStressTest,
    ExecutiveSummaryBuilder,
    RunMetadataBuilder,
)


class TestBundledRiskStressTest:
    def test_calculate_returns_baseline_and_cluster_impacts(self):
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
                dependency_cluster="Team Alpha",
            ),
        ]
        results = {
            "A": SimulationResult(
                "A", np.array([10.0, 11.0, 9.0]), scenarios=3, expected_value=10.0
            ),
            "B": SimulationResult(
                "B", np.array([6.0, 7.0, 5.0]), scenarios=3, expected_value=6.0
            ),
        }

        payload = BundledRiskStressTest().calculate(features, results)

        assert "baseline" in payload
        assert "cluster_impacts" in payload
        assert "Team Alpha" in payload["cluster_impacts"]


class TestExecutiveSummaryBuilder:
    def test_build_contains_expected_top_level_keys(self):
        features = [
            Feature(name="A", expected_users=100, conversion_rate=0.2, uncertainty=0.1)
        ]
        results = {
            "A": SimulationResult(
                "A", np.array([10.0, 11.0, 9.0]), scenarios=3, expected_value=10.0
            )
        }
        ranking_result = {
            "rankings": [
                {
                    "feature": "A",
                    "expected_business_value": 10.0,
                    "var_95_business_value": 9.0,
                    "risk_ratio": 0.1,
                    "recommendation": "Low risk",
                }
            ]
        }
        concentration = {"is_concentrated": False, "hhi": 1.0, "warnings": []}
        stress_crash = {"scenario": "market_crash"}
        stress_failure = {"scenario": "feature_failure"}
        metadata = {"timestamp": "2026-03-10 10:00:00"}

        summary = ExecutiveSummaryBuilder().build(
            features,
            results,
            ranking_result,
            concentration,
            stress_crash,
            stress_failure,
            metadata,
            correlation_matrix=None,
        )

        assert "portfolio" in summary
        assert "feature_ranking" in summary
        assert "stress_tests" in summary
        assert "methodology_warnings" in summary


class TestRunMetadataBuilder:
    def test_build_includes_diversification_warning_for_many_independent_features(self):
        features = [
            Feature(name="A", expected_users=100, conversion_rate=0.2, uncertainty=0.1),
            Feature(name="B", expected_users=100, conversion_rate=0.2, uncertainty=0.1),
            Feature(
                name="C",
                expected_users=100,
                conversion_rate=0.2,
                uncertainty=0.1,
                dependency_cluster="Team Alpha",
            ),
        ]

        metadata = RunMetadataBuilder().build(
            features,
            scenarios=1000,
            distribution="normal",
            correlation_source="independent",
            seed=42,
        )

        assert metadata["n_features"] == 3
        assert metadata["independent_features_count"] == 2
        assert "diversification_warning" in metadata
