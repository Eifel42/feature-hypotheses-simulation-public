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

"""Application service for advanced portfolio notebooks with business-domain sub-facades.

This service implements PortfolioContext protocol and organizes operations
into fachliche (business-domain) sub-facades:
- service.risk → Risk attribution and loss metrics
- service.delivery → Delivery risk and profitability
- service.multi_year → Multi-year simulations and NPV/IRR
- service.decisions → Portfolio decisions and optimization
- service.layers → Risk layer simulations
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from fhs.application.optimization_service import PortfolioOptimizer
from fhs.core.model import (
    DeliveryRiskConfig,
    Feature,
    OptimizationResult,
    PortfolioSnapshot,
    ScenarioRiskModel,
    SimulationResult,
)
from fhs.core.services import (
    FeatureSimulator,
    PortfolioDecisionSupportService,
    PortfolioViewService,
    RiskCalculator,
)
from fhs.core.services.risk import PortfolioLayerRiskService

from .decision_operations import DecisionOperations
from .delivery_analysis_operations import DeliveryAnalysisOperations
from .dtos import ScenarioContext
from .multi_year_analysis_operations import MultiYearAnalysisOperations
from .risk_analysis_operations import RiskAnalysisOperations
from .risk_layers_operations import RiskLayersOperations


class AdvancedPortfolioService:
    """Portfolio analysis facade with business-domain sub-facades.

    Sub-Facades (fachliche Bereiche):
        service.risk: Risk attribution, loss metrics, Shapley analysis
        service.delivery: Delivery risk, sprint overruns, profitability
        service.multi_year: Multi-year simulations, NPV/IRR, financial views
        service.decisions: Portfolio decisions, optimization, budget analysis
        service.layers: Risk layer simulations (delivery, market, component, global)
    """

    # noinspection PyTypeHintsInspection
    def __init__(
        self,
        features: list[Feature],
        *,
        budget: float,
        discount_rate: float,
        risk_model: ScenarioRiskModel | dict | None = None,
        delivery_config: DeliveryRiskConfig | None = None,
        seed: int = 42,
        scenarios: int = 100_000,
    ):
        # Public state (PortfolioContext properties)
        self._features = features
        self._budget = budget
        self._discount_rate = discount_rate
        self._seed = seed
        self._scenarios = scenarios
        self._risk_model = PortfolioLayerRiskService.normalize_risk_model(risk_model)
        self._delivery_config = delivery_config or DeliveryRiskConfig()

        # Infrastructure
        self._feature_by_name = {feature.name: feature for feature in features}
        self._simulator = FeatureSimulator(seed=seed)
        self._risk_calculator = RiskCalculator()
        self._simulation_results: dict[str, SimulationResult] | None = None
        self._optimizer: PortfolioOptimizer | None = None

        # Sub-Facades (fachliche Bereiche)
        self.risk = RiskAnalysisOperations(self)
        self.delivery = DeliveryAnalysisOperations(self)
        self.multi_year = MultiYearAnalysisOperations(self)
        self.decisions = DecisionOperations(self)
        self.layers = RiskLayersOperations(self)

    @classmethod
    def from_scenario(
        cls,
        scenario: ScenarioContext,
        *,
        seed: int = 42,
        scenarios: int | None = None,
        warm_cache: bool = True,
    ) -> AdvancedPortfolioService:
        """Create a portfolio service directly from notebook scenario context."""
        resolved_scenarios = scenario.scenarios if scenarios is None else scenarios
        service = cls(
            scenario.features,
            budget=scenario.budget,
            discount_rate=scenario.discount_rate,
            risk_model=scenario.risk_model,
            delivery_config=scenario.delivery_config,
            seed=seed,
            scenarios=resolved_scenarios,
        )
        if warm_cache:  # pragma: no cover - partial branch
            _ = service.simulation_results
        return service

    # PortfolioContext protocol implementation
    @property
    def features(self) -> list[Feature]:
        """All features in the portfolio."""
        return self._features

    @property
    def simulation_results(self) -> dict[str, SimulationResult]:
        """Simulate all features once and cache results."""
        if self._simulation_results is None:
            self._simulation_results = {
                feature.name: self._simulator.simulate_feature(
                    feature,
                    scenarios=self._scenarios,
                )
                for feature in self._features
            }
        return self._simulation_results

    @property
    def budget(self) -> float:
        """Total budget for portfolio optimization."""
        return self._budget

    @property
    def discount_rate(self) -> float:
        """Discount rate for NPV calculations."""
        return self._discount_rate

    @property
    def seed(self) -> int:
        """Random seed for reproducibility."""
        return self._seed

    @property
    def scenarios(self) -> int:
        """Number of Monte Carlo scenarios."""
        return self._scenarios

    @property
    def risk_model(self) -> ScenarioRiskModel:
        """Normalized scenario risk model used by advanced analyses."""
        return self._risk_model

    @property
    def delivery_config(self) -> DeliveryRiskConfig:
        """Delivery-risk configuration associated with this portfolio context."""
        return self._delivery_config

    def resolve_names(self, names: Iterable[str] | None) -> list[str]:
        """Resolve feature names, defaulting to all features if None."""
        if names is None:
            return [feature.name for feature in self._features]
        return [name for name in names if name in self._feature_by_name]

    def get_feature(self, name: str) -> Feature:
        """Get feature by name."""
        return self._feature_by_name[name]  # pragma: no cover - defensive

    def sum_portfolio_scenarios(
        self,
        simulation_subset: dict[str, SimulationResult],
    ) -> np.ndarray:
        """Sum business value scenarios across multiple features."""
        if not simulation_subset:
            return np.array([], dtype=float)  # pragma: no cover - defensive
        arrays = [
            result.results_array
            * self._feature_by_name[name].business_value_per_conversion
            for name, result in simulation_subset.items()
        ]
        return np.asarray(np.sum(arrays, axis=0), dtype=float)

    # Infrastructure (non-protocol)
    @property
    def optimizer(self) -> PortfolioOptimizer:
        """Create optimizer lazily with cached simulation results."""
        if self._optimizer is None:
            self._optimizer = PortfolioOptimizer(
                features=self._features,
                simulation_results=self.simulation_results,
                risk_calculator=self._risk_calculator,
            )
        return self._optimizer

    def _spawn_subset_service(
        self,
        subset_features: list[Feature],
        *,
        budget: float,
    ) -> AdvancedPortfolioService:
        """Create a subset-scoped service with shared runtime configuration."""
        subset_service = AdvancedPortfolioService(
            subset_features,
            budget=float(budget),
            discount_rate=self._discount_rate,
            seed=self._seed,
            scenarios=self._scenarios,
        )
        # Warm simulations once so downstream decision support can reuse cache.
        _ = subset_service.simulation_results
        return subset_service

    def _optimizer_sum_fn(
        self,
        combination: dict[str, SimulationResult],
    ) -> np.ndarray:
        return self.sum_portfolio_scenarios(combination)

    def subset_results(
        self,
        names: Iterable[str] | None = None,
    ) -> dict[str, SimulationResult]:
        """Get simulation results for selected feature names."""
        resolved = self.resolve_names(names)
        return {name: self.simulation_results[name] for name in resolved}

    # Core Portfolio Methods (remain in facade)
    def portfolio_snapshot(
        self,
        names: Iterable[str] | None = None,
        *,
        investment: float | None = None,
    ) -> PortfolioSnapshot:
        """Portfolio metrics from selected feature names."""
        subset = self.subset_results(names)
        scenarios = self.sum_portfolio_scenarios(subset)
        inferred_investment = (
            float(investment)
            if investment is not None
            else float(
                sum(self._feature_by_name[name].development_cost for name in subset)
            )
        )
        return PortfolioViewService.portfolio_snapshot_from_scenarios(
            scenarios,
            investment=inferred_investment,
        )

    def portfolio_scenarios(self, names: Iterable[str] | None = None) -> np.ndarray:
        """Business value scenarios (EUR) for selected features."""
        return self.sum_portfolio_scenarios(
            self.subset_results(names)
        )  # pragma: no cover - defensive

    def optimize(
        self,
        *,
        solver: str,
        budget: float | None = None,
        strategy: str = "var_floor",
        k: int = 20,
        alpha: float = 0.95,
        n_scenarios: int = 300,
    ) -> OptimizationResult:
        """Run one solver and add derived business metrics."""
        solver_budget = float(self._budget if budget is None else budget)
        return PortfolioViewService.optimize_portfolio(
            optimizer=self.optimizer,
            solver=solver,
            budget=solver_budget,
            strategy=strategy,
            sum_portfolio_scenarios_fn=self._optimizer_sum_fn,
            seed=self._seed,
            discount_rate=self._discount_rate,
            k=k,
            alpha=alpha,
            n_scenarios=n_scenarios,
        )

    def optimize_budget_levels_with_guardrails(
        self,
        budget_levels: dict[str, float],
        *,
        solver: str = "ilp",
        strategy: str = "var_floor",
    ) -> dict[str, OptimizationResult]:
        """Run optimization across budget levels with 04-style guardrails."""
        return PortfolioDecisionSupportService.optimize_budget_levels_with_guardrails(  # pragma: no cover - defensive
            budget_levels=budget_levels,
            features=self._features,
            simulation_results=self.simulation_results,
            optimize_for_budget=lambda budget: self.optimize(
                solver=solver,
                budget=budget,
                strategy=strategy,
            ),
        )

    # Convenience wrappers for Decision operations that need callbacks
    def negative_score_analysis(
        self,
        *,
        budget: float | None = None,
        strategy: str = "var_floor",
    ):
        """Analyze features with negative scores (convenience wrapper)."""
        return self.decisions.negative_score_analysis(
            budget=budget,
            strategy=strategy,
            spawn_subset_fn=self._spawn_subset_service,
            optimize_fn=self.optimize,
        )

    def budget_risk_path(
        self, levels, *, solver="ilp", strategy="var_floor", seed=42, **kwargs
    ):
        """Budget risk path across levels (convenience wrapper)."""
        return self.decisions.budget_risk_path(
            levels,
            solver=solver,
            strategy=strategy,
            seed=seed,
            optimize_fn=self.optimize,
            analyze_delivery_risk_fn=self.optimizer.analyze_delivery_risk,
            **kwargs,
        )

    def budget_sensitivity(self, levels, *, solver="ilp", strategy="var_floor"):
        """Budget sensitivity analysis (convenience wrapper)."""
        return self.decisions.budget_sensitivity(
            levels,
            solver=solver,
            strategy=strategy,
            optimize_fn=self.optimize,
        )

    def budget_frontier(self, budgets, *, solver="ilp", strategy="var_floor"):
        """Efficient frontier across budgets (convenience wrapper)."""
        return self.decisions.budget_frontier(
            budgets,
            solver=solver,
            strategy=strategy,
            optimize_fn=self.optimize,
        )

    def compare_solvers(
        self, include=("exact", "ilp", "greedy"), *, budget=None, strategy="var_floor"
    ):
        """Compare optimization solvers (convenience wrapper)."""
        return self.decisions.compare_solvers(
            include=include,
            budget=budget,
            strategy=strategy,
            optimize_fn=self.optimize,
        )

    def stress_scenarios(self, names=None):
        """Stress scenario analysis (convenience wrapper)."""
        return self.decisions.stress_scenarios(
            names,
            portfolio_snapshot_fn=self.portfolio_snapshot,
        )
