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
Unit tests for repository implementations.
"""

import copy
import shutil
import tempfile
from pathlib import Path

import pytest

from fhs.core.model import Feature
from fhs.infra.repositories import YamlFeatureRepository


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_scenario_config():
    """Sample scenario configuration for testing."""
    return {
        "scenario_id": "test",
        "name": "Test Scenario",
        "budget": 50000,
        "features": [
            {
                "name": "Test Feature 1",
                "expected_users": 1000,
                "conversion_rate": 0.5,
                "uncertainty": 0.2,
                "business_value_per_conversion": 100.0,
                "development_cost": 10000,
            },
            {
                "name": "Test Feature 2",
                "expected_users": 2000,
                "conversion_rate": 0.3,
                "uncertainty": 0.15,
                "business_value_per_conversion": 50.0,
                "development_cost": 20000,
            },
        ],
        "metadata": {"version": "1.0"},
    }


class TestYamlFeatureRepository:
    """Tests for YamlFeatureRepository."""

    def test_init_creates_repository(self, temp_config_dir):
        """Test repository initialization."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)
        assert repo.config_dir == temp_config_dir

    def test_init_fails_with_nonexistent_dir(self):
        """Test repository fails with non-existent directory."""
        with pytest.raises(ValueError, match="Config directory not found"):
            YamlFeatureRepository(config_dir=Path("/nonexistent/path"))

    def test_save_and_load_scenario(self, temp_config_dir, sample_scenario_config):
        """Test saving and loading scenario configuration."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)

        # Save scenario
        repo.save_scenario("test", sample_scenario_config)

        # Verify file exists
        config_file = temp_config_dir / "test.yaml"
        assert config_file.exists()

        # Load scenario
        loaded_config = repo.get_scenario("test")

        assert loaded_config["scenario_id"] == "test"
        assert loaded_config["budget"] == 50000
        assert len(loaded_config["features"]) == 2

    def test_get_scenario_fails_for_nonexistent(self, temp_config_dir):
        """Test get_scenario fails for non-existent scenario."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)

        with pytest.raises(ValueError, match="Scenario not found"):
            repo.get_scenario("nonexistent")

    def test_get_features_returns_feature_objects(
        self, temp_config_dir, sample_scenario_config
    ):
        """Test get_features returns Feature objects."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)
        repo.save_scenario("test", sample_scenario_config)

        features = repo.get_features("test")

        assert len(features) == 2
        assert all(isinstance(f, Feature) for f in features)
        assert features[0].name == "Test Feature 1"
        assert features[0].expected_users == 1000
        assert features[1].name == "Test Feature 2"
        assert features[1].expected_users == 2000

    def test_get_features_fails_without_features_key(self, temp_config_dir):
        """Test get_features fails when features key is missing."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)

        # This will now fail during get_scenario (via get_features)
        # because ScenarioConfig requires features list
        invalid_config = {"scenario_id": "test", "budget": 100000}
        repo.save_scenario("test", invalid_config)

        # Validation error from ScenarioConfig
        with pytest.raises(ValueError, match="Validation error"):
            repo.get_features("test")

    def test_get_features_fails_with_invalid_feature_data(self, temp_config_dir):
        """Test get_features fails with invalid feature data."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)

        invalid_config = {
            "scenario_id": "test",
            "features": [
                {
                    "name": "Invalid Feature",
                    # Missing required fields
                }
            ],
        }
        repo.save_scenario("test", invalid_config)

        # Validation error from ScenarioConfig/Feature
        with pytest.raises(ValueError, match="Validation error"):
            repo.get_features("test")

    def test_get_scenario_loads_delivery_risk_block(
        self, temp_config_dir, sample_scenario_config
    ):
        """Repository should parse optional delivery_risk block into ScenarioConfig."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)
        config = copy.deepcopy(sample_scenario_config)
        config["delivery_risk"] = {
            "quarterly_capacity_sprints": 6,
            "delay_model": {
                "sprint_uncertainty": 25,
                "sprint_ceiling": 2.5,
            },
            "cancellation": {
                "max_sprints_over_plan": 3,
                "cancellation_probability": 0.4,
            },
        }

        repo.save_scenario("test", config)
        loaded = repo.get_scenario("test")

        assert loaded["delivery_risk"]["quarterly_capacity_sprints"] == 6
        assert loaded["delivery_risk"]["delay_model"]["sprint_uncertainty"] == (
            pytest.approx(0.25)
        )
        assert loaded["delivery_risk"]["cancellation"]["cancellation_probability"] == (
            pytest.approx(0.4)
        )

    def test_get_scenario_without_delivery_risk_defaults_to_none(
        self, temp_config_dir, sample_scenario_config
    ):
        """Repository should accept configs that omit optional delivery_risk block."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)
        config = copy.deepcopy(sample_scenario_config)
        config.pop("delivery_risk", None)

        repo.save_scenario("test", config)
        loaded = repo.get_scenario("test")

        assert "delivery_risk" in loaded
        assert loaded["delivery_risk"] is None

    def test_save_creates_directory_if_missing(self, temp_config_dir):
        """Test save creates config directory if it doesn't exist."""
        # Remove the directory
        shutil.rmtree(temp_config_dir)

        repo = YamlFeatureRepository.__new__(YamlFeatureRepository)
        repo.config_dir = temp_config_dir

        config = {"scenario_id": "test", "budget": 100000, "features": []}
        repo.save_scenario("test", config)

        assert temp_config_dir.exists()
        assert (temp_config_dir / "test.yaml").exists()

    def test_save_preserves_unicode(self, temp_config_dir):
        """Test save preserves Unicode characters."""
        repo = YamlFeatureRepository(config_dir=temp_config_dir)

        config = {
            "scenario_id": "unicode_test",
            "name": "Test mit Ümlauten und €-Zeichen",
            "features": [],
        }
        repo.save_scenario("unicode_test", config)

        loaded = repo.get_scenario("unicode_test")
        assert loaded["name"] == "Test mit Ümlauten und €-Zeichen"

    def test_blockchain_config_has_h1_binomial_without_static_3y_forecast(self):
        """Validate real blockchain scenario config fields used by notebooks."""
        config_dir = Path(__file__).resolve().parents[3] / "notebooks" / "config"
        repo = YamlFeatureRepository(config_dir=config_dir)

        scenario = repo.get_scenario("blockchain")
        features_by_name = {f["name"]: f for f in scenario["features"]}
        h1 = features_by_name["H1: Simplified UI"]
        # Keep this check resilient to notebook-driven scenario tuning.
        assert h1["expected_users"] > 0
        assert h1["acceptance_model"] == "binomial"
        assert "business_value_forecast_3y" not in h1

        loaded_features = repo.get_features("blockchain")
        loaded_by_name = {f.name: f for f in loaded_features}
        h1_feature = loaded_by_name["H1: Simplified UI"]
        assert h1_feature.acceptance_model == "binomial"
        assert h1_feature.get_base_annual_business_value() == pytest.approx(
            h1_feature.expected_users
            * h1_feature.conversion_rate
            * h1_feature.business_value_per_conversion
        )

        for feature in loaded_features:
            assert feature.get_base_annual_business_value() >= 0
