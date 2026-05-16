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

"""Compact portfolio snapshot value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioSnapshot:
    """Compact snapshot for a portfolio or subset."""

    expected: float
    var_95: float
    cvar_95: float
    std_dev: float
    investment: float

    @property
    def safety_buffer(self) -> float:
        """Business value floor minus investment cost."""
        return self.var_95 - self.investment

    @property
    def roi(self) -> float:
        """Expected ROI based on annual expected value."""
        if self.investment <= 0:
            return 0.0
        return (self.expected - self.investment) / self.investment
