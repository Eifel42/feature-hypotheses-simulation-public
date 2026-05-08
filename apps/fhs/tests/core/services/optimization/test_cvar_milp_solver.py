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

"""Tests for CVaR MILP solver and facade integration."""

from __future__ import annotations

import time

import numpy as np
import pytest

from fhs.application.optimization_service import PortfolioOptimizer
from fhs.core.model import Feature, SimulationResult
from fhs.core.services import RiskCalculator
from fhs.core.services.optimization.domain import RiskSolver
from fhs.core.services.optimization.solvers import CVaRMILPSolver


@pytest.fixture
def cvar_features() -> list[Feature]:
    return [
        Feature(
            name="Stable A",
            expected_users=1,
            conversion_rate=1.0,
            uncertainty=0.01,
            business_value_per_conversion=1.0,
            development_cost=40.0,
        ),
        Feature(
            name="Tail Risk B",
            expected_users=1,
            conversion_rate=1.0,
            uncertainty=0.01,
            business_value_per_conversion=1.0,
            development_cost=40.0,
        ),
        Feature(
            name="Stable C",
            expected_users=1,
            conversion_rate=1.0,
            uncertainty=0.01,
            business_value_per_conversion=1.0,
            development_cost=40.0,
        ),
    ]


@pytest.fixture
def cvar_sim_results(cvar_features: list[Feature]) -> dict[str, SimulationResult]:
    feature_arrays = {
        "Stable A": np.array([10.0] * 95 + [8.0] * 5),
        "Tail Risk B": np.array([14.0] * 95 + [-50.0] * 5),
        "Stable C": np.array([9.0] * 95 + [7.0] * 5),
    }

    return {
        feature.name: SimulationResult(
            feature_name=feature.name,
            results=feature_arrays[feature.name],
            scenarios=len(feature_arrays[feature.name]),
            expected_value=float(np.mean(feature_arrays[feature.name])),
            business_value_per_conversion=feature.business_value_per_conversion,
            development_cost=feature.development_cost,
        )
        for feature in cvar_features
    }


def test_cvar_solver_implements_risk_solver_protocol():
    solver = CVaRMILPSolver(seed=7, n_scenarios=100)
    assert isinstance(solver, RiskSolver)


def test_cvar_solver_selects_expected_subset(cvar_features, cvar_sim_results):
    solver = CVaRMILPSolver(seed=42, n_scenarios=100)

    result = solver.solve(
        features=cvar_features,
        sim_results=cvar_sim_results,
        budget=80.0,
        alpha=0.95,
    )

    assert set(result.recommended_features) == {"Stable A", "Stable C"}
    assert result.total_cost <= 80.0
    assert result.solver == "cvar_milp"
    assert result.portfolio_cvar_95 == pytest.approx(15.0)


def test_cvar_solver_is_deterministic(cvar_features, cvar_sim_results):
    solver = CVaRMILPSolver(seed=123, n_scenarios=100)

    result_1 = solver.solve(
        features=cvar_features,
        sim_results=cvar_sim_results,
        budget=80.0,
        alpha=0.95,
    )
    result_2 = solver.solve(
        features=cvar_features,
        sim_results=cvar_sim_results,
        budget=80.0,
        alpha=0.95,
    )

    assert result_1.recommended_features == result_2.recommended_features
    assert result_1.total_cost == pytest.approx(result_2.total_cost)
    assert result_1.portfolio_cvar_95 == pytest.approx(result_2.portfolio_cvar_95)


def test_optimizer_supports_cvar_dispatch(cvar_features, cvar_sim_results):
    optimizer = PortfolioOptimizer(
        features=cvar_features,
        simulation_results=cvar_sim_results,
        risk_calculator=RiskCalculator(),
    )

    via_dispatch = optimizer.optimize(
        budget=80.0,
        solver="cvar_milp",
        alpha=0.95,
        n_scenarios=100,
    )
    via_method = optimizer.optimize_cvar(
        budget=80.0,
        alpha=0.99,
        n_scenarios=100,
    )
    auto = optimizer.optimize(
        budget=80.0,
        solver="auto",
    )

    assert via_dispatch.solver == "cvar_milp"
    assert via_method.solver == "cvar_milp"
    assert via_dispatch.total_cost <= 80.0
    assert via_method.total_cost <= 80.0
    assert auto.solver == "exact"


def test_optimizer_cvar_can_optimize_on_profit_scenarios(
    cvar_features, cvar_sim_results
):
    optimizer = PortfolioOptimizer(
        features=cvar_features,
        simulation_results=cvar_sim_results,
        risk_calculator=RiskCalculator(),
    )
    baseline = optimizer.optimize_cvar(
        budget=80.0,
        alpha=0.95,
        n_scenarios=100,
    )
    profit_scenarios = {
        feature.name: (
            cvar_sim_results[feature.name].results_array
            * feature.business_value_per_conversion
            - feature.development_cost
        )
        for feature in cvar_features
    }

    profit_result = optimizer.optimize_cvar(
        budget=80.0,
        alpha=0.95,
        n_scenarios=100,
        profit_scenarios=profit_scenarios,
    )

    assert set(baseline.recommended_features) == {"Stable A", "Stable C"}
    assert profit_result.solver == "cvar_milp"
    assert set(profit_result.recommended_features) == {"Stable A"}
    assert profit_result.total_cost <= 80.0


def test_optimizer_cvar_profit_scenarios_require_all_features(
    cvar_features, cvar_sim_results
):
    optimizer = PortfolioOptimizer(
        features=cvar_features,
        simulation_results=cvar_sim_results,
        risk_calculator=RiskCalculator(),
    )
    incomplete = {
        "Stable A": cvar_sim_results["Stable A"].results_array - 40.0,
    }

    with pytest.raises(ValueError, match="Missing profit scenarios"):
        optimizer.optimize_cvar(
            budget=80.0,
            alpha=0.95,
            n_scenarios=100,
            profit_scenarios=incomplete,
        )


def test_cvar_solver_handles_10_features_under_30_seconds():
    rng = np.random.default_rng(42)
    features = [
        Feature(
            name=f"Feature {idx}",
            expected_users=1000,
            conversion_rate=0.2,
            uncertainty=0.2,
            business_value_per_conversion=1.0,
            development_cost=20.0,
        )
        for idx in range(10)
    ]
    sim_results = {}
    for idx, feature in enumerate(features):
        base = rng.normal(loc=100.0 + idx * 2.0, scale=10.0 + idx, size=1_200)
        # Inject a mild downside tail in every feature.
        base[:60] -= (idx + 1) * 15.0
        sim_results[feature.name] = SimulationResult(
            feature_name=feature.name,
            results=base,
            scenarios=len(base),
            expected_value=float(np.mean(base)),
            business_value_per_conversion=feature.business_value_per_conversion,
            development_cost=feature.development_cost,
        )

    solver = CVaRMILPSolver(seed=42, n_scenarios=300)

    start = time.perf_counter()
    result = solver.solve(
        features=features,
        sim_results=sim_results,
        budget=120.0,
        alpha=0.95,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 30.0
    assert result.total_cost <= 120.0
    assert result.solver == "cvar_milp"
