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

"""Delivery risk configuration value objects."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DelayModelConfig(BaseModel):
    """Configuration for sprint duration uncertainty using truncated lognormal model.

    Models sprint duration variation using a **truncated lognormal distribution**:
    - Lower bound: 1.0 (no sprint finishes faster than planned)
    - Upper bound: sprint_ceiling × planned_sprints

    This ensures mathematically sound probability distributions without artificial
    probability "stacking" observed with simple capping approaches.
    """

    sprint_uncertainty: float = Field(
        default=30,
        description=(
            "Sprint duration volatility as **percentage (5–100)** or decimal (0.05–1.0). "
            "E.g., 30 or 0.30 = ±30% variation around planned duration. "
            "Interpretation: ~68% of sprints finish within this ±range. "
            "Typical range: 15–30% (stable/experienced teams) to 40–50% (volatile/new teams). "
            "Internally normalized to decimal: 30 → 0.30 for distribution parameter."
        ),
    )
    sprint_ceiling: float = Field(
        default=3.0,
        gt=1.0,
        le=10.0,
        description=(
            "Hard upper bound on worst-case sprint duration as multiple of planned. "
            "E.g., 3.0 = no sprint can exceed 3× its planned duration. "
            "This is the upper bound of the truncated lognormal distribution. "
            "Typical range: 2.0–5.0 (realistic worst-case overruns). "
            "Recommended: align with organizational risk appetite (3.0–4.0 common)."
        ),
    )

    model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)

    # noinspection PyNestedDecoratorsInspection
    @field_validator("sprint_uncertainty", mode="before")
    @classmethod
    def normalize_uncertainty_to_decimal(cls, v: float | str) -> float:
        """Accept percentage values (0–100) or decimal (0.0–1.0) and normalize to decimal.

        Examples:
            - 30 (percent) → 0.30
            - 0.30 (decimal) → 0.30
            - 0 (no variation) → 0.0
            - "30%" (string) → 0.30
        """
        if isinstance(v, str):
            v = float(v.replace("%", "").strip())

        # Normalize: if v > 1.0, assume it's a percentage
        if v > 1.0:
            v = v / 100.0

        # Validate range (0.0 to 1.0 as decimal = 0% to 100%)
        # Special case: 0.0 means no variation (deterministic)
        if v < 0.0:
            raise ValueError(
                f"sprint_uncertainty must be ≥ 0% (decimal 0.0), got {v}. "
                f"Use 0 for deterministic (no delay variation)."
            )
        if v > 1.0:
            raise ValueError(
                f"sprint_uncertainty must be ≤ 100% (decimal 1.0), got {v}. "
                f"Typical range: 15–50% (decimal 0.15–0.50)."
            )

        return v

    # noinspection PyNestedDecoratorsInspection
    @field_validator("sprint_ceiling")
    @classmethod
    def validate_ceiling_is_realistic(cls, v: float, info) -> float:
        """Ensure sprint_ceiling allows meaningful overruns and is realistic."""
        if v <= 1.0:
            raise ValueError(  # pragma: no cover - defensive
                f"sprint_ceiling must be > 1.0 to allow sprint overruns "
                f"(got {v}). Typical values: 2.0–5.0."
            )

        if v > 10.0:
            raise ValueError(  # pragma: no cover - defensive
                f"sprint_ceiling > 10.0 is unrealistic (got {v}). "
                f"Typical range: 2.0–5.0. Recommended max: 10.0."
            )

        # Get normalized uncertainty as decimal (0.0-1.0)
        sprint_uncertainty_decimal = info.data.get("sprint_uncertainty", 0.30)
        if sprint_uncertainty_decimal > 1.0:
            sprint_uncertainty_decimal = (
                sprint_uncertainty_decimal / 100.0
            )  # pragma: no cover - defensive

        # Warn if ceiling clips too much probability mass
        # For lognormal with σ: ~95% of samples fall within mean × exp(±2σ)
        typical_95_percentile = 1.0 + 2.0 * sprint_uncertainty_decimal
        if v < typical_95_percentile:
            import warnings

            warnings.warn(
                f"sprint_ceiling={v} is close to the 95% percentile of the "
                f"distribution (≈{typical_95_percentile:.2f}). "
                f"This will cap extreme scenarios. "
                f"Consider increasing to ≥{typical_95_percentile:.1f} for better tail accuracy.",
                UserWarning,
                stacklevel=2,
            )

        return v

    def get_uncertainty_decimal(self) -> float:
        """Return normalized uncertainty as decimal (e.g., 0.30 for 30%)."""
        if self.sprint_uncertainty > 1.0:
            return self.sprint_uncertainty / 100.0  # pragma: no cover - defensive
        return self.sprint_uncertainty


class CancellationConfig(BaseModel):
    """Rules for cancelling a feature when overrun exceeds threshold."""

    max_sprints_over_plan: int = Field(
        default=4,
        ge=1,
        description="Sprints over plan before cancellation is considered.",
    )
    cancellation_probability: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Probability of cancellation when overrun exceeds threshold.",
    )

    model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)


class DeliveryRiskConfig(BaseModel):
    """Configuration block for sprint-based delivery risk simulation.

    Models development overruns, cost escalation, and cancellation
    decisions using Monte Carlo simulation over sprint durations.

    Scenario sizing guidance:
    - 1_000      : development / fast iteration
    - 5_000      : default — stable metrics for daily use
    - 10_000     : production — board presentations
    - 100_000    : audit — reliable tail analysis (LaR 95%, CVaR)
    - 1_000_000  : risk management / regulatory sign-off
    """

    scenarios: int = Field(
        default=5000,
        ge=100,
        description=(
            "Number of Monte Carlo scenarios for delivery risk simulation. "
            "Higher values give more precise tail metrics at the cost of runtime. "
            "Overrides the global scenario.scenarios for delivery-specific analysis."
        ),
    )
    sprint_length_weeks: Literal[2] = Field(
        default=2,
        description="Sprint length is fixed to 2 weeks in delivery-risk simulation.",
    )
    quarterly_capacity_sprints: int = Field(
        default=6,
        ge=1,
        description="Available development capacity per quarter in full sprints.",
    )
    delay_model: DelayModelConfig = Field(default_factory=DelayModelConfig)
    cancellation: CancellationConfig = Field(default_factory=CancellationConfig)

    model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)
