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

"""Spike test: ILP proxy vs. CVaR-MILP on blockchain scenario."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter

import pytest

from fhs.application.optimization_service import PortfolioOptimizer
from fhs.application.scenario_service import ScenarioService
from fhs.core.services import (
    FeatureSimulator,
    RiskCalculator,
    aggregate_portfolio_scenarios_from_results,
)


@pytest.mark.slow
def test_cvar_milp_vs_ilp_comparison():
    """Compare ILP proxy vs. CVaR-MILP on blockchain scenario."""
    config_dir = Path(__file__).resolve().parents[2] / "notebooks" / "config"
    scenario = ScenarioService.create_default(config_dir=config_dir).load_scenario(
        "blockchain"
    )

    simulator = FeatureSimulator(seed=42)
    sim_results = {
        feature.name: simulator.simulate_feature(feature, scenarios=20_000)
        for feature in scenario.features
    }

    optimizer = PortfolioOptimizer(
        features=scenario.features,
        simulation_results=sim_results,
        risk_calculator=RiskCalculator(),
    )

    ilp_start = perf_counter()
    ilp_result = optimizer.optimize_ilp(
        budget=scenario.budget,
        strategy="var_floor",
        sum_portfolio_scenarios_fn=aggregate_portfolio_scenarios_from_results,
    )
    ilp_runtime = perf_counter() - ilp_start

    cvar_start = perf_counter()
    cvar_result = optimizer.optimize_cvar(
        budget=scenario.budget,
        alpha=0.95,
        n_scenarios=300,
        sum_portfolio_scenarios_fn=aggregate_portfolio_scenarios_from_results,
    )
    cvar_runtime = perf_counter() - cvar_start

    print(
        f"[SPIKE] ILP runtime={ilp_runtime:.3f}s, CVaR-MILP runtime={cvar_runtime:.3f}s, "
        f"ILP CVaR95={ilp_result.portfolio_cvar_95:.2f}, CVaR-MILP CVaR95={cvar_result.portfolio_cvar_95:.2f}"
    )
    print(
        f"[SPIKE] ILP features={ilp_result.recommended_features}, CVaR-MILP features={cvar_result.recommended_features}"
    )

    assert ilp_result.total_cost <= scenario.budget
    assert cvar_result.total_cost <= scenario.budget
    assert ilp_result.feature_count >= 1
    assert cvar_result.feature_count >= 1

    # Loss-CVaR convention (lower is better): loss = -business value
    ilp_cvar_loss_95 = -ilp_result.portfolio_cvar_95
    cvar_cvar_loss_95 = -cvar_result.portfolio_cvar_95
    assert cvar_cvar_loss_95 <= ilp_cvar_loss_95 + 1e-6
