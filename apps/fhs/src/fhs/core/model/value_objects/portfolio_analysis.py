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

"""Portfolio analysis value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioMetrics:
    """Portfolio-level risk metrics."""

    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    expected_value: float
    std_dev: float


@dataclass(frozen=True)
class IndividualRiskMetrics:
    """Single-feature risk metrics used in portfolio decomposition."""

    var_95: float
    cvar_95: float
    mean: float
    std: float


@dataclass(frozen=True)
class DiversificationMetrics:
    """Diversification effect metrics for a portfolio."""

    weighted_individual_var: float
    portfolio_var: float
    diversification_benefit: float
    diversification_ratio: float


@dataclass(frozen=True)
class PortfolioRiskResult:
    """Typed result of portfolio risk analysis."""

    portfolio_metrics: PortfolioMetrics
    individual_risks: dict[str, IndividualRiskMetrics]
    diversification: DiversificationMetrics
    weights: dict[str, float]
    n_features: int


@dataclass(frozen=True)
class CorrelationPair:
    """One feature-pair correlation with features identified."""

    value: float
    features: tuple[str, str]


@dataclass(frozen=True)
class CorrelationStatistics:
    """Summary statistics for portfolio correlation matrix."""

    average_correlation: float
    max_correlation: CorrelationPair
    min_correlation: CorrelationPair


@dataclass(frozen=True)
class CorrelationResult:
    """Typed result of correlation matrix analysis."""

    correlation_matrix: list[list[float]]
    p_value_matrix: list[list[float]]
    feature_names: list[str]
    statistics: CorrelationStatistics


@dataclass(frozen=True)
class RiskContributionResult:
    """Risk contribution decomposition for a portfolio."""

    baseline_risk: float
    risk_metric: str
    risk_contributions: dict[str, float]
    marginal_risks: dict[str, float]
    percentage_contributions: dict[str, float]
    weights: dict[str, float]
