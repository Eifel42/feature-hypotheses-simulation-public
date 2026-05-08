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

"""Value objects for multi-dimensional executive decisions."""

from __future__ import annotations

from dataclasses import dataclass

# Decision signal constants
GO = "GO"
CONDITIONAL_GO = "CONDITIONAL_GO"
REVIEW = "REVIEW"


@dataclass(frozen=True)
class DecisionDimension:
    """One dimension of a multi-dimensional investment decision.

    Each dimension answers a different question about the portfolio:
    business value, financial return, portfolio optimization, risk profile,
    or delivery cost risk.
    """

    name: str
    signal: str  # GO, CONDITIONAL_GO, or REVIEW
    key_metric: str
    assessment: str


@dataclass(frozen=True)
class ExecutiveDecisionResult:
    """Aggregated recommendation from multiple decision dimensions.

    The overall signal follows governance rules:
    - GO: all dimensions show GO
    - REVIEW: two or more dimensions show REVIEW
    - CONDITIONAL_GO: everything else
    """

    dimensions: tuple[DecisionDimension, ...]
    overall_signal: str
    strengths: tuple[str, ...]
    attention_needed: tuple[str, ...]

    @property
    def go_count(self) -> int:
        return sum(1 for d in self.dimensions if d.signal == GO)

    @property
    def conditional_count(self) -> int:
        return sum(1 for d in self.dimensions if d.signal == CONDITIONAL_GO)

    @property
    def review_count(self) -> int:
        return sum(1 for d in self.dimensions if d.signal == REVIEW)


@dataclass(frozen=True)
class ScenarioComparison:
    """One row in a what-if scenario comparison."""

    label: str
    delivery_factor: float
    market_probability: float
    bv_after_risk: float
    net_profit: float
    profitable: bool


def aggregate_decision_signals(
    dimensions: tuple[DecisionDimension, ...],
) -> ExecutiveDecisionResult:
    """Aggregate multiple decision dimensions into a single recommendation.

    Governance rules:
    - GO: all dimensions show GO
    - REVIEW: two or more dimensions show REVIEW
    - CONDITIONAL_GO: everything else
    """
    signals = [d.signal for d in dimensions]
    go_count = signals.count(GO)
    review_count = signals.count(REVIEW)

    if review_count >= 2:
        overall = REVIEW
    elif go_count == len(dimensions):
        overall = GO
    else:
        overall = CONDITIONAL_GO

    strengths = tuple(d.name for d in dimensions if d.signal == GO)
    attention_needed = tuple(d.name for d in dimensions if d.signal != GO)

    return ExecutiveDecisionResult(
        dimensions=dimensions,
        overall_signal=overall,
        strengths=strengths,
        attention_needed=attention_needed,
    )
