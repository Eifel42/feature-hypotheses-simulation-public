#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""
Portfolio Facade for Simplified API Access

.. deprecated:: 0.9.0
    Use `AdvancedPortfolioService` instead. This module will be removed in v1.0.0.

Provides a high-level, simplified API for notebooks and CLI usage.
Orchestrates multiple services to provide complete portfolio analysis workflows.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

import numpy as np

from fhs.application.service_factory import ServiceFactory

from ..core.model import Feature
from ..core.model.value_objects import Budget, OptimizationStrategy
from ..core.services import (
    FeatureAssessmentService,
    RankingService,
    ScenarioAnalysisService,
    aggregate_portfolio_scenarios_from_results,
)
from ..core.services.simulation.simulator import FeatureSimulator
from .advanced_portfolio_service import AdvancedPortfolioService
from .export_service import PortfolioExporter
from .optimization_service import PortfolioOptimizer

logger = logging.getLogger("fhs.portfolio_facade")


@dataclass
class _SimulationConfig:
    """Simulation parameters for PortfolioFacade.

    .. deprecated:: 0.9.0
        Used only by the deprecated `PortfolioFacade`.
    """

    seed: int | None = None
    scenarios: int = 10000
    distribution: str = "normal"
    correlation_matrix: np.ndarray | None = field(default=None)


@dataclass
class _PortfolioServicesConfig:
    """Service injection container for PortfolioFacade.

    .. deprecated:: 0.9.0
        Used only by the deprecated `PortfolioFacade`.
    """

    simulator: FeatureSimulator | None = None
    assessment_service: FeatureAssessmentService | None = None
    ranking_service: RankingService | None = None
    scenario_analysis_service: ScenarioAnalysisService | None = None
    exporter: PortfolioExporter | None = None


