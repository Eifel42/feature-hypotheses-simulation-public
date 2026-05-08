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

"""OptimizationResult value object for portfolio optimization output."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationResult:
    """Output of an optimization run in AdvancedPortfolioService."""

    recommended_features: tuple[str, ...]
    total_cost: float
    portfolio_expected: float
    portfolio_var_95: float
    portfolio_cvar_95: float
    portfolio_std_dev: float
    budget: float
    budget_remaining: float
    computation_time_sec: float
    combinations_evaluated: int
    solver: str
    strategy: str
    portfolio_roi: float
    roi: float
    safety_buffer: float
    message: str
    metadata: dict[str, object]

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)
