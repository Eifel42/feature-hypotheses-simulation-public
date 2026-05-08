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

"""Tests for SprintOverrunService — sprint-based delivery risk simulation."""

import numpy as np
import pytest

from fhs.core.model import (
    DeliverySimulationResult,
    Feature,
    PortfolioProfitabilityResult,
    ProfitabilityResult,
    SprintPlan,
)
from fhs.core.model.config import (
    CancellationConfig,
    DelayModelConfig,
    DeliveryRiskConfig,
)
from fhs.core.services.risk.sprint_overrun import SprintOverrunService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def default_config() -> DeliveryRiskConfig:
    return DeliveryRiskConfig()


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
        Feature(
            name="H3: Expiration Alerts",
            expected_users=40_400,
            conversion_rate=0.29,
            uncertainty=0.35,
            business_value_per_conversion=0.435,
            development_cost=20_000.0,
            development_weeks=4,
            likelihood_of_non_delivery=0.8,
        ),
    ]


@pytest.fixture
def feature_no_weeks() -> Feature:
    """Feature without development_weeks set."""
    return Feature(
        name="No Weeks",
        expected_users=10_000,
        conversion_rate=0.1,
        uncertainty=0.2,
    )


# ---------------------------------------------------------------------------
# Sprint Plan Tests
# ---------------------------------------------------------------------------


