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

"""Multi-year P&L value objects."""

from __future__ import annotations

from dataclasses import dataclass

from .risk_layer_stats import RiskLayerStats


@dataclass(frozen=True)
class MultiYearLayerYear:
    """One year in a multi-year risk layer."""

    year: int
    expected: float
    var_95: float
    cvar_95: float
    std: float


@dataclass(frozen=True)
class MultiYearLayer:
    """Layered portfolio outcome for the full horizon."""

    years: tuple[MultiYearLayerYear, ...]
    total_3y: RiskLayerStats
    npv: RiskLayerStats


@dataclass(frozen=True)
class MultiYearRiskProbabilities:
    """Applied risk probabilities for the simulation run."""

    risk_2: float
    risk_3: float
    component_portfolio: float


@dataclass(frozen=True)
class MultiYearPnLMeta:
    """Meta data and realized hit rates for a simulation run."""

    selected: tuple[str, ...]
    years: int
    probabilities: MultiYearRiskProbabilities
    delivery_hit_pct: dict[str, float]
    market_hit_pct_by_year: tuple[float, ...]
    global_hit_pct_by_year: tuple[float, ...]
    cluster_hit_pct_by_year: tuple[dict[str, float], ...]


@dataclass(frozen=True)
class MultiYearPnLResult:
    """Typed result for multi-year portfolio P&L risk simulation."""

    investment: float
    discount_rate: float
    base: MultiYearLayer
    risk1: MultiYearLayer
    risk2: MultiYearLayer
    component: MultiYearLayer
    risk3: MultiYearLayer
    meta: MultiYearPnLMeta
    installment_schedule: tuple[float, ...] = ()
    """Annual installment charge per year (EUR). Length == number of simulated years.
    installment_schedule[i] is the total installment cost charged in year i+1.
    After the installment period, the charge drops to 0."""
