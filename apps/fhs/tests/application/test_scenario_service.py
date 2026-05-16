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

from unittest.mock import MagicMock

import pytest

from fhs.application.scenario_service import ScenarioContext, ScenarioService
from fhs.core.model import DeliveryRiskConfig, Feature, ScenarioRiskModel
from fhs.core.model.repositories import FeatureRepository


@pytest.fixture
def mock_repo(tmp_path):
    repo = MagicMock(spec=FeatureRepository)
    repo.config_dir = tmp_path / "mock_config"
    repo.config_dir.mkdir()
    return repo


@pytest.fixture
def sample_config():
    return {
        "scenario_id": "blockchain",
        "name": "Blockchain Scenario",
        "budget": 100000,
        "risk_model": {
            "risk_2_market_probability": 0.20,
            "risk_3_global_probability": 0.05,
            "component_risk_by_cluster": {"Alpha": 0.12},
        },
        "deployment_risk": {
            "sprint_length_weeks": 2,
            "quarterly_capacity_sprints": 9,
        },
        "features": [
            {
                "key": "H1",
                "name": "H1: Feature 1",
                "expected_users": 1000,
                "conversion_rate": 0.5,
                "uncertainty": 0.2,
                "business_value_per_conversion": 100.0,
                "development_cost": 10000,
                "category": "Business Value Driver",
                "dependency_cluster": "Alpha",
                "weight": 0.6,
            },
            {
                "key": "H2",
                "name": "H2: Feature 2",
                "expected_users": 2000,
                "conversion_rate": 0.3,
                "uncertainty": 0.15,
                "business_value_per_conversion": 50.0,
                "development_cost": 20000,
                "category": "Compliance",
                "dependency_cluster": "Alpha",
                "weight": 0.4,
                "depends_on": ["H1"],
            },
        ],
    }


@pytest.fixture
def sample_features():
    return [
        Feature(
            name="H1: Feature 1",
            expected_users=1000,
            conversion_rate=0.5,
            uncertainty=0.2,
            business_value_per_conversion=100.0,
            development_cost=10000,
        ),
        Feature(
            name="H2: Feature 2",
            expected_users=2000,
            conversion_rate=0.3,
            uncertainty=0.15,
            business_value_per_conversion=50.0,
            development_cost=20000,
        ),
    ]


def test_scenario_service_loads_context(mock_repo, sample_config, sample_features):
    mock_repo.get_scenario.return_value = sample_config
    mock_repo.get_features.return_value = sample_features

    service = ScenarioService(repository=mock_repo)
    context = service.load_scenario("blockchain")

    assert isinstance(context, ScenarioContext)
    assert context.scenario_id == "blockchain"
    assert len(context.features) == 2
    assert context.budget == 100000
    assert isinstance(context.risk_model, ScenarioRiskModel)
    assert context.risk_model.risk_2_market_probability == pytest.approx(0.20)
    assert context.risk_model.risk_3_global_probability == pytest.approx(0.05)
    assert isinstance(context.delivery_config, DeliveryRiskConfig)
    assert context.delivery_config.sprint_length_weeks == 2
    assert context.delivery_config.quarterly_capacity_sprints == 9
    assert "H1" in context.features_by_key
    assert "H2" in context.features_by_key
    assert context.features_by_key["H1"].name == "H1: Feature 1"


def test_scenario_service_uses_default_seed_and_scenarios(
    mock_repo, sample_config, sample_features
):
    mock_repo.get_scenario.return_value = sample_config
    mock_repo.get_features.return_value = sample_features

    service = ScenarioService(repository=mock_repo)
    context = service.load_scenario("blockchain")

    assert context.seed == 42
    assert context.scenarios == 100000


def test_scenario_service_reads_seed_and_scenarios_from_config(
    mock_repo, sample_config, sample_features
):
    config = dict(sample_config)
    config["seed"] = 99
    config["scenarios"] = 12345
    mock_repo.get_scenario.return_value = config
    mock_repo.get_features.return_value = sample_features

    service = ScenarioService(repository=mock_repo)
    context = service.load_scenario("blockchain")

    assert context.seed == 99
    assert context.scenarios == 12345


def test_scenario_service_calculates_weights(mock_repo, sample_config, sample_features):
    mock_repo.get_scenario.return_value = sample_config
    mock_repo.get_features.return_value = sample_features

    service = ScenarioService(repository=mock_repo)
    context = service.load_scenario("blockchain")

    # Weights should be normalized (0.6 and 0.4 sum to 1.0)
    assert context.weights["H1: Feature 1"] == 0.6
    assert context.weights["H2: Feature 2"] == 0.4


def test_scenario_service_builds_dependency_matrix(
    mock_repo, sample_config, sample_features
):
    mock_repo.get_scenario.return_value = sample_config
    mock_repo.get_features.return_value = sample_features

    service = ScenarioService(repository=mock_repo)
    context = service.load_scenario("blockchain")

    # H1 and H2 share cluster "Alpha" (0.5) and H2 depends on H1 (0.8)
    # Max should be 0.8
    assert context.dependency_matrix[0, 1] == 0.8
    assert context.dependency_matrix[1, 0] == 0.8
    assert context.dependency_matrix[0, 0] == 1.0


def test_scenario_service_saves_scenario(mock_repo, sample_features):
    service = ScenarioService(repository=mock_repo)
    strategy = {"H1: Feature 1": {"category": "Test", "reason": "Because"}}

    service.save_scenario(
        scenario_id="test_save",
        features=sample_features,
        budget=50000,
        strategy=strategy,
    )

    mock_repo.save_scenario.assert_called_once()
    args = mock_repo.save_scenario.call_args[0]
    assert args[0] == "test_save"
    assert args[1]["budget"] == 50000
    assert len(args[1]["features"]) == 2
    assert "key" not in args[1]["features"][0]
    assert "category" not in args[1]["features"][0]
    assert "reason" not in args[1]["features"][0]
    assert args[1]["strategy"] == strategy
