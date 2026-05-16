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

"""Tests for fhs.application.service_factory — ServiceFactory."""

import pytest

from fhs.application.service_factory import ServiceFactory
from fhs.core.services.assessment import FeatureAssessmentService, RankingService
from fhs.core.services.monte_carlo import MonteCarloEngine
from fhs.core.services.portfolio import PortfolioRiskAnalyzer, ScenarioAnalysisService
from fhs.core.services.risk import RiskCalculator
from fhs.core.services.simulation import FeatureSimulator


@pytest.fixture
def factory():
    return ServiceFactory(seed=42)


class TestServiceFactory:
    def test_init_stores_seed(self):
        f = ServiceFactory(seed=99)
        assert f.seed == 99

    def test_init_no_seed(self):
        f = ServiceFactory()
        assert f.seed is None

    def test_create_risk_calculator(self, factory):
        calc = factory.create_risk_calculator()
        assert isinstance(calc, RiskCalculator)

    def test_create_monte_carlo_engine_default_seed(self, factory):
        engine = factory.create_monte_carlo_engine()
        assert isinstance(engine, MonteCarloEngine)

    def test_create_monte_carlo_engine_custom_seed(self, factory):
        engine = factory.create_monte_carlo_engine(seed=99)
        assert isinstance(engine, MonteCarloEngine)

    def test_create_feature_simulator(self, factory):
        sim = factory.create_feature_simulator()
        assert isinstance(sim, FeatureSimulator)

    def test_create_feature_simulator_custom_seed(self, factory):
        sim = factory.create_feature_simulator(seed=7)
        assert isinstance(sim, FeatureSimulator)

    def test_create_portfolio_risk_analyzer(self, factory):
        analyzer = factory.create_portfolio_risk_analyzer()
        assert isinstance(analyzer, PortfolioRiskAnalyzer)

    def test_create_feature_assessment_service_default(self, factory):
        svc = factory.create_feature_assessment_service()
        assert isinstance(svc, FeatureAssessmentService)

    def test_create_feature_assessment_service_with_calculator(self, factory):
        calc = RiskCalculator()
        svc = factory.create_feature_assessment_service(calculator=calc)
        assert isinstance(svc, FeatureAssessmentService)
        assert svc.calculator is calc

    def test_create_ranking_service_default(self, factory):
        svc = factory.create_ranking_service()
        assert isinstance(svc, RankingService)

    def test_create_ranking_service_with_calculator(self, factory):
        calc = RiskCalculator()
        svc = factory.create_ranking_service(calculator=calc)
        assert svc.calculator is calc

    def test_create_scenario_analysis_service(self, factory):
        svc = factory.create_scenario_analysis_service()
        assert isinstance(svc, ScenarioAnalysisService)

    def test_create_scenario_analysis_service_with_calculator(self, factory):
        calc = RiskCalculator()
        svc = factory.create_scenario_analysis_service(calculator=calc)
        assert isinstance(svc, ScenarioAnalysisService)
