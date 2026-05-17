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

"""Tests for fhs.application.portfolio_facade."""

from pathlib import Path

import numpy as np
import pytest

# noinspection PyProtectedMember
from fhs.application.portfolio_facade import (
    PortfolioFacade,
    _PortfolioServicesConfig,
)
from fhs.core.model import Feature


class _DummySimulator:
    def __init__(self):
        self.calls = 0

    # noinspection PyUnusedLocal
    def simulate_feature(self, feature, scenarios=10000, distribution="normal"):
        self.calls += 1
        from fhs.core.model import SimulationResult

        values = np.array([10.0, 12.0, 11.0, 9.0])
        return SimulationResult(
            feature_name=feature.name,
            results=values,
            scenarios=len(values),
            expected_value=float(np.mean(values)),
            business_value_per_conversion=feature.business_value_per_conversion,
            development_cost=feature.development_cost,
        )


class _DummyRankingService:
    @staticmethod
    def rank_features(features, _results):
        return {
            "rankings": [
                {
                    "feature": f.name,
                    "expected_business_value": 100.0,
                    "var_95_business_value": 80.0,
                    "risk_ratio": 0.2,
                    "uncertainty": f.uncertainty,
                    "recommendation": "Medium risk",
                }
                for f in features
            ]
        }

    @staticmethod
    def get_risk_concentration(_features, _results):
        return {
            "is_concentrated": False,
            "hhi": 0.5,
            "warnings": [],
        }


class _DummyScenarioService:
    @staticmethod
    def stress_test(_features, _results, scenario="market_crash"):
        return {"scenario": scenario, "impact": {"expected_change": -10.0}}


class _DummyAssessmentService:
    # noinspection PyUnusedLocal
    @staticmethod
    def assess_feature(feature, simulation_result):
        return {"feature": feature.name, "expected_business_value": 42.0}


class _DummyExporter:
    def __init__(self):
        self.called = False

    def export_optimization_result_csv(self, _result, output_path):
        self.called = True
        return str(Path(output_path) / "result.csv")


@pytest.fixture
def features():
    return [
        Feature(name="A", expected_users=100, conversion_rate=0.2, uncertainty=0.1),
        Feature(name="B", expected_users=150, conversion_rate=0.15, uncertainty=0.2),
    ]


def test_init_requires_features():
    with pytest.raises(ValueError, match="At least one feature"):
        PortfolioFacade([])


def test_simulate_all_uses_cache(features):
    sim = _DummySimulator()
    facade = PortfolioFacade(
        features,
        services=_PortfolioServicesConfig(simulator=sim, exporter=_DummyExporter()),
    )

    first = facade.simulate_all()
    second = facade.simulate_all()

    assert first is second
    assert sim.calls == len(features)


def test_analyze_returns_expected_structure(features):
    facade = PortfolioFacade(
        features,
        services=_PortfolioServicesConfig(
            simulator=_DummySimulator(),
            ranking_service=_DummyRankingService(),
            scenario_analysis_service=_DummyScenarioService(),
            exporter=_DummyExporter(),
        ),
    )

    payload = facade.analyze()

    assert set(payload.keys()) == {
        "summary",
        "ranking",
        "concentration",
        "stress_tests",
    }
    assert payload["summary"]["n_features"] == 2
    assert len(payload["ranking"]) == 2


def test_assess_feature_success_and_not_found(features):
    facade = PortfolioFacade(
        features,
        services=_PortfolioServicesConfig(
            simulator=_DummySimulator(),
            assessment_service=_DummyAssessmentService(),
            exporter=_DummyExporter(),
        ),
    )

    result = facade.assess_feature("A")
    assert result["feature"] == "A"

    with pytest.raises(ValueError, match="Feature not found"):
        facade.assess_feature("X")


def test_compare_features_filters_by_names(features):
    facade = PortfolioFacade(
        features,
        services=_PortfolioServicesConfig(
            simulator=_DummySimulator(),
            assessment_service=_DummyAssessmentService(),
            exporter=_DummyExporter(),
        ),
    )

    result = facade.compare_features(["B"])
    assert result["count"] == 1
    assert result["assessments"][0]["feature"] == "B"


def test_optimize_and_export_budget_path(monkeypatch, features, tmp_path):
    class _DummyOptimizer:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        @staticmethod
        def optimize_exact(**kwargs):
            return {"recommended_features": ["A"], "budget": kwargs.get("budget")}

    monkeypatch.setattr(
        "fhs.application.portfolio_facade.PortfolioOptimizer",
        _DummyOptimizer,
    )

    exporter = _DummyExporter()
    facade = PortfolioFacade(
        features,
        services=_PortfolioServicesConfig(
            simulator=_DummySimulator(), exporter=exporter
        ),
    )

    result = facade.optimize_and_export(budget=100000, output_dir=tmp_path)

    assert result["recommended_features"] == ["A"]
    assert exporter.called is True


def test_optimize_and_export_input_validation(features):
    facade = PortfolioFacade(
        features,
        services=_PortfolioServicesConfig(
            simulator=_DummySimulator(),
            exporter=_DummyExporter(),
        ),
    )

    with pytest.raises(ValueError, match="either budget OR max_sprints"):
        facade.optimize_and_export(budget=1, max_sprints=1)

    with pytest.raises(NotImplementedError, match="Sprint-based optimization"):
        facade.optimize_and_export(max_sprints=2)

    with pytest.raises(ValueError, match="Must specify either budget or max_sprints"):
        facade.optimize_and_export()
