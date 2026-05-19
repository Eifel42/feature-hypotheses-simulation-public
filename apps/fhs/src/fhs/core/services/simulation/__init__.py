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

"""Simulation Domain Services."""

__all__ = [
    "FeatureSimulator",
    "PnLMultiYearService",
    "PortfolioMultiYearService",
]


# Lazy import to avoid circular dependency with monte_carlo
def __getattr__(name):
    if name == "FeatureSimulator":
        from .simulator import FeatureSimulator

        return FeatureSimulator
    if name == "PortfolioMultiYearService":
        from .portfolio_multi_year import PortfolioMultiYearService

        return PortfolioMultiYearService
    if name == "PnLMultiYearService":
        from .multi_year_pnl import PnLMultiYearService

        return PnLMultiYearService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
