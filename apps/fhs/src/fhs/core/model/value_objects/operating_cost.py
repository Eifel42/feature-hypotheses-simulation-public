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

"""Operating cost simulation value objects.

Captures the result of a Monte Carlo simulation of portfolio operating costs
with a shared cost inflation factor across all features.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class FeatureOperatingCostStats:
    """Operating cost statistics for a single feature.

    The same inflation factor (drawn from Uniform[0, inflation_max]) is used
    for all features in a scenario — shared infrastructure assumption.
    """

    feature_name: str
    base_annual_cost: float
    """Base annual operating cost from config (EUR/year), before inflation."""

    expected_cost: float
    """Expected annual cost = base × (1 + inflation_max / 2)."""

    worst_case_cost: float
    """Worst-case annual cost = base × (1 + inflation_max)."""

    scenarios: np.ndarray = field(compare=False, repr=False)
    """Per-scenario operating cost values (EUR/year)."""

    @property
    def cost_uplift_eur(self) -> float:
        """Maximum additional cost from inflation (worst case minus base)."""
        return self.worst_case_cost - self.base_annual_cost


@dataclass(frozen=True)
class OperatingCostResult:
    """Portfolio operating cost simulation result.

    One shared inflation factor is drawn from Uniform(0, inflation_max) per
    scenario and applied to every feature's ``annual_operating_cost``.
    This models a shared operational environment (local or cloud).
    """

    inflation_max: float
    """Maximum inflation rate configured for the scenario (e.g. 0.25 = 25%)."""

    inflation_scenarios: np.ndarray = field(compare=False, repr=False)
    """Per-scenario inflation factor — same draw applies to all features."""

    per_feature: dict[str, FeatureOperatingCostStats]
    """Per-feature cost statistics keyed by feature name."""

    @property
    def expected_inflation_pct(self) -> float:
        """Expected inflation rate as a percentage (0–100)."""
        return float(np.mean(self.inflation_scenarios)) * 100.0

    @property
    def portfolio_base_cost(self) -> float:
        """Sum of base annual operating costs across all features (EUR/year)."""
        return sum(s.base_annual_cost for s in self.per_feature.values())

    @property
    def portfolio_expected_cost(self) -> float:
        """Sum of expected annual operating costs across all features (EUR/year)."""
        return sum(s.expected_cost for s in self.per_feature.values())

    @property
    def portfolio_worst_case_cost(self) -> float:
        """Sum of worst-case annual operating costs across all features (EUR/year)."""
        return sum(s.worst_case_cost for s in self.per_feature.values())
