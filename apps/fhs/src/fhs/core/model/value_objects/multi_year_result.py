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

"""MultiYearResult Value Object — per-year Monte Carlo distributions."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class YearResult:
    """Simulation result for a single year."""

    year: int
    scenarios: np.ndarray
    expected: float
    var_95: float
    cvar_95: float
    p95: float
    std: float

    @property
    def spread_pct(self) -> float:
        """Spread as pct of expected: (P95 - VaR95) / expected × 100."""
        if self.expected == 0:
            return 0.0
        return (self.p95 - self.var_95) / self.expected * 100

    @classmethod
    def from_scenarios(cls, year: int, scenarios: np.ndarray) -> YearResult:
        """Factory method to construct YearResult from numpy array.

        Eliminates DRY violations across Application Services.

        Args:
            year: Year number
            scenarios: Monte Carlo scenarios (numpy array)

        Returns:
            YearResult with calculated statistics
        """
        if len(scenarios) == 0:
            return cls(
                year=year,
                scenarios=np.array([], dtype=float),
                expected=0.0,
                var_95=0.0,
                cvar_95=0.0,
                p95=0.0,
                std=0.0,
            )

        var_95 = float(np.percentile(scenarios, 5))
        tail = scenarios[scenarios <= var_95]
        cvar_95 = float(np.mean(tail)) if len(tail) > 0 else var_95

        return cls(
            year=year,
            scenarios=scenarios,
            expected=float(np.mean(scenarios)),
            var_95=var_95,
            cvar_95=cvar_95,
            p95=float(np.percentile(scenarios, 95)),
            std=float(np.std(scenarios)),
        )


@dataclass(frozen=True)
class MultiYearResult:
    """Pure data container for multi-year Monte Carlo results.

    Holds per-year distributions and a discount rate.
    All aggregate calculations (3Y totals, NPV) live in
    :class:`FinancialCalculator`.
    """

    feature_name: str
    years: list[YearResult] = field(default_factory=list)
    discount_rate: float = 0.10