class PortfolioFacade:
    """Simplified API facade for portfolio analysis workflows.

    .. deprecated:: 0.9.0
        Use `AdvancedPortfolioService` instead. This class will be removed in v1.0.0.
        It duplicates simulation caching and portfolio aggregation logic from other services.

    Provides high-level methods that combine multiple services for common
    use cases in notebooks and CLI applications.

    Example:
        >>> features = []
        >>> facade = PortfolioFacade(features, sim_config=_SimulationConfig(seed=42))
        >>> analysis = facade.analyze()
        >>> print(analysis["summary"])
        >>> result = facade.optimize_and_export(budget=100_000, output_dir=".")
    """

    # noinspection PyTypeHintsInspection
    def __init__(
        self,
        features: list[Feature],
        budget: float | None = None,
        discount_rate: float = 0.10,
        sim_config: _SimulationConfig | None = None,
        services: _PortfolioServicesConfig | None = None,
    ):
        """
        Initialize Portfolio Facade.

        .. deprecated:: 0.9.0
            Use `AdvancedPortfolioService` instead.

        Args:
            features: List of features to analyze
            budget: Optional total budget constraint
            discount_rate: Discount rate for NPV calculations (default 0.10)
            sim_config: Simulation parameters (seed, scenarios, distribution, correlation)
            services: Optional service injection overrides for testing
        """
        warnings.warn(
            "PortfolioFacade is deprecated and will be removed in v1.0.0. "
            "Use AdvancedPortfolioService instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not features:
            raise ValueError("At least one feature is required")

        sim = sim_config or _SimulationConfig()
        svc = services or _PortfolioServicesConfig()

        seed = sim.seed
        scenarios = sim.scenarios
        distribution = sim.distribution
        correlation_matrix = sim.correlation_matrix
        simulator = svc.simulator
        assessment_service = svc.assessment_service
        ranking_service = svc.ranking_service
        scenario_analysis_service = svc.scenario_analysis_service
        exporter = svc.exporter

        self.features = features
        self.seed = seed
        self.scenarios = scenarios
        self.distribution = distribution
        self.correlation_matrix = correlation_matrix
        self.budget = (
            float(budget)
            if budget is not None
            else float(sum(feature.development_cost for feature in features))
        )
        self.discount_rate = float(discount_rate)

        factory = ServiceFactory(seed=seed)

        # Constructor injection with sensible defaults.
        self.simulator = simulator or factory.create_feature_simulator(seed=seed)
        self.calculator = factory.create_risk_calculator()
        self.assessment_service = (
            assessment_service
            or factory.create_feature_assessment_service(self.calculator)
        )
        self.ranking_service = ranking_service or factory.create_ranking_service(
            self.calculator
        )
        self.scenario_analysis_service = (
            scenario_analysis_service
            or factory.create_scenario_analysis_service(self.calculator)
        )
        self.exporter = exporter or PortfolioExporter(
            features=self.features,
            discount_rate=self.discount_rate,
        )

        self._delegate_to_advanced = (
            simulator is None
            and assessment_service is None
            and ranking_service is None
            and scenario_analysis_service is None
            and distribution == "normal"
            and correlation_matrix is None
        )
        self._advanced_service: AdvancedPortfolioService | None = None
        if self._delegate_to_advanced:
            self._advanced_service = (
                AdvancedPortfolioService(  # pragma: no cover - deprecated facade
                    features,
                    budget=self.budget,
                    discount_rate=self.discount_rate,
                    seed=seed or 42,
                    scenarios=scenarios,
                )
            )

        # Cache for simulation results
        self._simulation_results: dict[str, Any] | None = None

    def simulate_all(self) -> dict[str, Any]:
        """
        Simulate all features and cache results.

        Returns:
            Dictionary mapping feature names to simulation results
        """
        if self._delegate_to_advanced and self._advanced_service is not None:
            return (
                self._advanced_service.simulation_results
            )  # pragma: no cover - deprecated facade

        if self._simulation_results is not None:
            logger.info("Using cached simulation results")
            return self._simulation_results

        logger.info(f"Simulating {len(self.features)} features...")
        results = {}
        for feature in self.features:
            results[feature.name] = self.simulator.simulate_feature(
                feature,
                scenarios=self.scenarios,
                distribution=self.distribution,
            )

        self._simulation_results = results
        return results

    def analyze(self) -> dict[str, Any]:
        """
        Complete portfolio analysis in one call.

        Returns:
            Dictionary containing:
                - summary: Portfolio summary with totals
                - ranking: Feature rankings by multiple criteria
                - concentration: Risk concentration analysis
                - stress_tests: Stress test results
        """
        logger.info("Running complete portfolio analysis...")

        if self._delegate_to_advanced and self._advanced_service is not None:
            names = [
                feature.name for feature in self.features
            ]  # pragma: no cover - deprecated facade
            snapshot = self._advanced_service.portfolio_snapshot(
                names
            )  # pragma: no cover - deprecated facade
            ranking_rows = (
                self._advanced_service.decisions.rank_features()
            )  # pragma: no cover - deprecated facade
            concentration = self._advanced_service.decisions.concentration(
                names
            )  # pragma: no cover - deprecated facade
            stress_payload = self._advanced_service.stress_scenarios(
                names
            )  # pragma: no cover - deprecated facade
            scenarios = stress_payload.get(
                "scenarios", []
            )  # pragma: no cover - deprecated facade
            # pragma: no cover - deprecated facade
            market = next(  # pragma: no cover - deprecated facade
                (
                    row for row in scenarios if row.get("name") == "Market pullback"
                ),  # pragma: no cover - deprecated facade
                {
                    "name": "Market pullback",
                    "expected": 0.0,
                    "var_95": 0.0,
                },  # pragma: no cover - deprecated facade
            )  # pragma: no cover - deprecated facade
            failure = next(  # pragma: no cover - deprecated facade
                (
                    row for row in scenarios if row.get("name") == "Top feature delay"
                ),  # pragma: no cover - deprecated facade
                {
                    "name": "Top feature delay",
                    "expected": 0.0,
                    "var_95": 0.0,
                },  # pragma: no cover - deprecated facade
            )  # pragma: no cover - deprecated facade
            # pragma: no cover - deprecated facade
            return {  # pragma: no cover - deprecated facade
                "summary": {
                    "total_expected_business_value": float(snapshot.expected),
                    "portfolio_var_95": float(snapshot.var_95),
                    "n_features": len(self.features),
                },
                "ranking": self._build_ranking_rows(ranking_rows),
                "concentration": {
                    "is_concentrated": concentration.hhi >= 0.25,
                    "hhi": concentration.hhi,
                    "warnings": (
                        [concentration.verdict]
                        if concentration.verdict != "Low concentration"
                        else []
                    ),
                },
                "stress_tests": {
                    "market_crash": {
                        "scenario": market.get("name", "market_crash"),
                        "impact": {
                            "expected_change": market.get("expected_delta_pct", 0.0)
                        },
                    },
                    "feature_failure": {
                        "scenario": failure.get("name", "feature_failure"),
                        "impact": {
                            "expected_change": failure.get("expected_delta_pct", 0.0)
                        },
                    },
                },
            }

        # Ensure simulations are run
        results = self.simulate_all()

        # Portfolio summary
        portfolio_scenarios = aggregate_portfolio_scenarios_from_results(results)
        total_expected = float(np.mean(portfolio_scenarios))
        total_var = self.calculator.calculate_var(portfolio_scenarios, 0.95)

        # Feature ranking
        ranking_result = self.ranking_service.rank_features(self.features, results)

        # Risk concentration
        concentration_data = self.ranking_service.get_risk_concentration(
            self.features, results
        )
        if isinstance(concentration_data, dict):
            concentration_payload = concentration_data
        else:
            concentration_payload = {  # pragma: no cover - deprecated facade
                "is_concentrated": bool(
                    getattr(concentration_data, "hhi", 0.0) >= 0.25
                ),
                "hhi": float(getattr(concentration_data, "hhi", 0.0)),
                "warnings": [str(getattr(concentration_data, "verdict", ""))],
            }

        # Stress tests
        stress_crash = self.scenario_analysis_service.stress_test(
            self.features, results, scenario="market_crash"
        )
        stress_failure = self.scenario_analysis_service.stress_test(
            self.features, results, scenario="feature_failure"
        )

        return {
            "summary": {
                "total_expected_business_value": total_expected,
                "portfolio_var_95": total_var,
                "n_features": len(self.features),
            },
            "ranking": ranking_result["rankings"],
            "concentration": {
                "is_concentrated": concentration_payload.get("is_concentrated", False),
                "hhi": concentration_payload.get("hhi", 0.0),
                "warnings": concentration_payload.get("warnings", []),
            },
            "stress_tests": {
                "market_crash": stress_crash,
                "feature_failure": stress_failure,
            },
        }

    def optimize_and_export(
        self,
        budget: float | Budget | None = None,
        max_sprints: int | None = None,
        strategy: str | OptimizationStrategy = "var_floor",
        output_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        """
        Optimize portfolio and export results.

        Args:
            budget: Budget constraint (exclusive with max_sprints)
            max_sprints: Sprint constraint (exclusive with budget)
            strategy: Optimization strategy ("var_floor", "expected", "sharpe")
            output_dir: Directory for export files (if None, no export)

        Returns:
            Optimization result dictionary
        """
        logger.info("Running portfolio optimization...")

        def validate_inputs() -> None:
            if budget is not None and max_sprints is not None:
                raise ValueError("Specify either budget OR max_sprints, not both")
            if max_sprints is not None:
                raise NotImplementedError(
                    "Sprint-based optimization is not available in this facade version. "
                    "Use budget-based optimization via 'budget=' instead."
                )
            if budget is None:
                raise ValueError("Must specify either budget or max_sprints")

        def export_payload(result_payload: dict[str, Any]) -> None:
            if not output_dir:
                return  # pragma: no cover - deprecated facade
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            self.exporter.export_optimization_result_csv(result_payload, output_path)
            logger.info(f"Results exported to {output_path}")

        validate_inputs()

        if self._delegate_to_advanced and self._advanced_service is not None:
            optimized = (
                self._advanced_service.optimize(  # pragma: no cover - deprecated facade
                    solver="exact",  # pragma: no cover - deprecated facade
                    budget=float(
                        budget.amount if isinstance(budget, Budget) else budget
                    ),  # pragma: no cover - deprecated facade
                    strategy=str(strategy),  # pragma: no cover - deprecated facade
                )
            )  # pragma: no cover - deprecated facade
            result_payload = asdict(optimized)  # pragma: no cover - deprecated facade
            result_payload["recommended_features"] = (
                list(  # pragma: no cover - deprecated facade
                    optimized.recommended_features  # pragma: no cover - deprecated facade
                )
            )  # pragma: no cover - deprecated facade
            export_payload(result_payload)  # pragma: no cover - deprecated facade
            return result_payload  # pragma: no cover - deprecated facade

        # Ensure simulations are run
        results = self.simulate_all()

        # Run optimization
        optimizer = PortfolioOptimizer(
            features=self.features,
            simulation_results=results,
            risk_calculator=self.calculator,
        )
        solver_result = optimizer.optimize_exact(
            budget=budget,
            strategy=strategy,
            sum_portfolio_scenarios_fn=aggregate_portfolio_scenarios_from_results,
        )
        result_payload = (
            solver_result.to_dict()
            if hasattr(solver_result, "to_dict")
            else dict(cast(dict[str, Any], solver_result))
        )
        export_payload(result_payload)

        return result_payload

    def assess_feature(self, feature_name: str) -> dict[str, Any]:
        """
        Assess a single feature.

        Args:
            feature_name: Name of the feature to assess

        Returns:
            Feature assessment dictionary
        """
        feature = next((f for f in self.features if f.name == feature_name), None)
        if not feature:
            raise ValueError(f"Feature not found: {feature_name}")

        results = self.simulate_all()

        return self.assessment_service.assess_feature(
            feature, simulation_result=results[feature.name]
        )

    def compare_features(
        self, feature_names: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Compare multiple features.

        Args:
            feature_names: List of feature names (None = all features)

        Returns:
            Feature comparison dictionary
        """
        if feature_names:
            features = [f for f in self.features if f.name in feature_names]
        else:
            features = self.features  # pragma: no cover - deprecated facade

        results = self.simulate_all()
        assessments = [
            self.assessment_service.assess_feature(feature, results[feature.name])
            for feature in features
        ]
        assessments.sort(key=lambda row: row["expected_business_value"], reverse=True)
        return {
            "assessments": assessments,
            "count": len(assessments),
        }

    @staticmethod
    def _build_ranking_rows(ranking_rows: Any) -> list[dict[str, Any]]:
        result = []  # pragma: no cover - deprecated facade
        for row in ranking_rows:  # pragma: no cover - deprecated facade
            if row.risk_ratio > 0.35:  # pragma: no cover - deprecated facade
                recommendation = "High risk"  # pragma: no cover - deprecated facade
            elif row.risk_ratio > 0.15:  # pragma: no cover - deprecated facade
                recommendation = "Medium risk"  # pragma: no cover - deprecated facade
            else:  # pragma: no cover - deprecated facade
                recommendation = "Low risk"  # pragma: no cover - deprecated facade
            result.append(  # pragma: no cover - deprecated facade
                {  # pragma: no cover - deprecated facade
                    "feature": row.feature,  # pragma: no cover - deprecated facade
                    "expected_business_value": row.expected_business_value,  # pragma: no cover - deprecated facade
                    "var_95_business_value": row.var_95_business_value,  # pragma: no cover - deprecated facade
                    "risk_ratio": row.risk_ratio,  # pragma: no cover - deprecated facade
                    "uncertainty": row.llp,  # pragma: no cover - deprecated facade
                    "recommendation": recommendation,  # pragma: no cover - deprecated facade
                }  # pragma: no cover - deprecated facade
            )  # pragma: no cover - deprecated facade
        return result  # pragma: no cover - deprecated facade
