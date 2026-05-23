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

"""Financial view value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NpvSummary:
    """NPV analysis summary."""

    expected: float
    var_95: float
    p95: float
    std: float


@dataclass(frozen=True)
class IrrSummary:
    """IRR analysis summary."""

    expected: float
    floor: float
    ceiling: float


@dataclass(frozen=True)
class NpvAssessment:
    """Decision assessment for NPV business-case interpretation."""

    verdict: str
    primary_message: str
    downside_message: str | None
    positive_expected: bool
    downside_risk: bool


@dataclass(frozen=True)
class IrrAssessment:
    """Decision assessment for IRR versus cost-of-capital interpretation."""

    verdict: str
    primary_message: str
    downside_message: str | None
    margin_to_discount_rate: float
    expected_above_hurdle: bool
    downside_below_hurdle: bool


@dataclass(frozen=True)
class FinancialViewResult:
    """Combined financial view of a portfolio (NPV, IRR, 3Y totals)."""

    npv_expected: float
    npv_floor: float
    npv_ceiling: float
    irr_expected: float
    irr_floor: float
    irr_ceiling: float
    total_3y_expected: float
    total_3y_floor: float
