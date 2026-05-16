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

"""Advisor-oriented value objects for advanced portfolio notebook flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .multi_year_result import MultiYearResult

from .optimization_result import OptimizationResult


@dataclass(frozen=True)
class FeatureRanking:
    """One ranked feature with risk and cost context."""

    feature: str
    expected_business_value: float
    var_95_business_value: float
    risk_ratio: float
    llp: float
    cost: float
    bv_cvar_business_value: float = 0.0
    loss_var: float = 0.0
    loss_cvar: float = 0.0
    rorac: float = 0.0
    risk_adjusted_roi: float = 0.0
    confidence_level: float = 0.95


@dataclass(frozen=True)
class FeatureRankingRow:
    """Board-ready ranking row with key, name, and multi-year payload."""

    key: str
    name: str
    expected_eur: float
    var95_eur: float
    cost: float
    multi_year: MultiYearResult


@dataclass(frozen=True)
class NegativeScoreFeature:
    """Individual var_floor score and ILP treatment for one feature."""

    feature: str
    cost: float
    var_95_business_value: float
    var_floor_score: float
    ilp_considers: bool


@dataclass(frozen=True)
class NegativeScoreComparisonRow:
    """Comparison row for all-features vs positive-score-only candidate sets."""

    candidate_set: str
    solver: str
    selected_features: tuple[str, ...]
    selected_count: int
    portfolio_var_95: float
    total_cost: float


@dataclass(frozen=True)
class NegativeScoreReport:
    """Structured result for ILP negative-score gap analysis."""

    scores: tuple[NegativeScoreFeature, ...]
    positive_features: tuple[str, ...]
    negative_features: tuple[str, ...]
    comparisons: tuple[NegativeScoreComparisonRow, ...]
    all_features_exact: OptimizationResult
    all_features_ilp: OptimizationResult
    positive_only_exact: OptimizationResult
    positive_only_ilp: OptimizationResult
    gap_exact_minus_ilp: float
    ilp_matches_exact: bool


@dataclass(frozen=True)
class StrategyCategoryCostRow:
    """Cost share by strategy category for selected features."""

    category: str
    cost: float
    share: float


@dataclass(frozen=True)
class BudgetRiskRow:
    """One budget-path row with floors and qualitative risk class."""

    label: str
    budget: float
    selected_count: int
    investment: float
    l1_floor: float
    l2_floor: float
    l3_floor: float
    l3_safety_buffer: float
    risk_class: str
