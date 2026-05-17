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

"""Scenario metadata and risk model configuration value objects."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScenarioMetadata(BaseModel):
    """Metadata for a scenario."""

    created: str | None = None
    last_modified: str | None = None
    version: str | None = None
    author: str | None = None
    config_source: str = "yaml"
    config_path: str = "N/A"


class ScenarioRiskModel(BaseModel):
    """Portfolio-level risk assumptions used by advanced notebooks."""

    risk_2_market_probability: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description="Risk 2: probability of market shock.",
    )
    risk_2_market_multiplier: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Risk 2: business value multiplier if market shock occurs.",
    )
    risk_3_global_probability: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Risk 3: probability of global shock.",
    )
    risk_3_global_multiplier: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Risk 3: business value multiplier if global shock occurs.",
    )
    component_risk_multiplier: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Business value multiplier for component risk hits.",
    )
    default_component_probability: float = Field(
        default=0.08,
        ge=0.0,
        le=1.0,
        description="Fallback component risk probability per cluster.",
    )
    component_risk_by_cluster: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
    )

    # noinspection PyNestedDecoratorsInspection
    @field_validator("component_risk_by_cluster")
    @classmethod
    def validate_component_risk_by_cluster(
        cls, values: dict[str, float]
    ) -> dict[str, float]:
        """Ensure component probabilities are valid [0, 1] values."""
        validated: dict[str, float] = {}
        for cluster, probability in values.items():
            prob = float(probability)
            if prob < 0.0 or prob > 1.0:
                raise ValueError(
                    f"component_risk_by_cluster['{cluster}'] must be between 0.0 and 1.0"
                )
            validated[str(cluster)] = round(prob, 4)
        return validated
