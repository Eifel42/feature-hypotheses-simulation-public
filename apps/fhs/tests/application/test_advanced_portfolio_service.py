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

"""Tests for AdvancedPortfolioService multi-year portfolio risk views."""

import numpy as np
import pytest

from fhs.application.advanced_portfolio_service import AdvancedPortfolioService
from fhs.application.delivery_analysis_operations import DeliveryAnalysisOperations
from fhs.application.dtos import ScenarioContext
from fhs.application.risk_layers_operations import FeatureRiskLayerTables
from fhs.core.model import (
    BudgetFrontierRow,
    ConcentrationResult,
    DeliveryRiskConfig,
    DeliverySimulationResult,
    DeliveryStressResult,
    Feature,
    FeatureRanking,
    FeatureRiskProfile,
    FeatureSensitivityResult,
    FinancialViewResult,
    NegativeScoreReport,
    OptimizationResult,
    PnLAssessment,
    PortfolioPnLLayers,
    PortfolioProfitabilityResult,
    PortfolioRiskLayers,
    PortfolioSensitivityRow,
    PortfolioSnapshot,
    RetentionMatrix,
    RiskManagementROI,
    ScenarioRiskModel,
)

# sample_features, risk_model, service fixtures provided by conftest.py


def test_simulate_portfolio_pnl_multi_year_returns_expected_structure(
    service,
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    result = service.multi_year.simulate_pnl(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        years=3,
        seed=42,
    )

    assert result.investment == pytest.approx(125_000.0)
    assert result.meta.years == 3
    assert len(result.risk3.years) == 3
    assert result.risk3.npv is not None
    assert result.risk3.total_3y is not None


def test_multi_year_risk_layers_degrade_from_base_to_risk3(
    service,
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    result = service.multi_year.simulate_pnl(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        years=3,
        seed=42,
    )

    assert result.risk3.total_3y.expected <= result.base.total_3y.expected
    assert result.risk3.npv.var_95 <= result.base.npv.var_95


def test_portfolio_component_risk_summary_aggregates_clusters(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=1_000,
    )

    summary = service.risk.component_summary(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
    )

    assert len(summary.cluster_risks) == 2
    assert summary.portfolio_component_probability == pytest.approx(0.1904)
    assert summary.portfolio_expected_incremental_loss_eur > 0


def test_portfolio_component_risk_summary_multi_year_exposes_3y_metrics(
    service,
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    summary = service.multi_year.component_risk_summary(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        years=3,
    )

    assert len(summary.cluster_risks) == 2
    assert summary.portfolio_component_probability == pytest.approx(0.1904)
    assert (
        summary.portfolio_expected_incremental_loss_eur
        > summary.portfolio_var_incremental_loss_eur
    )


def test_loss_metrics_exposes_catastrophe_and_conditional_tail(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=5_000,
    )

    metrics = service.risk.loss_metrics(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        confidence=0.95,
        seed=42,
    )

    assert metrics.investment == pytest.approx(125_000.0)
    assert metrics.catastrophe_probability == pytest.approx(0.10, abs=0.02)
    assert metrics.catastrophe_threshold == pytest.approx(125_000.0)
    assert metrics.cvar_loss == metrics.year1.loss_cvar


def test_financial_view_returns_typed_result(
    service,
    sample_features: list[Feature],
):
    view = service.multi_year.financial_view(
        [feature.name for feature in sample_features],
        investment=125_000.0,
        discount_rate=0.08,
    )

    assert isinstance(view, FinancialViewResult)
    assert view.npv_floor <= view.npv_expected <= view.npv_ceiling


def test_concentration_returns_typed_result(
    service,
    sample_features: list[Feature],
):
    result = service.decisions.concentration(
        [feature.name for feature in sample_features]
    )

    assert isinstance(result, ConcentrationResult)
    assert 0.0 <= result.hhi <= 1.0
    assert sum(result.shares.values()) == pytest.approx(1.0)


def test_portfolio_snapshot_returns_typed_result_and_inferred_investment(
    service,
    sample_features: list[Feature],
):
    result = service.portfolio_snapshot([feature.name for feature in sample_features])

    assert isinstance(result, PortfolioSnapshot)
    assert result.investment == pytest.approx(125_000.0)
    assert result.var_95 <= result.expected


def test_optimize_returns_typed_result(
    service,
    sample_features: list[Feature],
):
    result = service.optimize(solver="greedy", strategy="var_floor")

    assert isinstance(result, OptimizationResult)
    assert result.solver in {"greedy", "exact", "ilp"}


def test_compare_solvers_accepts_cvar_milp(
    service,
    sample_features: list[Feature],
):
    results = service.compare_solvers(
        ("exact", "cvar_milp"),
        budget=155_000.0,
        strategy="var_floor",
    )

    assert set(results.keys()) == {"exact", "cvar_milp"}
    assert results["exact"].solver == "exact"
    assert results["cvar_milp"].solver == "cvar_milp"


def test_budget_frontier_returns_sorted_typed_rows(
    service,
    sample_features: list[Feature],
):
    rows = service.budget_frontier(
        budgets=[160_000.0, 120_000.0],
        solver="greedy",
        strategy="var_floor",
    )

    assert all(isinstance(row, BudgetFrontierRow) for row in rows)
    assert [row.budget for row in rows] == [120_000.0, 160_000.0]


def test_stress_scenarios_returns_three_named_scenarios(
    service,
    sample_features: list[Feature],
):
    result = service.stress_scenarios([feature.name for feature in sample_features])

    assert "baseline" in result
    assert "scenarios" in result
    assert len(result["scenarios"]) == 3
    assert [scenario["name"] for scenario in result["scenarios"]] == [
        "Market pullback",
        "Top feature delay",
        "Execution pressure",
    ]


def test_dependency_correlation_returns_expected_keys(
    service,
    sample_features: list[Feature],
):
    result = service.decisions.dependency_correlation(
        [feature.name for feature in sample_features]
    )

    assert set(result.keys()) == {
        "labels",
        "dependency_matrix",
        "empirical_matrix",
        "spearman_matrix",
        "average_corr",
    }
    assert result["labels"] == [feature.name for feature in sample_features]


def test_risk_contributions_shapley_balances_to_total_risk(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=4_000,
    )

    result = service.risk.shapley_attribution(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        confidence=0.95,
        metric="cvar_loss",
        seed=42,
    )

    contribution_sum = sum(c.contribution_eur for c in result.contributions)
    assert contribution_sum == pytest.approx(result.total_risk_eur, abs=1e-6)
    assert any(c.risk == "delivery" for c in result.contributions)
    assert abs(result.interaction_residual_eur) <= 1e-5


def test_typed_layer_and_sensitivity_returns(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]

    normalized = service.risk_model
    assert isinstance(normalized, ScenarioRiskModel)

    feature_profile = service.layers.simulate_feature_risk_layers(
        sample_features[0].name,
        risk_model=risk_model,
        seed=42,
    )
    assert isinstance(feature_profile, FeatureRiskProfile)
    assert feature_profile.after_risk_3.expected <= feature_profile.base.expected

    feature_sensitivity = service.layers.feature_sensitivity(
        risk_model=risk_model,
        feature_names=selected,
        seed=42,
    )
    assert isinstance(feature_sensitivity, FeatureSensitivityResult)
    assert len(feature_sensitivity.details) == 8
    assert len(feature_sensitivity.drivers) == 2

    portfolio_layers = service.layers.simulate_portfolio_risk_layers(
        selected,
        risk_model=risk_model,
        seed=42,
    )
    assert isinstance(portfolio_layers, PortfolioRiskLayers)
    assert portfolio_layers.after_risk_3.expected <= portfolio_layers.base.expected

    portfolio_pnl_layers = service.layers.simulate_portfolio_pnl_layers(
        selected,
        risk_model=risk_model,
        seed=42,
    )
    assert isinstance(portfolio_pnl_layers, PortfolioPnLLayers)
    assert portfolio_pnl_layers.meta.selected == tuple(selected)

    sensitivity_grid = service.layers.portfolio_sensitivity(
        selected,
        risk_model=risk_model,
        seed=42,
    )
    assert len(sensitivity_grid) == 9
    assert all(isinstance(row, PortfolioSensitivityRow) for row in sensitivity_grid)


def test_from_scenario_warms_cache_and_uses_typed_configs(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    context = ScenarioContext(
        scenario_id="blockchain",
        features=sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        strategy={},
        weights={feature.name: 0.5 for feature in sample_features},
        dependency_matrix=np.eye(len(sample_features)),
        config_path="blockchain.yaml",
        config_source="yaml",
        exam_report={"passed": True, "checks": []},
        risk_model=ScenarioRiskModel(**risk_model),
        delivery_config=DeliveryRiskConfig(),
    )

    service = AdvancedPortfolioService.from_scenario(context, scenarios=1_000)

    assert service.risk_model.risk_2_market_probability == pytest.approx(0.20)
    assert service.delivery_config.quarterly_capacity_sprints == 6
    assert len(service.simulation_results) == len(sample_features)


def test_feature_risk_retention_returns_typed_matrix(
    service,
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    profiles = service.layers.feature_layer_profiles(
        feature_names=[feature.name for feature in sample_features],
        risk_model=risk_model,
        seed=42,
    )
    retention = service.layers.feature_risk_retention(profiles)

    assert isinstance(retention, RetentionMatrix)
    assert len(retention.rows) == 2
    assert 0.0 <= retention.portfolio_expected_retention_pct <= 1.0
    assert 0.0 <= retention.portfolio_floor_retention_pct <= 1.0
    assert retention.rows[0].after_risk_3_expected <= retention.rows[0].base_expected


def test_feature_risk_layer_tables_returns_notebook_ready_rows(
    service,
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    profiles = service.layers.feature_layer_profiles(
        feature_names=[feature.name for feature in sample_features],
        risk_model=risk_model,
        seed=42,
    )
    tables = service.layers.feature_risk_layer_tables(profiles)

    assert isinstance(tables, FeatureRiskLayerTables)
    assert len(tables.expected_rows) == 2
    assert len(tables.probability_rows) == 2
    assert len(tables.retention_rows) == 2
    assert tables.expected_headers[0] == "Feature"
    assert tables.prob_headers[2] == "Development LLP"
    assert (
        tables.retention_headers[1] == "Business value retained (Base → After Global)"
    )
    assert tables.expected_rows[0][0] == "Simplified UI"


def test_probability_sensitivity_rows_return_notebook_ready_format(
    service,
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    selected = [feature.name for feature in sample_features]
    market_levels = [0.10, 0.20, 0.30]
    global_levels = [0.025, 0.05, 0.075]

    market_results = {
        level: service.layers.simulate_portfolio_risk_layers(
            selected,
            risk_model=risk_model,
            risk2_probability=level,
            seed=42,
        )
        for level in market_levels
    }
    global_results = {
        level: service.layers.simulate_portfolio_risk_layers(
            selected,
            risk_model=risk_model,
            risk3_probability=level,
            seed=42,
        )
        for level in global_levels
    }

    market_rows = service.layers.market_sensitivity_rows(
        market_results,
        levels=market_levels,
    )
    global_rows = service.layers.global_sensitivity_rows(
        global_results,
        levels=global_levels,
    )

    assert len(market_rows) == 3
    assert len(global_rows) == 3
    assert market_rows[0][0] == "10%"
    assert global_rows[0][0] == "2.5%"
    assert market_rows[0][1].startswith("EUR ")
    assert global_rows[0][1].startswith("EUR ")


def test_rank_features_returns_typed_sorted_rows(
    service,
    sample_features: list[Feature],
):
    ranking = service.decisions.rank_features()

    assert len(ranking) == 2
    assert all(isinstance(row, FeatureRanking) for row in ranking)
    assert ranking[0].expected_business_value >= ranking[1].expected_business_value


def test_negative_score_analysis_returns_typed_report(
    service,
    sample_features: list[Feature],
):
    report = service.negative_score_analysis(budget=155_000.0, strategy="var_floor")

    assert isinstance(report, NegativeScoreReport)
    assert len(report.scores) == 2
    assert len(report.comparisons) == 4
    assert report.all_features_exact.solver == "exact"
    assert report.all_features_ilp.solver == "ilp"


def test_spawn_subset_service_keeps_runtime_configuration(
    service,
    sample_features: list[Feature],
):
    subset = service._spawn_subset_service(
        [sample_features[0]],
        budget=90_000.0,
    )

    assert isinstance(subset, AdvancedPortfolioService)
    assert [feature.name for feature in subset.features] == [sample_features[0].name]
    assert subset.budget == pytest.approx(90_000.0)
    assert subset.discount_rate == pytest.approx(service.discount_rate)
    assert subset.seed == service.seed
    assert subset.scenarios == service.scenarios
    assert sample_features[0].name in subset.simulation_results


def test_strategy_category_cost_share_returns_sorted_rows(
    service,
    sample_features: list[Feature],
):
    rows = service.decisions.strategy_category_cost_share(
        [feature.name for feature in sample_features],
        {
            sample_features[0].name: {"category": "Growth"},
            sample_features[1].name: {"category": "Efficiency"},
        },
    )

    assert len(rows) == 2
    assert rows[0].cost >= rows[1].cost
    assert rows[0].share + rows[1].share == pytest.approx(1.0)


def test_budget_risk_path_returns_typed_rows(
    service,
    sample_features: list[Feature],
):
    rows = service.budget_risk_path(
        {
            "50% Budget": 77_500.0,
            "100% Budget": 155_000.0,
        },
        strategy="var_floor",
        seed=42,
    )

    assert len(rows) == 2
    assert rows[0].label == "50% Budget"
    assert rows[1].budget == pytest.approx(155_000.0)
    assert rows[0].risk_class in {"No selection", "Low", "Medium", "High"}


def test_feature_score_analysis_returns_var_floor_scores(
    service,
    sample_features: list[Feature],
):
    scores = service.decisions.feature_score_analysis()

    assert set(scores.keys()) == {feature.name for feature in sample_features}
    for feature in sample_features:
        sim = service.simulation_results[feature.name]
        assert scores[feature.name] == pytest.approx(
            sim.business_value_at_risk_95 - feature.development_cost
        )


def test_budget_sensitivity_returns_typed_results_with_guardrails(
    service,
    sample_features: list[Feature],
):
    results = service.budget_sensitivity(
        {
            "Low": 1_000.0,
            "Base": 155_000.0,
        },
        solver="ilp",
        strategy="var_floor",
    )

    assert set(results.keys()) == {"Low", "Base"}
    assert results["Low"].solver == "not_run"
    assert "cheapest feature" in results["Low"].message
    assert results["Base"].solver in {"ilp", "exact", "greedy"}


def test_delivery_risk_analysis_exposes_safety_buffers(
    service,
    sample_features: list[Feature],
):
    plan = service.optimize(solver="ilp", strategy="var_floor")
    l2 = service.optimizer.analyze_delivery_risk(plan, seed=42)
    l3 = service.optimizer.analyze_delivery_risk(
        plan,
        seed=42,
        systematic_shock_probability=0.05,
        systematic_shock_multiplier=0.30,
    )

    assert "investment" in l2
    assert "market_safety_buffer" in l2
    assert "simulated_safety_buffer" in l2
    assert "shocked_safety_buffer" in l3


def test_component_risk_simulated_matches_analytical_probability(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=8_000,
    )

    result = service.risk.component_simulated(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        confidence=0.95,
        seed=42,
    )

    assert len(result.cluster_risks) == 2
    assert result.portfolio_component_probability == pytest.approx(
        result.portfolio_component_probability_analytical, abs=0.03
    )
    assert result.portfolio_expected_incremental_loss_eur > 0


def test_stress_test_delivery_returns_typed_result_and_profile_ordering(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=5_000,
    )

    baseline = service.delivery.stress_test(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        fail_multiplier=1.0,
        delay_multiplier=1.0,
        shock_sensitivity=1.0,
        seed=42,
    )
    stressed = service.delivery.stress_test(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        fail_multiplier=1.10,
        delay_multiplier=1.15,
        shock_sensitivity=1.30,
        seed=42,
    )
    managed = service.delivery.stress_test(
        [feature.name for feature in sample_features],
        risk_model=risk_model,
        fail_multiplier=0.65,
        delay_multiplier=0.70,
        shock_sensitivity=0.55,
        seed=42,
    )

    assert isinstance(baseline, DeliveryStressResult)
    assert isinstance(stressed, DeliveryStressResult)
    assert isinstance(managed, DeliveryStressResult)

    assert stressed.expected_impact_eur >= baseline.expected_impact_eur
    assert managed.expected_impact_eur <= baseline.expected_impact_eur
    assert managed.impact_var_95_eur <= stressed.impact_var_95_eur


def test_simulate_delivery_risk_returns_typed_feature_results(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=300)

    results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    assert set(results.keys()) == set(selected)
    assert all(
        isinstance(result, DeliverySimulationResult) for result in results.values()
    )
    for result in results.values():
        assert len(result.actual_sprints) == 300
        assert len(result.actual_cost) == 300
        assert len(result.cancelled) == 300
        assert 0.0 <= result.cancelled_pct <= 1.0
        assert result.expected_actual_cost > 0.0


def test_portfolio_profitability_aggregates_delivery_results(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    profitability = service.delivery.profitability(
        selected,
        delivery_results,
    )

    assert isinstance(profitability, PortfolioProfitabilityResult)
    assert len(profitability.feature_results) == len(selected)
    assert len(profitability.portfolio_profit) == 2_000
    assert profitability.total_investment == pytest.approx(125_000.0)
    assert 0.0 <= profitability.portfolio_break_even_probability <= 1.0
    assert profitability.portfolio_loss_at_risk_95 >= 0.0


def test_profitability_rows_returns_notebook_ready_rows(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    profitability = service.delivery.profitability(
        selected,
        delivery_results,
    )
    rows = service.delivery.profitability_rows(profitability)

    assert len(rows) == len(selected)
    assert all(len(row) == 6 for row in rows)
    assert [row[0] for row in rows] == ["Simplified UI", "Traceability"]
    assert all(row[-1].endswith("%") for row in rows)


def test_delivery_row_helpers_return_notebook_ready_rows(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    plan_rows = service.delivery.sprint_plan_rows(
        sample_features,
        DeliveryRiskConfig(),
    )
    delay_rows = service.delivery.delay_summary_rows(delivery_results, selected)
    cost_rows = service.delivery.cost_comparison_rows(sample_features, delivery_results)

    assert len(plan_rows) == len(sample_features)
    assert len(delay_rows) == len(selected)
    assert len(cost_rows) == len(sample_features)
    assert all(len(row) == 4 for row in plan_rows)
    assert all(len(row) == 9 for row in delay_rows)
    assert all(len(row) == 6 for row in cost_rows)


def test_delivery_cost_risk_rows_shape(
    sample_features: list[Feature],
):
    """delivery_cost_risk_rows produces 7-column rows with CaR and CVaR."""
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    risk_rows = service.delivery.delivery_cost_risk_rows(
        sample_features, delivery_results
    )

    assert len(risk_rows) == len(sample_features)
    assert all(len(row) == 7 for row in risk_rows)
    # Uplift column is 6th (index 5), must look like "+X.Y%"
    assert all(row[5].startswith(("+", "-")) for row in risk_rows)
    # Cancelled % column is 7th (index 6), must end with "%"
    assert all(row[6].endswith("%") for row in risk_rows)


def test_sprint_plan_rows_round_up_partial_sprints():
    feature = Feature(
        name="H9: Partial Sprint",
        expected_users=10_000,
        conversion_rate=0.1,
        uncertainty=0.2,
        business_value_per_conversion=1.0,
        development_cost=12_000.0,
        development_weeks=5,
    )

    rows = DeliveryAnalysisOperations.sprint_plan_rows(
        [feature],
        DeliveryRiskConfig(),
    )

    assert rows == [("Partial Sprint", "5.0", "3", "EUR 12,000")]


def test_optimize_profit_cvar_returns_typed_result(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    result = service.delivery.optimize_profit_cvar(
        selected,
        delivery_results,
        budget=155_000.0,
        alpha=0.95,
        n_scenarios=300,
    )

    assert isinstance(result, OptimizationResult)
    assert result.solver == "cvar_milp"
    assert result.total_cost <= 155_000.0
    assert set(result.recommended_features).issubset(set(selected))


def test_profit_optimization_comparison_returns_notebook_ready_rows(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    comparison = service.delivery.profit_optimization_comparison(
        selected,
        delivery_results,
        budget=155_000.0,
    )

    assert comparison.headers == (
        "Method",
        "Selected features",
        "Total cost",
        "Tail floor (P5)",
        "Tail mean (CVaR 95%)",
    )
    assert len(comparison.rows) == 2
    assert comparison.rows[0][0] == "Profit-CVaR MILP (alpha=95%)"
    assert comparison.rows[1][0] == "Expected-profit ratio baseline"


def test_profit_optimization_comparison_uses_alpha_specific_tail_labels(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=2_000)
    delivery_results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    comparison = service.delivery.profit_optimization_comparison(
        selected,
        delivery_results,
        budget=155_000.0,
        alpha=0.90,
    )

    assert comparison.headers == (
        "Method",
        "Selected features",
        "Total cost",
        "Tail floor (P10)",
        "Tail mean (CVaR 90%)",
    )
    assert comparison.rows[0][0] == "Profit-CVaR MILP (alpha=90%)"


def test_delivery_config_scenarios_override_service_scenarios(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    selected = [feature.name for feature in sample_features]
    delivery_config = DeliveryRiskConfig(scenarios=500)

    results = service.delivery.simulate_risk(
        selected,
        delivery_config=delivery_config,
        seed=42,
    )

    assert all(len(result.actual_sprints) == 500 for result in results.values())
    assert all(
        len(result.business_value_after_risk) == 500 for result in results.values()
    )


def test_optimize_profit_cvar_raises_on_missing_delivery_results(
    sample_features: list[Feature],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=500,
    )

    with pytest.raises(ValueError, match="Missing delivery simulation results"):
        service.delivery.optimize_profit_cvar(
            [feature.name for feature in sample_features],
            delivery_results={},
        )


def test_risk_management_assessment_compares_baseline_and_managed(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=4_000,
    )
    selected = [feature.name for feature in sample_features]

    profiles = {
        "Baseline": service.delivery.stress_test(
            selected,
            risk_model=risk_model,
            fail_multiplier=1.0,
            delay_multiplier=1.0,
            shock_sensitivity=1.0,
            seed=42,
        ),
        "Managed": service.delivery.stress_test(
            selected,
            risk_model=risk_model,
            fail_multiplier=0.65,
            delay_multiplier=0.70,
            shock_sensitivity=0.55,
            seed=42,
        ),
    }

    roi = service.delivery.risk_management_assessment(
        profiles,
        investment=125_000.0,
        baseline_label="Baseline",
        managed_label="Managed",
        program_cost_share=0.06,
    )
    assert isinstance(roi, RiskManagementROI)
    assert roi.program_cost_eur == pytest.approx(7_500.0)
    assert roi.avoided_expected_loss_eur >= 0
    assert roi.tail_risk_reduction_var_95_eur >= 0


def test_pnl_assessment_returns_typed_break_even_summary(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=3_000,
    )
    selected = [feature.name for feature in sample_features]

    pnl_layers = service.layers.simulate_portfolio_pnl_layers(
        selected,
        risk_model=risk_model,
        seed=42,
    )
    assessment = service.delivery.pnl_assessment(
        pnl_layers,
        investment=125_000.0,
    )

    assert isinstance(assessment, PnLAssessment)
    assert assessment.expected_business_value_eur == pytest.approx(
        pnl_layers.after_risk_3.expected
    )
    assert assessment.var_95_business_value_eur == pytest.approx(
        pnl_layers.after_risk_3.var_95
    )
    assert assessment.net_expected_eur == pytest.approx(
        assessment.expected_business_value_eur - assessment.investment_eur
    )


def test_decision_table_rows_returns_notebook_ready_rows(
    sample_features: list[Feature],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    budget_levels = {
        "50% Budget": 77_500.0,
        "100% Budget": 155_000.0,
    }
    ilp_results = service.budget_sensitivity(
        budget_levels,
        solver="ilp",
        strategy="var_floor",
    )

    rows = service.decisions.decision_table_rows(budget_levels, ilp_results)

    assert len(rows) == 2
    assert all(len(row) == 10 for row in rows)
    # First column is budget label
    assert rows[0][0] == "50% Budget"
    assert rows[1][0] == "100% Budget"
    # Second column is formatted EUR budget
    assert "EUR" in rows[0][1]
    # Last column is action string
    assert isinstance(rows[0][-1], str)
    assert len(rows[0][-1]) > 0


def test_component_sensitivity_rows_returns_notebook_ready_rows(
    sample_features: list[Feature],
    risk_model: dict[str, object],
):
    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=1_500,
    )
    selected = [feature.name for feature in sample_features]

    clusters = dict(risk_model["component_risk_by_cluster"])
    comp_expected: dict[str, list[tuple[float, float]]] = {c: [] for c in clusters}
    for cluster_name, base_prob in clusters.items():
        for factor in (0.5, 1.0, 1.5):
            result = service.layers.simulate_portfolio_risk_layers(
                selected,
                risk_model=risk_model,
                component_probability_by_cluster={
                    cluster_name: min(base_prob * factor, 0.95)
                },
                seed=42,
            )
            comp_expected[cluster_name].append(
                (min(base_prob * factor, 0.95), result.after_risk_3.expected)
            )

    rows = service.layers.component_sensitivity_rows(comp_expected)

    assert rows
    assert all(len(row) == 3 for row in rows)
    assert all("EUR" in row[2] for row in rows)


def test_feature_selection_view_returns_notebook_ready_view(
    sample_features: list[Feature],
):
    from fhs.application.decision_operations import FeatureSelectionView

    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    budget_levels = {
        "50% Budget": 77_500.0,
        "100% Budget": 155_000.0,
    }
    ilp_results = service.budget_sensitivity(
        budget_levels,
        solver="ilp",
        strategy="var_floor",
    )

    view = service.decisions.feature_selection_view(
        sample_features, ilp_results, full_label="100% Budget"
    )

    assert isinstance(view, FeatureSelectionView)
    assert len(view.rows) == len(sample_features)
    assert len(view.rows[0]) == 9
    assert view.headers[0] == "Feature"
    assert view.headers[-1] == "Impact on objective"
    # selected_features is a sorted list of names
    assert isinstance(view.selected_features, list)
    assert all(isinstance(n, str) for n in view.selected_features)
    # proxy score analytics
    assert isinstance(view.all_proxy_score, float)
    assert isinstance(view.selected_proxy_score, float)
    assert isinstance(view.has_negative_roi, bool)
    # short_names stripped from feature.name → not present in view.rows[0][0]
    # (view keeps full name in col 0)
    assert "H1" in view.rows[0][0] or "H2" in view.rows[0][0]


def test_decision_row_helpers_return_notebook_ready_rows(
    service,
    sample_features: list[Feature],
):
    solver_results = service.compare_solvers(
        budget=service.budget,
        strategy="var_floor",
        include=("exact", "ilp", "greedy"),
    )
    comparison_rows = service.decisions.solver_comparison_rows(solver_results)
    negative_view = service.decisions.negative_score_rows()

    assert len(comparison_rows) == 3
    assert all(len(row) == 8 for row in comparison_rows)
    assert len(negative_view.rows) == len(sample_features)
    assert len(negative_view.positive_features) + len(
        negative_view.negative_features
    ) == len(sample_features)

    negative_rows = service.decisions.negative_score_comparison_rows(
        {"exact": solver_results["exact"], "ilp": solver_results["ilp"]},
        {"exact": solver_results["exact"], "ilp": solver_results["ilp"]},
    )
    assert len(negative_rows) == 4

    runtime_data = {
        "exact": {"x": [2], "runtime": [0.1], "floor": [10_000.0]},
        "ilp": {"x": [2], "runtime": [0.01], "floor": [9_500.0]},
        "greedy": {"x": [2], "runtime": [0.001], "floor": [9_000.0]},
    }
    runtime_rows = service.decisions.runtime_scaling_rows(
        runtime_data,
        budgets_by_feature_count={2: 125_000.0},
    )
    assert len(runtime_rows) == 3
    assert all(len(row) == 5 for row in runtime_rows)

    selected_portfolio_rows = service.decisions.selected_portfolio_rows(
        solver_results["ilp"].recommended_features,
        strategy={},
    )
    assert selected_portfolio_rows
    assert all(len(row) == 5 for row in selected_portfolio_rows)


def test_portfolio_comparison_rows_returns_two_option_rows(
    sample_features: list[Feature],
):
    from fhs.application.decision_operations import (
        PortfolioComparisonView,
    )

    service = AdvancedPortfolioService(
        sample_features,
        budget=155_000.0,
        discount_rate=0.08,
        seed=42,
        scenarios=2_000,
    )
    budget_levels = {
        "50% Budget": 77_500.0,
        "100% Budget": 155_000.0,
    }
    ilp_results = service.budget_sensitivity(
        budget_levels,
        solver="ilp",
        strategy="var_floor",
    )
    selection = service.decisions.feature_selection_view(
        sample_features, ilp_results, full_label="100% Budget"
    )
    all_feature_names = sorted(f.name for f in sample_features)
    selected_snapshot = service.portfolio_snapshot(selection.selected_features)
    all_snapshot = service.portfolio_snapshot(all_feature_names)
    full_budget = 155_000.0

    comparison = service.decisions.portfolio_comparison_rows(
        selection, selected_snapshot, all_snapshot, full_budget, all_feature_names
    )

    assert isinstance(comparison, PortfolioComparisonView)
    assert len(comparison.rows) == 2
    assert comparison.rows[0][0] == "ILP selected"
    assert comparison.rows[1][0] == "All features option"
    assert len(comparison.rows[0]) == 8
    assert len(comparison.rows[1]) == 8
    assert comparison.headers[0] == "Portfolio Option"
    assert comparison.headers[2] == "Fits 100% Budget"
    # Budget fit column is Yes or No
    assert comparison.rows[0][2] in ("Yes", "No")
    assert comparison.rows[1][2] in ("Yes", "No")
    # EUR formatting in cost column
    assert "EUR" in comparison.rows[0][3]
    assert "EUR" in comparison.rows[1][3]
