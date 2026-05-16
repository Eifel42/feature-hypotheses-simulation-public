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

"""Portfolio Analysis, Optimization, and Correlation Services."""

from .analysis import (
    DEPENDENCY_CORRELATION_DEFAULTS,
    PortfolioRiskAnalyzer,
    build_correlation_matrix_from_clusters,
)
from .decision_support import PortfolioDecisionSupportService
from .optimizer import PortfolioOptimizer
from .scenarios import ScenarioAnalysisService
from .utils import aggregate_portfolio_scenarios_from_results
from .views import PortfolioViewService

__all__ = [
    "DEPENDENCY_CORRELATION_DEFAULTS",
    "PortfolioDecisionSupportService",
    "PortfolioOptimizer",
    "PortfolioRiskAnalyzer",
    "PortfolioViewService",
    "ScenarioAnalysisService",
    "aggregate_portfolio_scenarios_from_results",
    "build_correlation_matrix_from_clusters",
]
