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
Data Transfer Objects (DTOs) for the Application Layer.

DTOs are simple data containers that transfer data between layers.
They have no business logic.
"""

from dataclasses import dataclass, field

import numpy as np

from fhs.core.model import DeliveryRiskConfig, Feature, ScenarioRiskModel


@dataclass
class ScenarioContext:
    """
    Immutable scenario context for notebooks.

    This is the main data structure returned to notebooks.
    Contains all data needed for simulation and analysis.
    """

    scenario_id: str
    features: list[Feature]
    budget: float
    discount_rate: float
    strategy: dict[str, dict[str, str]]
    weights: dict[str, float]
    dependency_matrix: np.ndarray
    config_path: str
    config_source: str
    exam_report: dict
    seed: int = 42
    scenarios: int = 100000
    cost_inflation_max: float = 0.25
    name: str = "Unnamed Scenario"
    risk_model: ScenarioRiskModel = field(default_factory=ScenarioRiskModel)
    delivery_config: DeliveryRiskConfig = field(default_factory=DeliveryRiskConfig)

    @property
    def features_by_key(self) -> dict[str, Feature]:
        """Index features by their short key (e.g., 'H1', 'H2')."""
        result = {}
        for f in self.features:
            # Use feature key if available, fallback to name prefix
            key = getattr(f, "key", f.name.split(":")[0].strip())
            result[key] = f
        return result

    @property
    def biz_values(self) -> dict[str, float]:
        """Business value per conversion indexed by key."""
        result = {}  # pragma: no cover - defensive
        for f in self.features:  # pragma: no cover - defensive
            key = getattr(
                f, "key", f.name.split(":")[0].strip()
            )  # pragma: no cover - defensive
            result[key] = (
                f.business_value_per_conversion
            )  # pragma: no cover - defensive
        return result  # pragma: no cover - defensive
