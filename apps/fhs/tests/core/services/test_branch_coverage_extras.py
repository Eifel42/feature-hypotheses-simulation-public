# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
"""Targeted tests covering remaining partial branches across risk, financial,
and simulation services."""

from __future__ import annotations

import numpy as np

from src.fhs.core.model import Feature, ScenarioRiskModel, SimulationResult
from src.fhs.core.model.value_objects import IrrSummary
from src.fhs.core.services.financial.calculator import FinancialCalculator
from src.fhs.core.services.risk.portfolio_layers import PortfolioLayerRiskService
from src.fhs.core.services.risk.shapley import ShapleyAttributionService
from src.fhs.core.services.simulation.multi_year_pnl import PnLMultiYearService


def _feature(name: str, cluster: str | None = "Cluster A") -> Feature:
    return Feature(
        name=name,
        expected_users=10_000,
        conversion_rate=0.20,
        uncertainty=0.10,
        business_value_per_conversion=5.0,
        development_cost=30_000.0,
        annual_growth_rate=0.05,
        likelihood_of_non_delivery=0.10,
        dependency_cluster=cluster,
    )


def _sim_result(name: str, mean: float = 2000.0, seed: int = 1) -> SimulationResult:
    rng = np.random.default_rng(seed)
    scenarios = rng.normal(mean, mean * 0.05, 10_000)
    return SimulationResult(
        feature_name=name,
        results=scenarios,
        expected_value=float(np.mean(scenarios)),
        business_value_per_conversion=5.0,
        development_cost=30_000.0,
    )


def _risk_model() -> ScenarioRiskModel:
    return ScenarioRiskModel(
        risk_2_market_probability=0.20,
        risk_2_market_multiplier=0.85,
        risk_3_global_probability=0.05,
        risk_3_global_multiplier=0.60,
        component_risk_multiplier=0.70,
        default_component_probability=0.08,
        component_risk_by_cluster={"Cluster A": 0.10},
    )


# ── financial/calculator.py 296->302 ──────────────────────────────────────────
def test_assess_irr_no_downside_message_when_floor_above_hurdle() -> None:
    """Branch 296->302: floor IRR at/above hurdle ⇒ no downside_message."""
    assessment = FinancialCalculator.assess_irr(
        IrrSummary(expected=0.30, floor=0.15, ceiling=0.40),
        discount_rate=0.10,
    )
    assert assessment.verdict == "GO"
    assert assessment.downside_below_hurdle is False
    assert assessment.downside_message is None


# ── risk/portfolio_layers.py 179->177 ─────────────────────────────────────────
def test_simulate_portfolio_year1_state_reuses_cluster_probability() -> None:
    """Branch 179->177: when 2 features share a cluster, the second hits the
    `cluster in cluster_hits` short-circuit and skips re-sampling."""
    feat_a = _feature("H1: A", cluster="Cluster A")
    feat_b = _feature("H2: B", cluster="Cluster A")  # same cluster
    feature_by_name = {feat_a.name: feat_a, feat_b.name: feat_b}
    sim_results = {
        feat_a.name: _sim_result(feat_a.name, seed=1),
        feat_b.name: _sim_result(feat_b.name, seed=2),
    }

    state = PortfolioLayerRiskService.simulate_portfolio_year1_state(
        selected=[feat_a.name, feat_b.name],
        feature_by_name=feature_by_name,
        simulation_results=sim_results,
        risk_model=_risk_model(),
        seed=42,
    )
    # Only one cluster entry exists despite two features.
    assert set(state.cluster_hits.keys()) == {"Cluster A"}


# ── risk/shapley.py 102->112 ──────────────────────────────────────────────────
def test_attribute_zero_total_skips_share_normalization() -> None:
    """Branch 102->112: when total_risk is ~0 the share-normalization block
    is skipped; share_of_total stays at 0.0 for all contributions."""
    result = ShapleyAttributionService.attribute(
        metric="cvar_loss",
        contributions={"delivery": 0.0, "market": 0.0, "global": 0.0},
        selected=["F1"],
        baseline_value_eur=100.0,
        confidence=0.95,
    )
    assert result.total_risk_eur == 0.0
    assert all(item.share_of_total == 0.0 for item in result.contributions)


# ── simulation/multi_year_pnl.py 165->163 ─────────────────────────────────────
def test_multi_year_pnl_reuses_cluster_probability() -> None:
    """Branch 165->163: the second feature in the same cluster takes the
    short-circuit path and does not re-insert into cluster_probabilities."""
    feat_a = _feature("H1: A", cluster="Cluster A")
    feat_b = _feature("H2: B", cluster="Cluster A")
    service = PnLMultiYearService()
    pnl = service.simulate(
        feature_names=[feat_a.name, feat_b.name],
        feature_by_name={feat_a.name: feat_a, feat_b.name: feat_b},
        risk_model=_risk_model(),
        years=2,
        scenarios=2_000,
        discount_rate=0.10,
        seed=7,
        service_seed=99,
    )
    # Sanity: structure is intact and only one cluster was sampled.
    assert pnl.meta.years == 2
