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

"""FHS Domain Services: simulation, risk calculation, portfolio analysis."""

from .assessment import (
    CVaRRanking,
    ExpectedValueRanking,
    FeatureAssessmentService,
    RankingService,
    RankingStrategy,
    ROIRanking,
    VaRRanking,
)
from .financial import FinancialCalculator
from .monte_carlo import MonteCarloEngine
from .portfolio import (
    DEPENDENCY_CORRELATION_DEFAULTS,
    PortfolioDecisionSupportService,
    PortfolioOptimizer,
    PortfolioRiskAnalyzer,
    PortfolioViewService,
    ScenarioAnalysisService,
    aggregate_portfolio_scenarios_from_results,
    build_correlation_matrix_from_clusters,
)
from .reporting import PortfolioReportingService
from .risk import RiskCalculator

# ServiceFactory moved to application layer (fhs.application.service_factory)
from .simulation import FeatureSimulator

__all__ = [
    "DEPENDENCY_CORRELATION_DEFAULTS",
    "CVaRRanking",
    "ExpectedValueRanking",
    "FeatureAssessmentService",
    "FeatureSimulator",
    "FinancialCalculator",
    "MonteCarloEngine",
    "PortfolioDecisionSupportService",
    "PortfolioOptimizer",
    "PortfolioReportingService",
    "PortfolioRiskAnalyzer",
    "PortfolioViewService",
    "ROIRanking",
    "RankingService",
    "RankingStrategy",
    "RiskCalculator",
    "ScenarioAnalysisService",
    "VaRRanking",
    "aggregate_portfolio_scenarios_from_results",
    "build_correlation_matrix_from_clusters",
]
