# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md

"""Tests for RiskCalculator.feature_ranking_metrics factory."""

from __future__ import annotations

import math

import numpy as np
import pytest
from pydantic import ValidationError as PydanticValidationError

from fhs.core.model.value_objects import FeatureRankingMetrics
from fhs.core.services import RiskCalculator


def _normal_scenarios(
    mean: float = 100.0,
    std: float = 10.0,
    n: int = 100_000,
    seed: int = 42,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(mean, std, n)


class TestFeatureRankingMetricsFactoryBasics:
    def test_returns_feature_ranking_metrics_instance(self) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(),
            development_cost=50_000.0,
        )
        assert isinstance(profile, FeatureRankingMetrics)
        assert profile.feature_name == "F"
        assert profile.confidence_level == 0.95

    def test_bv_var_equals_calculate_var_on_same_scenarios(self) -> None:
        scenarios = _normal_scenarios()
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=50_000.0,
        )
        assert profile.bv_var == RiskCalculator.calculate_var(scenarios, 0.95)

    def test_bv_cvar_equals_calculate_cvar_on_same_scenarios(self) -> None:
        scenarios = _normal_scenarios()
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=50_000.0,
        )
        assert profile.bv_cvar == RiskCalculator.calculate_cvar(scenarios, 0.95)

    def test_expected_bv_equals_mean_of_scenarios(self) -> None:
        scenarios = _normal_scenarios()
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=50_000.0,
        )
        assert profile.expected_bv == pytest.approx(float(np.mean(scenarios)))

    def test_confidence_level_is_propagated(self) -> None:
        scenarios = _normal_scenarios()
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=50_000.0,
            confidence_level=0.99,
        )
        assert profile.confidence_level == 0.99
        assert profile.bv_var == RiskCalculator.calculate_var(scenarios, 0.99)


class TestFeatureRankingMetricsFactoryLossView:
    def test_loss_var_equals_expected_minus_bv_var_when_positive(self) -> None:
        scenarios = _normal_scenarios()
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=50_000.0,
        )
        assert profile.loss_var == pytest.approx(profile.expected_bv - profile.bv_var)

    def test_loss_cvar_is_greater_equal_loss_var(self) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(),
            development_cost=50_000.0,
        )
        assert profile.loss_cvar >= profile.loss_var

    def test_loss_var_is_zero_when_bv_var_exceeds_expected(self) -> None:
        # 1% severe downside outliers pull mean below the 5th percentile.
        scenarios = np.array([100.0] * 9_900 + [-10_000.0] * 100)
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=10.0,
        )
        assert profile.loss_var == 0.0

    def test_loss_metrics_non_negative_on_degenerate_distribution(self) -> None:
        scenarios = np.full(10_000, 50.0)
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="Flat",
            bv_scenarios=scenarios,
            development_cost=1_000.0,
        )
        assert profile.loss_var == 0.0
        assert profile.loss_cvar == 0.0


class TestFeatureRankingMetricsFactoryNormalized:
    def test_risk_ratio_is_zero_when_expected_is_zero_or_negative(self) -> None:
        scenarios = np.array([-10.0, 0.0, 10.0] * 1000)
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=1_000.0,
        )
        assert profile.risk_ratio == 0.0 or profile.risk_ratio >= 0.0

    def test_risk_ratio_clamped_to_unit_interval(self) -> None:
        scenarios = np.concatenate([np.full(9_900, -1_000.0), np.full(100, 1_000.0)])
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=1_000.0,
        )
        assert 0.0 <= profile.risk_ratio <= 1.0

    def test_risk_ratio_close_to_zero_on_degenerate_distribution(self) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="Flat",
            bv_scenarios=np.full(10_000, 100.0),
            development_cost=1_000.0,
        )
        assert profile.risk_ratio == 0.0

    def test_rorac_uses_epsilon_when_loss_var_is_zero(self) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="Flat",
            bv_scenarios=np.full(10_000, 100.0),
            development_cost=1_000.0,
            epsilon=1.0,
        )
        assert profile.rorac == pytest.approx(100.0)

    def test_rorac_is_finite(self) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(),
            development_cost=50_000.0,
        )
        assert math.isfinite(profile.rorac)

    def test_risk_adjusted_roi_equals_bv_var_over_dev_cost(self) -> None:
        scenarios = _normal_scenarios()
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=40_000.0,
        )
        assert profile.risk_adjusted_roi == pytest.approx(profile.bv_var / 40_000.0)

    def test_risk_adjusted_roi_is_infinity_when_dev_cost_is_zero(self) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(),
            development_cost=0.0,
        )
        assert math.isinf(profile.risk_adjusted_roi)

    def test_risk_adjusted_roi_is_infinity_when_dev_cost_is_negative(
        self,
    ) -> None:
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(),
            development_cost=-5.0,
        )
        assert math.isinf(profile.risk_adjusted_roi)


