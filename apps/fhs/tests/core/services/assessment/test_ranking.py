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

"""Tests for fhs.core.services.assessment.ranking — RankingService and strategies."""

import numpy as np
import pytest

from fhs.core.model import Feature, SimulationResult
from fhs.core.model.exceptions import ValidationError
from fhs.core.services.assessment.ranking import (
    CVaRRanking,
    ExpectedValueRanking,
    RankingService,
    ROIRanking,
    VaRRanking,
)


@pytest.fixture
def features():
    return [
        Feature(
            name="A",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.2,
            business_value_per_conversion=10.0,
            development_cost=5000.0,
        ),
        Feature(
            name="B",
            expected_users=500,
            conversion_rate=0.3,
            uncertainty=0.1,
            business_value_per_conversion=20.0,
            development_cost=2000.0,
        ),
    ]


@pytest.fixture
def simulation_results():
    return {
        "A": SimulationResult(
            feature_name="A",
            results=np.random.RandomState(42).normal(500, 50, 1000),
            expected_value=500.0,
            business_value_per_conversion=10.0,
            development_cost=5000.0,
        ),
        "B": SimulationResult(
            feature_name="B",
            results=np.random.RandomState(42).normal(150, 10, 1000),
            expected_value=150.0,
            business_value_per_conversion=20.0,
            development_cost=2000.0,
        ),
    }


class TestRankingStrategies:
    def test_expected_value(self, simulation_results):
        s = ExpectedValueRanking()
        assert s.sort_key("A", simulation_results["A"]) == 5000.0  # 500 * 10

    def test_var_ranking(self, simulation_results):
        s = VaRRanking()
        val = s.sort_key("A", simulation_results["A"])
        assert val > 0

    def test_cvar_ranking(self, simulation_results):
        s = CVaRRanking()
        val = s.sort_key("A", simulation_results["A"])
        assert val > 0

    def test_roi_ranking(self, simulation_results):
        s = ROIRanking()
        val = s.sort_key("A", simulation_results["A"])
        assert val >= 0  # ROI = (business value - cost) / cost


class TestRankingService:
    def test_rank_by_expected(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(features, simulation_results, by="expected")
        assert len(result["rankings"]) == 2
        # A has higher expected business value (500*10=5000 vs 150*20=3000)
        assert result["rankings"][0]["feature"] == "A"

    def test_rank_by_var(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(features, simulation_results, by="var_95")
        assert len(result["rankings"]) == 2

    def test_rank_by_cvar(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(features, simulation_results, by="cvar_95")
        assert len(result["rankings"]) == 2

    def test_rank_by_roi(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(features, simulation_results, by="roi")
        assert len(result["rankings"]) == 2

    def test_invalid_criterion(self, features, simulation_results):
        svc = RankingService()
        with pytest.raises(ValidationError, match="Invalid criterion"):
            svc.rank_features(features, simulation_results, by="invalid")

    def test_custom_strategy(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(
            features, simulation_results, strategy=ExpectedValueRanking()
        )
        assert result["rankings"][0]["feature"] == "A"

    def test_ranking_has_recommendation(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(features, simulation_results)
        for item in result["rankings"]:
            assert "recommendation" in item
            assert len(item["recommendation"]) > 0

    def test_ranking_has_risk_ratio(self, features, simulation_results):
        svc = RankingService()
        result = svc.rank_features(features, simulation_results)
        for item in result["rankings"]:
            assert 0.0 <= item["risk_ratio"] <= 1.0


class TestRiskConcentration:
    def test_basic(self, features, simulation_results):
        svc = RankingService()
        result = svc.get_risk_concentration(features, simulation_results)
        assert "total_expected_business_value" in result
        assert "feature_contributions" in result
        assert "top_3_concentration" in result
        assert "herfindahl_index" in result
        assert "concentration_level" in result

    def test_hhi_range(self, features, simulation_results):
        svc = RankingService()
        result = svc.get_risk_concentration(features, simulation_results)
        assert 0.0 <= result["herfindahl_index"] <= 1.0

    def test_contributions_sum_to_100(self, features, simulation_results):
        svc = RankingService()
        result = svc.get_risk_concentration(features, simulation_results)
        total = sum(c["contribution_pct"] for c in result["feature_contributions"])
        assert abs(total - 100.0) < 0.01

    def test_concentration_level_text(self, features, simulation_results):
        svc = RankingService()
        result = svc.get_risk_concentration(features, simulation_results)
        assert isinstance(result["concentration_level"], str)


def test_concentration_level_moderate():
    """Test _concentration_level with moderate HHI (0.15-0.25)."""
    from fhs.core.services.assessment.ranking import RankingService

    label = RankingService._concentration_level(0.20)
    assert label == "Moderate concentration"


def test_concentration_level_high():
    """Test _concentration_level with high HHI (>= 0.25)."""
    from fhs.core.services.assessment.ranking import RankingService

    label = RankingService._concentration_level(0.30)
    assert label == "High concentration (risky, dominated by few features)"


def test_concentration_level_low():
    """Test _concentration_level with low HHI (< 0.15)."""
    from fhs.core.services.assessment.ranking import RankingService

    label = RankingService._concentration_level(0.10)
    assert label == "Low concentration (diversified portfolio)"
