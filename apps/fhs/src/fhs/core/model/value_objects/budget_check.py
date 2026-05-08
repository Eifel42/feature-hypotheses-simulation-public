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

"""Budget-check value objects for notebook decision snapshots."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureBudgetCheckRow:
    """Budget check details for one feature."""

    feature_key: str
    feature_name: str
    short_name: str
    development_cost: float
    budget_share: float
    fits_budget: bool


@dataclass(frozen=True)
class BudgetCheckResult:
    """Portfolio-level budget check summary for selected features."""

    rows: tuple[FeatureBudgetCheckRow, ...]
    budget: float
    total_cost: float
    budget_left: float
    budget_share: float
    fits_budget: bool
    small_buffer: bool