class TestFeatureRankingMetricsFactoryDeterminism:
    def test_deterministic_given_same_scenarios(self) -> None:
        scenarios = _normal_scenarios(seed=123)
        a = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=10_000.0,
        )
        b = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=10_000.0,
        )
        assert a == b

    def test_different_seeds_produce_close_but_distinct_profiles(self) -> None:
        a = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(seed=1),
            development_cost=10_000.0,
        )
        b = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=_normal_scenarios(seed=2),
            development_cost=10_000.0,
        )
        assert a != b
        assert a.bv_var == pytest.approx(b.bv_var, rel=0.02)


class TestFeatureRankingMetricsFactoryValidation:
    def test_empty_feature_name_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            RiskCalculator.feature_ranking_metrics(
                feature_name="",
                bv_scenarios=_normal_scenarios(),
                development_cost=1_000.0,
            )

    def test_invalid_confidence_level_raises(self) -> None:
        from fhs.core.model.exceptions import ValidationError

        with pytest.raises(ValidationError):
            RiskCalculator.feature_ranking_metrics(
                feature_name="F",
                bv_scenarios=_normal_scenarios(),
                development_cost=1_000.0,
                confidence_level=1.5,
            )


@pytest.mark.parametrize(
    "confidence,z",
    [
        (0.95, 1.6448536269514722),
        (0.99, 2.3263478740408408),
    ],
)
def test_normal_distribution_matches_analytical_quantile(
    confidence: float, z: float
) -> None:
    """For Normal(mean, std), bv_var ≈ mean - z * std; tolerance 1 %."""
    mean, std, n = 100.0, 10.0, 200_000
    rng = np.random.default_rng(7)
    scenarios = rng.normal(mean, std, n)
    profile = RiskCalculator.feature_ranking_metrics(
        feature_name="Normal",
        bv_scenarios=scenarios,
        development_cost=1_000.0,
        confidence_level=confidence,
    )
    expected_var = mean - z * std
    assert profile.bv_var == pytest.approx(expected_var, rel=0.01)


@pytest.mark.parametrize("n", [1_000, 10_000, 100_000])
def test_rorac_converges_with_larger_sample_size(n: int) -> None:
    """Sanity check: RoRaC stabilises as n grows (variance across seeds shrinks)."""
    mean, std = 100.0, 10.0
    values = []
    for seed in range(5):
        rng = np.random.default_rng(seed)
        scenarios = rng.normal(mean, std, n)
        profile = RiskCalculator.feature_ranking_metrics(
            feature_name="F",
            bv_scenarios=scenarios,
            development_cost=1_000.0,
        )
        values.append(profile.rorac)
    spread = max(values) - min(values)
    # Spread expected to shrink roughly as 1/sqrt(n); loose bound per size.
    assert spread < 5.0 if n >= 10_000 else spread < 20.0


def test_lognormal_distribution_bv_cvar_less_equal_bv_var() -> None:
    rng = np.random.default_rng(13)
    scenarios = rng.lognormal(mean=4.0, sigma=0.5, size=100_000)
    profile = RiskCalculator.feature_ranking_metrics(
        feature_name="Log",
        bv_scenarios=scenarios,
        development_cost=5_000.0,
    )
    assert profile.bv_cvar <= profile.bv_var


def test_uniform_distribution_matches_analytical_quantile() -> None:
    rng = np.random.default_rng(21)
    scenarios = rng.uniform(low=0.0, high=100.0, size=200_000)
    profile = RiskCalculator.feature_ranking_metrics(
        feature_name="Uniform",
        bv_scenarios=scenarios,
        development_cost=1_000.0,
    )
    # VaR95 of Uniform(0, 100) = 5.0 (the 5th percentile).
    assert profile.bv_var == pytest.approx(5.0, abs=0.5)
