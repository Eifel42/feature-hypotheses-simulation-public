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

"""YAML-based repository implementation (Infrastructure Layer)."""

from pathlib import Path

import yaml

from fhs.core.model import Feature, ScenarioConfig


class YamlFeatureRepository:
    """YAML-based feature repository implementation."""

    def __init__(self, config_dir: Path):
        """
        Initialize repository.

        Args:
            config_dir: Directory containing YAML scenario files
        """
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise ValueError(f"Config directory not found: {config_dir}")

    def get_scenario(self, scenario_id: str) -> dict:
        """Load scenario configuration from YAML file."""
        config_path = self.config_dir / f"{scenario_id}.yaml"
        if not config_path.exists():
            raise ValueError(
                f"Scenario not found: {scenario_id} (expected: {config_path})"
            )

        with open(config_path, encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        if not isinstance(raw_config, dict):
            raise ValueError(  # pragma: no cover - defensive
                f"Invalid scenario config in {config_path}: must be a dict"
            )

        # Validate with Pydantic
        try:
            scenario_config = ScenarioConfig(**raw_config)
            config = scenario_config.model_dump()
            # Ensure metadata reflects source
            if "metadata" not in config:
                config["metadata"] = {}  # pragma: no cover - defensive
            config["metadata"]["config_source"] = "yaml"
            config["metadata"]["config_path"] = str(config_path)
            return config
        except Exception as exc:
            raise ValueError(f"Validation error in {config_path}: {exc}") from exc

    def save_scenario(self, scenario_id: str, config: dict) -> None:
        """Save scenario configuration to YAML file."""
        if not isinstance(config, dict):
            raise ValueError("Config must be a dict")  # pragma: no cover - defensive

        config_path = self.config_dir / f"{scenario_id}.yaml"

        # Ensure directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def get_features(self, scenario_id: str) -> list[Feature]:
        """Load features from scenario configuration."""
        config = self.get_scenario(scenario_id)

        if "features" not in config:
            raise ValueError(
                f"Scenario {scenario_id} has no 'features' key"
            )  # pragma: no cover - defensive

        features_data = config["features"]
        if not isinstance(features_data, list):
            raise ValueError(
                f"Scenario {scenario_id}: 'features' must be a list"
            )  # pragma: no cover - defensive

        features = []
        for idx, feature_data in enumerate(features_data):
            try:
                # Filter to only Feature model fields
                feature_fields = set(Feature.model_json_schema().get("properties", {}))
                filtered_data = {
                    k: v for k, v in feature_data.items() if k in feature_fields
                }
                features.append(Feature(**filtered_data))
            except Exception as exc:  # pragma: no cover - defensive
                raise ValueError(  # pragma: no cover - defensive
                    f"Invalid feature at index {idx} in {scenario_id}: {exc}"
                ) from exc

        return features