class TestComputeSprintPlans:
    def test_computes_correct_sprint_counts(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans(features)
        # 14-day sprint = 2 weeks per sprint, partial sprints round up.
        assert plans["H1: Simplified UI"].planned_sprints == 4  # ceil(8 / 2)
        assert plans["H2: Traceability"].planned_sprints == 3  # ceil(6 / 2)
        assert plans["H3: Expiration Alerts"].planned_sprints == 2  # ceil(4 / 2)

    def test_skips_features_without_development_weeks(
        self, feature_no_weeks: Feature, default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans([feature_no_weeks])
        assert len(plans) == 0

    def test_plans_use_fixed_two_week_sprint(self, features: list[Feature]):
        plans = SprintOverrunService.compute_sprint_plans(features)
        # 8 weeks / 2 weeks per sprint = 4 full sprints
        assert plans["H1: Simplified UI"].planned_sprints == 4

    def test_planned_sprints_round_up_partial_sprints(self):
        feature = Feature(
            name="Partial Sprint Test",
            expected_users=10_000,
            conversion_rate=0.1,
            uncertainty=0.2,
            development_weeks=5,
        )
        plans = SprintOverrunService.compute_sprint_plans([feature])
        assert plans["Partial Sprint Test"].planned_sprints == 3  # ceil(5 / 2)

    def test_planned_sprints_helper_matches_expected_rounding(self):
        assert SprintOverrunService.planned_sprints_for_weeks(5) == 3
        assert SprintOverrunService.planned_sprints_for_weeks(4) == 2
        assert SprintOverrunService.planned_sprints_for_weeks(7) == 4

    def test_planned_weeks_property(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans(features)
        plan = plans["H1: Simplified UI"]
        # 4 sprints × (14 // 7 = 2) = 8 weeks
        assert plan.planned_weeks == 8


# ---------------------------------------------------------------------------
# Single Feature Simulation Tests
# ---------------------------------------------------------------------------


class TestSimulateDelivery:
    def test_returns_correct_shape(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(10_000, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        assert isinstance(result, DeliverySimulationResult)
        assert len(result.actual_sprints) == 10_000
        assert len(result.actual_cost) == 10_000
        assert len(result.cancelled) == 10_000
        assert result.planned_sprints == 4
        assert result.feature_name == feature.name

    def test_actual_sprints_at_least_one(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(50_000, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        assert np.all(result.actual_sprints >= 1)

    def test_cost_positive(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(10_000, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        assert np.all(result.actual_cost > 0)

    def test_cancelled_scenarios_have_zero_business_value(
        self, features: list[Feature]
    ):
        # Use config that forces cancellation (low threshold, high probability)
        config = DeliveryRiskConfig(
            delay_model=DelayModelConfig(
                sprint_uncertainty=50,
                sprint_ceiling=5.0,
            ),
            cancellation=CancellationConfig(
                max_sprints_over_plan=1,
                cancellation_probability=1.0,
            ),
        )
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(10_000, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=config,
            seed=42,
        )

        # All cancelled scenarios should have zero business value
        cancelled_mask = result.cancelled
        if np.any(cancelled_mask):
            assert np.all(result.business_value_after_risk[cancelled_mask] == 0.0)

    def test_deterministic_with_same_seed(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(1_000, 80_000.0)

        r1 = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=default_config,
            seed=123,
        )
        r2 = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=default_config,
            seed=123,
        )

        np.testing.assert_array_equal(r1.actual_sprints, r2.actual_sprints)
        np.testing.assert_array_equal(r1.actual_cost, r2.actual_cost)
        np.testing.assert_array_equal(r1.cancelled, r2.cancelled)

    def test_no_std_means_deterministic_delay(self, features: list[Feature]):
        config = DeliveryRiskConfig(
            delay_model=DelayModelConfig(
                sprint_uncertainty=0.0,
            ),
        )
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(1_000, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=config,
            seed=42,
        )

        # Mean is always planned sprints; zero std collapses to planned duration.
        assert np.all(result.actual_sprints == 4)

    def test_delay_factor_capped(self, features: list[Feature]):
        config = DeliveryRiskConfig(
            delay_model=DelayModelConfig(
                sprint_uncertainty=100,
                sprint_ceiling=2.5,
            ),
        )
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(50_000, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=config,
            seed=42,
        )

        # Max sprints = ceil(4 * 2.5) = 10
        assert np.all(result.actual_sprints <= 10)

    def test_planned_sprints_are_always_distribution_mean(
        self, features: list[Feature]
    ):
        config = DeliveryRiskConfig(
            delay_model=DelayModelConfig(
                sprint_uncertainty=0.0,
                sprint_ceiling=3.0,
            ),
        )
        feature = features[0]
        plan = SprintPlan(feature_name=feature.name, planned_sprints=4)
        business_value = np.full(500, 80_000.0)

        result = SprintOverrunService.simulate_delivery(
            feature=feature,
            sprint_plan=plan,
            business_value_after_risk=business_value,
            config=config,
            seed=42,
        )

        # With zero std, the distribution collapses to planned_sprints.
        assert np.all(result.actual_sprints == 4)


# ---------------------------------------------------------------------------
# Simulate All Features Tests
# ---------------------------------------------------------------------------


class TestSimulateAll:
    def test_simulates_all_features_with_plans(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans(features)
        business_value = {f.name: np.full(5_000, 50_000.0) for f in features}

        results = SprintOverrunService.simulate_all(
            features=features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        assert len(results) == 3
        for name in plans:
            assert name in results
            assert len(results[name].actual_sprints) == 5_000

    def test_skips_features_without_plan(
        self,
        features: list[Feature],
        feature_no_weeks: Feature,
        default_config: DeliveryRiskConfig,
    ):
        all_features = [*features, feature_no_weeks]
        plans = SprintOverrunService.compute_sprint_plans(all_features)
        business_value = {f.name: np.full(1_000, 50_000.0) for f in all_features}

        results = SprintOverrunService.simulate_all(
            features=all_features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        assert feature_no_weeks.name not in results
        assert len(results) == 3


# ---------------------------------------------------------------------------
# Profitability Tests
# ---------------------------------------------------------------------------


class TestComputeProfitability:
    def test_returns_portfolio_result(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans(features)
        business_value = {f.name: np.full(5_000, 50_000.0) for f in features}

        delivery = SprintOverrunService.simulate_all(
            features=features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        result = SprintOverrunService.compute_profitability(delivery, features)

        assert isinstance(result, PortfolioProfitabilityResult)
        assert len(result.feature_results) == 3
        assert len(result.portfolio_profit) == 5_000
        assert result.total_investment == 75_000 + 50_000 + 20_000

    def test_break_even_probability_in_range(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans(features)
        business_value = {f.name: np.full(10_000, 50_000.0) for f in features}

        delivery = SprintOverrunService.simulate_all(
            features=features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        result = SprintOverrunService.compute_profitability(delivery, features)

        for fr in result.feature_results:
            assert 0.0 <= fr.break_even_probability <= 1.0

        assert 0.0 <= result.portfolio_break_even_probability <= 1.0

    def test_high_business_value_means_high_break_even(self, features: list[Feature]):
        config = DeliveryRiskConfig(
            delay_model=DelayModelConfig(sprint_uncertainty=10),
        )
        plans = SprintOverrunService.compute_sprint_plans(features)
        # Very high business value -> almost always profitable
        business_value = {f.name: np.full(10_000, 500_000.0) for f in features}

        delivery = SprintOverrunService.simulate_all(
            features=features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=config,
            seed=42,
        )

        result = SprintOverrunService.compute_profitability(delivery, features)
        assert result.portfolio_break_even_probability > 0.95

    def test_zero_business_value_means_always_loss(self, features: list[Feature]):
        config = DeliveryRiskConfig()
        plans = SprintOverrunService.compute_sprint_plans(features)
        # Zero business value -> always loss
        business_value = {f.name: np.full(5_000, 0.0) for f in features}

        delivery = SprintOverrunService.simulate_all(
            features=features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=config,
            seed=42,
        )

        result = SprintOverrunService.compute_profitability(delivery, features)
        assert result.portfolio_break_even_probability == 0.0
        assert result.portfolio_loss_at_risk_95 > 0.0

    def test_loss_at_risk_positive_when_losses_exist(
        self, features: list[Feature], default_config: DeliveryRiskConfig
    ):
        plans = SprintOverrunService.compute_sprint_plans(features)
        # Moderate business value -> some scenarios profitable, some not
        business_value = {f.name: np.full(10_000, 30_000.0) for f in features}

        delivery = SprintOverrunService.simulate_all(
            features=features,
            sprint_plans=plans,
            business_value_after_risk=business_value,
            config=default_config,
            seed=42,
        )

        result = SprintOverrunService.compute_profitability(delivery, features)

        # With moderate business value and 3 features x costs, there will be losses
        assert result.portfolio_loss_at_risk_95 > 0.0


# ---------------------------------------------------------------------------
# Value Object Property Tests
# ---------------------------------------------------------------------------


class TestDeliverySimulationResultProperties:
    def test_cancelled_pct(self):
        result = DeliverySimulationResult(
            feature_name="test",
            planned_sprints=4,
            actual_sprints=np.array([4, 5, 6, 7]),
            actual_cost=np.array([60_000, 75_000, 90_000, 105_000]),
            cancelled=np.array([False, False, True, True]),
            business_value_after_risk=np.array([80_000, 80_000, 0, 0]),
        )
        assert result.cancelled_pct == 0.5

    def test_sunk_cost_if_cancelled(self):
        result = DeliverySimulationResult(
            feature_name="test",
            planned_sprints=4,
            actual_sprints=np.array([4, 5, 6, 7]),
            actual_cost=np.array([60_000, 75_000, 90_000, 105_000]),
            cancelled=np.array([False, False, True, True]),
            business_value_after_risk=np.array([80_000, 80_000, 0, 0]),
        )
        # Mean of cancelled costs: (90_000 + 105_000) / 2 = 97_500
        assert result.sunk_cost_if_cancelled == 97_500.0

    def test_sunk_cost_zero_when_no_cancellation(self):
        result = DeliverySimulationResult(
            feature_name="test",
            planned_sprints=4,
            actual_sprints=np.array([4, 5]),
            actual_cost=np.array([60_000, 75_000]),
            cancelled=np.array([False, False]),
            business_value_after_risk=np.array([80_000, 80_000]),
        )
        assert result.sunk_cost_if_cancelled == 0.0

    def test_profit_computation(self):
        result = DeliverySimulationResult(
            feature_name="test",
            planned_sprints=4,
            actual_sprints=np.array([4, 5]),
            actual_cost=np.array([60_000, 75_000]),
            cancelled=np.array([False, False]),
            business_value_after_risk=np.array([80_000, 80_000]),
        )
        expected_profit = np.array([20_000, 5_000])
        np.testing.assert_array_equal(result.profit, expected_profit)


class TestProfitabilityResultProperties:
    def test_break_even_probability(self):
        result = ProfitabilityResult(
            feature_name="test",
            profit_distribution=np.array([10_000, -5_000, 20_000, -3_000]),
            planned_cost=50_000,
            expected_business_value=60_000,
            expected_cost=55_000,
        )
        assert result.break_even_probability == 0.5

    def test_expected_loss(self):
        result = ProfitabilityResult(
            feature_name="test",
            profit_distribution=np.array([10_000, -5_000, 20_000, -3_000]),
            planned_cost=50_000,
            expected_business_value=60_000,
            expected_cost=55_000,
        )
        # Mean of losses: (5_000 + 3_000) / 2 = 4_000
        assert result.expected_loss == 4_000.0

    def test_expected_loss_zero_when_no_losses(self):
        result = ProfitabilityResult(
            feature_name="test",
            profit_distribution=np.array([10_000, 5_000]),
            planned_cost=50_000,
            expected_business_value=60_000,
            expected_cost=55_000,
        )
        assert result.expected_loss == 0.0

    def test_profit_margin(self):
        result = ProfitabilityResult(
            feature_name="test",
            profit_distribution=np.array([10_000, 20_000]),
            planned_cost=50_000,
            expected_business_value=60_000,
            expected_cost=50_000,
        )
        # Expected profit = 15_000, margin = 15_000 / 50_000 = 0.3
        assert abs(result.profit_margin - 0.3) < 0.01


# ---------------------------------------------------------------------------
# DeliveryRiskConfig Validation Tests
# ---------------------------------------------------------------------------


class TestDeliveryRiskConfig:
    def test_defaults(self):
        config = DeliveryRiskConfig()
        assert config.sprint_length_weeks == 2
        assert config.quarterly_capacity_sprints == 6
        assert config.delay_model.get_uncertainty_decimal() == 0.3
        assert config.cancellation.max_sprints_over_plan == 4

    def test_custom_values(self):
        config = DeliveryRiskConfig(
            quarterly_capacity_sprints=8,
            delay_model=DelayModelConfig(sprint_uncertainty=40),
            cancellation=CancellationConfig(max_sprints_over_plan=2),
        )
        assert config.quarterly_capacity_sprints == 8
        assert config.delay_model.get_uncertainty_decimal() == 0.4
        assert config.cancellation.max_sprints_over_plan == 2

    def test_validation_rejects_invalid(self):
        with pytest.raises(Exception):
            DeliveryRiskConfig(scenarios=0)
        with pytest.raises(Exception):
            DeliveryRiskConfig(sprint_length_weeks=3)
        with pytest.raises(Exception):
            CancellationConfig(cancellation_probability=1.5)
        with pytest.raises(Exception):
            DelayModelConfig(sprint_uncertainty=-1)
