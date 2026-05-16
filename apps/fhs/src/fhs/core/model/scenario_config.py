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

"""ScenarioConfig aggregate — links Feature entities with scenario settings."""

from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from fhs.core.model.config import (
    DeliveryRiskConfig,
    ScenarioMetadata,
    ScenarioRiskModel,
)
from fhs.core.model.entities.feature import Feature
from fhs.core.model.value_objects import Budget
from fhs.core.model.value_objects.governance import (
    AssumptionMetadata,
    DecisionPolicy,
    ModelCard,
    RiskAppetitePolicy,
)


class ScenarioConfig(BaseModel):
    """
    Configuration model for a full scenario.
    Validates the structure of scenario YAML files.
    """

    scenario_id: str = Field(..., min_length=1)
    name: str = Field(default="Unnamed Scenario")
    description: str | None = None
    budget: float = Field(default=100000.0, ge=0.0)
    seed: int = Field(
        default=42,
        description="Random seed for reproducible Monte Carlo simulation.",
    )
    scenarios: int = Field(
        default=100000,
        ge=1,
        description="Number of Monte Carlo scenarios per feature.",
    )
    cost_inflation_max: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description=(
            "Maximum annual operating cost inflation rate (e.g. 0.25 = up to 25%). "
            "One inflation factor is drawn from Uniform(0, cost_inflation_max) per scenario "
            "and applied to all features equally (shared infrastructure assumption)."
        ),
    )
    discount_rate: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Annual discount rate for NPV calculations (e.g. 0.10 = 10 %)",
    )
    risk_model: ScenarioRiskModel = Field(default_factory=ScenarioRiskModel)
    # noinspection PyTypeHintsInspection
    delivery_risk: DeliveryRiskConfig | None = Field(
        default=None,
        validation_alias=AliasChoices("deployment_risk", "delivery_risk"),
        serialization_alias="deployment_risk",
        description="Optional sprint-based deployment risk configuration.",
    )
    features: list[Feature] = Field(...)
    strategy: dict[str, dict[str, str]] = Field(default_factory=dict)
    metadata: ScenarioMetadata = Field(default_factory=ScenarioMetadata)
    assumptions: dict[str, dict] = Field(
        default_factory=dict,
        description=(
            "Per-parameter assumption provenance. Keys are parameter names "
            "(e.g. 'conversion_rate'), values are AssumptionMetadata dicts."
        ),
    )
    decision_policy: dict = Field(
        default_factory=dict,
        description="DecisionPolicy thresholds for GO/Conditional GO/Review grading.",
    )
    risk_appetite: dict = Field(
        default_factory=dict,
        description="RiskAppetitePolicy thresholds — bank-grade extension of decision_policy.",
    )
    value_model: str = Field(
        default="conversion_based",
        description=(
            "Value calculation model: 'conversion_based' (expected_users × conversion_rate × value), "
            "'cost_saving' (cases × saved_cost), 'risk_avoidance' (exposure × reduction × probability)."
        ),
    )
    model_card: dict = Field(
        default_factory=dict,
        description="ModelCard metadata for governance and report embedding.",
    )

    def get_decision_policy(self) -> DecisionPolicy:
        """Return a DecisionPolicy from the scenario configuration."""
        return DecisionPolicy.from_dict(
            self.decision_policy
        )  # pragma: no cover - notebook widget helper

    def get_risk_appetite_policy(self) -> RiskAppetitePolicy:
        """Return a RiskAppetitePolicy from the scenario configuration."""
        return RiskAppetitePolicy.from_dict(
            self.risk_appetite
        )  # pragma: no cover - notebook widget helper

    def get_model_card(self) -> ModelCard:
        """Return a ModelCard from scenario config or defaults."""
        if not self.model_card:  # pragma: no cover - notebook widget helper
            return ModelCard()  # pragma: no cover - notebook widget helper
        _defaults = ModelCard()  # pragma: no cover - notebook widget helper
        return ModelCard(  # pragma: no cover - notebook widget helper
            model_name=self.model_card.get("model_name", _defaults.model_name),
            version=self.model_card.get("version", _defaults.version),
            purpose=self.model_card.get("purpose", _defaults.purpose),
            validation_status=self.model_card.get(
                "validation_status", _defaults.validation_status
            ),
            owner=self.model_card.get("owner", ""),
        )

    def get_assumption(self, parameter: str) -> AssumptionMetadata | None:
        """Return AssumptionMetadata for a parameter name, or None if not set."""
        raw = self.assumptions.get(
            parameter
        )  # pragma: no cover - notebook widget helper
        if raw is None:  # pragma: no cover - notebook widget helper
            return None  # pragma: no cover - notebook widget helper
        return AssumptionMetadata.from_dict(
            raw
        )  # pragma: no cover - notebook widget helper

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_deployment_risk(cls, data: Any) -> Any:
        """Accept the scenario-facing deployment_risk key for sprint risk config."""
        if not isinstance(data, dict):
            return data  # pragma: no cover - defensive for non-mapping validators
        if "deployment_risk" in data:
            if "delivery_risk" in data:
                raise ValueError(
                    "Use either deployment_risk or delivery_risk, not both"
                )
            data = dict(data)
            data["delivery_risk"] = data.pop("deployment_risk")
        return data

    # noinspection PyNestedDecoratorsInspection
    @field_validator("name")
    @classmethod
    def scenario_name_not_empty(cls, v: str) -> str:
        """Validate that name is not empty or whitespace-only"""
        if not v or not v.strip():
            raise ValueError(
                "Scenario name cannot be empty or whitespace"
            )  # pragma: no cover - notebook widget helper
        return v.strip()

    # noinspection PyNestedDecoratorsInspection
    @field_validator("strategy", mode="before")
    @classmethod
    def normalize_strategy(
        cls, v: dict[str, dict[str, str]] | dict[str, list[str]] | None
    ) -> dict[str, dict[str, str]]:
        """
        Normalize strategy mapping to ``{feature_name: {category, reason}}``.

        Accepts both:
        - Current format: ``{"H1": {"category": "...", "reason": "..."}}``
        - Legacy format: ``{"H1": ["category", "reason"]}``
        """
        if v is None:
            return {}  # pragma: no cover - notebook widget helper
        if not isinstance(v, dict):
            raise ValueError(
                "strategy must be a dictionary"
            )  # pragma: no cover - notebook widget helper

        normalized: dict[str, dict[str, str]] = {}
        for feature_name, value in v.items():
            if isinstance(value, dict):
                normalized[str(feature_name)] = {
                    "category": str(value.get("category", "Unknown")),
                    "reason": str(value.get("reason", "")),
                }
            elif isinstance(value, list):  # pragma: no cover - notebook widget helper
                category = (
                    str(value[0]) if len(value) > 0 else "Unknown"
                )  # pragma: no cover - notebook widget helper
                reason = (
                    str(value[1]) if len(value) > 1 else ""
                )  # pragma: no cover - notebook widget helper
                normalized[
                    str(feature_name)
                ] = {  # pragma: no cover - notebook widget helper
                    "category": category,  # pragma: no cover - notebook widget helper
                    "reason": reason,  # pragma: no cover - notebook widget helper
                }  # pragma: no cover - notebook widget helper
            else:  # pragma: no cover - notebook widget helper
                raise ValueError(  # pragma: no cover - notebook widget helper
                    "strategy values must be dicts with category/reason "
                    "or legacy [category, reason] lists"
                )

        return normalized

    @property
    def budget_value_object(self) -> Budget:
        """Return the scenario budget as a typed Budget value object."""
        return Budget(amount=self.budget)
