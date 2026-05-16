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
Repository pattern for feature scenario persistence (Domain Layer - Protocol only).

Defines the contract for feature data access.
Implementations belong in the Infrastructure Layer (fhs.infra.repositories).
"""

from pathlib import Path
from typing import Protocol

from .entities import Feature


class FeatureRepository(Protocol):
    """Repository protocol for feature scenario persistence."""

    @property
    def config_dir(self) -> Path:
        """
        Return the configuration directory.

        Returns:
            Path to the directory containing scenario configuration files.
        """
        ...

    def get_scenario(self, scenario_id: str) -> dict:
        """
        Load scenario configuration.

        Args:
            scenario_id: Scenario identifier (e.g., "blockchain")

        Returns:
            Dict with scenario config (features, budget, strategy, metadata)

        Raises:
            ValueError: If scenario not found
        """
        ...

    def save_scenario(self, scenario_id: str, config: dict) -> None:
        """
        Save scenario configuration.

        Args:
            scenario_id: Scenario identifier
            config: Configuration dict with features, budget, strategy

        Raises:
            ValueError: If config is invalid
        """
        ...

    def get_features(self, scenario_id: str) -> list[Feature]:
        """
        Load features for a scenario.

        Args:
            scenario_id: Scenario identifier

        Returns:
            List of Feature objects

        Raises:
            ValueError: If scenario not found or features invalid
        """
        ...
