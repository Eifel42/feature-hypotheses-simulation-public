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

"""RiskMetric Value Object — VaR and CVaR at a confidence level.

This model represents gain-convention risk pairs where ``cvar <= var``.
For feature-ranking views that need both gain and loss conventions plus
normalized metrics, use ``FeatureRankingMetrics``.
"""

from pydantic import BaseModel, Field, field_validator


class RiskMetric(BaseModel):
    """
    Risk Metric Value Object.

    Represents Value at Risk (VaR) and Conditional Value at Risk (CVaR)
    at a specific confidence level.
    """

    var: float = Field(..., description="Value at Risk")
    cvar: float = Field(
        ..., description="Conditional Value at Risk (Expected Shortfall)"
    )
    confidence_level: float = Field(
        default=0.95, ge=0.0, le=1.0, description="Confidence level (e.g., 0.95 = 95%)"
    )

    model_config = {"frozen": True}  # Immutable

    # noinspection PyNestedDecoratorsInspection
    @field_validator("cvar")
    @classmethod
    def cvar_must_be_less_than_or_equal_to_var(cls, v, info):
        """CVaR must be <= VaR (worst-case tail is always worse than percentile)."""
        var_value = info.data.get("var")
        if var_value is not None and v > var_value:
            raise ValueError(f"CVaR ({v}) must be <= VaR ({var_value})")
        return v

    def is_acceptable(self, threshold: float) -> bool:
        """Check if VaR is above acceptable threshold."""
        return self.var >= threshold

    def __str__(self) -> str:
        cl = int(self.confidence_level * 100)
        return f"VaR{cl}={self.var:,.0f}, CVaR{cl}={self.cvar:,.0f}"
