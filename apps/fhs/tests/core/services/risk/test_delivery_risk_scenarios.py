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

"""Scenario-scale tests for DeliveryRiskConfig.scenarios field.

Verifies that SprintOverrunService produces valid, stable metrics across
a range of Monte Carlo scenario counts — from quick dev runs to audit-grade.
"""

from __future__ import annotations

import numpy as np
import pytest

from fhs.core.model import Feature
from fhs.core.model.config import DeliveryRiskConfig
from fhs.core.services.risk.sprint_overrun import SprintOverrunService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SCENARIO_SIZES = [100, 1_000, 10_000, 100_000]


@pytest.fixture
def feature() -> Feature:
    return Feature(
        name="H1: Simplified UI",
        expected_users=100_000,
        conversion_rate=0.26,
        uncertainty=0.4,
        business_value_per_conversion=4.7,
        development_cost=75_000.0,
        development_weeks=8,
        likelihood_of_non_delivery=0.2,
    )


@pytest.fixture
def features() -> list[Feature]:
    return [
        Feature(
            name="H1: Simplified UI",
            expected_users=100_000,
            conversion_rate=0.26,
            uncertainty=0.4,
            business_value_per_conversion=4.7,
            development_cost=75_000.0,
            development_weeks=8,
            likelihood_of_non_delivery=0.2,
        ),
        Feature(
            name="H2: Traceability",
            expected_users=69_700,
            conversion_rate=0.55,
            uncertainty=0.35,
            business_value_per_conversion=1.77,
            development_cost=50_000.0,
            development_weeks=6,
            likelihood_of_non_delivery=0.5,
        ),
    ]


def _config(n_scenarios: int) -> DeliveryRiskConfig:
    return DeliveryRiskConfig(scenarios=n_scenarios)


def _bv_array(n: int, seed: int = 42) -> np.ndarray:
    """Synthetic business-value-after-risk array with n scenarios."""
    rng = np.random.default_rng(seed)
    return rng.normal(50_000, 10_000, size=n).clip(0)


# ---------------------------------------------------------------------------
# DeliveryRiskConfig.scenarios field
# ---------------------------------------------------------------------------


def test_default_scenarios_is_5000() -> None:
    assert DeliveryRiskConfig().scenarios == 5000


def test_scenarios_minimum_guard() -> None:
    with pytest.raises(Exception):
        DeliveryRiskConfig(scenarios=99)


@pytest.mark.parametrize("n", SCENARIO_SIZES)
def test_scenarios_field_roundtrip(n: int) -> None:
    config = _config(n)
    assert config.scenarios == n


# ---------------------------------------------------------------------------
# simulate_delivery: correct scenario count propagation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", SCENARIO_SIZES)
def test_simulate_delivery_output_length(feature: Feature, n: int) -> None:
    """Output arrays must match the input business-value array length."""
    config = _config(n)
    bv = _bv_array(n)
    plan = SprintOverrunService.compute_sprint_plans([feature])[feature.name]

    result = SprintOverrunService.simulate_delivery(
        feature=feature,
        sprint_plan=plan,
        business_value_after_risk=bv,
        config=config,
    )

    assert len(result.actual_sprints) == n
    assert len(result.actual_cost) == n
    assert len(result.cancelled) == n
    assert len(result.business_value_after_risk) == n


# ---------------------------------------------------------------------------
# simulate_delivery: metric validity across scenario counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", SCENARIO_SIZES)
def test_delivery_metrics_are_valid(feature: Feature, n: int) -> None:
    """Core metrics must be in sensible ranges regardless of scenario count."""
    config = _config(n)
    bv = _bv_array(n)
    plan = SprintOverrunService.compute_sprint_plans([feature])[feature.name]

    result = SprintOverrunService.simulate_delivery(
        feature=feature,
        sprint_plan=plan,
        business_value_after_risk=bv,
        config=config,
    )

    assert result.planned_sprints >= 1
    assert result.expected_actual_sprints >= result.planned_sprints * 0.5
    assert result.sprints_p95 >= result.sprints_p50
    assert result.cancelled_pct >= 0.0
    assert result.cancelled_pct <= 1.0
    assert result.expected_actual_cost > 0


# ---------------------------------------------------------------------------
# simulate_delivery: metric convergence
# ---------------------------------------------------------------------------


def test_metrics_converge_with_more_scenarios(feature: Feature) -> None:
    """P95 sprint estimate should stabilise as scenarios increase.

    Tests that the difference between 10k and 100k is smaller than
    between 100 and 1k — a basic convergence signal.
    """
    results = {}
    for n in [100, 1_000, 10_000, 100_000]:
        config = _config(n)
        bv = _bv_array(n, seed=0)
        plan = SprintOverrunService.compute_sprint_plans([feature])[feature.name]
        r = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=bv,
            config=config,
            seed=0,
        )
        results[n] = r.sprints_p95

    # The spread should narrow as n grows
    spread_small = abs(results[1_000] - results[100])
    spread_large = abs(results[100_000] - results[10_000])
    assert spread_large <= spread_small + 2, (
        f"Metrics did not converge: spread(100→1k)={spread_small:.2f} "
        f"spread(10k→100k)={spread_large:.2f}"
    )


# ---------------------------------------------------------------------------
# simulate_all: portfolio-level scenario count
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", SCENARIO_SIZES)
def test_simulate_all_output_length(features: list[Feature], n: int) -> None:
    """All features in simulate_all must share the same scenario count."""
    config = _config(n)
    sprint_plans = SprintOverrunService.compute_sprint_plans(features)
    bv_map = {f.name: _bv_array(n, seed=i) for i, f in enumerate(features)}

    results = SprintOverrunService.simulate_all(
        features=features,
        sprint_plans=sprint_plans,
        business_value_after_risk=bv_map,
        config=config,
    )

    assert len(results) == len(features)
    for name, result in results.items():
        assert len(result.actual_sprints) == n, f"{name}: expected {n} scenarios"


# ---------------------------------------------------------------------------
# profitability: valid metrics across scenario counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", SCENARIO_SIZES)
def test_profitability_valid(features: list[Feature], n: int) -> None:
    """Profitability metrics must be valid for all scenario counts."""
    config = _config(n)
    sprint_plans = SprintOverrunService.compute_sprint_plans(features)
    bv_map = {f.name: _bv_array(n, seed=i) for i, f in enumerate(features)}

    delivery_results = SprintOverrunService.simulate_all(
        features=features,
        sprint_plans=sprint_plans,
        business_value_after_risk=bv_map,
        config=config,
    )
    profitability = SprintOverrunService.compute_profitability(
        delivery_results=delivery_results,
        features=features,
    )

    assert 0.0 <= profitability.portfolio_break_even_probability <= 1.0
    assert profitability.portfolio_loss_at_risk_95 >= 0.0
    assert len(profitability.feature_results) == len(features)

    for fr in profitability.feature_results:
        assert 0.0 <= fr.break_even_probability <= 1.0
        assert fr.expected_loss >= 0.0
        assert fr.loss_at_risk_95 >= 0.0
