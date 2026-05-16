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

"""FeatureRankingMetrics value object — multi-view risk metrics for ranking.

Provides both gain-convention (BV-Floor) and loss-convention (VaR-Loss) views
plus normalized ranking metrics so that Product Owners, Risk Managers and CFO
can each work with their preferred metric without reinterpreting the numbers.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FeatureRankingMetrics(BaseModel):
    """Risk metrics for a single feature, suitable for ranking comparisons.

    Contains:
      - Gain convention: ``bv_var`` (BV-floor), ``bv_cvar`` (tail mean).
      - Loss convention: ``loss_var`` (loss vs. expected), ``loss_cvar`` (tail loss).
      - Normalized metrics: ``risk_ratio`` (relative drawdown ∈ [0, 1]),
        ``rorac`` (return per € risk), ``risk_adjusted_roi`` (floor per € cost).

    All fields are floats and the object is immutable.
    """

    feature_name: str = Field(..., min_length=1)
    confidence_level: float = Field(..., ge=0.0, le=1.0)

    expected_bv: float
    bv_var: float
    bv_cvar: float

    loss_var: float = Field(..., ge=0.0)
    loss_cvar: float = Field(..., ge=0.0)

    risk_ratio: float = Field(..., ge=0.0, le=1.0)
    rorac: float
    risk_adjusted_roi: float

    model_config = ConfigDict(frozen=True, validate_default=True)

    @model_validator(mode="after")
    def _check_conventions(self) -> FeatureRankingMetrics:
        if self.bv_cvar > self.bv_var:
            raise ValueError(
                f"bv_cvar ({self.bv_cvar}) must be <= bv_var ({self.bv_var}) "
                "in gain convention"
            )
        if self.loss_cvar < self.loss_var:
            raise ValueError(
                f"loss_cvar ({self.loss_cvar}) must be >= loss_var "
                f"({self.loss_var}) in loss convention"
            )
        return self
