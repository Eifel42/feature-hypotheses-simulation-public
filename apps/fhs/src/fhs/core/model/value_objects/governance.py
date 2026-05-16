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

"""Governance domain value objects: AssumptionMetadata, DecisionPolicy,
RiskAppetitePolicy, ModelCard.

These objects support Phase 2 of the industry-neutral positioning roadmap:
configurable decision rules, assumption quality tracking, and model governance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AssumptionConfidence(StrEnum):
    """Confidence level for an assumption input."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssumptionStatus(StrEnum):
    """Review status for an assumption input."""

    VALIDATED = "validated"
    REVIEWED = "reviewed"
    EXPERT_ESTIMATE = "expert-estimate"
    PLACEHOLDER = "placeholder"


@dataclass(frozen=True)
class AssumptionMetadata:
    """Per-parameter assumption provenance and quality metadata.

    Attached to feature input fields (e.g. conversion_rate, expected_users)
    to communicate how rigorously the estimate was derived.  Prevents the
    "garbage in, gauge out" false-confidence effect.

    Example YAML fragment::

        assumptions:
          conversion_rate:
            value: 0.22
            source: user research panel
            owner: product analytics
            confidence: medium
            status: reviewed
            last_reviewed: "2026-04-27"
    """

    source: str = ""
    owner: str = ""
    confidence: AssumptionConfidence = AssumptionConfidence.LOW
    status: AssumptionStatus = AssumptionStatus.PLACEHOLDER
    last_reviewed: str | None = None
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssumptionMetadata:
        """Construct from a raw YAML/dict mapping."""
        return cls(
            source=str(data.get("source", "")),
            owner=str(data.get("owner", "")),
            confidence=AssumptionConfidence(
                data.get("confidence", AssumptionConfidence.LOW)
            ),
            status=AssumptionStatus(data.get("status", AssumptionStatus.PLACEHOLDER)),
            last_reviewed=data.get("last_reviewed"),
            notes=str(data.get("notes", "")),
        )

    @property
    def is_decision_grade(self) -> bool:
        """True when the assumption is reviewed or validated — suitable for GO decisions."""
        return self.status in (
            AssumptionStatus.REVIEWED,
            AssumptionStatus.VALIDATED,
        )


class DecisionGrade(StrEnum):
    """Recommendation grade for a feature or portfolio."""

    GO = "GO"
    CONDITIONAL_GO = "Conditional GO"
    REVIEW = "Review"


@dataclass(frozen=True)
class DecisionPolicyResult:
    """Outcome of evaluating a DecisionPolicy against simulation results."""

    grade: DecisionGrade
    reasons: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.grade == DecisionGrade.GO


@dataclass(frozen=True)
class DecisionPolicy:
    """Product-Owner-facing decision thresholds.

    Maps simulation results to GO / Conditional GO / Review recommendations
    using plain business language.  The policy is loaded from scenario YAML::

        decision_policy:
          min_break_even_probability: 0.75
          min_bvf_ratio: 0.80
          require_assumption_status: reviewed

    All thresholds have conservative defaults so an unconfigured policy is
    still useful.
    """

    min_break_even_probability: float = 0.60
    min_bvf_ratio: float = 0.70
    require_assumption_status: AssumptionStatus | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionPolicy:
        status_raw = data.get("require_assumption_status")
        return cls(
            min_break_even_probability=float(
                data.get("min_break_even_probability", 0.60)
            ),
            min_bvf_ratio=float(data.get("min_bvf_ratio", 0.70)),
            require_assumption_status=(
                AssumptionStatus(status_raw) if status_raw else None
            ),
        )

    def evaluate(
        self,
        break_even_probability: float,
        bvf_95: float,
        expected_value: float,
        assumption_status: AssumptionStatus | None = None,
    ) -> DecisionPolicyResult:
        """Return a DecisionPolicyResult for the given simulation metrics."""
        reasons: list[str] = []
        fails = 0

        if break_even_probability < self.min_break_even_probability:
            reasons.append(
                f"Break-even probability {break_even_probability:.0%} is below "
                f"the minimum {self.min_break_even_probability:.0%}."
            )
            fails += 1

        if expected_value > 0:
            actual_ratio = bvf_95 / expected_value
            if actual_ratio < self.min_bvf_ratio:
                reasons.append(
                    f"Business Value Floor ratio {actual_ratio:.0%} is below "
                    f"the minimum {self.min_bvf_ratio:.0%}."
                )
                fails += 1

        if self.require_assumption_status and assumption_status:
            order = [
                AssumptionStatus.PLACEHOLDER,
                AssumptionStatus.EXPERT_ESTIMATE,
                AssumptionStatus.REVIEWED,
                AssumptionStatus.VALIDATED,
            ]
            if order.index(assumption_status) < order.index(
                self.require_assumption_status
            ):
                reasons.append(
                    f"Assumption status '{assumption_status.value}' does not meet "
                    f"the required '{self.require_assumption_status.value}'."
                )
                fails += 1

        if fails == 0:
            grade = DecisionGrade.GO
        elif fails == 1:
            grade = DecisionGrade.CONDITIONAL_GO
        else:
            grade = DecisionGrade.REVIEW

        return DecisionPolicyResult(grade=grade, reasons=tuple(reasons))


