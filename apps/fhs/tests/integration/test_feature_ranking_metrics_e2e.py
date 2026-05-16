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

"""End-to-end tests for feature ranking metrics and ranking strategies."""

from __future__ import annotations

import json
from pathlib import Path

from fhs.application.advanced_portfolio_service import AdvancedPortfolioService
from fhs.application.scenario_service import ScenarioService


def _build_service_from_blockchain_config() -> AdvancedPortfolioService:
    config_dir = Path(__file__).resolve().parents[2] / "notebooks" / "config"
    scenario = ScenarioService.create_default(config_dir=config_dir).load_scenario(
        "blockchain"
    )
    return AdvancedPortfolioService(
        scenario.features,
        budget=scenario.budget,
        discount_rate=scenario.discount_rate,
        seed=scenario.seed,
        scenarios=5_000,
    )


def _load_var_floor_snapshot() -> dict[str, object]:
    snapshot_path = (
        Path(__file__).resolve().parent
        / "snapshots"
        / "var_floor_blockchain_seed42_s5000.json"
    )
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def test_full_pipeline_blockchain_yaml_to_strategy_rankings() -> None:
    service = _build_service_from_blockchain_config()

    strategies = ("var_floor", "risk_ratio", "rorac", "risk_adjusted_roi")
    rankings = {
        strategy: service.decisions.rank_features(strategy=strategy)
        for strategy in strategies
    }

    assert all(rankings[strategy] for strategy in strategies)
    assert all(
        0.0 <= row.risk_ratio <= 1.0
        for strategy in strategies
        for row in rankings[strategy]
    )

    top3 = {
        strategy: tuple(row.feature for row in rankings[strategy][:3])
        for strategy in strategies
    }
    assert len(set(top3.values())) >= 2


def test_var_floor_strategy_matches_previous_sorting_behavior() -> None:
    service = _build_service_from_blockchain_config()

    ranked = service.decisions.rank_features(strategy="var_floor")
    expected = sorted(
        service.features,
        key=lambda feature: (
            service.simulation_results[feature.name].business_value_at_risk_95
        ),
        reverse=True,
    )

    assert [row.feature for row in ranked] == [feature.name for feature in expected]


def test_var_floor_strategy_matches_golden_snapshot() -> None:
    service = _build_service_from_blockchain_config()
    snapshot = _load_var_floor_snapshot()

    ranked = service.decisions.rank_features(strategy="var_floor")
    feature_order = [row.feature for row in ranked]

    assert snapshot["strategy"] == "var_floor"
    assert snapshot["scenario_id"] == "blockchain"
    assert snapshot["seed"] == 42
    assert snapshot["scenarios"] == 5_000
    assert feature_order == snapshot["ordered_features"]


def test_strategy_ranking_is_stable_for_same_seed_and_inputs() -> None:
    service = _build_service_from_blockchain_config()

    first = [row.feature for row in service.decisions.rank_features(strategy="rorac")]
    second = [row.feature for row in service.decisions.rank_features(strategy="rorac")]

    assert first == second
