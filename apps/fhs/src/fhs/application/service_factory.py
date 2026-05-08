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

"""Service Factory — produces configured service instances for Dependency Injection.

This factory simplifies the creation of complex service graphs while maintaining
loose coupling and testability.

Part of the Infrastructure Layer.

**Usage:**

```python
factory = ServiceFactory(seed=42)
simulator = factory.create_feature_simulator()
analyzer  = factory.create_portfolio_risk_analyzer()
```
"""

from __future__ import annotations

import logging
from typing import cast

from fhs.core.services.assessment import FeatureAssessmentService, RankingService
from fhs.core.services.monte_carlo import MonteCarloEngine
from fhs.core.services.portfolio import PortfolioRiskAnalyzer, ScenarioAnalysisService
from fhs.core.services.risk import RiskCalculator
from fhs.core.services.simulation.simulator import FeatureSimulator

logger = logging.getLogger("fhs.service_factory")


class ServiceFactory:
    """Factory for creating configured service instances.

    Provides sensible defaults while allowing customization for testing
    and special use cases.

    **Design Pattern:** Factory Pattern with Dependency Injection
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize the service factory with default configuration.

        Args:
            seed: Default random seed for all services needing randomization.
        """
        self.seed = seed
        logger.info(f"ServiceFactory initialized with seed={seed}")

    @staticmethod
    def create_risk_calculator() -> RiskCalculator:
        """Create a RiskCalculator instance."""
        return RiskCalculator()

    def create_monte_carlo_engine(self, seed: int | None = None) -> MonteCarloEngine:
        """Create a MonteCarloEngine instance."""
        return MonteCarloEngine(seed=seed or self.seed)

    def create_feature_simulator(self, seed: int | None = None) -> FeatureSimulator:
        """Create a FeatureSimulator instance."""
        return FeatureSimulator(seed=seed or self.seed)

    def create_portfolio_risk_analyzer(
        self, seed: int | None = None
    ) -> PortfolioRiskAnalyzer:
        """Create a PortfolioRiskAnalyzer instance."""
        return PortfolioRiskAnalyzer(seed=seed or self.seed)

    # noinspection PyTypeHintsInspection
    def create_feature_assessment_service(
        self, calculator: RiskCalculator | None = None
    ) -> FeatureAssessmentService:
        """Create a FeatureAssessmentService instance."""
        if calculator is None:
            calculator = self.create_risk_calculator()
        return FeatureAssessmentService(calculator)

    # noinspection PyTypeHintsInspection
    def create_ranking_service(
        self, calculator: RiskCalculator | None = None
    ) -> RankingService:
        """Create a RankingService instance."""
        if calculator is None:
            calculator = self.create_risk_calculator()
        return RankingService(calculator)

    # noinspection PyTypeHintsInspection
    def create_scenario_analysis_service(
        self, calculator: RiskCalculator | None = None
    ) -> ScenarioAnalysisService:
        """Create a ScenarioAnalysisService instance."""
        if calculator is None:
            calculator = self.create_risk_calculator()
        return ScenarioAnalysisService(cast(RiskCalculator, calculator))
