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

"""Shapley attribution value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ShapleyContribution:
    """Risk contribution of one feature via Shapley values."""

    feature: str
    marginal_risk: float
    shapley_value: float
    risk_share_pct: float


@dataclass(frozen=True)
class ShapleyAttribution:
    """Complete Shapley risk attribution for a portfolio."""

    total_risk: float
    risk_metric: str  # "cvar_95" etc.
    contributions: tuple[ShapleyContribution, ...]
    selected_features: tuple[str, ...]


@dataclass(frozen=True)
class RiskFactorContribution:
    """Shapley contribution of one risk factor (delivery, market, component, global)."""

    risk: str
    contribution_eur: float
    share_of_total: float


@dataclass(frozen=True)
class RiskFactorShapley:
    """Shapley decomposition of risk factors for a portfolio."""

    metric: str
    confidence: float
    selected: tuple[str, ...]
    baseline_value_eur: float
    full_value_eur: float
    total_risk_eur: float
    contributions: tuple[RiskFactorContribution, ...]
    interaction_residual_eur: float
    subset_values_eur: dict[str, float]
