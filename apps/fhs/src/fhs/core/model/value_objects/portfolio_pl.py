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

"""Portfolio P&L variant value objects.

Used by BlockchainCaseStudyService.portfolio_pl_variants() to present
combined portfolio net values under two accounting conventions:

- Variant 1 (cash-flow): BV − full development investment − year-1 opex
- Variant 2 (installment): BV − annual installment − year-1 opex
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PLVariantRow:
    """One row in the portfolio P&L variant table."""

    label: str  # "Best (P95)", "Mean (Expected)", "Floor (VaR 95%)", "Tail (CVaR 95%)"
    bv: float  # portfolio business value statistic in EUR
    v1_net: float  # bv − total_investment − total_opex
    v2_net: float  # bv − total_annual_installment − total_opex


@dataclass(frozen=True)
class PortfolioPLVariants:
    """Portfolio P&L variant view: 4 BV statistics × 2 cost variants."""

    rows: tuple[PLVariantRow, ...]
    total_investment: float
    total_annual_installment: float
    total_annual_opex: float
