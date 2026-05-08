#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
Data models for Feature Hypotheses Simulation

Defines core data structures for feature risk analysis and simulation results.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Feature(BaseModel):
    """
    Represents a feature hypothesis for risk analysis.

    Attributes:
        name: Feature identifier/name
        expected_users: Expected number of users (must be positive)
        conversion_rate: Success rate (0.0-1.0)
        uncertainty: Relative uncertainty as decimal (0.0-1.0, e.g., 0.3 = ±30%)
        business_value_per_conversion: Business value per conversion
            (e.g., EUR income or internal company value per conversion)
        development_cost: Development cost to implement feature (e.g., EUR)
        likelihood_of_non_delivery: Risk that feature is not delivered (0.0-1.0)
        dependency_cluster: Optional dependency cluster identifier
            (e.g., "Team Alpha", "Payment API", "Power Users")
        planned_release: Optional release identifier (e.g., "R3")
        acceptance_model: How user acceptance is modeled in simulation:
            - "rate": continuous acceptance-rate simulation (legacy behavior)
            - "binomial": per-user yes/no acceptance simulation
    """

    name: str = Field(..., min_length=1, description="Feature name")
    expected_users: int = Field(..., gt=0, description="Expected number of users")
    conversion_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Conversion rate (0-1)"
    )
    uncertainty: float = Field(
        ..., ge=0.0, le=1.0, description="Uncertainty level (0-1)"
    )
    business_value_per_conversion: float = Field(
        default=1.0,
        description=(
            "Business value per conversion "
            "(e.g., EUR income or internal company value per conversion)"
        ),
    )
    development_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Development cost to implement feature (e.g., EUR)",
    )
    installment_years: int = Field(
        default=1,
        ge=1,
        le=30,
        description=(
            "Number of annual installments for the development cost (straight-line). "
            "Default 1 = full cost charged in year 1. "
            "Example: 3 = cost spread equally over 3 annual installments (EUR/year)."
        ),
    )
    development_weeks: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Estimated development duration in working weeks (optional). "
            "Required for sprint capacity planning via "
            "PortfolioAdvisor.optimize_portfolio_by_sprint()."
        ),
    )
    annual_growth_rate: float = Field(
        default=0.0,
        ge=-1.0,
        le=5.0,
        description=(
            "Annual business value growth rate (e.g., 0.15 = 15% YoY growth). "
            "Used by multi-year Monte Carlo simulation."
        ),
    )
    likelihood_of_non_delivery: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Likelihood that feature is not delivered (0.0-1.0)",
    )
    dependency_cluster: str | None = Field(
        default=None,
        description=(
            "Dependency cluster identifier for correlation modeling "
            "(e.g., 'Team Alpha', 'Payment API', 'Power Users')"
        ),
    )
    planned_release: str | None = Field(
        default=None,
        description="Planned release identifier (e.g., 'R3')",
    )
    acceptance_model: str = Field(
        default="rate",
        description=(
            "User-acceptance simulation model: "
            "'rate' (continuous) or 'binomial' (per-user yes/no acceptance)."
        ),
    )
    annual_operating_cost: float = Field(
        default=0.0,
        ge=0.0,
        description=(
            "Annual cost to run this feature in production (EUR/year). "
            "Covers hosting, cloud infrastructure, licenses, and support. "
            "Net business value = business value - operating cost."
        ),
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        arbitrary_types_allowed=False,
    )

    # noinspection PyNestedDecoratorsInspection
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate that name is not empty or whitespace-only"""
        if not v or not v.strip():
            raise ValueError("Feature name cannot be empty or whitespace")
        return v.strip()

    # noinspection PyNestedDecoratorsInspection
    @field_validator("expected_users")
    @classmethod
    def validate_expected_users(cls, v: int) -> int:
        """Validate expected_users is positive"""
        if v <= 0:
            raise ValueError(
                f"Expected users must be positive. Got {v}. Use a value > 0."
            )
        return v

    # noinspection PyNestedDecoratorsInspection
    @field_validator("conversion_rate")
    @classmethod
    def conversion_rate_precision(cls, v: float) -> float:
        """Validate conversion rate precision and range"""
        if v < 0.0 or v > 1.0:
            raise ValueError(
                f"Conversion rate must be between 0.0 and 1.0. Got {v}. "
                f"Valid range: [0.0, 1.0]"
            )
        # Round to 4 decimal places
        return round(v, 4)

    # noinspection PyNestedDecoratorsInspection
    @field_validator("uncertainty")
    @classmethod
    def uncertainty_precision(cls, v: float) -> float:
        """Validate uncertainty precision and range"""
        if v < 0.0 or v > 1.0:
            raise ValueError(
                f"Uncertainty must be between 0.0 and 1.0. Got {v}. "
                f"Valid range: [0.0, 1.0]. Example: 0.3 means ±30%"
            )
        # Round to 4 decimal places
        return round(v, 4)

    # noinspection PyNestedDecoratorsInspection
    @field_validator("acceptance_model")
    @classmethod
    def validate_acceptance_model(cls, v: str) -> str:
        """Validate acceptance-model selection."""
        allowed = {"rate", "binomial"}
        if v not in allowed:
            raise ValueError(
                f"acceptance_model must be one of {sorted(allowed)}. Got '{v}'."
            )
        return v

    def __str__(self) -> str:
        """String representation"""
        return (
            f"Feature(name={self.name}, users={self.expected_users}, "
            f"conversion_rate={self.conversion_rate}, uncertainty={self.uncertainty})"
        )

    def get_base_annual_business_value(self) -> float:
        """Deterministic Year-0 business value base.

        Returns:
            expected_users × conversion_rate × business_value_per_conversion
        """
        return (
            self.expected_users
            * self.conversion_rate
            * self.business_value_per_conversion
        )

    @property
    def year1_business_value_at_risk(self) -> float:
        """
        Year-1 Business Value at Risk (Y1 BVaR).

        Expected business value loss in the first 12 months after release if a feature
        is not delivered and users churn or reduce usage.

        Calculated as: get_base_annual_business_value() × likelihood_of_non_delivery

        Returns:
            float: Y1 BVaR value
        """
        return self.get_base_annual_business_value() * self.likelihood_of_non_delivery

    @property
    def year1_profit_at_risk(self) -> float:
        """
        Year-1 Profit at Risk (Y1 PaR).

        Expected profit loss in the first 12 months after release if a feature
        is not delivered and users churn or reduce usage.

        Calculated as:
        (get_base_annual_business_value() - development_cost) × likelihood_of_non_delivery

        Returns:
            float: Y1 PaR value
        """
        profit = max(0.0, self.get_base_annual_business_value() - self.development_cost)
        return profit * self.likelihood_of_non_delivery

    @property
    def annual_installment(self) -> float:
        """Annual installment of development cost (straight-line).

        Returns:
            development_cost / installment_years
            (equals development_cost when installment_years == 1, the default)
        """
        return self.development_cost / self.installment_years

    def get_risk_category(self, metric: str = "business_value") -> str:
        """
        Get risk category (Low/Medium/High) for this feature.

        Args:
            metric: Either "business_value" or "profit"

        Returns:
            str: "Low", "Medium", or "High"
        """
        value = (
            self.year1_business_value_at_risk
            if metric == "business_value"
            else self.year1_profit_at_risk
        )

        # Simple thresholds - can be customized
        if value < 50000:
            return "Low"
        elif value < 150000:
            return "Medium"
        else:
            return "High"
