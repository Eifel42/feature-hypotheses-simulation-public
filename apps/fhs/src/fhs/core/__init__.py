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

"""FHS core domain: models, simulation engine, risk calculation."""

from fhs.ux_simulation import (
    TaskComplexity,
    TaskScenario,
    UserProfile,
    UserSurveySimulator,
    UserType,
)

from .model import Feature, SimulationResult
from .model.exceptions import (
    FHSException,
    SimulationError,
    ValidationError,
)
from .model.value_objects import (
    Budget,
    ConfidenceLevel,
    OptimizationStrategy,
    RiskMetric,
)
from .services.assessment import FeatureAssessmentService, RankingService
from .services.monte_carlo import MonteCarloEngine
from .services.portfolio import PortfolioRiskAnalyzer, ScenarioAnalysisService
from .services.risk import RiskCalculator
from .services.simulation import FeatureSimulator

__all__ = [
    "Budget",
    "ConfidenceLevel",
    "FHSException",
    "Feature",
    "FeatureAssessmentService",
    "FeatureSimulator",
    "MonteCarloEngine",
    "OptimizationStrategy",
    "PortfolioRiskAnalyzer",
    "RankingService",
    "RiskCalculator",
    "RiskMetric",
    "ScenarioAnalysisService",
    "SimulationError",
    "SimulationResult",
    "TaskComplexity",
    "TaskScenario",
    "UserProfile",
    "UserSurveySimulator",
    "UserType",
    "ValidationError",
]