@dataclass(frozen=True)
class RiskAppetitePolicy:
    """Bank-grade extension of DecisionPolicy adding concentration and tail-risk limits.

    Adds CVaR-loss cap, cluster-concentration limit, and sunk-cost cap to the
    base break-even and BVF thresholds from DecisionPolicy.  Suitable for Risk
    Manager and Investment Committee use cases.

    YAML example::

        risk_appetite:
          min_break_even_probability: 0.75
          min_bvf_ratio: 0.80
          max_cvar_loss: 50000
          max_cluster_concentration: 0.40
          max_sunk_cost_at_cancellation: 30000
          require_assumption_status: reviewed
    """

    min_break_even_probability: float = 0.70
    min_bvf_ratio: float = 0.80
    max_cvar_loss: float | None = None
    max_cluster_concentration: float | None = None
    max_sunk_cost_at_cancellation: float | None = None
    require_assumption_status: AssumptionStatus | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskAppetitePolicy:
        status_raw = data.get("require_assumption_status")
        return cls(
            min_break_even_probability=float(
                data.get("min_break_even_probability", 0.70)
            ),
            min_bvf_ratio=float(data.get("min_bvf_ratio", 0.80)),
            max_cvar_loss=(
                float(data["max_cvar_loss"]) if "max_cvar_loss" in data else None
            ),
            max_cluster_concentration=(
                float(data["max_cluster_concentration"])
                if "max_cluster_concentration" in data
                else None
            ),
            max_sunk_cost_at_cancellation=(
                float(data["max_sunk_cost_at_cancellation"])
                if "max_sunk_cost_at_cancellation" in data
                else None
            ),
            require_assumption_status=(
                AssumptionStatus(status_raw) if status_raw else None
            ),
        )

    def as_decision_policy(self) -> DecisionPolicy:
        """Return a DecisionPolicy with matching thresholds for interop."""
        return DecisionPolicy(
            min_break_even_probability=self.min_break_even_probability,
            min_bvf_ratio=self.min_bvf_ratio,
            require_assumption_status=self.require_assumption_status,
        )

    def evaluate_portfolio(
        self,
        break_even_probability: float,
        bvf_95: float,
        expected_value: float,
        cvar_loss: float | None = None,
        cluster_concentration: float | None = None,
        sunk_cost: float | None = None,
        assumption_status: AssumptionStatus | None = None,
    ) -> DecisionPolicyResult:
        """Evaluate all risk appetite thresholds and return a graded result."""
        base_result = self.as_decision_policy().evaluate(
            break_even_probability, bvf_95, expected_value, assumption_status
        )
        extra_reasons: list[str] = []

        if (
            self.max_cvar_loss is not None
            and cvar_loss is not None
            and cvar_loss > self.max_cvar_loss
        ):
            extra_reasons.append(
                f"CVaR loss {cvar_loss:,.0f} exceeds risk appetite cap "
                f"{self.max_cvar_loss:,.0f}."
            )

        if (
            self.max_cluster_concentration is not None
            and cluster_concentration is not None
            and cluster_concentration > self.max_cluster_concentration
        ):
            extra_reasons.append(
                f"Cluster concentration {cluster_concentration:.0%} exceeds "
                f"the limit {self.max_cluster_concentration:.0%}."
            )

        if (
            self.max_sunk_cost_at_cancellation is not None
            and sunk_cost is not None
            and sunk_cost > self.max_sunk_cost_at_cancellation
        ):
            extra_reasons.append(
                f"Sunk cost at cancellation {sunk_cost:,.0f} exceeds "
                f"the cap {self.max_sunk_cost_at_cancellation:,.0f}."
            )

        all_reasons = base_result.reasons + tuple(extra_reasons)
        total_fails = len(all_reasons)
        if total_fails == 0:
            grade = DecisionGrade.GO
        elif total_fails == 1:
            grade = DecisionGrade.CONDITIONAL_GO
        else:
            grade = DecisionGrade.REVIEW

        return DecisionPolicyResult(grade=grade, reasons=all_reasons)


@dataclass(frozen=True)
class ModelCard:
    """Lightweight model governance artifact attached to simulation outputs.

    Every Decision Report should reference a ModelCard so stakeholders know
    which model produced the numbers, its approved use cases, and its limitations.
    Inspired by bank model governance requirements; intentionally lightweight
    for agile contexts.
    """

    model_name: str = "Feature Hypotheses Simulation"
    version: str = "1.0.0"
    purpose: str = (
        "Quantify business value uncertainty and downside risk for product backlog "
        "decisions using Monte Carlo simulation."
    )
    approved_use: tuple[str, ...] = field(
        default_factory=lambda: (  # type: ignore[assignment]
            "Feature prioritization under uncertainty",
            "Portfolio risk analysis (VaR, CVaR, stress tests)",
            "Budget optimization and frontier analysis",
            "Sprint planning with delivery risk quantification",
        )
    )
    limitations: tuple[str, ...] = field(
        default_factory=lambda: (  # type: ignore[assignment]
            "Inputs are expert estimates — output precision reflects input quality.",
            "Normal/Lognormal distributions may underestimate fat-tail outcomes.",
            "Development costs are point estimates (typical error ±30–50%).",
            "Single-user local tool — no multi-tenant audit trail.",
        )
    )
    validation_status: str = "Internal — not externally audited"
    owner: str = ""

    def summary_lines(self) -> list[str]:
        """Return a list of human-readable summary lines for report embedding."""
        lines = [
            f"**Model:** {self.model_name} v{self.version}",
            f"**Purpose:** {self.purpose}",
            f"**Validation status:** {self.validation_status}",
        ]
        if self.owner:
            lines.append(f"**Owner:** {self.owner}")
        lines.append("**Approved use:**")
        lines.extend(f"  - {u}" for u in self.approved_use)
        lines.append("**Limitations:**")
        lines.extend(f"  - {lim}" for lim in self.limitations)
        return lines
